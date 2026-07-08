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
    const webpack = window.webpackChunkwhatsapp_web_client;
    if (!webpack) { setTimeout(findStore, 1000); return; }
    try {
        const scan = (obj, depth=0) => {
            if (depth > 5 || !obj || typeof obj !== 'object') return;
            if (obj.Chat && obj.Msg && obj.Contact) { window.__WA_STORE = obj; return; }
            if (Array.isArray(obj)) { obj.forEach(i => scan(i, depth+1)); return; }
            Object.values(obj).forEach(v => scan(v, depth+1));
        };
        Object.values(webpack.c || {}).forEach(m => { if (m && m.exports) scan(m.exports); });
    } catch(e) {}
    if (!window.__WA_STORE) {
        for (const key of ['Store', 'store', 'WAMyStore', 'WapStore']) {
            if (window[key] && window[key].Chat) { window.__WA_STORE = window[key]; break; }
        }
    }
    if (window.__WA_STORE) {
        try {
            window.__WA_STORE.Msg.on('add', (msg) => {
                if (!msg.fromMe && msg.body) {
                    window.__WA_MSGS.push({
                        id: msg.id?._serialized || '', from: msg.from?.user || '',
                        body: msg.body, type: msg.type || 'chat',
                        timestamp: msg.t || Math.floor(Date.now()/1000),
                        chatId: msg.id?.remote || '',
                        isGroup: (msg.id?.remote || '').includes('-') || false,
                    });
                }
            });
        } catch(e) {}
        try {
            window.__WA_STORE.Call.on('add', (call) => {
                window.__WA_CALLS.push({
                    id: call.id || '', from: call.from?.user || '',
                    status: call.status || '', isVideo: call.isVideo || false,
                });
            });
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
        
        # Find Chromium binary: try system path first, fall back to Playwright's bundled
        import shutil, os
        chrome_path = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
        launch_opts = dict(
            user_data_dir=str(SESSION_DIR / self.name),
            headless=True, viewport={"width": 800, "height": 600}, locale="en-US",
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                  "--disable-gpu", "--no-first-run"],
        )
        if chrome_path:
            launch_opts["executable_path"] = chrome_path
            print(f"  🌐 Using Chromium: {chrome_path}")
        else:
            print("  ⚠️  No Chromium found. Install chromium-browser or set CHROMIUM_PATH")
        
        self._context = await p.chromium.launch_persistent_context(**launch_opts)
        self.page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
        await self.page.evaluate(STORE_INJECT_JS)
        asyncio.create_task(self._auth_loop())
        asyncio.create_task(self._message_poll())
        asyncio.create_task(self._call_poll())
        return self

    async def stop(self):
        self._stop = True
        try:
            if self._context: await self._context.close()
        except Exception:
            pass

    async def _auth_loop(self):
        page = self.page
        retries = 0
        while not self._stop:
            try:
                # Check if already logged in
                try:
                    await page.wait_for_selector("div[data-testid='chat-list']", timeout=5)
                    if not self.connected:
                        self.connected = True
                        print("  ✅ WhatsApp Web authenticated!")
                        await page.evaluate(STORE_INJECT_JS)
                        if self._on_ready: await self._safe_call(self._on_ready)
                    await asyncio.sleep(5)
                    continue
                except TimeoutError:
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
        while not self._stop:
            if self.connected and self.page:
                try:
                    count = await self.page.evaluate("window.__WA_MSGS.length")
                    while self._last_msg_count < count:
                        msg = await self.page.evaluate(f"window.__WA_MSGS[{self._last_msg_count}]")
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
            await asyncio.sleep(1)
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

    @staticmethod
    async def _safe_call(fn, *args):
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(*args)
            else:
                fn(*args)
        except Exception:
            pass
