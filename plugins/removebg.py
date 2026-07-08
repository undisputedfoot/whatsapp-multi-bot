"""
Remove Background (like Levanter's rmbg.js).
Usage: Reply to an image with !rmbg
Note: Requires RMBG_KEY in .env for remove.bg API.
"""

from core.config import BASE_DIR

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!rmbg":
        return False

    await wapp.send_text(sender,
        "🖼️ *Remove Background*\n"
        "Reply to an image with !rmbg to remove its background.\n"
        "Set RMBG_KEY in .env for remove.bg API access.")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!rmbg", "Remove image background")
