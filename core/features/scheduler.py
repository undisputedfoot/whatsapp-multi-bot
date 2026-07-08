"""
Scheduled Messages — sends queued messages at their appointed time.
Also handles birthday reminders.
"""

import asyncio
from datetime import datetime

from .. import db
from ..config import AUTO_REPLY_ON


class Scheduler:
    def __init__(self, manager_ref, on_log=None):
        """
        manager_ref: reference to the global Manager so we can get WApp instances
        """
        self._manager = manager_ref
        self._log = on_log or (lambda *a: None)
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._schedule_loop())
        asyncio.create_task(self._birthday_loop())
        self._log("scheduler", "⏰ Scheduler started")

    async def _schedule_loop(self):
        """Check every 15 seconds for pending scheduled messages."""
        while self._running:
            try:
                pending = db.get_pending_scheduled()
                for msg in pending:
                    sess = self._manager.get_session(msg["session"])
                    if sess and sess.wapp and sess.wapp.connected:
                        await sess.wapp.send_text(msg["peer"], msg["body"])
                        db.mark_scheduled_sent(msg["id"])
                        self._log("scheduler",
                            f"📨 Sent scheduled to {msg['peer']}: {msg['body'][:50]}")
            except Exception as e:
                self._log("scheduler", f"⚠️ Schedule error: {e}")
            await asyncio.sleep(15)

    async def _birthday_loop(self):
        """Check once per hour for today's birthdays."""
        last_check = ""
        while self._running:
            today = datetime.utcnow().strftime("%m-%d")
            if today != last_check:
                last_check = today
                for sname in list(self._manager.sessions.keys()):
                    try:
                        birthdays = db.get_todays_birthdays(sname)
                        for b in birthdays:
                            sess = self._manager.get_session(sname)
                            if sess and sess.wapp and sess.wapp.connected:
                                msg = f"🎂 Happy Birthday {b['name'] or b['peer']}! 🎉"
                                await sess.wapp.send_text(b["peer"], msg)
                                self._log("scheduler",
                                    f"🎂 Birthday wish sent to {b['name'] or b['peer']}")
                    except Exception:
                        pass
            await asyncio.sleep(3600)  # every hour

    def stop(self):
        self._running = False
