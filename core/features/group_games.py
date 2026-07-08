"""
Group Games — trivia, polls, and would-you-rather for interactive group fun.
"""

import asyncio
import random
from ..lang import t

# ── Trivia data ──────────────────────────────────────
TRIVIA_QUESTIONS = [
    {"q": "What planet is known as the Red Planet?", "a": "Mars"},
    {"q": "What is the largest ocean on Earth?", "a": "Pacific"},
    {"q": "Who wrote Romeo and Juliet?", "a": "Shakespeare"},
    {"q": "What is the chemical symbol for gold?", "a": "Au"},
    {"q": "What year did the Titanic sink?", "a": "1912"},
    {"q": "Which animal is known as the King of the Jungle?", "a": "Lion"},
    {"q": "What is the hardest natural substance?", "a": "Diamond"},
    {"q": "Which country has the largest population?", "a": "India"},
    {"q": "What is the fastest land animal?", "a": "Cheetah"},
    {"q": "How many continents are there?", "a": "7"},
]

WYR_QUESTIONS = [
    "Would you rather have the ability to fly or be invisible?",
    "Would you rather live without music or without television?",
    "Would you rather be able to time travel or read minds?",
    "Would you rather always be 10 minutes late or always 20 minutes early?",
    "Would you rather have unlimited pizza or unlimited sushi for life?",
    "Would you rather speak every language or play every instrument?",
    "Would you rather live in space or under the ocean?",
    "Would you rather have a rewind button or a pause button on your life?",
]


class GroupGames:
    """Interactive games for WhatsApp groups."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._trivia_active = {}  # {group_id: {"question": ..., "answer": ...}}

    async def handle_trivia(self, group_id: str, wapp) -> str:
        """Start a trivia game in the group."""
        q = random.choice(TRIVIA_QUESTIONS)
        self._trivia_active[group_id] = {"answer": q["a"].lower()}
        await wapp.send_text(group_id,
            f"🧠 *Trivia Time!*\n\n{q['q']}\n\nReply with your answer!")
        self._log("games", f"Trivia started in {group_id[:15]}")

        # Auto-close after 30 seconds
        await asyncio.sleep(30)
        if group_id in self._trivia_active:
            answer = self._trivia_active.pop(group_id)["answer"]
            await wapp.send_text(group_id,
                f"⏰ Time's up! The answer was: *{answer.title()}*")
        return True

    async def check_trivia_answer(self, group_id: str, body: str, wapp) -> bool:
        """Check if a message answers an active trivia question."""
        if group_id not in self._trivia_active:
            return False
        expected = self._trivia_active[group_id]["answer"]
        if body.lower().strip("?.,! ") == expected:
            del self._trivia_active[group_id]
            await wapp.send_text(group_id, f"🎉 *Correct!* Well done! 🎉")
            return True
        return False

    async def handle_wyr(self, group_id: str, wapp) -> str:
        """Send a 'Would You Rather' question to the group."""
        q = random.choice(WYR_QUESTIONS)
        await wapp.send_text(group_id, f"🤔 *Would You Rather…*\n\n{q}")
        self._log("games", f"WYR sent to {group_id[:15]}")
        return True

    async def handle_poll(self, group_id: str, question: str, options: list[str], wapp):
        """Send a poll to the group."""
        text = f"📊 *Poll:* {question}\n\n"
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, opt in enumerate(options[:5]):
            text += f"{emojis[i]} {opt}\n"
        text += "\nReply with your choice!"
        await wapp.send_text(group_id, text)
        self._log("games", f"Poll sent to {group_id[:15]}")
