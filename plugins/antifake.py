"""
AntiFake — block numbers from specific country codes (like Levanter's antifake.js).
Usage: !antifake on/off, !antifake add/remove <country_code>, !antifake list
"""

from core import db

_cache = {}

def _get_config(session_name):
    key = f"antifake:{session_name}"
    if key not in _cache:
        cfg = db.get_setting(key, "")
        if cfg:
            import json
            try:
                _cache[key] = json.loads(cfg)
            except (json.JSONDecodeError, TypeError):
                _cache[key] = {"enabled": False, "codes": []}
        else:
            _cache[key] = {"enabled": False, "codes": []}
    return _cache[key]

def _save_config(session_name):
    import json
    key = f"antifake:{session_name}"
    db.set_setting(key, json.dumps(_cache[key]))

async def check_participant(participant_jid: str, session_name: str, group_jid: str, wapp) -> bool:
    """Check if a participant should be blocked. Returns True if blocked."""
    cfg = _get_config(session_name)
    if not cfg["enabled"] or not cfg["codes"]:
        return False

    number = participant_jid.split("@")[0]
    for code in cfg["codes"]:
        if number.startswith(code):
            await wapp.send_text(group_jid,
                f"🚫 Blocked +{code} user (@{number[-4:]}).")
            return True
    return False

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!antifake":
        return False

    if not session_name:
        session_name = "default"

    if len(parts) < 2:
        cfg = _get_config(session_name)
        status = "on" if cfg["enabled"] else "off"
        codes = ", ".join(cfg["codes"]) if cfg["codes"] else "none"
        await wapp.send_text(sender,
            f"*AntiFake*\nStatus: {status}\nBlocked codes: {codes}")
        return True

    cmd2 = parts[1].lower()
    args = parts[2] if len(parts) > 2 else ""

    if cmd2 in ("on", "off"):
        cfg = _get_config(session_name)
        cfg["enabled"] = (cmd2 == "on")
        _save_config(session_name)
        await wapp.send_text(sender, f"✅ AntiFake {cmd2}")
        return True

    if cmd2 == "add" and args:
        cfg = _get_config(session_name)
        code = args.replace("+", "").strip()
        if code and code not in cfg["codes"]:
            cfg["codes"].append(code)
            _save_config(session_name)
        await wapp.send_text(sender, f"✅ Blocked country code: +{code}")
        return True

    if cmd2 == "remove" and args:
        cfg = _get_config(session_name)
        code = args.replace("+", "").strip()
        if code in cfg["codes"]:
            cfg["codes"].remove(code)
            _save_config(session_name)
        await wapp.send_text(sender, f"✅ Unblocked country code: +{code}")
        return True

    if cmd2 == "list":
        cfg = _get_config(session_name)
        if cfg["codes"]:
            text = "🚫 *Blocked Country Codes:*\n" + "\n".join(f"  • +{c}" for c in cfg["codes"])
            await wapp.send_text(sender, text)
        else:
            await wapp.send_text(sender, "No country codes blocked.")
        return True

    await wapp.send_text(sender, "Usage: !antifake on/off | add/remove <code> | list")
    return True


def register(session_ref):
    session_ref.features["plugins"].register_command("!antifake", "Block numbers from specific countries")
