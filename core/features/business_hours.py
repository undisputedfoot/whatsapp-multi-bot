"""
Business Hours — only auto-reply during configured hours.
Outside hours, sends a "we're closed" message.
"""

from datetime import datetime, timezone, timedelta
from ..config import (BIZ_HOURS_ENABLED, BIZ_HOURS_START, BIZ_HOURS_END,
                      BIZ_HOURS_TZ, BIZ_HOURS_WEEKDAYS, BIZ_CLOSED_MSG)
from .. import db


class BusinessHours:
    """Check if within business hours before auto-replying."""

    def is_open_now(self, session: str = None) -> bool:
        """Check if current time falls within business hours."""
        if not BIZ_HOURS_ENABLED:
            return True

        # Check session-specific config first
        if session:
            cfg = db.get_business_hours(session)
            if cfg:
                if not cfg.get("enabled", 0):
                    return True
                start_t = cfg.get("start_time", BIZ_HOURS_START)
                end_t = cfg.get("end_time", BIZ_HOURS_END)
                weekdays = cfg.get("weekdays", BIZ_HOURS_WEEKDAYS)
            else:
                start_t, end_t, weekdays = BIZ_HOURS_START, BIZ_HOURS_END, BIZ_HOURS_WEEKDAYS
        else:
            start_t, end_t, weekdays = BIZ_HOURS_START, BIZ_HOURS_END, BIZ_HOURS_WEEKDAYS

        now = datetime.now()
        weekday = str(now.weekday() + 1)  # 1=Mon .. 7=Sun
        allowed_days = [d.strip() for d in weekdays.split(",")]

        if weekday not in allowed_days:
            return False

        current_min = now.hour * 60 + now.minute
        start_parts = start_t.split(":")
        end_parts = end_t.split(":")
        start_min = int(start_parts[0]) * 60 + int(start_parts[1])
        end_min = int(end_parts[0]) * 60 + int(end_parts[1])

        return start_min <= current_min < end_min

    def get_closed_message(self, session: str = None) -> str:
        """Get the configured closed message."""
        if session:
            cfg = db.get_business_hours(session)
            if cfg and cfg.get("closed_msg"):
                return cfg["closed_msg"]

        return BIZ_CLOSED_MSG.format(
            start=BIZ_HOURS_START,
            end=BIZ_HOURS_END
        )
