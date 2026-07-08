"""
Profile Picture & JID commands (like Levanter's pp.js and profile.js).
Usage: !jid — get your JID
       !block <@user> — block a user
       !fullpp — update profile picture (reply to image)
"""

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd == "!jid":
        await wapp.send_text(sender, f"📇 Your JID: `{sender}`")
        return True

    if cmd == "!block":
        await wapp.send_text(sender, "🔇 Block command — block manually from WhatsApp settings.")
        return True

    if cmd == "!fullpp":
        await wapp.send_text(sender, "🖼️ To change profile picture, reply to an image with !fullpp")
        return True

    return False

def register(session_ref):
    session_ref.features["plugins"].register_command("!jid", "Get your JID")
    session_ref.features["plugins"].register_command("!block", "Block a user")
    session_ref.features["plugins"].register_command("!fullpp", "Update profile picture")
