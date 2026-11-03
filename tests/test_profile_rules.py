from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.profile_rules import parse_profile_rules


def _rule(config_id, **overrides):
    return {
        "__template_key": "two_persona",
        "config_id": config_id,
        "enabled": True,
        "mode": "shift",
        "primary_persona": "Arona",
        "secondary_persona": "Plana",
        "start_time": "07:00",
        "end_time": "19:00",
        **overrides,
    }


def test_empty_legacy_not_implicitly_enabled():
    rules, errors = parse_profile_rules([])
    assert rules == {} and not errors


def test_profiles_independent_and_unlisted_not_managed():
    rules, errors = parse_profile_rules([
        _rule("profile-A"),
        _rule("profile-B", primary_persona="X", secondary_persona="Y"),
    ])
    assert not errors
    assert rules["profile-A"].primary_persona == "Arona"
    assert rules["profile-B"].primary_persona == "X"
    assert "profile-C" not in rules
    assert not rules["profile-A"].takeover_existing_conversations


def test_duplicate_id_disables_all_same_id():
    rules, errors = parse_profile_rules([_rule("same"), _rule("same")])
    assert "same" not in rules and any("重复" in item for item in errors)


def test_invalid_configurations_are_skipped():
    rules, errors = parse_profile_rules([
        _rule("*"),
        _rule("tz", timezone="Nowhere/Unknown"),
        _rule("equal", secondary_persona="arona"),
        _rule("time", start_time="19:00", end_time="19:00"),
    ])
    assert rules == {} and len(errors) == 4


def test_disabled_and_keyword_only():
    disabled = _rule("disabled", enabled=False)
    keyword = _rule("keyword", mode="keyword", primary_persona="", secondary_persona="")
    rules, errors = parse_profile_rules([disabled, keyword])
    assert not errors
    assert "disabled" not in rules
    assert rules["keyword"].mode == "keyword"


def test_strict_types_fail_closed():
    rules, errors = parse_profile_rules([
        _rule("bad", enabled="false"),
        _rule("bad2", idle_seconds=True),
        _rule("bad3", mode="*"),
    ])
    assert not rules and len(errors) == 3


def test_overnight_and_takeover():
    rules, errors = parse_profile_rules([
        _rule("night", start_time="19:00", end_time="07:00",
              takeover_existing_conversations=True),
    ])
    assert not errors
    assert rules["night"].start_minutes == 1140
    assert rules["night"].takeover_existing_conversations

def test_takeover_policy_respects_unrelated_existing_persona():
    from core.profile_rules import can_take_over_persona

    rule = parse_profile_rules([_rule("profile-A")])[0]["profile-A"]
    assert can_take_over_persona(rule, None)
    assert can_take_over_persona(rule, "Arona")
    assert can_take_over_persona(rule, "PlAnA")
    assert not can_take_over_persona(rule, "OtherBot")

    forced = parse_profile_rules([
        _rule("profile-A", takeover_existing_conversations=True)
    ])[0]["profile-A"]
    assert can_take_over_persona(forced, "OtherBot")

    keyword = parse_profile_rules([
        _rule("profile-B", mode="keyword")
    ])[0]["profile-B"]
    assert not can_take_over_persona(keyword, "OtherBot")
