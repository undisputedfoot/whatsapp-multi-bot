"""
PDM — Private Message mode / PM Permit (like Levanter's pdm.js).
When enabled, only allows PMs from group members and admins.
Usage: !pdm on/off
"""

from core import db

_cache = {}  # {session_name: bool}

def _is_enabled(session_name):
    if session_name not in _cache:
        val = db.get_setting(f"pdm:{session_name}", "off")
        _cache[session_name] = (val == "on")
    return _cache[session_name]

def _set_enabled(session_name, enabled):
    _cache[session_name] = enabled
    db.set_setting(f"pdm:{session_name}", "on" if enabled else "off")

async def check_pm(sender: str, session_name: str, wapp) -> bool:
    """Check if a PM is allowed. Returns True if blocked."""
    if not _is_enabled(session_name):
        return False
    if "@g.us" in sender:
        return False  # Group messages not affected
    # Check if sender is admin
    if db.is_admin(session_name, sender):
        return False
    # Check if sender is in any group
    groups = db.get_all_groups(session_name)
    for g in groups:
        members = db.get_group_members(session_name, g["group_id"])
        for m in members:
            if m.get("peer") == sender:
                return False
    # Block: not in any group, not admin
    await wapp.send_text(sender, "🚫 PMs are restricted. Join a group first or contact an admin.")
    return True

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!pdm":
        return False

    if not session_name:
        await wapp.send_text(sender, "❌ Session required.")
        return True

    if len(parts) < 2:
        status = "on" if _is_enabled(session_name) else "off"
        await wapp.send_text(sender, f"📩 PM Mode: {status}")
        return True

    sub = parts[1].lower()
    if sub == "on":
        _set_enabled(session_name, True)
        await wapp.send_text(sender, "✅ PM Mode ON — only group members can PM")
    elif sub == "off":
        _set_enabled(session_name, False)
        await wapp.send_text(sender, "✅ PM Mode OFF — anyone can PM")
    else:
        await wapp.send_text(sender, "Usage: !pdm on/off")
    return True


def register(session_ref):
    session_ref.features["plugins"].register_command("!pdm", "Private message mode / PM Permit")
