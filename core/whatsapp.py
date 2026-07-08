"""
WhatsApp Web engine - auto-selects HTTP (Baileys), Playwright, or Selenium.

Engine is chosen lazily when WApp() is first constructed, not at import time.
Override with WA_ENGINE env var: http, playwright, selenium, auto
"""

import sys
import platform
import os
import importlib


def WApp(*args, **kwargs):
    """Factory that selects the best available engine at call time."""
    engine = os.environ.get("WA_ENGINE", "auto").lower()
    is_arm = platform.machine() in ("aarch64", "armv8l", "arm")
    is_termux = "com.termux" in (sys.executable or "")

    # Check what's available
    has_httpx = False
    has_playwright = False
    try:
        import httpx  # noqa
        has_httpx = True
    except ImportError:
        pass
    try:
        import playwright  # noqa
        has_playwright = True
    except ImportError:
        pass
    if is_arm or is_termux:
        has_playwright = False

    # Select engine
    mod_name = None
    label = ""

    if engine == "http" or (engine == "auto" and has_httpx and not is_arm and not is_termux):
        mod_name = ".whatsapp_http"
        label = "HTTP (whatsapp-web.js via Baileys)"
    elif engine == "playwright" or (engine == "auto" and has_playwright):
        mod_name = ".whatsapp_playwright"
        label = "Playwright (desktop browser)"
    else:
        mod_name = ".whatsapp_selenium"
        label = "Selenium (mobile/Termux)"

    mod = importlib.import_module(mod_name, __package__)
    cls = getattr(mod, "WApp")
    print(f"  🚀 Engine: {label}")
    return cls(*args, **kwargs)
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
