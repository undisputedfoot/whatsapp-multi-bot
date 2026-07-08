"""
Call Blocker — automatically reject incoming calls with optional message.
"""

from ..config import AUTO_REJECT_CALLS, CALL_REJECT_MSG
from ..lang import t


class CallBlocker:
    def __init__(self, on_log=None):
        self._log = on_log or (lambda *a: None)

    async def handle(self, call: dict, wapp, session_name: str):
        if not AUTO_REJECT_CALLS:
            return
        try:
            caller = call.get("from", "unknown")
            call_id = call.get("id", "")

            # Reject the call
            await wapp.reject_call(call_id)
            self._log("call_blocker", f"📞 Rejected call from {caller}")

            # Send optional rejection message
            msg = CALL_REJECT_MSG or t("en", "call_rejected", number=caller)
            if msg:
                await wapp.send_text(caller, msg)

        except Exception as e:
            self._log("call_blocker", f"Error rejecting call: {e}")
