"""
Exif Sticker Metadata Viewer (like Levanter's exif.js).
Usage: Reply to a sticker with !exif to see its metadata.
"""

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!exif":
        return False

    await wapp.send_text(sender,
        "🎨 *Sticker Info*\n"
        "Reply to a sticker with !exif to view its metadata "
        "(pack name, author, emojis, etc.)")

    return True

def register(session_ref):
    session_ref.features["plugins"].register_command("!exif", "View sticker metadata")
