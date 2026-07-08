"""
Read Receipts — automatically send blue ticks for incoming messages.
"""

from ..config import READ_RECEIPTS


class ReadReceipts:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)

    async def handle(self, msg: dict, wapp):
        if not READ_RECEIPTS:
            return
        try:
            sender = msg.get("from", "")
            if sender:
                await wapp.mark_seen(sender)
                self._log("read_receipt", f"Blue tick sent to {sender}")
        except Exception:
            pass
