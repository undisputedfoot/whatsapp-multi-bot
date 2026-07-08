"""
WhatsApp Web engine built on Playwright.
Uses Store injection + DOM interaction for reliable message handling.
"""

import asyncio
import json
import base64
import re
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, TimeoutError

from .config import BROWSER_MODE, CHROME_WS, SESSION_DIR


# ──────────────────────────────────────────────
#  JS injection payload — hooks into WhatsApp's
#  internal webpack module store.
# ──────────────────────────────────────────────

STORE_INJECT_JS = """
// Store reference
window.__WA_STORE = null;
window.__WA_MSGS = [];
window.__WA_CALLS = [];
window.__WA_QR = null;
window.__WA_READY = false;
window.__WA_GROUP_EVENTS = [];  // {type: 'join'|'leave', groupId, peer, by}

// Find WhatsApp's internal Store via webpack
(function findStore() {
    const webpack = window.webpackChunkwhatsapp_web_client;
    if (!webpack) { setTimeout(findStore, 1000); return; }

    // Push a dummy chunk to get the module cache
    const exportsCache = {};
    webpack.push([
        [Symbol('wa')], {},
        function(e) {
            Object.keys(e.c).forEach((mod) => {
                const m = e.c[mod];
                if (m && m.exports && m.exports.__esModule) {
                    Object.keys(m.exports).forEach((k) => {
                        if (k === 'default' && m.exports.default && m.exports.default.Chat) {
                            exportsCache['Store'] = m.exports.default;
                        }
                    });
                }
            });
        }
    ]);

    // Also try to find by scanning exports
    try {
        const scan = (obj, depth=0) => {
            if (depth > 5 || !obj || typeof obj !== 'object') return;
            if (obj.Chat && obj.Msg && obj.Contact) {
                window.__WA_STORE = obj;
                return;
            }
            if (Array.isArray(obj)) {
                obj.forEach(i => scan(i, depth+1));
                return;
            }
            Object.values(obj).forEach(v => scan(v, depth+1));
        };

        Object.values(webpack.c || {}).forEach(m => {
            if (m && m.exports) scan(m.exports);
        });
    } catch(e) {}

    // Fallback: try attaching to the Store from the global scope
    if (!window.__WA_STORE) {
        // Look for it in common locations
        for (const key of ['Store', 'store', 'WAMyStore', 'WapStore']) {
            if (window[key] && window[key].Chat) {
                window.__WA_STORE = window[key];
                break;
            }
        }
    }

    if (window.__WA_STORE) {
        console.log('WA Store found ✅');

        // Listen for new messages
        try {
            window.__WA_STORE.Msg.on('add', (msg) => {
                if (!msg.fromMe && msg.body) {
                    window.__WA_MSGS.push({
                        id: msg.id?._serialized || '',
                        from: msg.from?.user || msg.from?._serialized || '',
                        body: msg.body,
                        type: msg.type || 'chat',
                        timestamp: msg.t || Math.floor(Date.now()/1000),
                        chatId: msg.id?.remote || '',
                        isGroup: msg.id?.remote?.includes('-') || false,
                    });
                }
                // Detect group participant changes
                if (msg.type === 'gp2' || msg.type === 'group') {
                    try {
                        const sub = msg.subtype || '';
                        if (sub === 'add' || sub === 'invite' || msg.body?.includes('added') || msg.body?.includes('joined')) {
                            window.__WA_GROUP_EVENTS.push({
                                type: 'join',
                                groupId: msg.id?.remote || '',
                                peer: msg.from?.user || '',
                                by: msg.author?.user || msg.t === '0' ? 'invite' : '',
                                body: msg.body || ''
                            });
                        } else if (sub === 'remove' || sub === 'leave' || msg.body?.includes('left') || msg.body?.includes('removed')) {
                            window.__WA_GROUP_EVENTS.push({
                                type: 'leave',
                                groupId: msg.id?.remote || '',
                                peer: msg.from?.user || '',
                                by: msg.author?.user || '',
                                body: msg.body || ''
                            });
                        }
                    } catch(e) {}
                }
            });
        } catch(e) {
            console.log('Msg listener error:', e);
        }

        // Listen for calls
        try {
            window.__WA_STORE.Call.on('add', (call) => {
                window.__WA_CALLS.push({
                    id: call.id || '',
                    from: call.from?.user || call.peerJid || '',
                    status: call.status || 'ringing',
                    isVideo: call.isVideo || false,
                });
            });
        } catch(e) {}

        window.__WA_READY = true;
    } else {
        console.log('WA Store not found, will retry...');
        setTimeout(findStore, 3000);
    }
})();

// QR code capture
setInterval(() => {
    const canvas = document.querySelector('canvas');
    if (canvas && canvas.toDataURL) {
        window.__WA_QR = canvas.toDataURL();
    }
}, 2000);
"""

# ──────────────────────────────────────────────
#  Browser lifecycle
# ──────────────────────────────────────────────

_browser: Browser | None = None
_playwright = None


async def get_browser():
    global _browser, _playwright
    if _browser and _browser.is_connected():
        return _browser
    _playwright = await async_playwright().start()
    if BROWSER_MODE == "remote" and CHROME_WS:
        _browser = await _playwright.chromium.connect_over_cdp(CHROME_WS)
    else:
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
            ],
        )
    return _browser


# ──────────────────────────────────────────────
#  Session wrapper
# ──────────────────────────────────────────────

class WApp:
    """One Playwright page = one WhatsApp account."""

    def __init__(self, name: str, on_qr=None, on_ready=None, on_msg=None, on_call=None,
                 on_group_event=None):
        self.name = name
        self._context = None
        self.page: Page | None = None
        self.connected = False
        self._on_qr = on_qr
        self._on_ready = on_ready
        self._on_msg = on_msg
        self._on_call = on_call
        self._on_group_event = on_group_event
        self._stop = False
        self._qr_sent = False
        self._last_msg_count = 0

    async def start(self):
        # Use persistent context for saved sessions
        self._context = await _playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR / self.name),
            headless=True,
            viewport={"width": 800, "height": 600},
            locale="en-US",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
            ],
        )
        self.page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

        # Inject the Store hook script
        await self.page.evaluate(STORE_INJECT_JS)

        # Start watchers
        asyncio.create_task(self._auth_loop())
        asyncio.create_task(self._message_poll())
        asyncio.create_task(self._call_poll())
        asyncio.create_task(self._group_event_poll())
        return self

    async def stop(self):
        self._stop = True
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        try:
            if self.page:
                await self.page.close()
        except Exception:
            pass

    # ── Auth ──────────────────────────────────

    async def _auth_loop(self):
        """Wait for QR or ready, emit callbacks."""
        page = self.page
        while not self._stop:
            try:
                # Check if already logged in (restored session via user data dir)
                try:
                    chat_list = await page.wait_for_selector(
                        "div[data-testid='chat-list']", timeout=3000
                    )
                    if chat_list:
                        if not self.connected:
                            self.connected = True
                            # Inject store again now that page is fully loaded
                            await page.evaluate(STORE_INJECT_JS)
                            if self._on_ready:
                                await self._safe_call(self._on_ready)
                        await asyncio.sleep(3)
                        continue
                except TimeoutError:
                    pass

                # Check QR code
                qr = await page.evaluate("window.__WA_QR || null")
                if qr and not self._qr_sent:
                    self._qr_sent = True
                    if self._on_qr:
                        await self._safe_call(self._on_qr, qr)
                elif qr and self._qr_sent:
                    # QR still there, but might have been scanned
                    # Check for the main UI once in a while
                    try:
                        await page.wait_for_selector(
                            "div[data-testid='chat-list']", timeout=1000
                        )
                        self.connected = True
                        await page.evaluate(STORE_INJECT_JS)
                        if self._on_ready:
                            await self._safe_call(self._on_ready)
                        continue
                    except TimeoutError:
                        pass
                else:
                    # No QR = page still loading
                    await asyncio.sleep(2)
                    continue

            except Exception:
                pass

            await asyncio.sleep(2)

    # ── Message polling ───────────────────────

    async def _message_poll(self):
        while not self._stop:
            if self.connected and self.page:
                try:
                    count = await self.page.evaluate("window.__WA_MSGS.length")
                    while self._last_msg_count < count:
                        msg = await self.page.evaluate(
                            f"window.__WA_MSGS[{self._last_msg_count}]"
                        )
                        self._last_msg_count += 1
                        if msg and msg.get("body") and self._on_msg:
                            await self._safe_call(self._on_msg, msg)
                except Exception:
                    pass
            await asyncio.sleep(1.5)

    async def _call_poll(self):
        while not self._stop:
            if self.connected and self.page:
                try:
                    calls = await self.page.evaluate(
                        "(() => { const c = [...window.__WA_CALLS]; "
                        "window.__WA_CALLS.length = 0; return c; })()"
                    )
                    for call in calls:
                        if self._on_call:
                            await self._safe_call(self._on_call, call)
                except Exception:
                    pass
            await asyncio.sleep(2)

    async def _group_event_poll(self):
        while not self._stop:
            if self.connected and self.page:
                try:
                    events = await self.page.evaluate(
                        "(() => { const e = [...window.__WA_GROUP_EVENTS]; "
                        "window.__WA_GROUP_EVENTS.length = 0; return e; })()"
                    )
                    for evt in events:
                        if self._on_group_event:
                            await self._safe_call(self._on_group_event, evt)
                except Exception:
                    pass
            await asyncio.sleep(2)

    # ── Actions ───────────────────────────────

    async def send_text(self, to: str, text: str):
        """Send a message by navigating to the wa.me link and pressing Enter."""
        if not self.page or not self.connected:
            return False
        try:
            await self.page.goto(
                f"https://web.whatsapp.com/send?phone={to}&text={text}",
                wait_until="domcontentloaded", timeout=15000,
            )
            await asyncio.sleep(3)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1)
            return True
        except Exception:
            return False

    async def send_text_dom(self, to: str, text: str):
        """Send message by searching chat, clicking, typing, and pressing Enter.
        More reliable than navigating to send URL."""
        if not self.page or not self.connected:
            return False
        try:
            # Use the search box to find the contact
            search = self.page.locator("div[contenteditable='true'][data-tab='3']")
            if await search.count():
                await search.click()
                await search.fill(to)
                await asyncio.sleep(2)

                # Click the first result
                result = self.page.locator("div[data-testid='chat-list'] > div").first
                if await result.count():
                    await result.click()
                    await asyncio.sleep(1)

                    # Type message
                    msg_box = self.page.locator("div[contenteditable='true'][data-tab='10']")
                    if await msg_box.count():
                        await msg_box.fill(text)
                        await asyncio.sleep(0.5)
                        await self.page.keyboard.press("Enter")
                        await asyncio.sleep(1)
                        return True
            return False
        except Exception:
            return False

    async def send_image(self, to: str, image_path: str, caption: str = ""):
        """Send an image via the attachment menu."""
        if not self.page:
            return False
        try:
            await self.page.goto(
                f"https://web.whatsapp.com/send?phone={to}",
                wait_until="domcontentloaded", timeout=15000,
            )
            await asyncio.sleep(3)

            file_input = self.page.locator('input[accept*="image"], input[type="file"]')
            if await file_input.count():
                await file_input.set_input_files(image_path)
                await asyncio.sleep(2)
                if caption:
                    await self.page.keyboard.type(caption)
                    await asyncio.sleep(1)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1)
                return True
            return False
        except Exception:
            return False

    async def mark_seen(self, chat_id: str):
        """Send read receipt via Store if available."""
        try:
            await self.page.evaluate(f"""
                try {{
                    window.__WA_STORE?.sendSeen?.('{chat_id}');
                }} catch(e) {{}}
            """)
        except Exception:
            pass

    async def reject_call(self, call_id: str):
        """Reject incoming call via Store if available."""
        try:
            await self.page.evaluate(f"""
                try {{
                    window.__WA_STORE?.rejectCall?.('{call_id}');
                }} catch(e) {{}}
            """)
        except Exception:
            pass

    async def get_qr_data(self) -> str | None:
        """Get current QR code as data URL."""
        try:
            return await self.page.evaluate("window.__WA_QR || null")
        except Exception:
            return None

    async def get_chat_list(self) -> list[dict]:
        """Get recent chats from the sidebar."""
        chats = []
        try:
            items = self.page.locator("div[data-testid='chat-list'] > div")
            count = await items.count()
            for i in range(min(count, 50)):
                name_el = items.nth(i).locator("span[dir='auto']").first
                name = await name_el.text_content() if await name_el.count() else "?"
                chats.append({"name": name or "?", "index": i})
            return chats
        except Exception:
            return chats

    @staticmethod
    async def _safe_call(fn, *args):
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(*args)
            else:
                fn(*args)
        except Exception:
            pass
