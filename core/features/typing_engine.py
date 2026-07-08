"""
Human-like Typing Engine — adds realistic delays and typing indicators before sending messages.
Makes the bot feel like a real person.
"""

import asyncio
import random
from ..config import HUMAN_TYPING, TYPING_MIN_DELAY, TYPING_MAX_DELAY


class TypingEngine:
    """Adds human-like behavior to outgoing messages."""

    def __init__(self):
        self.enabled = HUMAN_TYPING

    async def simulate_typing(self, page, chat_id: str = None):
        """
        Show typing indicator for a random delay.
        Uses WhatsApp Web's built-in typing indicator if Store is available,
        otherwise just waits.
        """
        if not self.enabled:
            return

        delay = random.uniform(TYPING_MIN_DELAY, TYPING_MAX_DELAY)

        # Try to show typing indicator via Store
        if page:
            try:
                await page.evaluate("""
                    try {
                        const chat = window.__WA_STORE?.Chat?.get('""" + (chat_id or '') + """');
                        if (chat) chat.sendTyping();
                    } catch(e) {}
                """)
            except Exception:
                pass

        # Random realistic delay
        await asyncio.sleep(delay)

        # Stop typing
        if page:
            try:
                await page.evaluate("""
                    try {
                        const chat = window.__WA_STORE?.Chat?.get('""" + (chat_id or '') + """');
                        if (chat) chat.clearTyping();
                    } catch(e) {}
                """)
            except Exception:
                pass

    async def simulate_reading(self, message_length: int):
        """Simulate reading time based on message length."""
        if not self.enabled:
            return
        # Reading speed ~ 4 chars per second, min 1s, max 8s
        reading_time = min(max(message_length / 4, 1), 8)
        await asyncio.sleep(reading_time)
