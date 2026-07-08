"""
AntiWords — bad word filter for groups (like Levanter's antiwords.js).
Usage: !antiword on/off, !antiword add/remove <word>, !antiword action kick/warn/null
"""

from core import db

# In-memory cache: {group_jid: {"enabled": bool, "action": str, "words": list}}
_cache = {}

def _get_config(group_jid):
    if group_jid not in _cache:
        cfg = db.get_setting(f"antiwords:{group_jid}", "")
        if cfg:
            import json
            try:
                _cache[group_jid] = json.loads(cfg)
            except (json.JSONDecodeError, TypeError):
                _cache[group_jid] = {"enabled": False, "action": "warn", "words": []}
        else:
            _cache[group_jid] = {"enabled": False, "action": "warn", "words": []}
    return _cache[group_jid]

def _save_config(group_jid):
    import json
    db.set_setting(f"antiwords:{group_jid}", json.dumps(_cache[group_jid]))

async def check_message(body: str, group_jid: str, wapp, lang: str) -> bool:
    """Check message against bad words. Returns True if action taken."""
    cfg = _get_config(group_jid)
    if not cfg["enabled"] or not cfg["words"]:
        return False

    body_lower = body.lower()
    for word in cfg["words"]:
        if word.lower() in body_lower:
            action = cfg["action"]
            if action == "warn":
                try:
                    current = db.get_warns("__unknown__", group_jid)
                    db.set_warns("__unknown__", group_jid, current + 1)
                    await wapp.send_text(group_jid,
                        f"⚠️ Bad word detected! Warn {current+1}/3")
                except Exception:
                    await wapp.send_text(group_jid,
                        f"⚠️ Watch your language!")
                return True
            elif action == "kick":
                await wapp.send_text(group_jid,
                    f"⚠️ Kicked for bad words!")
                return True
            else:
                await wapp.send_text(group_jid, f"⚠️ Bad word detected!")
                return True
    return False

async def handle_command(cmd, parts, body, sender, wapp, lang, session_name=""):
    if cmd != "!antiword":
        return False

    group_jid = sender if "@g.us" in sender else ""
    if not group_jid:
        await wapp.send_text(sender, "❌ Antiwords only works in groups!")
        return True

    if len(parts) < 2:
        cfg = _get_config(group_jid)
        status = "on" if cfg["enabled"] else "off"
        action = cfg["action"]
        words = ", ".join(cfg["words"]) if cfg["words"] else "none"
        await wapp.send_text(group_jid,
            f"*AntiWords*\nStatus: {status}\nAction: {action}\nWords: {words}")
        return True

    cmd2 = parts[1].lower()
    args = " ".join(parts[2:]) if len(parts) > 2 else ""

    if cmd2 in ("on", "off"):
        cfg = _get_config(group_jid)
        cfg["enabled"] = (cmd2 == "on")
        _save_config(group_jid)
        await wapp.send_text(group_jid, f"✅ AntiWords {cmd2}")
        return True

    if cmd2 in ("kick", "warn", "null"):
        cfg = _get_config(group_jid)
        cfg["action"] = cmd2
        _save_config(group_jid)
        await wapp.send_text(group_jid, f"✅ AntiWords action: {cmd2}")
        return True

    if cmd2 == "add" and args:
        cfg = _get_config(group_jid)
        for w in args.split(","):
            w = w.strip()
            if w and w not in cfg["words"]:
                cfg["words"].append(w)
        _save_config(group_jid)
        await wapp.send_text(group_jid, f"✅ Added words: {args}")
        return True

    if cmd2 == "remove" and args:
        cfg = _get_config(group_jid)
        for w in args.split(","):
            w = w.strip()
            if w in cfg["words"]:
                cfg["words"].remove(w)
        _save_config(group_jid)
        await wapp.send_text(group_jid, f"✅ Removed words: {args}")
        return True

    if cmd2 == "clear":
        cfg = _get_config(group_jid)
        cfg["words"] = []
        _save_config(group_jid)
        await wapp.send_text(group_jid, "✅ All words cleared")
        return True

    await wapp.send_text(group_jid, "Usage: !antiword on/off | add/remove <word> | action kick/warn/null | clear")
    return True


def register(session_ref):
    session_ref.features["plugins"].register_command("!antiword", "Bad word filter for groups")
