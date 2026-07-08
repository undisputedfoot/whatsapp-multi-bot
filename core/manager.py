"""
Multi-session manager. Creates, monitors, and destroys WApp sessions.
Integrates all features: auto-reply, AI, scheduler, birthdays, etc.
"""

import asyncio
import re
from datetime import datetime

from .whatsapp import WApp
from .config import (SESSION_NAMES, AUTO_REPLY_ON, AUTO_STATUS_VIEW,
                     READ_RECEIPTS, AUTO_REJECT_CALLS, STICKER_MAKER,
                     CALL_REJECT_MSG, AI_PROVIDER, AI_API_KEY, ADMIN_NUMBERS)
from .lang import t, supported_langs
from . import db

from core.features.auto_reply import AutoReply
from core.features.auto_status import AutoStatusViewer
from core.features.read_receipts import ReadReceipts
from core.features.call_blocker import CallBlocker
from core.features.sticker_maker import StickerMaker
from core.features.ai_reply import AIReply
from core.features.group_manager import GroupManager
from core.features.typing_engine import TypingEngine
from core.features.business_hours import BusinessHours
from core.features.persona_manager import PersonaManager
from core.features.group_games import GroupGames
from core.features.plugin_loader import PluginLoader
from core.features.auto_update import AutoUpdater
from core.features.warn_system import WarnSystem
from core.features.custom_cmds import CustomCommands
from core.features.anti_delete import AntiDelete


class Session:
    """Holds one WApp + its per-session state."""

    def __init__(self, name: str, on_log=None, manager_ref=None):
        self.name = name
        sess_db = db.get_session(name)
        self.lang = sess_db.get("language", "en") if sess_db else "en"
        self.auto_reply_on = AUTO_REPLY_ON
        self.ai_reply_on = bool(sess_db.get("ai_reply", 0)) if sess_db else False
        self.wapp = None  # Will be set to a WApp instance
        self._on_log = on_log or (lambda *a: None)
        self._manager = manager_ref
        self.features = {
            "auto_reply": AutoReply(on_log),
            "auto_status": AutoStatusViewer(on_log),
            "read_receipts": ReadReceipts(on_log),
            "call_blocker": CallBlocker(on_log),
            "sticker_maker": StickerMaker(on_log),
            "ai_reply": AIReply(on_log),
            "group_manager": GroupManager(self, on_log),
            "typing": TypingEngine(),
            "business_hours": BusinessHours(),
            "personas": PersonaManager(name),
            "games": GroupGames(on_log),
            "plugins": PluginLoader(on_log),
            "updater": AutoUpdater(on_log),
            "warn_system": WarnSystem(on_log),
            "custom_cmds": CustomCommands(on_log),
            "anti_delete": AntiDelete(on_log),
        }

    def log(self, msg: str):
        self._on_log(self.name, msg)

    # ── Event handlers ────────────────────────

    async def _on_qr(self, qr_data: str):
        db.upsert_session(self.name, status="qr")
        self.log(f"📱 QR generated for {self.name}")

    async def _on_ready(self):
        db.upsert_session(self.name, status="connected", language=self.lang,
                          auto_reply=int(self.auto_reply_on),
                          ai_reply=int(self.ai_reply_on))
        self.log(f"✅ {self.name} connected!")

        if AUTO_STATUS_VIEW:
            asyncio.create_task(
                self.features["auto_status"].start(self.wapp, self.name)
            )

        # Load plugins
        self.features["plugins"].load_all(self)

    async def _on_msg(self, msg: dict):
        body = (msg.get("body") or "").strip()
        sender = msg.get("from", "") or msg.get("chatId", "")
        msg_id = msg.get("id", "")

        if not body:
            return

        # Save to DB
        db.save_message(self.name, sender, "in", body, msg_id)
        db.upsert_chat(self.name, sender, last_msg=body[:80])

        # ── Anti-words check (group bad word filter) ──
        if ("@g.us" in sender or "-" in sender) and body:
            from plugins import antiwords
            blocked = await antiwords.check_message(body, sender, self.wapp, self.lang)
            if blocked:
                return

        # ── Group-specific processing (anti-link, member tracking) ──
        handled = await self.features["group_manager"].handle_message(msg, body, sender)
        if handled:
            return

        # ── Anti-delete tracking ──
        admin_num = ADMIN_NUMBERS[0] if ADMIN_NUMBERS else ""
        await self.features["anti_delete"].handle(msg, self.wapp, self.name, admin_num)

        # ── Commands ──
        if body.startswith("!"):
            await self._handle_cmd(body, sender)
            return

        # ── PDM check (block PMs from non-members) ──
        if "@g.us" not in sender and "-" not in sender:
            from plugins import pdm
            blocked = await pdm.check_pm(sender, self.name, self.wapp)
            if blocked:
                return

        # ── AI reply (takes priority) ──
        _has_ai_key = bool(AI_API_KEY)
        if AI_PROVIDER == "groq":
            from .config import GROQ_API_KEY as _k
            _has_ai_key = bool(_k)
        elif AI_PROVIDER == "nvidia":
            from .config import NVIDIA_API_KEY as _k
            _has_ai_key = bool(_k)
        elif AI_PROVIDER == "gemini":
            from .config import GOOGLE_API_KEY as _k
            _has_ai_key = bool(_k)
        if self.ai_reply_on and _has_ai_key:
            replied = await self.features["ai_reply"].handle(body, sender, self.wapp, self.lang)
            if replied:
                return

        # ── Business hours check ──
        if not self.features["business_hours"].is_open_now(self.name):
            closed_msg = self.features["business_hours"].get_closed_message(self.name)
            if self.auto_reply_on:
                await self.wapp.send_text(sender, closed_msg)
            return

        # ── Keyword auto-reply ──
        if self.auto_reply_on:
            replied = await self.features["auto_reply"].handle(body, sender, self.wapp, self.lang)
            if not replied:
                await self.features["auto_reply"].send_default(sender, self.wapp, self.lang)

        # ── Read receipts ──
        if READ_RECEIPTS:
            await self.features["read_receipts"].handle(msg, self.wapp)

    async def _on_call(self, call: dict):
        if AUTO_REJECT_CALLS:
            await self.features["call_blocker"].handle(call, self.wapp, self.name)

    async def _on_group_event(self, evt: dict):
        """Called when a member joins or leaves a group."""
        await self.features["group_manager"].handle_group_event(evt)

        # AntiFake check for new joiners
        if evt.get("type") == "join" and evt.get("peer"):
            from plugins import antifake
            await antifake.check_participant(
                evt["peer"], self.name, evt.get("groupId", ""), self.wapp
            )

    # ── Commands ─────────────────────────────

    async def _handle_cmd(self, body: str, sender: str):
        parts = body.lower().split()
        cmd = parts[0]

        # ── Tog check: skip if command is toggled off ──
        from plugins import tog as tog_plugin
        if not tog_plugin.is_command_enabled(self.name, cmd):
            return

        # ── Group/admin commands ──
        handled = await self.features["group_manager"].handle_command(cmd, parts, body, sender)
        if handled:
            return

        if cmd == "!help":
            text = f"{t(self.lang, 'help_title')}\n{t(self.lang, 'help_body')}"
            await self.wapp.send_text(sender, text)

        elif cmd == "!ping":
            n = len([s for s in (self._manager.sessions if self._manager else {}).values()
                     if s.wapp and s.wapp.connected])
            await self.wapp.send_text(sender, t(self.lang, "pong", n=n))

        elif cmd == "!sticker":
            if STICKER_MAKER:
                await self.features["sticker_maker"].handle(sender, self.wapp, self.lang)
            else:
                await self.wapp.send_text(sender, t(self.lang, "sticker_fail"))

        elif cmd in ("!lang", "!language"):
            if len(parts) >= 2:
                new = parts[1]
                if new in supported_langs():
                    self.lang = new
                    db.upsert_session(self.name, language=new)
                    await self.wapp.send_text(sender, t(new, "greeting"))
                else:
                    await self.wapp.send_text(sender, t(self.lang, "lang_prompt"))

        elif cmd == "!autoreply":
            sub = parts[1] if len(parts) > 1 else ""
            if sub == "on":
                self.auto_reply_on = True
                db.upsert_session(self.name, auto_reply=1)
                await self.wapp.send_text(sender, t(self.lang, "auto_on"))
            elif sub == "off":
                self.auto_reply_on = False
                db.upsert_session(self.name, auto_reply=0)
                await self.wapp.send_text(sender, t(self.lang, "auto_off"))
            elif sub == "status":
                st = "ON" if self.auto_reply_on else "OFF"
                await self.wapp.send_text(sender, f"Auto-reply: {st}")

        elif cmd == "!ai":
            # Check if the current provider's API key is configured
            provider_key = AI_API_KEY
            if AI_PROVIDER == "groq":
                from .config import GROQ_API_KEY
                provider_key = GROQ_API_KEY
            elif AI_PROVIDER == "nvidia":
                from .config import NVIDIA_API_KEY
                provider_key = NVIDIA_API_KEY
            elif AI_PROVIDER == "gemini":
                from .config import GOOGLE_API_KEY
                provider_key = GOOGLE_API_KEY
            if AI_PROVIDER == "none" or not provider_key:
                await self.wapp.send_text(sender, f"❌ {AI_PROVIDER} not configured. Set the API key in .env")
                return
            sub = parts[1] if len(parts) > 1 else ""
            if sub == "on":
                self.ai_reply_on = True
                db.upsert_session(self.name, ai_reply=1)
                await self.wapp.send_text(sender, t(self.lang, "ai_on"))
            elif sub == "off":
                self.ai_reply_on = False
                db.upsert_session(self.name, ai_reply=0)
                await self.wapp.send_text(sender, t(self.lang, "ai_off"))
            elif sub == "status":
                st = "ON" if self.ai_reply_on else "OFF"
                await self.wapp.send_text(sender, f"AI replies: {st}")

        elif cmd == "!persona":
            await self._handle_persona(parts, body, sender)

        elif cmd == "!trivia":
            if "-" in sender:  # only in groups
                await self.features["games"].handle_trivia(sender, self.wapp)
            else:
                await self.wapp.send_text(sender, "❌ Trivia is for groups only!")

        elif cmd == "!wyr":
            if "-" in sender:
                await self.features["games"].handle_wyr(sender, self.wapp)
            else:
                await self.wapp.send_text(sender, "❌ WYR is for groups only!")

        elif cmd == "!poll":
            if "-" in sender and len(parts) >= 3:
                poll_text = body[len("!poll "):]
                options = [o.strip() for o in poll_text.split("|")]
                if len(options) >= 2:
                    question = options[0]
                    choices = options[1:]
                    await self.features["games"].handle_poll(sender, question, choices, self.wapp)
                else:
                    await self.wapp.send_text(sender, "Usage: !poll Question? | Option1 | Option2 | Option3")
            else:
                await self.wapp.send_text(sender, "Usage: !poll Question? | Option1 | Option2 | Option3")

        elif cmd == "!update":
            if await self._is_admin(sender):
                msg = await self.features["updater"].update()
                await self.wapp.send_text(sender, msg)
            else:
                await self.wapp.send_text(sender, "❌ Admin only.")

        elif cmd == "!plugins":
            plugins = self.features["plugins"].discover()
            if plugins:
                text = "🔌 *Plugins:*\n" + "\n".join(f"  • {p['name']}" for p in plugins)
            else:
                text = "No plugins found. Add .py files to the plugins/ folder."
            await self.wapp.send_text(sender, text)

        elif cmd == "!schedule":
            await self._handle_schedule(parts, body, sender)

        elif cmd == "!sessions":
            lines = []
            ref = self._manager.sessions if self._manager else {}
            for s in ref.values():
                status = "🟢" if s.wapp and s.wapp.connected else "🔴"
                lines.append(f"  {status} {s.name}")
            text = "📡 *Sessions*\n" + "\n".join(lines) if lines else t(self.lang, "no_sessions")
            await self.wapp.send_text(sender, text)

        # ── Levanter: AntiWord (bad word filter) ──
        elif cmd == "!antiword":
            from plugins import antiwords
            handled = await antiwords.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: AntiFake (block numbers by country code) ──
        elif cmd == "!antifake":
            from plugins import antifake
            handled = await antifake.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: ISON (check if number is on WhatsApp) ──
        elif cmd == "!ison":
            from plugins import ison
            handled = await ison.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: MSGS (group message stats) ──
        elif cmd == "!msgs":
            from plugins import msgs_stats
            handled = await msgs_stats.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: PDM (private message mode) ──
        elif cmd == "!pdm":
            from plugins import pdm
            handled = await pdm.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: TOG (toggle commands on/off) ──
        elif cmd == "!tog":
            from plugins import tog
            handled = await tog.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: VARS (variable storage) ──
        elif cmd in ("!getvar", "!setvar", "!delvar", "!listvars"):
            from plugins import vars as vars_plugin
            handled = await vars_plugin.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: Facebook downloader ──
        elif cmd == "!fb":
            from plugins import facebook
            handled = await facebook.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: Story downloader ──
        elif cmd == "!story":
            from plugins import story
            handled = await story.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: Screenshot (ss/fullss) ──
        elif cmd in ("!ss", "!fullss"):
            from plugins import ss
            handled = await ss.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: QR code ──
        elif cmd == "!qr":
            from plugins import qr
            handled = await qr.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: Profile (jid/block/fullpp) ──
        elif cmd in ("!jid", "!block", "!fullpp"):
            from plugins import profile
            handled = await profile.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: Exif sticker viewer ──
        elif cmd == "!exif":
            from plugins import exif
            handled = await exif.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: RemoveBG ──
        elif cmd == "!rmbg":
            from plugins import removebg
            handled = await removebg.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Levanter: APK downloader ──
        elif cmd == "!apk":
            from plugins import apk
            handled = await apk.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Custom commands (setcmd/delcmd/listcmds) ──
        elif cmd in ("!setcmd", "!delcmd", "!listcmds"):
            handled = await self.features["custom_cmds"].handle_command(
                cmd, parts, body, sender, self.wapp, self.lang, self.name
            )
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Warn system (warn/warnreset/warns) ──
        elif cmd in ("!warn", "!warnreset", "!warns"):
            handled = await self.features["warn_system"].handle_command(
                cmd, parts, body, sender, self.wapp, self.lang, self.name
            )
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Plugin: tagall (mention all group members) ──
        elif cmd == "!tagall":
            from plugins import tagall
            handled = await tagall.handle_command(cmd, parts, body, sender, self.wapp, self.lang, self.name)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Plugin: weather (get weather for a city) ──
        elif cmd == "!weather":
            from plugins import weather
            handled = await weather.handle_command(cmd, parts, body, sender, self.wapp, self.lang)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Plugin downloader (yt/yta/tiktok/instagram) ──
        elif cmd in ("!yt", "!yta", "!tiktok", "!instagram"):
            from plugins import downloader
            handled = await downloader.handle_command(cmd, parts, body, sender, self.wapp, self.lang)
            if not handled:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

        # ── Custom command lookup (user-defined !commands) ──
        else:
            # Check if it's a stored custom command
            response = self.features["custom_cmds"].get_response(self.name, cmd)
            if response:
                await self.wapp.send_text(sender, response)
            else:
                await self.wapp.send_text(sender, t(self.lang, "not_found"))

    async def _handle_persona(self, parts: list, body: str, sender: str):
        """Switch or list AI personas."""
        if len(parts) < 2:
            personas = self.features["personas"].list_personas()
            text = "🧠 *Available Personas:*\n"
            for p in personas:
                mark = " ✅" if p.get("key", "").lower() == self.features["personas"].current_persona.lower() else ""
                text += f"  • {p['name']}{mark}\n"
            text += "\nUse: !persona <name>"
            await self.wapp.send_text(sender, text)
        else:
            name = " ".join(parts[1:])
            if self.features["personas"].set_persona(name):
                await self.wapp.send_text(sender, f"🧠 Switched to *{name}* persona!")
            else:
                await self.wapp.send_text(sender, f"❌ Persona '{name}' not found. Use !persona to list.")

    async def _is_admin(self, peer: str) -> bool:
        """Check if peer is a bot admin."""
        if db.is_admin(self.name, peer):
            return True
        if peer in ADMIN_NUMBERS:
            return True
        return False

    async def _handle_schedule(self, parts: list, body: str, sender: str):
        """!schedule YYYY-MM-DD HH:MM message text"""
        if len(parts) < 4:
            await self.wapp.send_text(sender, t(self.lang, "schedule_help"))
            return

        match = re.match(r'!schedule\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)', body)
        if not match:
            await self.wapp.send_text(sender, t(self.lang, "schedule_help"))
            return

        date_str, time_str, msg_text = match.groups()
        send_at = f"{date_str} {time_str}:00"
        db.add_scheduled(self.name, sender, msg_text, send_at)
        await self.wapp.send_text(sender, t(self.lang, "schedule_done", time=f"{date_str} {time_str}"))

    # ── Start / Stop ─────────────────────────

    async def start(self):
        self.wapp = WApp(
            name=self.name,
            on_qr=self._on_qr,
            on_ready=self._on_ready,
            on_msg=self._on_msg,
            on_call=self._on_call,
            on_group_event=self._on_group_event,
        )
        await self.wapp.start()

    async def stop(self):
        if self.wapp:
            await self.wapp.stop()


# ──────────────────────────────────────────────
#  Global manager (singleton)
# ──────────────────────────────────────────────

class Manager:
    """Manages all sessions."""

    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self.logs: list[dict] = []
        self.scheduler = None

    def _on_log(self, session: str, msg: str):
        entry = {"time": datetime.utcnow().isoformat(), "session": session, "msg": msg}
        self.logs.append(entry)
        # Keep last 500 logs in memory
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    async def start_all(self):
        db.migrate()
        for name in SESSION_NAMES:
            sess = Session(name, on_log=self._on_log, manager_ref=self)
            self.sessions[name] = sess
            await sess.start()
            await asyncio.sleep(3)

        # Start scheduler
        from core.features.scheduler import Scheduler
        self.scheduler = Scheduler(self, on_log=self._on_log)
        await self.scheduler.start()

    async def stop_all(self):
        if self.scheduler:
            self.scheduler.stop()
        for sess in self.sessions.values():
            await sess.stop()
        self.sessions.clear()

    def get_session(self, name: str) -> Session | None:
        return self.sessions.get(name)

    def status_summary(self) -> list[dict]:
        return [
            {
                "name": s.name,
                "connected": s.wapp.connected if s.wapp else False,
                "lang": s.lang,
                "auto_reply": s.auto_reply_on,
                "ai_reply": s.ai_reply_on,
            }
            for s in self.sessions.values()
        ]


manager = Manager()
