"""
TOG — Toggle commands on/off for the session (like Levanter's tog.js).
Usage: !tog <command> on/off
"""

from core import db

_cache = {}  # {session_name: {cmd: bool}}

def _get_toggles(session_name):
    if session_name not in _cache:
        raw = db.get_setting(f"toggles:{session_name}", "{}")
        import json
        try:
            _cache[session_name] = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            _cache[session_name] = {}
    return _cache[session_name]

def _save_toggles(session_name):
    import json
    db.set_setting(f"toggles:{session_name}", json.dumps(_cache[session_name]))

def is_command_enabled(session_name, cmd):
    """Check if a command is toggled on (default: on unless explicitly off)."""
    toggles = _get_toggles(session_name)
    return toggles.get(cmd, True)

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!tog":
        return False

    if not session_name:
        await wapp.send_text(sender, "❌ Session required.")
        return True

    if len(parts) < 3:
        toggles = _get_toggles(session_name)
        if toggles:
            text = "🔘 *Toggled Commands:*\n"
            for c, enabled in toggles.items():
                icon = "🟢" if enabled else "🔴"
                text += f"  {icon} {c}\n"
            await wapp.send_text(sender, text)
        else:
            await wapp.send_text(sender, "No toggled commands. Usage: !tog <command> on/off")
        return True

    target_cmd = parts[1].lower()
    if not target_cmd.startswith("!"):
        target_cmd = f"!{target_cmd}"
    state = parts[2].lower()

    if state not in ("on", "off"):
        await wapp.send_text(sender, "Usage: !tog <command> on/off\nExample: !tog !sticker off")
        return True

    toggles = _get_toggles(session_name)
    toggles[target_cmd] = (state == "on")
    _save_toggles(session_name)
    await wapp.send_text(sender, f"✅ {target_cmd} turned {state}")
    return True


def register(session_ref):
    session_ref.features["plugins"].register_command("!tog", "Toggle commands on/off")
