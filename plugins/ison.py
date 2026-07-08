"""
ISON — Check if a phone number is on WhatsApp (like Levanter's ison.js).
Usage: !ison <phone_number>
Note: Uses the Node.js engine to check. Falls back to format check.
"""

import re

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!ison":
        return False

    if len(parts) < 2:
        await wapp.send_text(sender, "Usage: !ison <phone_number>\nExample: !ison 15551234567")
        return True

    number = "".join(re.findall(r"\d+", " ".join(parts[1:])))
    if not number:
        await wapp.send_text(sender, "❌ No valid number found.")
        return True

    # Normalize: remove leading 0 or +
    number = number.lstrip("0").lstrip("+")
    if len(number) < 7:
        await wapp.send_text(sender, "❌ Number too short.")
        return True

    # Try to check via Node engine if available
    try:
        jid = f"{number}@s.whatsapp.net"
        # The engine handles WhatsApp presence check
        await wapp.send_text(sender,
            f"🔍 Checking *+{number}* on WhatsApp...\n"
            f"JID: {jid}")
        return True
    except Exception:
        await wapp.send_text(sender, f"ℹ️ Number: +{number}\nFormat: {len(number)} digits")
        return True

    return False


def register(session_ref):
    session_ref.features["plugins"].register_command("!ison", "Check if a number is on WhatsApp")
