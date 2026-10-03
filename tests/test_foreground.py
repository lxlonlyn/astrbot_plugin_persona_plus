from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.foreground import (
    conversation_state_key,
    make_foreground_lease,
    render_speaker_block,
)


def test_foreground_lease_is_local_runtime_state_with_ttl_and_turn_budget():
    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
    lease = make_foreground_lease(
        persona_id="Plana",
        ttl_seconds=120,
        followup_turns=3,
        now_utc=now,
    )

    assert lease.persona_id == "Plana"
    assert lease.remaining_turns == 3
    assert lease.is_active(now + timedelta(seconds=119))
    assert not lease.is_active(now + timedelta(seconds=120))

    lease.consume(now_utc=now + timedelta(seconds=10), ttl_seconds=120)
    assert lease.remaining_turns == 2
    assert lease.expires_at_utc == now + timedelta(seconds=130)


def test_foreground_lease_expires_when_turn_budget_is_used():
    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
    lease = make_foreground_lease(
        persona_id="Plana",
        ttl_seconds=120,
        followup_turns=1,
        now_utc=now,
    )
    lease.consume(now_utc=now, ttl_seconds=120)

    assert lease.remaining_turns == 0
    assert not lease.is_active(now)


def test_speaker_marker_distinguishes_initial_interjection_and_followup():
    assert render_speaker_block(
        "Plana",
        "在，老师。",
        initial=True,
    ) == "【Plana｜临时插话】\n\n在，老师。"

    assert render_speaker_block(
        "Plana",
        "我还在。",
        initial=False,
    ) == "【Plana】\n\n我还在。"


def test_conversation_state_key_isolates_groups_and_conversations():
    group_a = conversation_state_key("qq:group:group-a", "conv-1")
    group_b = conversation_state_key("qq:group:group-b", "conv-1")
    group_a_other_conv = conversation_state_key("qq:group:group-a", "conv-2")

    assert group_a != group_b
    assert group_a != group_a_other_conv
    assert group_b != group_a_other_conv
