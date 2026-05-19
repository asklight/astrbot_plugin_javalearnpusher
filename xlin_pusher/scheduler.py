from __future__ import annotations

import re
from datetime import datetime

from .models import ScheduleState

PUSH_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def is_valid_push_time(value: str) -> bool:
    return bool(PUSH_TIME_RE.match(value or ""))


def should_push_now(state: ScheduleState, now: datetime) -> bool:
    if not state.enabled or not state.target_session or not is_valid_push_time(state.push_time):
        return False
    if now.strftime("%H:%M") != state.push_time:
        return False
    return state.last_push_date != now.date().isoformat()
