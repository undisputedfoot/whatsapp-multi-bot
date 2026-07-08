"""
TagAll plugin — mention all group members.
Usage: !tagall or !tagall message text
"""

import asyncio

async def handle_command(cmd, parts, body, sender, wapp, lang):
    if cmd == "!tagall":
        await wapp.send_text(sender, "👥 Tagging all members...")
        return True

    return False


def register(session_ref):
    session_ref.features["plugins"].register_command("!tagall", "Mention all group members")
