"""
Screenshot tool (like Levanter's ss.js).
Usage: !ss <url> or !fullss <url>
"""

import re
import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd not in ("!ss", "!fullss"):
        return False

    url = " ".join(parts[1:]) if len(parts) > 1 else ""
    if not url:
        await wapp.send_text(sender, f"Usage: {cmd} <url>\nExample: {cmd} https://example.com")
        return True

    if not url.startswith("http"):
        url = "https://" + url

    full = "true" if cmd == "!fullss" else "false"

    await wapp.send_text(sender, f"📸 _Taking screenshot of {url}..._")

    # Use free screenshot API
    try:
        api = f"https://api.screenshotmachine.com/?key=free&url={urllib.parse.quote(url)}&dimension=1024x768&format=png"
        await wapp.send_text(sender, f"📸 Screenshot: {api}")
    except Exception:
        await wapp.send_text(sender, f"📸 Screenshot of {url}")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!ss", "Take webpage screenshot")
    session_ref.features["plugins"].register_command("!fullss", "Take full webpage screenshot")
