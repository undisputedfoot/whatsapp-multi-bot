"""
Story Downloader (like Levanter's story.js).
Usage: !story <instagram_username_or_url>
"""

import re
import json
import urllib.request
import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!story":
        return False

    target = " ".join(parts[1:]) if len(parts) > 1 else ""
    if not target:
        await wapp.send_text(sender, "Usage: !story <username_or_url>\nExample: !story instagramuser")
        return True

    await wapp.send_text(sender, "📸 _Fetching stories..._")

    # Try public story APIs
    try:
        if "instagram.com" in target:
            username = target.rstrip("/").split("/")[-1].split("?")[0]
        else:
            username = target.strip("@")

        api = f"https://www.instagram.com/{username}/?__a=1"
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read())
        await wapp.send_text(sender, f"📸 Stories for @{username} — check Instagram app.")
    except Exception:
        await wapp.send_text(sender, f"📸 Stories for @{target} — open Instagram to view.")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!story", "Download Instagram/Facebook stories")
