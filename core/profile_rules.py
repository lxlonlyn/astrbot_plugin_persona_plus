"""Fail-closed, per-AstrBot-config profile routing for Persona+.

This module is intentionally free of AstrBot imports so validation can be tested
without starting a bot. Every automatic Persona+ action must opt in through a
rule identified by AstrBot's stable configuration ID, not its display name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .shift_schedule import parse_hhmm


@dataclass(frozen=True, slots=True)
class ProfileRule:
    config_id: str
    mode: str
    primary_persona: str = ""
    secondary_persona: str = ""
    start_minutes: int = 420
    end_minutes: int = 1140
    timezone: str = ""
    idle_seconds: int = 60
    grace_seconds: int = 300
    takeover_existing_conversations: bool = False


def _non_negative_int(raw: Any, field: str) -> int:
    if isinstance(raw, bool):
        raise ValueError(f"{field} 必须为非负整数")
    try:
        value = int(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} 必须为非负整数") from exc
    if value < 0:
        raise ValueError(f"{field} 必须为非负整数")
    return value


def parse_profile_rules(raw: Any) -> tuple[dict[str, ProfileRule], list[str]]:
    """Return enabled rules and diagnostics. Invalid/duplicate IDs fail closed.

    No wildcard, implicit global rule, or legacy schedule fallback is accepted.
    Disabled entries are known but never enable automatic runtime hooks.
    """

    if not isinstance(raw, list):
        return {}, ["shift_profile_rules 必须是列表，已禁止自动轮班"]

    rules: dict[str, ProfileRule] = {}
    seen: set[str] = set()
    duplicates: set[str] = set()
    errors: list[str] = []
    for index, item in enumerate(raw, start=1):
        prefix = f"shift_profile_rules 第 {index} 项"
        if not isinstance(item, dict):
            errors.append(f"{prefix} 不是对象，已跳过")
            continue
        config_id = str(item.get("config_id") or "").strip()
        if not config_id or config_id.lower() in {"*", "all"}:
            errors.append(f"{prefix} 必须填写实际 AstrBot 配置文件 ID，不能使用通配符")
            continue
        if config_id in seen:
            duplicates.add(config_id)
            rules.pop(config_id, None)
            errors.append(f"{prefix} 的配置文件 ID {config_id!r} 重复，全部同名规则禁用")
            continue
        seen.add(config_id)

        if not isinstance(item.get("enabled", True), bool):
            errors.append(f"{prefix} 的 enabled 必须为布尔值，已跳过")
            continue
        if not item.get("enabled", True):
            continue

        try:
            template = item.get("__template_key", "two_persona")
            if template != "two_persona":
                raise ValueError(f"未知模板 {template!r}")
            mode = str(item.get("mode", "shift") or "shift").strip().lower()
            if mode not in {"shift", "keyword"}:
                raise ValueError("mode 必须为 shift 或 keyword")
            takeover = item.get("takeover_existing_conversations", False)
            if not isinstance(takeover, bool):
                raise ValueError("takeover_existing_conversations 必须为布尔值")

            if mode == "shift":
                primary = str(item.get("primary_persona") or "").strip()
                secondary = str(item.get("secondary_persona") or "").strip()
                if not primary or not secondary or primary.casefold() == secondary.casefold():
                    raise ValueError("轮班需要两个不相同的非空人格 ID")
                start = parse_hhmm(str(item.get("start_time", "07:00")))
                end = parse_hhmm(str(item.get("end_time", "19:00")))
                if start == end:
                    raise ValueError("开始和结束时间不能相同")
                tz = str(item.get("timezone") or "").strip()
                if tz:
                    try:
                        ZoneInfo(tz)
                    except (ZoneInfoNotFoundError, ValueError) as exc:
                        raise ValueError(f"不存在的时区 {tz!r}") from exc
                idle = _non_negative_int(item.get("idle_seconds", 60), "idle_seconds")
                grace = _non_negative_int(item.get("grace_seconds", 300), "grace_seconds")
            else:
                primary, secondary, tz = "", "", ""
                start, end, idle, grace = 420, 1140, 60, 300

            rules[config_id] = ProfileRule(
                config_id=config_id,
                mode=mode,
                primary_persona=primary,
                secondary_persona=secondary,
                start_minutes=start,
                end_minutes=end,
                timezone=tz,
                idle_seconds=idle,
                grace_seconds=grace,
                takeover_existing_conversations=takeover,
            )
        except ValueError as exc:
            errors.append(f"{prefix} ({config_id}) 配置无效，已跳过：{exc}")
    for config_id in duplicates:
        rules.pop(config_id, None)
    return rules, errors


def can_take_over_persona(rule: ProfileRule, current_persona: str | None) -> bool:
    """Allow scheduled shifts, never take over third-party personas by default."""
    if rule.mode != "shift":
        return False
    if not current_persona:
        return True
    return (
        rule.takeover_existing_conversations
        or current_persona.casefold()
        in {rule.primary_persona.casefold(), rule.secondary_persona.casefold()}
    )
