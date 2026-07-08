"""
Weather Plugin — Example plugin for the WhatsApp Multi-Bot plugin system.
Provides !weather command.
"""

import httpx

help_text = "!weather <city> — Get current weather"

# Store session reference for logging
_bot = None


def register(session_ref):
    """Called by the plugin loader. session_ref is the Session instance."""
    global _bot
    _bot = session_ref
    print(f"  🌤️  Weather plugin loaded for {session_ref.name}")


def commands():
    """Return list of (command, description) tuples."""
    return [("!weather <city>", "Get current weather for a city")]


async def handle_command(cmd: str, parts: list, body: str, sender: str, wapp, lang: str):
    """Called by the bot when a message starts with !weather."""
    if cmd == "!weather":
        city = " ".join(parts[1:]) if len(parts) > 1 else ""
        if not city:
            await wapp.send_text(sender, "🌤️ Usage: !weather London")
            return True

        await wapp.send_text(sender, f"🌤️ Looking up weather for {city}...")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://wttr.in/{city}?format=%C+%t+%w+%h"
                )
                if resp.status_code == 200:
                    await wapp.send_text(sender,
                        f"🌤️ *Weather in {city.title()}*\n{resp.text.strip()}")
                else:
                    await wapp.send_text(sender, f"❌ Could not find weather for {city}")
        except Exception as e:
            await wapp.send_text(sender, f"❌ Weather error: {e}")

        return True
    return False
