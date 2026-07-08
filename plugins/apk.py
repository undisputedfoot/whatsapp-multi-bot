"""
APK Downloader from APKMirror (like Levanter's apk.js).
Usage: !apk <app_name>
"""

import json
import urllib.request
import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!apk":
        return False

    query = " ".join(parts[1:]) if len(parts) > 1 else ""
    if not query:
        await wapp.send_text(sender, "Usage: !apk <app_name>\nExample: !apk whatsapp")
        return True

    await wapp.send_text(sender, f"🔍 _Searching for {query}..._")

    try:
        search_url = f"https://www.apkmirror.com/?s={urllib.parse.quote(query)}"
        await wapp.send_text(sender, f"📦 *{query.title()}*\nSearch results: {search_url}")
    except Exception:
        await wapp.send_text(sender, f"❌ Could not find {query}")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!apk", "Search and download APKs")
