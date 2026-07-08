"""
Custom Commands — user-defined !commands like Levanter's setcmd/getcmd/delcmd.
"""

from .. import db


class CustomCommands:
    """User-defined command system."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._cache = {}

    def _load(self, session: str):
        """Load custom commands from DB."""
        if session not in self._cache:
            cmds = db.get_custom_commands(session)
            self._cache[session] = {cmd["name"]: cmd["response"] for cmd in cmds}
        return self._cache[session]

    def get_response(self, session: str, cmd_name: str) -> str | None:
        """Get response for a custom command."""
        cmds = self._load(session)
        return cmds.get(cmd_name)

    async def handle_command(self, cmd, parts, body, sender, wapp, lang, session_name: str) -> bool:
        """Handle setcmd/getcmd/delcmd commands."""

        if cmd == "!setcmd":
            # !setcmd name response text here
            rest = body[len("!setcmd "):].strip() if len(body) > 8 else ""
            space_idx = rest.find(" ")
            if space_idx == -1:
                await wapp.send_text(sender, "❌ Usage: !setcmd name response text")
                return True
            name = rest[:space_idx].strip().lower()
            response = rest[space_idx:].strip()
            if not name or not response:
                await wapp.send_text(sender, "❌ Usage: !setcmd name response text")
                return True
            db.set_custom_command(session_name, name, response)
            self._cache.pop(session_name, None)
            await wapp.send_text(sender, f"✅ Command !{name} saved!")
            return True

        elif cmd == "!delcmd":
            name = parts[1] if len(parts) > 1 else ""
            if not name:
                await wapp.send_text(sender, "❌ Usage: !delcmd name")
                return True
            name = name.lower().lstrip("!")
            db.delete_custom_command(session_name, name)
            self._cache.pop(session_name, None)
            await wapp.send_text(sender, f"✅ Command !{name} deleted")
            return True

        elif cmd == "!listcmds":
            cmds = db.get_custom_commands(session_name)
            if not cmds:
                await wapp.send_text(sender, "📋 No custom commands. Use !setcmd name text")
            else:
                msg = "📋 *Custom Commands:*\n" + "\n".join(f"!{c['name']}" for c in cmds)
                await wapp.send_text(sender, msg)
            return True

        return False
