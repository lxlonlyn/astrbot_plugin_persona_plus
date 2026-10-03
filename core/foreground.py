from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class ForegroundLease:
    """Temporary foreground speaker state for exactly one conversation."""

    persona_id: str
    expires_at_utc: datetime
    remaining_turns: int

    def is_active(self, now_utc: datetime) -> bool:
        return self.remaining_turns > 0 and now_utc < self.expires_at_utc

    def consume(self, *, now_utc: datetime, ttl_seconds: int) -> None:
        self.remaining_turns = max(0, self.remaining_turns - 1)
        self.expires_at_utc = now_utc + timedelta(seconds=max(0, ttl_seconds))


def make_foreground_lease(
    *,
    persona_id: str,
    ttl_seconds: int,
    followup_turns: int,
    now_utc: datetime | None = None,
) -> ForegroundLease:
    now = now_utc or datetime.now(timezone.utc)
    return ForegroundLease(
        persona_id=persona_id,
        expires_at_utc=now + timedelta(seconds=max(0, ttl_seconds)),
        remaining_turns=max(0, followup_turns),
    )


def render_speaker_block(
    persona_id: str,
    reply: str,
    *,
    initial: bool,
) -> str:
    """Render a visible but implementation-agnostic speaker marker."""

    label = (
        f"【{persona_id}｜临时插话】"
        if initial
        else f"【{persona_id}】"
    )
    return f"{label}\n\n{reply.strip()}"


def conversation_state_key(
    unified_msg_origin: str,
    conversation_id: str | None,
) -> str:
    """Build an isolation key that cannot leak runtime state across chats."""

    return f"{unified_msg_origin}:{conversation_id or '<current>'}"
