from datetime import datetime, timedelta, timezone

import pytest

from core.shift_schedule import parse_hhmm, resolve_shift, should_handover


TZ = timezone(timedelta(hours=8))


def test_parse_hhmm():
    assert parse_hhmm("07:00") == 420
    assert parse_hhmm("23:59") == 1439
    with pytest.raises(ValueError):
        parse_hhmm("24:00")
    with pytest.raises(ValueError):
        parse_hhmm("7")


def test_day_window_boundaries():
    start = parse_hhmm("07:00")
    end = parse_hhmm("19:00")

    at_start = resolve_shift(
        now=datetime(2026, 10, 3, 7, 0, tzinfo=TZ),
        start_minutes=start,
        end_minutes=end,
        primary_persona="arona",
        secondary_persona="plana",
    )
    assert at_start.target_persona == "arona"
    assert at_start.boundary_at == datetime(2026, 10, 3, 7, 0, tzinfo=TZ)

    at_end = resolve_shift(
        now=datetime(2026, 10, 3, 19, 0, tzinfo=TZ),
        start_minutes=start,
        end_minutes=end,
        primary_persona="arona",
        secondary_persona="plana",
    )
    assert at_end.target_persona == "plana"
    assert at_end.boundary_at == datetime(2026, 10, 3, 19, 0, tzinfo=TZ)


def test_day_window_before_start_uses_previous_end_boundary():
    decision = resolve_shift(
        now=datetime(2026, 10, 3, 6, 30, tzinfo=TZ),
        start_minutes=parse_hhmm("07:00"),
        end_minutes=parse_hhmm("19:00"),
        primary_persona="arona",
        secondary_persona="plana",
    )
    assert decision.target_persona == "plana"
    assert decision.boundary_at == datetime(2026, 10, 2, 19, 0, tzinfo=TZ)


def test_overnight_primary_window():
    start = parse_hhmm("19:00")
    end = parse_hhmm("07:00")

    evening = resolve_shift(
        now=datetime(2026, 10, 3, 22, 0, tzinfo=TZ),
        start_minutes=start,
        end_minutes=end,
        primary_persona="plana",
        secondary_persona="arona",
    )
    assert evening.target_persona == "plana"
    assert evening.boundary_at == datetime(2026, 10, 3, 19, 0, tzinfo=TZ)

    after_midnight = resolve_shift(
        now=datetime(2026, 10, 4, 2, 0, tzinfo=TZ),
        start_minutes=start,
        end_minutes=end,
        primary_persona="plana",
        secondary_persona="arona",
    )
    assert after_midnight.target_persona == "plana"
    assert after_midnight.boundary_at == datetime(2026, 10, 3, 19, 0, tzinfo=TZ)

    daytime = resolve_shift(
        now=datetime(2026, 10, 4, 10, 0, tzinfo=TZ),
        start_minutes=start,
        end_minutes=end,
        primary_persona="plana",
        secondary_persona="arona",
    )
    assert daytime.target_persona == "arona"
    assert daytime.boundary_at == datetime(2026, 10, 4, 7, 0, tzinfo=TZ)


def test_handover_waits_for_idle_but_respects_grace():
    boundary = datetime(2026, 10, 3, 19, 0, tzinfo=timezone.utc)

    allowed, reason = should_handover(
        now_utc=boundary + timedelta(seconds=20),
        boundary_utc=boundary,
        last_turn_finished_at_utc=boundary + timedelta(seconds=10),
        turn_inflight=False,
        idle_seconds=60,
        grace_seconds=300,
    )
    assert allowed is False
    assert reason == "cooldown"

    allowed, reason = should_handover(
        now_utc=boundary + timedelta(seconds=310),
        boundary_utc=boundary,
        last_turn_finished_at_utc=boundary + timedelta(seconds=305),
        turn_inflight=False,
        idle_seconds=60,
        grace_seconds=300,
    )
    assert allowed is True
    assert reason == "grace_elapsed"


def test_handover_never_interrupts_inflight_turn():
    boundary = datetime(2026, 10, 3, 19, 0, tzinfo=timezone.utc)
    allowed, reason = should_handover(
        now_utc=boundary + timedelta(seconds=600),
        boundary_utc=boundary,
        last_turn_finished_at_utc=None,
        turn_inflight=True,
        idle_seconds=60,
        grace_seconds=300,
    )
    assert allowed is False
    assert reason == "turn_inflight"
