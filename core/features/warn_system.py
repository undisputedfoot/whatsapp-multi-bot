"""
Warn System — group moderation with warn/kick thresholds.
Like Levanter's warn system.
"""

from .. import db


class WarnSystem:
    """Warn/kick moderation for groups."""

    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)
        self._warn_limit = 3

    async def handle_command(self, cmd, parts, body, sender, wapp, lang, session_name: str) -> bool:
        """Handle warn-related commands."""

        if cmd == "!warn":
            target = parts[1] if len(parts) > 1 else ""
            if not target:
                await wapp.send_text(sender, "❌ Usage: !warn @user or !warn 1234567890")
                return True

            warns = db.get_warns(target, sender) + 1
            db.set_warns(target, sender, warns)
            limit = self._warn_limit
            remaining = limit - warns

            if remaining <= 0:
                await wapp.send_text(sender, f"⚠️ *{target}* kicked (warn limit reached).")
                db.clear_warns(target, sender)
            else:
                await wapp.send_text(sender, f"⚠️ Warn {target}: {warns}/{limit} ({remaining} left)")
            return True

        elif cmd in ("!warnreset", "!resetwarns"):
            target = parts[1] if len(parts) > 1 else ""
            if not target:
                await wapp.send_text(sender, "❌ Usage: !warnreset @user")
                return True
            db.clear_warns(target, sender)
            await wapp.send_text(sender, f"✅ Warns reset for {target}")
            return True

        elif cmd == "!warns":
            target = parts[1] if len(parts) > 1 else ""
            if target:
                warns = db.get_warns(target, sender)
                await wapp.send_text(sender, f"⚠️ {target}: {warns} warn(s)")
            else:
                await wapp.send_text(sender, "⚠️ Usage: !warns @user")
            return True

        return False
