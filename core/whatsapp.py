"""
WhatsApp Web engine - auto-selects Playwright or Selenium based on platform.
"""

import sys
import platform


# ── Auto-detect best engine ──────────────────
_HAS_PLAYWRIGHT = False
try:
    import playwright  # noqa
    _HAS_PLAYWRIGHT = True
except ImportError:
    pass

# On Termux / ARM, force Selenium
_IS_ARM = platform.machine() in ("aarch64", "armv8l", "arm")
_IS_TERMUX = "com.termux" in (sys.executable or "")

if _IS_ARM or _IS_TERMUX:
    _HAS_PLAYWRIGHT = False


# ── Import the right engine ──────────────────
if _HAS_PLAYWRIGHT:
    from .whatsapp_playwright import WApp
    print("  🖥️  Using Playwright engine (desktop)")
else:
    from .whatsapp_selenium import WApp
    print("  📱  Using Selenium engine (ARM/Termux)")

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
