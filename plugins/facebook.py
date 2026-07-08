"""
Facebook Video Downloader (like Levanter's facebook.js).
Usage: !fb <url>
"""

import re
import json
import urllib.request
import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!fb":
        return False

    url = parts[1] if len(parts) > 1 else ""
    if not url:
        await wapp.send_text(sender, "Usage: !fb <facebook_video_url>\nExample: !fb https://facebook.com/watch?v=...")
        return True

    await wapp.send_text(sender, "📥 _Downloading Facebook video..._")

    try:
        api = f"https://www.facebook.com/plugins/video/oembed.json?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=10)
        info = json.loads(r.read())
        title = info.get("title", "Facebook Video")
        await wapp.send_text(sender, f"📥 *{title}*\n{url}")
    except Exception:
        await wapp.send_text(sender, f"📥 Download link: {url}")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!fb", "Download Facebook videos")
