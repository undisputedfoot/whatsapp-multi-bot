"""
VARS — Per-session variable storage (like Levanter's vars.js).
Usage: !getvar <key>, !setvar <key> <value>, !delvar <key>, !listvars
"""

from core import db

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd not in ("!getvar", "!setvar", "!delvar", "!listvars"):
        return False

    if not session_name:
        await wapp.send_text(sender, "❌ Session required.")
        return True

    if cmd == "!listvars":
        import json
        raw = db.get_setting(f"vars:{session_name}", "{}")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {}
        if data:
            text = "📋 *Variables:*\n" + "\n".join(f"  • {k} = {v}" for k, v in data.items())
        else:
            text = "No variables set."
        await wapp.send_text(sender, text)
        return True

    if len(parts) < 2:
        await wapp.send_text(sender, f"Usage: {cmd} <key> [value]")
        return True

    key = parts[1].upper()

    if cmd == "!getvar":
        import json
        raw = db.get_setting(f"vars:{session_name}", "{}")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {}
        if key in data:
            await wapp.send_text(sender, f"{key} = {data[key]}")
        else:
            await wapp.send_text(sender, f"❌ {key} not found.")
        return True

    if cmd == "!setvar":
        if len(parts) < 3:
            await wapp.send_text(sender, "Usage: !setvar KEY value")
            return True
        import json
        value = " ".join(parts[2:])
        raw = db.get_setting(f"vars:{session_name}", "{}")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {}
        data[key] = value
        db.set_setting(f"vars:{session_name}", json.dumps(data))
        await wapp.send_text(sender, f"✅ {key} = {value}")
        return True

    if cmd == "!delvar":
        import json
        raw = db.get_setting(f"vars:{session_name}", "{}")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {}
        if key in data:
            del data[key]
            db.set_setting(f"vars:{session_name}", json.dumps(data))
            await wapp.send_text(sender, f"✅ {key} deleted.")
        else:
            await wapp.send_text(sender, f"❌ {key} not found.")
        return True

    return False


def register(session_ref):
    session_ref.features["plugins"].register_command("!getvar", "Get variable value")
    session_ref.features["plugins"].register_command("!setvar", "Set variable value")
    session_ref.features["plugins"].register_command("!delvar", "Delete variable")
    session_ref.features["plugins"].register_command("!listvars", "List all variables")
