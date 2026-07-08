"""
QR Code Reader/Generator (like Levanter's qr.js).
Usage: !qr <text> — generates a QR code
       Reply to image with !qr — reads QR code
"""

import urllib.parse

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!qr":
        return False

    text = " ".join(parts[1:]) if len(parts) > 1 else ""

    if text:
        # Generate QR code
        encoded = urllib.parse.quote(text)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
        await wapp.send_text(sender, f"📱 QR Code for: {text}\n{qr_url}")
    else:
        # Reply mode - would need to read an image
        await wapp.send_text(sender, "Usage:\n  !qr <text> — generate QR\n  Reply to QR image with !qr — read QR")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!qr", "Generate or read QR codes")
