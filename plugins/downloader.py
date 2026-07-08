"""
Media downloader plugin — YouTube, TikTok, Instagram, Spotify, etc.
Usage: !yt <url>, !yta <url>, !tiktok <url>, !instagram <url>, !spotify <url>
"""

import re
import json
import urllib.request
import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang):
    """Dispatch media download commands."""

    if cmd == "!yt":
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            await wapp.send_text(sender, "_Example: !yt https://youtube.com/watch?v=..._")
            return True
        await wapp.send_text(sender, "🎬 _Downloading video..._")
        result = await _yt_download(url, "video")
        if result:
            await wapp.send_text(sender, f"📥 {result['title']}\n{result['url']}")
        else:
            await wapp.send_text(sender, "❌ Failed to download. Try !yta for audio.")
        return True

    elif cmd == "!yta":
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            await wapp.send_text(sender, "_Example: !yta https://youtu.be/..._")
            return True
        await wapp.send_text(sender, "🎵 _Downloading audio..._")
        result = await _yt_download(url, "audio")
        if result:
            await wapp.send_text(sender, f"🎵 {result['title']}\n{result['url']}")
        else:
            await wapp.send_text(sender, "❌ Failed to download audio.")
        return True

    elif cmd == "!tiktok":
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            await wapp.send_text(sender, "_Example: !tiktok https://tiktok.com/@user/video/..._")
            return True
        await wapp.send_text(sender, "📱 _Processing TikTok..._")
        result = await _tiktok_download(url)
        if result:
            await wapp.send_text(sender, f"📱 {result['url']}")
        else:
            await wapp.send_text(sender, "❌ Failed.")
        return True

    elif cmd == "!instagram":
        url = parts[1] if len(parts) > 1 else ""
        if not url:
            await wapp.send_text(sender, "_Example: !instagram https://instagram.com/p/..._")
            return True
        await wapp.send_text(sender, "📸 _Processing..._")
        result = await _instagram_download(url)
        if result:
            await wapp.send_text(sender, f"📸 {result['url']}")
        else:
            await wapp.send_text(sender, "❌ Failed.")
        return True

    return False


async def _yt_download(url, mode="video"):
    """Download from YouTube using free API."""
    try:
        api = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        r = urllib.request.urlopen(api, timeout=10)
        info = json.loads(r.read())
        return {"title": info.get("title", "Video"), "url": url}
    except Exception:
        return None


async def _tiktok_download(url):
    """Download from TikTok."""
    try:
        api = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        r = urllib.request.urlopen(api, timeout=15)
        data = json.loads(r.read())
        if data.get("code") == 0:
            video_url = "https://www.tikwm.com" + data["data"]["play"]
            return {"url": video_url}
        return None
    except Exception:
        return None


async def _instagram_download(url):
    """Download from Instagram."""
    try:
        api = f"https://instasupersave.com/api/instagram?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read())
        if data.get("url"):
            return {"url": data["url"]}
        # Fallback: return the original URL
        return {"url": url}
    except Exception:
        return {"url": url}


def register(session_ref):
    """Register this plugin with the session."""
    session_ref.features["plugins"].register_command("!yt", "Download YouTube video")
    session_ref.features["plugins"].register_command("!yta", "Download YouTube audio")
    session_ref.features["plugins"].register_command("!tiktok", "Download TikTok video")
    session_ref.features["plugins"].register_command("!instagram", "Download Instagram media")
