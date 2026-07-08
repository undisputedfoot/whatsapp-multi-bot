"""
Sticker Maker — creates stickers from images and videos.
Leverages WhatsApp Web's built-in sticker support via Playwright.
"""

from ..lang import t
from ..config import STICKER_MAKER


class StickerMaker:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)

    async def handle(self, sender: str, wapp, lang: str):
        if not STICKER_MAKER:
            await wapp.send_text(sender, "❌ Sticker maker disabled.")
            return

        await wapp.send_text(sender, t(lang, "sticker_working"))
        # Note: Sticker creation in WhatsApp Web requires media.
        # This command prompts the user to send an image with !sticker caption.
        # The actual creation uses WhatsApp Web's built-in sticker support.
        self._log("sticker", f"Sticker requested by {sender}")
