"""
MSGS — Group message stats per user (like Levanter's msgs.js).
Usage: !msgs — shows top members by message count
"""

from core import db

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!msgs":
        return False

    group_jid = sender if "@g.us" in sender else ""
    if not group_jid:
        await wapp.send_text(sender, "❌ !msgs only works in groups!")
        return True

    if not session_name:
        await wapp.send_text(sender, "❌ Session required.")
        return True

    members = db.get_group_members(session_name, group_jid)
    if not members:
        await wapp.send_text(sender, "📊 No message stats yet.")
        return True

    # Sort by msg_count descending
    sorted_members = sorted(members, key=lambda m: m.get("msg_count", 0), reverse=True)
    total = sum(m.get("msg_count", 0) for m in sorted_members)

    text = f"📊 *Group Message Stats*\nTotal: {total} messages\n"
    for i, m in enumerate(sorted_members[:15]):
        peer = m.get("peer", "?")
        count = m.get("msg_count", 0)
        pct = (count / total * 100) if total > 0 else 0
        text += f"\n{i+1}. @{peer[:10]}... — {count} ({pct:.0f}%)"

    await wapp.send_text(group_jid, text)
    return True


def register(session_ref):
    session_ref.features["plugins"].register_command("!msgs", "Group message stats per user")
