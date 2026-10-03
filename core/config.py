from __future__ import annotations

from dataclasses import dataclass

from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig

from .models import KeywordMapping, parse_mapping_entry
from .shift_schedule import parse_hhmm

LLM_TOOL_OPTIONS = (
    "list",
    "delegate",
    "view",
    "create",
    "update",
    "avatar",
    "export",
    "delete",
)


def _normalize_str_set(values) -> set[str]:
    """将列表/字典输入压缩为去重后的字符串集合。"""

    return {str(item).lower().strip() for item in values if str(item).strip()}


def _default_admin_commands() -> set[str]:
    # switch 仅保留给管理员作为调试/故障恢复入口。
    return {"switch", "create", "update", "delete", "avatar", "export"}


def _read_non_negative_int(
    config: AstrBotConfig,
    key: str,
    default: int,
) -> int:
    raw = config.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning("Persona+ %s=%r 非法，使用默认值 %s", key, raw, default)
        return default
    if value < 0:
        logger.warning("Persona+ %s=%r 不能为负数，使用默认值 %s", key, raw, default)
        return default
    return value


def _read_shift_time(
    config: AstrBotConfig,
    key: str,
    default: str,
) -> int:
    raw = str(config.get(key, default) or default).strip()
    try:
        return parse_hhmm(raw)
    except ValueError:
        logger.warning(
            "Persona+ %s=%r 非法，必须为 HH:MM，使用默认值 %s",
            key,
            raw,
            default,
        )
        return parse_hhmm(default)


@dataclass(slots=True)
class PersonaPlusSettings:
    keyword_mappings: list[KeywordMapping]
    auto_switch_scope: str
    keyword_switch_enabled: bool
    manage_wait_timeout: int
    admin_commands: set[str]
    auto_switch_announce: bool
    clear_context_on_switch: bool
    llm_tool_options: set[str]

    shift_schedule_enabled: bool
    shift_primary_persona: str
    shift_secondary_persona: str
    shift_start_minutes: int
    shift_end_minutes: int
    shift_timezone: str
    handover_idle_seconds: int
    handover_grace_seconds: int


def load_settings(config: AstrBotConfig | None) -> PersonaPlusSettings:
    """从 AstrBot 配置中读取 Persona+ 的运行参数。"""

    loaded: list[KeywordMapping] = []

    if not config:
        logger.warning("Persona+ 未载入专用配置，将使用默认值。")
        return PersonaPlusSettings(
            keyword_mappings=[],
            auto_switch_scope="conversation",
            keyword_switch_enabled=True,
            manage_wait_timeout=60,
            admin_commands=_default_admin_commands(),
            auto_switch_announce=True,
            clear_context_on_switch=False,
            llm_tool_options=set(),
            shift_schedule_enabled=False,
            shift_primary_persona="arona",
            shift_secondary_persona="plana",
            shift_start_minutes=parse_hhmm("07:00"),
            shift_end_minutes=parse_hhmm("19:00"),
            shift_timezone="",
            handover_idle_seconds=60,
            handover_grace_seconds=300,
        )

    mappings_raw = config.get("keyword_mappings", [])

    if mappings_raw is None:
        entries: list[str | dict[str, str]] = []
    elif isinstance(mappings_raw, list):
        entries = mappings_raw
    elif isinstance(mappings_raw, str):
        entries = mappings_raw.splitlines()
    else:
        logger.warning(
            "Persona+ 关键词配置应为列表或文本，实际收到 %r (类型 %s)，尝试转换",
            mappings_raw,
            type(mappings_raw).__name__,
        )
        entries = [str(mappings_raw)] if str(mappings_raw).strip() else []

    for raw_entry in entries:
        if isinstance(raw_entry, dict):
            keyword = str(raw_entry.get("keyword", "")).strip()
            persona_id = str(raw_entry.get("persona_id", "")).strip()
            reply_template = str(raw_entry.get("reply_template", "")).strip()
            if keyword and persona_id:
                loaded.append(
                    KeywordMapping(
                        keyword=keyword,
                        persona_id=persona_id,
                        reply_template=reply_template,
                    )
                )
            continue

        entry = str(raw_entry).strip()
        if not entry or entry.startswith("#"):
            continue
        try:
            loaded.append(parse_mapping_entry(entry))
        except Exception as exc:  # noqa: BLE001
            logger.error("Persona+ 解析关键词配置失败: %s", exc)

    keyword_mappings = [m for m in loaded if m.keyword and m.persona_id]

    auto_switch_scope = config.get("auto_switch_scope", "conversation")
    keyword_switch_enabled = bool(config.get("enable_keyword_switching", True))

    admin_commands_raw = config.get(
        "admin_commands",
        ["switch", "create", "update", "delete", "avatar", "export"],
    )
    if isinstance(admin_commands_raw, list):
        admin_commands = _normalize_str_set(admin_commands_raw)
    elif isinstance(admin_commands_raw, dict):
        admin_commands = _normalize_str_set(
            command
            for command, required in admin_commands_raw.items()
            if bool(required)
        )
    else:
        logger.warning(
            "Persona+ admin_commands 配置应为列表或字典，实际收到 %r，已使用默认值",
            admin_commands_raw,
        )
        admin_commands = _default_admin_commands()

    # 人格直接切换只作为管理员调试/恢复命令保留，不能开放给普通用户。
    admin_commands.add("switch")

    auto_switch_announce = bool(config.get("enable_auto_switch_announce", True))
    clear_context_on_switch = bool(config.get("clear_context_on_switch", False))

    llm_tool_options_raw = config.get("llm_tool_options", None)
    llm_tool_options: set[str] = set()
    if llm_tool_options_raw is not None:
        if isinstance(llm_tool_options_raw, list):
            llm_tool_options = _normalize_str_set(llm_tool_options_raw)
        else:
            logger.warning(
                "Persona+ llm_tool_options 配置应为列表，实际收到 %r，已忽略",
                llm_tool_options_raw,
            )

    # 兼容旧配置：布尔开关 enable_llm_tools。
    if llm_tool_options_raw is None and bool(config.get("enable_llm_tools", False)):
        llm_tool_options = set(LLM_TOOL_OPTIONS)

    # v1.6 起不再向 LLM 暴露 switch。旧配置中的 switch 会在此被忽略。
    unsupported_llm_tool_options = llm_tool_options - set(LLM_TOOL_OPTIONS)
    if unsupported_llm_tool_options:
        logger.warning(
            "Persona+ llm_tool_options 包含不支持的项：%s，已忽略",
            sorted(unsupported_llm_tool_options),
        )
        llm_tool_options = llm_tool_options.intersection(set(LLM_TOOL_OPTIONS))

    raw_timeout = config.get("manage_wait_timeout_seconds", 60)
    try:
        timeout = int(raw_timeout)
    except (TypeError, ValueError):
        logger.warning(
            "Persona+ manage_wait_timeout_seconds=%r 非法，使用默认值 60",
            raw_timeout,
        )
        timeout = 60
    if timeout <= 0:
        logger.warning(
            "Persona+ manage_wait_timeout_seconds=%r 必须为正数，已重置为 60",
            raw_timeout,
        )
        timeout = 60

    shift_schedule_enabled = bool(config.get("enable_shift_schedule", False))
    shift_primary_persona = str(
        config.get("shift_primary_persona", "arona") or ""
    ).strip()
    shift_secondary_persona = str(
        config.get("shift_secondary_persona", "plana") or ""
    ).strip()
    shift_start_minutes = _read_shift_time(config, "shift_start_time", "07:00")
    shift_end_minutes = _read_shift_time(config, "shift_end_time", "19:00")
    shift_timezone = str(config.get("shift_timezone", "") or "").strip()
    handover_idle_seconds = _read_non_negative_int(
        config,
        "handover_idle_seconds",
        60,
    )
    handover_grace_seconds = _read_non_negative_int(
        config,
        "handover_grace_seconds",
        300,
    )

    if shift_schedule_enabled:
        if not shift_primary_persona or not shift_secondary_persona:
            logger.warning("Persona+ 定时轮班人格不能为空，已关闭本次运行的轮班功能。")
            shift_schedule_enabled = False
        elif shift_primary_persona == shift_secondary_persona:
            logger.warning("Persona+ 两个轮班人格不能相同，已关闭本次运行的轮班功能。")
            shift_schedule_enabled = False
        elif shift_start_minutes == shift_end_minutes:
            logger.warning("Persona+ 轮班开始和结束时间不能相同，已关闭本次运行的轮班功能。")
            shift_schedule_enabled = False

    return PersonaPlusSettings(
        keyword_mappings=keyword_mappings,
        auto_switch_scope=auto_switch_scope,
        keyword_switch_enabled=keyword_switch_enabled,
        manage_wait_timeout=timeout,
        admin_commands=admin_commands,
        auto_switch_announce=auto_switch_announce,
        clear_context_on_switch=clear_context_on_switch,
        llm_tool_options=llm_tool_options,
        shift_schedule_enabled=shift_schedule_enabled,
        shift_primary_persona=shift_primary_persona,
        shift_secondary_persona=shift_secondary_persona,
        shift_start_minutes=shift_start_minutes,
        shift_end_minutes=shift_end_minutes,
        shift_timezone=shift_timezone,
        handover_idle_seconds=handover_idle_seconds,
        handover_grace_seconds=handover_grace_seconds,
    )
