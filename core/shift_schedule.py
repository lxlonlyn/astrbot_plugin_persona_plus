from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


def parse_hhmm(value: str) -> int:
    """Parse HH:MM into minutes since midnight."""

    text = str(value).strip()
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError("时间必须使用 HH:MM 格式。")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise ValueError("时间必须使用 HH:MM 格式。") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("时间必须在 00:00 到 23:59 之间。")
    return hour * 60 + minute


def format_hhmm(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass(slots=True)
class ShiftDecision:
    target_persona: str
    boundary_at: datetime
    in_primary_window: bool


@dataclass(slots=True)
class ShiftRuntimeState:
    """Ephemeral per-conversation state used for safe handover timing."""

    turn_inflight: bool = False
    turn_started_at_utc: datetime | None = None
    last_turn_finished_at_utc: datetime | None = None
    pending_persona: str | None = None


def resolve_shift(
    *,
    now: datetime,
    start_minutes: int,
    end_minutes: int,
    primary_persona: str,
    secondary_persona: str,
) -> ShiftDecision:
    """Resolve scheduled persona and the boundary that activated it.

    now must be timezone-aware. The primary window is [start, end).
    When start > end, the primary window crosses midnight.
    """

    if now.tzinfo is None:
        raise ValueError("now 必须包含时区信息。")
    if start_minutes == end_minutes:
        raise ValueError("轮班开始时间和结束时间不能相同。")

    minute_of_day = now.hour * 60 + now.minute
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def at(minutes: int, day_offset: int = 0) -> datetime:
        return midnight + timedelta(
            days=day_offset,
            hours=minutes // 60,
            minutes=minutes % 60,
        )

    if start_minutes < end_minutes:
        in_primary = start_minutes <= minute_of_day < end_minutes
        if in_primary:
            boundary = at(start_minutes)
        elif minute_of_day >= end_minutes:
            boundary = at(end_minutes)
        else:
            boundary = at(end_minutes, -1)
    else:
        # Primary window crosses midnight, e.g. 19:00 -> 07:00.
        in_primary = minute_of_day >= start_minutes or minute_of_day < end_minutes
        if in_primary:
            boundary = (
                at(start_minutes)
                if minute_of_day >= start_minutes
                else at(start_minutes, -1)
            )
        else:
            boundary = at(end_minutes)

    return ShiftDecision(
        target_persona=primary_persona if in_primary else secondary_persona,
        boundary_at=boundary,
        in_primary_window=in_primary,
    )
