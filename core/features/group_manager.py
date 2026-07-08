"""
Group Manager — welcome messages, anti-spam, admin commands, member tracking, broadcast.
Integrates with the Session event system.
"""

import re
import asyncio
from .. import db
from ..config import (ADMIN_NUMBERS, GROUP_WELCOME_ON, GROUP_ANTI_LINK,
                      GROUP_ANTI_LINK_ACTION, GROUP_AUTO_REPLY_IN_GROUPS,
                      BROADCAST_INTERVAL_SEC)
from ..lang import t


# ── Compiled patterns ─────────────────────────────────
URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)


class GroupManager:
    """Per-session group management."""

    def __init__(self, session_ref, on_log=None):
        """
        session_ref: the Session instance this belongs to.
        """
        self.sess = session_ref
        self._log = on_log or (lambda *a: None)

    # ── Event: new message (possibly in a group) ───

    async def handle_message(self, msg: dict, body: str, sender: str):
        """Process a message for group-specific features. Called BEFORE commands."""
        # Detect if this is a group chat (WhatsApp group IDs contain '-')
        is_group = msg.get("isGroup", False) or "-" in sender
        if not is_group:
            return False

        group_id = sender  # sender IS the group ID for group messages
        chat_id = msg.get("chatId", group_id)

        # Track member activity
        db.upsert_group_member(self.sess.name, chat_id, sender, role="member")
        db.upsert_group_config(self.sess.name, chat_id)

        # Anti-link (if enabled)
        if GROUP_ANTI_LINK and not await self._is_admin(sender):
            if URL_PATTERN.search(body):
                await self._handle_link_in_group(chat_id, sender, body)
                return True  # message was handled (warned/deleted)

        return False

    # ── Event: group join/leave ──────────────────

    async def handle_group_event(self, evt: dict):
        """Called when a member joins or leaves a group."""
        evt_type = evt.get("type", "")  # 'join' or 'leave'
        group_id = evt.get("groupId", "")
        peer = evt.get("peer", "")

        if not group_id:
            return

        if evt_type == "join" and GROUP_WELCOME_ON:
            cfg = db.get_group_config(self.sess.name, group_id)
            welcome = (cfg or {}).get("welcome_msg", "")
            if welcome:
                await self.sess.wapp.send_text(group_id, welcome)
            else:
                default_welcome = (
                    f"👋 Welcome! Use *!grouprules* to see the group rules."
                )
                await self.sess.wapp.send_text(group_id, default_welcome)

            self._log("group", f"👋 Welcome sent in {group_id[:15]}...")

        db.upsert_group_member(self.sess.name, group_id, peer,
                               role="member" if evt_type == "join" else "left")

    # ── Commands ────────────────────────────────

    async def handle_command(self, cmd: str, parts: list[str],
                             body: str, sender: str) -> bool:
        """Returns True if the command was a group command."""
        is_group = "-" in sender

        if cmd == "!grouprules" and is_group:
            await self._cmd_rules(sender)
            return True

        if cmd == "!groupwelcome":
            await self._cmd_welcome(parts, body, sender)
            return True

        if cmd == "!grouplink" and is_group:
            await self._cmd_anti_link(parts, sender)
            return True

        if cmd == "!promote" and is_group:
            await self._cmd_promote(parts, sender)
            return True

        if cmd == "!demote" and is_group:
            await self._cmd_demote(parts, sender)
            return True

        if cmd == "!kick" and is_group:
            await self._cmd_kick(parts, sender)
            return True

        if cmd == "!groupstats" and is_group:
            await self._cmd_stats(sender)
            return True

        if cmd == "!admins":
            await self._cmd_list_admins(sender)
            return True

        if cmd == "!addadmin":
            await self._cmd_add_admin(parts, sender)
            return True

        if cmd == "!removeadmin":
            await self._cmd_remove_admin(parts, sender)
            return True

        if cmd == "!broadcast":
            await self._cmd_broadcast(parts, body, sender)
            return True

        return False

    # ── Command implementations ─────────────────

    async def _cmd_rules(self, group_id: str):
        cfg = db.get_group_config(self.sess.name, group_id)
        rules = (cfg or {}).get("rules", "")
        if rules:
            await self.sess.wapp.send_text(group_id, f"📋 *Group Rules:*\n{rules}")
        else:
            await self.sess.wapp.send_text(group_id,
                "📋 No rules set. An admin can set them with:\n"
                "!grouprules Be respectful, no spam")

    async def _cmd_welcome(self, parts: list, body: str, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        # !groupwelcome Welcome message here
        match = re.match(r'!groupwelcome\s+(.+)', body, re.DOTALL)
        if match:
            welcome = match.group(1).strip()
            db.upsert_group_config(self.sess.name, sender, welcome_msg=welcome)
            await self.sess.wapp.send_text(sender, "✅ Welcome message updated!")
        else:
            db.upsert_group_config(self.sess.name, sender, welcome_msg="")
            await self.sess.wapp.send_text(sender, "✅ Welcome message cleared.")

    async def _cmd_anti_link(self, parts: list, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        sub = parts[1] if len(parts) > 1 else ""
        if sub in ("on", "true", "1"):
            db.upsert_group_config(self.sess.name, sender, anti_link=1)
            await self.sess.wapp.send_text(sender, "✅ Anti-link enabled.")
        elif sub in ("off", "false", "0"):
            db.upsert_group_config(self.sess.name, sender, anti_link=0)
            await self.sess.wapp.send_text(sender, "✅ Anti-link disabled.")
        else:
            await self.sess.wapp.send_text(sender,
                "Usage: !grouplink on  |  !grouplink off")

    async def _cmd_promote(self, parts: list, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        if len(parts) >= 2:
            target = parts[1].replace("@", "").replace(" ", "")
            await self.sess.wapp.send_text(sender,
                f"✅ Promotion request sent for {target}. "
                f"(Requires WhatsApp Web group admin privileges)")
            self._log("group", f"Promote {target} in {sender[:15]}")

    async def _cmd_demote(self, parts: list, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        if len(parts) >= 2:
            target = parts[1].replace("@", "").replace(" ", "")
            await self.sess.wapp.send_text(sender,
                f"✅ Demotion request sent for {target}.")

    async def _cmd_kick(self, parts: list, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        if len(parts) >= 2:
            target = parts[1].replace("@", "").replace(" ", "")
            await self.sess.wapp.send_text(sender,
                f"✅ Removal request sent for {target}.")

    async def _cmd_stats(self, group_id: str):
        stats = db.get_group_stats(self.sess.name, group_id)
        members = db.get_group_members(self.sess.name, group_id)
        top = members[:5]
        text = (f"📊 *Group Stats*\n"
                f"👥 Members: {stats['total_members']}\n"
                f"🛡️ Admins: {stats['admins']}\n")
        if top:
            text += "\n*Most Active:*\n" + "\n".join(
                f"  {i+1}. {m['peer'][:10]}... ({m['msg_count']} msgs)"
                for i, m in enumerate(top)
            )
        await self.sess.wapp.send_text(group_id, text)

    async def _cmd_list_admins(self, sender: str):
        admins = db.get_admins(self.sess.name)
        env_admins = ADMIN_NUMBERS
        text = "🛡️ *Bot Admins:*\n"
        for a in admins:
            text += f"  • {a['peer']} ({a['role']})\n"
        for n in env_admins:
            text += f"  • {n} (super-admin)\n"
        if not admins and not env_admins:
            text += "  No admins configured.\n"
        text += "\n_Add: !addadmin 15551234567_\n_Remove: !removeadmin 15551234567_"
        await self.sess.wapp.send_text(sender, text)

    async def _cmd_add_admin(self, parts: list, sender: str):
        if not await self._is_super_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Only super-admins can add admins.")
            return
        if len(parts) >= 2:
            target = parts[1].replace("@", "").replace(" ", "")
            db.add_admin(self.sess.name, target)
            await self.sess.wapp.send_text(sender, f"✅ {target} added as admin.")

    async def _cmd_remove_admin(self, parts: list, sender: str):
        if not await self._is_super_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Only super-admins can remove admins.")
            return
        if len(parts) >= 2:
            target = parts[1].replace("@", "").replace(" ", "")
            db.remove_admin(self.sess.name, target)
            await self.sess.wapp.send_text(sender, f"✅ {target} removed from admins.")

    async def _cmd_broadcast(self, parts: list, body: str, sender: str):
        if not await self._is_admin(sender):
            await self.sess.wapp.send_text(sender, "❌ Admin only.")
            return
        # !broadcast listname Message text
        match = re.match(r'!broadcast\s+(\S+)\s+(.+)', body, re.DOTALL)
        if match:
            list_name = match.group(1)
            msg_text = match.group(2).strip()
            lists = db.get_broadcast_lists(self.sess.name)
            target = None
            for lst in lists:
                if lst["name"].lower() == list_name.lower():
                    target = lst
                    break
            if target:
                peers = target["members"]
                await self.sess.wapp.send_text(sender,
                    f"📨 Broadcasting to {len(peers)} recipients...")
                self._log("broadcast", f"Sending to {len(peers)} contacts...")
                asyncio.create_task(self._do_broadcast(peers, msg_text))
            else:
                await self.sess.wapp.send_text(sender,
                    f"❌ List '{list_name}' not found. Create one in the web dashboard.")
        else:
            await self.sess.wapp.send_text(sender,
                "Usage: !broadcast listname Your message here")

    async def _do_broadcast(self, peers: list[str], text: str):
        """Send messages with a delay between each."""
        for i, peer in enumerate(peers):
            if self.sess.wapp and self.sess.wapp.connected:
                await self.sess.wapp.send_text(peer, text)
                if i < len(peers) - 1:
                    await asyncio.sleep(BROADCAST_INTERVAL_SEC)
        self._log("broadcast", f"✅ Broadcast complete to {len(peers)} recipients.")

    # ── Helpers ────────────────────────────────

    async def _handle_link_in_group(self, group_id: str, sender: str, body: str):
        """Take action on a link posted by a non-admin."""
        action = GROUP_ANTI_LINK_ACTION
        if action == "warn":
            await self.sess.wapp.send_text(group_id,
                f"⚠️ @{sender[:8]} Links are not allowed in this group.")

    async def _is_admin(self, peer: str) -> bool:
        """Check if peer is a bot admin (DB or env)."""
        if db.is_admin(self.sess.name, peer):
            return True
        if peer in ADMIN_NUMBERS:
            return True
        return False

    async def _is_super_admin(self, peer: str) -> bool:
        """Super-admins are only from env var."""
        return peer in ADMIN_NUMBERS
