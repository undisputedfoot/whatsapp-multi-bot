"""
Anti-Delete — saves deleted messages and forwards them to admin.
Like Levanter's anti-delete feature.
"""

import asyncio
import os
from datetime import datetime


class AntiDelete:
    """Detect and log deleted messages."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._recent = {}  # {msg_id: {data}}

    async def handle(self, msg: dict, wapp, session_name: str, admin_number: str = ""):
        """Track incoming messages to detect deletions later."""
        msg_id = msg.get("id", "")
        if msg_id and msg.get("body"):
            self._recent[msg_id] = {
                "body": msg.get("body", ""),
                "from": msg.get("from", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Keep max 500
            if len(self._recent) > 500:
                keys = list(self._recent.keys())[:-500]
                for k in keys:
                    del self._recent[k]

    async def on_delete(self, msg_id: str, wapp, admin_number: str = ""):
        """Called when a message deletion is detected."""
        deleted = self._recent.pop(msg_id, None)
        if deleted and admin_number:
            text = f"🚫 *Deleted Message*\nFrom: {deleted['from']}\nMsg: {deleted['body']}"
            await wapp.send_text(admin_number, text)
            return True
        return False
