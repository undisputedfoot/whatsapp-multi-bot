"""
AI-powered smart replies using OpenAI or Google Gemini.
Toggle per session — replaces keyword auto-reply with natural conversations.
"""

import re
import json
from ..config import AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_SYSTEM_PROMPT, GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, GEMINI_MODEL


class AIReply:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._history = {}  # {sender: [messages]}

    async def handle(self, body: str, sender: str, wapp, lang: str) -> bool:
        """Send message to AI and reply. Returns True if replied."""
        # Determine which API key to use based on provider
        api_key = AI_API_KEY
        provider = AI_PROVIDER

        if provider == "groq":
            api_key = GROQ_API_KEY
            if not api_key:
                return False

        if provider in ("none", "") or not api_key:
            return False

        self._log("ai", f"🤖 AI ({provider}) replying to {sender}...")

        # Build conversation context
        if sender not in self._history:
            self._history[sender] = []
        self._history[sender].append({"role": "user", "content": body})
        self._history[sender] = self._history[sender][-10:]

        try:
            if provider in ("openai", "openrouter"):
                reply = await self._openai_chat(sender, provider)
            elif provider == "groq":
                reply = await self._groq_chat(sender)
            elif provider == "gemini":
                reply = await self._gemini_chat(sender)
            else:
                return False

            if reply:
                await wapp.send_text(sender, reply)
                self._history[sender].append({"role": "assistant", "content": reply})
                self._log("ai", f"💬 AI replied: {reply[:60]}...")
                return True
        except Exception as e:
            self._log("ai", f"❌ AI error: {e}")

        return False

    async def _openai_chat(self, sender: str, provider: str) -> str | None:
        """Call OpenAI-compatible API (OpenAI, OpenRouter, etc)."""
        import httpx

        base_url = "https://api.openai.com/v1"
        api_key = AI_API_KEY

        if provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"

        messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
        messages.extend(self._history[sender])

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/whatsapp-multi-bot"
            headers["X-Title"] = "WhatsApp Multi-Bot"

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": AI_MODEL,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _groq_chat(self, sender: str) -> str | None:
        """Call Groq API (fast inference)."""
        import httpx

        messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
        messages.extend(self._history[sender])

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _gemini_chat(self, sender: str) -> str | None:
        """Call Google Gemini API using the GOOGLE_API_KEY."""
        import httpx

        if not GOOGLE_API_KEY:
            return None

        contents = []
        for msg in self._history[sender]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Prepend system prompt as a user/model exchange
        system_content = [{"role": "user", "parts": [{"text": AI_SYSTEM_PROMPT}]},
                          {"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]}]
        contents = system_content + contents

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": contents,
                      "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}},
            )
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError):
                self._log("ai", f"⚠️ Gemini response parse error: {data}")
                return None
