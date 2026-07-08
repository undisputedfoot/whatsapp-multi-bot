"""
Auto Status Viewer — periodically views contacts' status updates.
Uses WhatsApp Web's status API via Playwright evaluation.
"""

import asyncio
from ..lang import t
from ..config import AUTO_STATUS_VIEW


class AutoStatusViewer:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._running = False

    async def start(self, wapp, session_name: str):
        if not AUTO_STATUS_VIEW:
            return
        self._running = True
        self._log("auto_status", f"📸 Status viewer started for {session_name}")

        while self._running:
            try:
                # Navigate to status view if WhatsApp exposes it
                page = wapp.page
                if page and not page.is_closed():
                    # Click on the Status tab (if available)
                    status_tab = page.locator("div[title='Status']")
                    if await status_tab.count():
                        await status_tab.click()
                        await asyncio.sleep(2)

                        # Click on contacts' statuses to view them
                        status_items = page.locator("div[data-testid='status-list'] > div")
                        count = await status_items.count()
                        for i in range(min(count, 20)):
                            try:
                                await status_items.nth(i).click()
                                await asyncio.sleep(1)
                                # Close status viewer
                                await page.keyboard.press("Escape")
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
            except Exception:
                pass

            # Check every 45 seconds
            await asyncio.sleep(45)

    def stop(self):
        self._running = False
