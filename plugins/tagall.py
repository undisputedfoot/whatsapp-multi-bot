"""
TagAll plugin — mention all group members.
Usage: !tagall or !tagall <message>
"""

import asyncio
from core import db


async def handle_command(cmd, parts, body, sender, wapp, lang, session_name="__any__"):
    if cmd == "!tagall":
        # Only works in groups
        if "-" not in sender and "@g.us" not in sender:
            await wapp.send_text(sender, "❌ Tagall only works in groups!")
            return True

        # Get group JID
        group_jid = sender if "@" in sender else sender

        # Get all active members from DB
        members = db.get_group_members(session_name, group_jid)
        if not members:
            await wapp.send_text(sender, "👥 No members tracked yet. Send some messages first!")
            return True

        # Build mention text with custom message
        custom_msg = " ".join(parts[1:]) if len(parts) > 1 else ""
        mention_ids = []
        mention_lines = []
        for m in members[:50]:  # WhatsApp limits mentions
            peer = m.get("peer", "")
            if peer and peer != sender.split("@")[0]:
                mention_ids.append(peer)
                mention_lines.append(f"@{peer.split('@')[0] if '@' in peer else peer[:12]}")

        if not mention_ids:
            await wapp.send_text(sender, "👥 No members to tag!")
            return True

        text = f"👥 *Tag All* {'— ' + custom_msg if custom_msg else ''}\n\n" + " ".join(mention_lines)

        try:
            await wapp.send_text(sender, text, mentions=mention_ids)
        except TypeError:
            # Fallback if send_text doesn't support mentions param yet
            await wapp.send_text(sender, text)

        return True

    return False


def register(session_ref):
    session_ref.features["plugins"].register_command("!tagall", "Mention all group members")
