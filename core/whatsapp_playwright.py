"""
WhatsApp Web engine built on Playwright (desktop).
Uses Store injection + persistent context for reliable messaging.
"""

import asyncio
from playwright.async_api import async_playwright, Page, TimeoutError

from .config import SESSION_DIR


# ── JS injection: hooks into WhatsApp's webpack Store ──

STORE_INJECT_JS = """
window.__WA_STORE = null;
window.__WA_MSGS = [];
window.__WA_CALLS = [];
window.__WA_QR = null;
window.__WA_READY = false;
window.__WA_GROUP_EVENTS = [];

(function findStore() {
    var wp = window.webpackChunkwhatsapp_web_client || window.webpackChunkwhatsapp;
    if (!wp) { setTimeout(findStore, 2000); return; }
    try {
        for (var key in wp.c) {
            var m = wp.c[key];
            if (!m || m.__scanned) continue;
            m.__scanned = true;
            (function scan(obj, depth) {
                if (depth > 8 || !obj || typeof obj !== 'object') return;
                try {
                    // Look for any object with common WhatsApp store methods
                    var keys = Object.keys(obj);
                    if (keys.length > 3 && keys.length < 30) {
                        // Check if it has model-like properties
                        var hasModel = false, hasEvents = false;
                        for (var k of keys) {
                            if (k === 'models' || k === 'Model') hasModel = true;
                            if (k === 'on' || k === 'emit') hasEvents = true;
                        }
                        // More specific: look for collections with models that have Chat/Msg
                        if (obj.models && typeof obj.models === 'object') {
                            var modelKeys = Object.keys(obj.models);
                            if (modelKeys.length >= 3) {
                                window.__WA_STORE = obj;
                                window.__WA_STORE_FOUND = true;
                                return;
                            }
                        }
                    }
                    if (Array.isArray(obj)) { obj.forEach(function(i) { scan(i, depth+1); }); return; }
                    for (var k in obj) { try { scan(obj[k], depth+1); } catch(e) {} }
                } catch(e) {}
            })(m.exports, 0);
            if (window.__WA_STORE) break;
        }
    } catch(e) {}
    if (!window.__WA_STORE) {
        for (var key of ['Store', 'store', 'WAMyStore', 'WapStore', 'WPP', 'WWebJS']) {
            try {
                var s = window[key];
                if (s && typeof s === 'object' && Object.keys(s).length > 5) {
                    // Check if this could be the store
                    for (var k in s) {
                        if (s[k] && typeof s[k] === 'object' && s[k].models) {
                            window.__WA_STORE = s;
                            window.__WA_STORE_FOUND = true;
                            break;
                        }
                    }
                    if (window.__WA_STORE) break;
                }
            } catch(e) {}
        }
    }
    if (window.__WA_STORE) {
        try {
            var store = window.__WA_STORE;
            // Try to find the Msg collection
            var msgCollection = null;
            for (var k in store) {
                if (store[k] && typeof store[k] === 'object' && typeof store[k].on === 'function') {
                    // Check if this looks like a message collection
                    var sk = Object.keys(store[k]);
                    if (sk.indexOf('add') >= 0 || sk.indexOf('models') >= 0) {
                        msgCollection = store[k];
                        break;
                    }
                }
            }
            if (!msgCollection) {
                // Try common names
                for (var name of ['Msg', 'msg', 'Message', 'message', 'Chat', 'chat']) {
                    if (store[name] && typeof store[name].on === 'function') {
                        msgCollection = store[name];
                        break;
                    }
                }
            }
            if (msgCollection && typeof msgCollection.on === 'function') {
                msgCollection.on('add', function(msg) {
                    try {
                        var body = msg.body || msg.bodyText || '';
                        var from = msg.from ? (msg.from.user || msg.from._serialized || '') : '';
                        var chatId = msg.id ? (msg.id.remote || '') : '';
                        if (!msg.fromMe && body) {
                            window.__WA_MSGS.push({
                                id: msg.id?._serialized || msg.id || '',
                                from: from, body: body,
                                chatId: chatId || from,
                            });
                        }
                    } catch(e) {}
                });
            }
        } catch(e) {}
        window.__WA_READY = true;
    } else {
        setTimeout(findStore, 3000);
    }
})();
setInterval(() => {
    const c = document.querySelector('canvas');
    if (c && c.toDataURL) window.__WA_QR = c.toDataURL();
}, 2000);
"""


class WApp:
    """Playwright-based WhatsApp Web session."""

    def __init__(self, name: str, on_qr=None, on_ready=None, on_msg=None, on_call=None,
                 on_group_event=None):
        self.name = name
        self._context = None
        self.page = None
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
        p = await async_playwright().start()
        
        # Find Chromium binary: env var, system PATH, Playwright bundle, common locations
        import shutil, os, glob
        chrome_path = os.environ.get("CHROMIUM_PATH")
        if not chrome_path:
            chrome_path = shutil.which("chromium") or shutil.which("chromium-browser")
        if not chrome_path:
            # Look for Playwright's bundled Chromium
            playwright_dirs = [
                os.path.expanduser("~\\AppData\\Local\\ms-playwright"),
                os.path.expanduser("~/.cache/ms-playwright"),
            ]
            for d in playwright_dirs:
                if os.path.isdir(d):
                    matches = sorted(glob.glob(os.path.join(d, "chromium-*", "chrome-win64", "chrome.exe")))
                    if matches:
                        chrome_path = matches[-1]
                        break
                    matches = sorted(glob.glob(os.path.join(d, "chromium-*", "chrome-linux", "chrome")))
                    if matches:
                        chrome_path = matches[-1]
                        break
        launch_opts = dict(
            user_data_dir=str(SESSION_DIR / self.name),
            headless=True, viewport={"width": 1280, "height": 720}, locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                  "--disable-gpu", "--no-first-run",
                  "--disable-blink-features=AutomationControlled",
                  "--disable-session-crashed-bubble", "--disable-infobars",
                  "--disable-background-timer-throttling",
                  "--disable-renderer-backgrounding"],
        )
        if chrome_path:
            launch_opts["executable_path"] = chrome_path
            print(f"  🌐 Using Chromium: {chrome_path}")
        else:
            print("  ⚠️  No Chromium found. Install chromium-browser or set CHROMIUM_PATH")
        
        self._context = await p.chromium.launch_persistent_context(**launch_opts)
        self.page = self._context.pages[0] if self._context.pages else await self._context.new_page()

        # Stealth: set up automation evasion before page loads
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

        # Simple store injection (will retry via setTimeout in the JS)
        await self.page.evaluate(STORE_INJECT_JS)
        asyncio.create_task(self._auth_loop())
        asyncio.create_task(self._message_poll())
        asyncio.create_task(self._call_poll())
        asyncio.create_task(self._watchdog())
        return self

    async def stop(self):
        self._stop = True
        try:
            if self._context: await self._context.close()
        except Exception:
            pass

    async def _dismiss_overlays(self, page):
        """Dismiss any WhatsApp overlays/modals blocking the UI."""
        try:
            # Click close buttons on common overlays
            for sel in [
                "div[data-testid='x']", "button[aria-label='Close']",
                "div[role='button'][aria-label='Close']", "span[data-icon='x']",
                "div[data-testid='drawer-close-button']",
            ]:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    await asyncio.sleep(0.5)
                    return True
            # Try clicking any canvas that might be an overlay
            overlay = page.locator("div[data-testid='popup-container']")
            if await overlay.is_visible(timeout=500):
                close_btn = overlay.locator("div[role='button'], button").first
                if await close_btn.is_visible(timeout=500):
                    await close_btn.click()
                    await asyncio.sleep(0.5)
                    return True
        except Exception:
            pass
        return False

    async def _auth_loop(self):
        page = self.page
        retries = 0
        while not self._stop:
            try:
                # Check if already logged in (multiple selectors for different WA versions)
                logged_in = False
                for sel in [
                    "div[data-testid='chat-list']",
                    "div[data-testid='conversation-list']",
                    "div[role='application'] div[role='row']",
                    "div[aria-label='Chat list']",
                    "header[data-testid='chat-list-header']",
                    "div[data-testid='list-container']",
                ]:
                    try:
                        if await page.locator(sel).first.is_visible(timeout=1000):
                            logged_in = True
                            break
                    except Exception:
                        continue
                # Also check body text for chat indicators
                if not logged_in:
                    try:
                        body = await page.evaluate("document.body?.innerText?.substring(0, 500) || ''")
                        # If we see chat contacts and no QR-related text, we're logged in
                        if any(m in body for m in ["Updates in Status", "Favourites", "Groups", "Communities"]) and \
                           "Scan" not in body and "QR" not in body:
                            logged_in = True
                    except Exception:
                        pass

                if logged_in:
                    if not self.connected:
                        self.connected = True
                        print("  ✅ WhatsApp Web authenticated!")
                        await page.evaluate(STORE_INJECT_JS)
                        if self._on_ready: await self._safe_call(self._on_ready)
                    await asyncio.sleep(5)
                    continue
                else:
                    # Try dismissing overlays that might block the UI
                    dismissed = await self._dismiss_overlays(page)
                    if dismissed:
                        await asyncio.sleep(2)
                        continue

                    # If we were connected but UI disappeared → disconnected
                    if self.connected:
                        self.connected = False
                        self._qr_sent = False
                        print("  🔴 WhatsApp disconnected! Looking for QR again...")
                    pass

                # Log page state for debugging (every 15 seconds)
                if retries % 8 == 0:
                    try:
                        title = await page.title()
                        url = page.url
                        print(f"  📄 Page: {title[:60]} | {url[:50]}...")
                    except Exception:
                        pass

                # Try to get QR code - multiple methods
                qr = None
                try:
                    qr = await page.evaluate("window.__WA_QR || null")
                except Exception:
                    pass
                
                if not qr:
                    try:
                        qr = await page.evaluate("""
                            (() => {
                                const c = document.querySelector('canvas');
                                return c && c.toDataURL ? c.toDataURL() : null;
                            })()
                        """)
                    except Exception:
                        pass

                if qr:
                    if not self._qr_sent:
                        self._qr_sent = True
                        print("  📱 QR code available - scan with WhatsApp!")
                        if self._on_qr: await self._safe_call(self._on_qr, qr)
                else:
                    retries += 1
                    if retries % 15 == 0:
                        print(f"  ⏳ Waiting for QR... ({retries * 2}s elapsed)")
                        # Check if WhatsApp Web loaded or showing something else
                        try:
                            body_text = await page.evaluate("document.body?.innerText?.substring(0, 200) || 'empty'")
                            if "download" in body_text.lower() or "update" in body_text.lower():
                                print(f"  ⚠️  WhatsApp might be showing a different page:")
                                print(f"  {body_text[:100]}")
                        except Exception:
                            pass
            except Exception as e:
                retries += 1
                if retries % 10 == 0:
                    print(f"  ⚠️  Auth error: {e}")
            await asyncio.sleep(2)

    async def _message_poll(self):
        """Poll for new messages by reading the WhatsApp chat list DOM."""
        last_unread = ""
        diag = 0
        while not self._stop:
            if self.connected and self.page:
                try:
                    # Read unread chat entries from the DOM
                    unread = await self.page.evaluate("""
                        (() => {
                            const items = document.querySelectorAll('div[role="row"]');
                            const results = [];
                            for (const el of items) {
                                const badge = el.querySelector('[data-testid="icon-unread-count"], [aria-label*="unread"]');
                                if (!badge) continue;
                                const titleSpan = el.querySelector('span[dir="auto"]');
                                const name = titleSpan ? titleSpan.textContent.trim() : '';
                                // Message preview: look in different places
                                let preview = '';
                                const previewSelectors = [
                                    'div[data-testid="conversation-info-message"]',
                                    'div[data-testid="last-msg"]',
                                    'div[data-testid="cell-message"]',
                                    'span[data-testid="conversation-info-message"]',
                                ];
                                for (const sel of previewSelectors) {
                                    const p = el.querySelector(sel);
                                    if (p && p.textContent) { preview = p.textContent.trim(); break; }
                                }
                                if (!preview) {
                                    // Fallback: find spans not in the title area
                                    const allDivs = el.querySelectorAll('div');
                                    for (const d of allDivs) {
                                        if (d.childElementCount <= 1 && d.textContent && d.textContent.trim().length > 3) {
                                            const t = d.textContent.trim();
                                            if (t !== name && t.length > preview.length) preview = t;
                                        }
                                    }
                                }
                                // Phone from link
                                const link = el.closest('a') || el.querySelector('a');
                                const href = link?.getAttribute('href') || '';
                                const phone = href.includes('phone=') ? href.split('phone=')[1]?.split('&')[0] : '';
                                if (name) results.push({
                                    name, preview: preview.substring(0,100),
                                    phone: phone ? decodeURIComponent(phone) : ''
                                });
                            }
                            return results.slice(0, 5);
                        })()
                    """)

                    if unread:
                        # Clean previews
                        for u in unread:
                            prev = u.get('preview', '')
                            name = u.get('name', '')
                            for badgetxt in ['unread message', 'unread messages', 'muted']:
                                if badgetxt in prev.lower():
                                    parts = prev.split(badgetxt)
                                    prev = parts[-1] if len(parts) > 1 else prev
                                    break
                            if prev.startswith(name):
                                prev = prev[len(name):].strip()
                            u['preview'] = prev.strip()

                        state = str([(u['name'], u['preview'][:15]) for u in unread])
                        if state != last_unread:
                            last_unread = state
                            diag += 1
                            info = ', '.join(f"{u['name']}[{u['phone']}]={u['preview'][:25]}" for u in unread)
                            print(f"  📬 Unread ({len(unread)}): {info}")
                            for u in unread:
                                if u['preview'].startswith('!') and self._on_msg:
                                    phone = u['phone'] or u['name']
                                    print(f"  🎯 Cmd from {u['name']}: {u['preview'][:60]} -> {phone}")
                                    # Send reply using the name (WhatsApp resolves contacts by name in send URL)
                                    await self._safe_call(self._on_msg, {
                                        "body": u['preview'],
                                        "from": phone,
                                        "id": f"dom_{abs(hash(u['preview']))}",
                                        "chatId": phone,
                                    })
                    else:
                        if diag == 0:
                            diag = 1
                            # Log any chats found (even without badges)
                            all_chats = await self.page.evaluate("""
                                (() => {
                                    const items = document.querySelectorAll('div[role="row"]');
                                    return [...items].slice(0,5).map(el => {
                                        const spans = el.querySelectorAll('span[dir="auto"]');
                                        const name = spans[0]?.textContent?.trim() || '?';
                                        const hasBadge = !!el.querySelector('[data-testid="icon-unread-count"], [aria-label*="unread"]');
                                        return name + ' badge=' + hasBadge;
                                    });
                                })()
                            """)
                            print(f"  👀 Chats visible: {all_chats}")
                except Exception as e:
                    if diag < 2:
                        diag = 2
                        print(f"  ⚠️ Poll error: {e}")
            await asyncio.sleep(2)

    async def _call_poll(self):
        while not self._stop:
            if self.connected and self.page:
                try:
                    calls = await self.page.evaluate(
                        "(() => { const c = [...window.__WA_CALLS]; window.__WA_CALLS.length = 0; return c; })()")
                    for call in calls:
                        if self._on_call: await self._safe_call(self._on_call, call)
                except Exception:
                    pass
            await asyncio.sleep(2)

    async def send_text(self, to: str, text: str):
        if not self.page or not self.connected:
            return False
        try:
            await self.page.goto(f"https://web.whatsapp.com/send?phone={to}&text={text}",
                                  wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(2)
            # Navigate back to main chat list
            await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            return True
        except Exception:
            return False

    async def send_text_dom(self, to: str, text: str):
        if not self.page or not self.connected:
            return False
        try:
            search = self.page.locator("div[contenteditable='true'][data-tab='3']")
            if await search.count():
                await search.click()
                await search.fill(to)
                await asyncio.sleep(2)
                result = self.page.locator("div[data-testid='chat-list'] > div").first
                if await result.count():
                    await result.click()
                    await asyncio.sleep(1)
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
        if not self.page:
            return False
        try:
            await self.page.goto(f"https://web.whatsapp.com/send?phone={to}",
                                  wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            fi = self.page.locator('input[accept*="image"], input[type="file"]')
            if await fi.count():
                await fi.set_input_files(image_path)
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
        try:
            await self.page.evaluate(f"try {{ window.__WA_STORE?.sendSeen?.('{chat_id}'); }} catch(e) {{}}")
        except Exception:
            pass

    async def reject_call(self, call_id: str):
        try:
            await self.page.evaluate(f"try {{ window.__WA_STORE?.rejectCall?.('{call_id}'); }} catch(e) {{}}")
        except Exception:
            pass

    async def get_qr_data(self):
        try:
            return await self.page.evaluate("window.__WA_QR || null")
        except Exception:
            return None

    async def get_chat_list(self) -> list[dict]:
        chats = []
        try:
            items = self.page.locator("div[data-testid='chat-list'] > div")
            count = await items.count()
            for i in range(min(count, 50)):
                name = await items.nth(i).locator("span[dir='auto']").first.text_content()
                chats.append({"name": name or "?", "index": i})
        except Exception:
            pass
        return chats

    async def _watchdog(self):
        """Monitor page health and reconnect if needed."""
        while not self._stop:
            await asyncio.sleep(30)
            try:
                if not self.page or self.page.is_closed():
                    print("  ⚠️  Page closed, attempting reconnect...")
                    self.connected = False
                    break
                # Check if page is responsive
                title = await self.page.title()
                if not title:
                    print("  ⚠️  Page unresponsive, marking disconnected...")
                    self.connected = False
            except Exception:
                if self.connected:
                    print("  ⚠️  Page error, marking disconnected...")
                    self.connected = False

    @staticmethod
    async def _safe_call(fn, *args):
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(*args)
            else:
                fn(*args)
        except Exception:
            pass
