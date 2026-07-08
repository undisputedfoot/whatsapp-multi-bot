"""
WhatsApp Web engine built on Selenium — for Termux/ARM where Playwright isn't available.
Same interface as the Playwright engine (WApp class).
"""

import asyncio
import base64
import json
import re
import os
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import SESSION_DIR


class WApp:
    """Selenium-based WhatsApp Web session."""

    def __init__(self, name: str, on_qr=None, on_ready=None, on_msg=None, on_call=None,
                 on_group_event=None):
        self.name = name
        self.driver = None
        self.connected = False
        self._on_qr = on_qr
        self._on_ready = on_ready
        self._on_msg = on_msg
        self._on_call = on_call
        self._on_group_event = on_group_event
        self._stop = False
        self._qr_sent = False
        self._last_msg_count = 0
        self._known_messages = set()

    async def start(self):
        """Launch Chrome and open WhatsApp Web.
        Note: On Termux/Android, Chrome headless may not work.
        Falls back gracefully so the dashboard still runs."""
        user_dir = str(SESSION_DIR / self.name)
        os.makedirs(user_dir, exist_ok=True)

        import shutil

        # Find Chromium binary
        chrome_bin = None
        for p in [
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chrome"),
            "/data/data/com.termux/files/usr/bin/chromium",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]:
            if p and os.path.exists(p):
                chrome_bin = p
                break

        # Find chromedriver binary
        driver_bin = None
        for p in [
            shutil.which("chromedriver"),
            "/data/data/com.termux/files/usr/bin/chromedriver",
            "/usr/bin/chromedriver",
        ]:
            if p and os.path.exists(p):
                driver_bin = p
                break

        if not chrome_bin:
            self.connected = False
            print("  ⚠️  Chrome not found. Dashboard will still work.")
            print("  📱  Run the bot on a desktop, then access from your phone.")
            print(f"  🌐  Dashboard: http://localhost:{os.environ.get('DASHBOARD_PORT', '5000')}")
            return self

        try:
            opts = Options()
            opts.add_argument(f"--user-data-dir={user_dir}")
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-setuid-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-software-rasterizer")
            opts.add_argument("--disable-features=VizDisplayCompositor")
            opts.add_argument("--window-size=800,600")
            opts.add_argument("--remote-debugging-port=0")
            opts.add_argument("--disable-extensions")
            opts.add_argument("--single-process")
            opts.add_argument("--no-zygote")
            opts.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
            opts.binary_location = chrome_bin

            if driver_bin:
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path=driver_bin, start_timeout=60)
                self.driver = webdriver.Chrome(options=opts, service=service)
            else:
                self.driver = webdriver.Chrome(options=opts)

            self.driver.set_page_load_timeout(60)
            self.driver.get("https://web.whatsapp.com")
        except Exception as e:
            print(f"  ⚠️  Could not start Chrome: {e}")
            print("  📱  Run the bot on a desktop instead.")
            print("  🌐  Dashboard will still work at http://localhost:5000")
            self.connected = False

        # Start monitoring loops
        asyncio.create_task(self._auth_loop())
        asyncio.create_task(self._message_poll())
        return self

    async def stop(self):
        self._stop = True
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    async def _auth_loop(self):
        """Check for QR code or main UI."""
        while not self._stop:
            try:
                # Check for main chat UI (already logged in)
                try:
                    wait = WebDriverWait(self.driver, 3)
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[data-testid='chat-list']")))
                    if not self.connected:
                        self.connected = True
                        if self._on_ready:
                            await self._safe_call(self._on_ready)
                    await asyncio.sleep(3)
                    continue
                except (TimeoutException, Exception):
                    pass

                # Get QR code from canvas
                if not self._qr_sent:
                    qr = await self._get_qr()
                    if qr:
                        self._qr_sent = True
                        if self._on_qr:
                            await self._safe_call(self._on_qr, qr)

            except Exception:
                pass
            await asyncio.sleep(2)

    async def _get_qr(self):
        """Extract QR code data URL from canvas."""
        try:
            return self.driver.execute_script("""
                const c = document.querySelector('canvas');
                return c ? c.toDataURL() : null;
            """)
        except Exception:
            return None

    async def get_qr_data(self):
        """Public method to get current QR data."""
        return await self._get_qr()

    async def _message_poll(self):
        """Poll for new messages by checking DOM."""
        while not self._stop:
            if self.connected and self.driver:
                try:
                    messages = self.driver.execute_script("""
                        const msgs = [];
                        const bubbles = document.querySelectorAll(
                            'div.message-in, div.message-out, ' +
                            'div[data-testid="conversation-panel-messages"] ' +
                            'div[role="row"]'
                        );
                        const seen = new Set();
                        bubbles.forEach(b => {
                            const textEl = b.querySelector('span.copyable-text, span.selectable-text');
                            const text = textEl ? textEl.textContent : '';
                            const id = b.getAttribute('data-id') || b.id || text;
                            if (text && !seen.has(id)) {
                                seen.add(id);
                                msgs.push({
                                    id: id,
                                    body: text,
                                    from: b.matches('.message-in') ? 'incoming' : 'me',
                                    isGroup: window.location.hash.includes('-') || false,
                                });
                            }
                        });
                        return msgs;
                    """)

                    for msg in messages:
                        msg_id = msg.get("id", "")
                        if msg_id and msg_id not in self._known_messages:
                            self._known_messages.add(msg_id)
                            body = msg.get("body", "").strip()
                            if body and msg.get("from") == "incoming" and self._on_msg:
                                await self._safe_call(self._on_msg, {
                                    "id": msg_id,
                                    "body": body,
                                    "from": "?",
                                    "chatId": "?",
                                    "isGroup": msg.get("isGroup", False),
                                })
                except Exception:
                    pass
            await asyncio.sleep(2)

    async def send_text(self, to: str, text: str):
        """Send a message by navigating to the wa.me link."""
        if not self.driver or not self.connected:
            return False
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={to}&text={text}")
            await asyncio.sleep(4)
            # Press Enter
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ENTER).perform()
            await asyncio.sleep(1)
            return True
        except Exception:
            return False

    async def send_text_dom(self, to: str, text: str):
        """Send message by searching and typing in the chat."""
        if not self.driver:
            return False
        try:
            # Use search box
            search = self.driver.find_element(By.CSS_SELECTOR,
                "div[contenteditable='true'][data-tab='3']")
            search.clear()
            search.send_keys(to)
            await asyncio.sleep(2)

            # Click first result
            from selenium.webdriver.common.keys import Keys
            first = self.driver.find_element(By.CSS_SELECTOR,
                "div[data-testid='chat-list'] > div")
            first.click()
            await asyncio.sleep(1)

            # Type message
            msg_box = self.driver.find_element(By.CSS_SELECTOR,
                "div[contenteditable='true'][data-tab='10']")
            msg_box.clear()
            msg_box.send_keys(text)
            await asyncio.sleep(0.5)
            msg_box.send_keys(Keys.ENTER)
            await asyncio.sleep(1)
            return True
        except Exception:
            return False

    async def mark_seen(self, chat_id: str):
        """Send read receipt."""
        try:
            self.driver.execute_script("""
                try { window.Store?.sendSeen?.('""" + chat_id + """'); } catch(e) {}
            """)
        except Exception:
            pass

    async def reject_call(self, call_id: str):
        """Reject incoming call."""
        try:
            self.driver.execute_script("""
                try { window.Store?.rejectCall?.('""" + call_id + """'); } catch(e) {}
            """)
        except Exception:
            pass

    async def send_image(self, to: str, image_path: str, caption: str = ""):
        """Send an image."""
        if not self.driver:
            return False
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={to}")
            await asyncio.sleep(3)
            file_input = self.driver.find_element(By.CSS_SELECTOR,
                'input[accept*="image"], input[type="file"]')
            file_input.send_keys(image_path)
            await asyncio.sleep(2)
            if caption:
                from selenium.webdriver.common.keys import Keys
                actions = webdriver.ActionChains(self.driver)
                actions.send_keys(caption).perform()
                await asyncio.sleep(1)
                actions.send_keys(Keys.ENTER).perform()
            await asyncio.sleep(1)
            return True
        except Exception:
            return False

    async def get_chat_list(self) -> list[dict]:
        """Get recent chats."""
        chats = []
        try:
            items = self.driver.find_elements(By.CSS_SELECTOR,
                "div[data-testid='chat-list'] > div")
            for i, item in enumerate(items[:50]):
                try:
                    name = item.find_element(By.CSS_SELECTOR, "span[dir='auto']").text
                    chats.append({"name": name or "?", "index": i})
                except Exception:
                    chats.append({"name": "?", "index": i})
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
