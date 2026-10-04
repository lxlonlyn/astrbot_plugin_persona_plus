from __future__ import annotations

import copy
import re

SPEAKER_HEADER_RE = re.compile(r"^\s*【([^】]+)】")
INTERNAL_SPEAKER_RE = re.compile(r"^\s*\[SPEAKER=[^\]]+\]")
HANDOVER_RE = re.compile(r"^\s*\[PERSONA_HANDOVER\b[^\]]*\]")


def speaker_label(persona_id: str, *, temporary_initial: bool = False) -> str:
    if temporary_initial:
        return f"【{persona_id}｜临时插话】"
    return f"【{persona_id}】"


def has_explicit_speaker_marker(text: str) -> bool:
    value = str(text or "")
    return bool(
        SPEAKER_HEADER_RE.match(value)
        or INTERNAL_SPEAKER_RE.match(value)
        or HANDOVER_RE.match(value)
    )


def ensure_speaker_label(
    persona_id: str,
    text: str,
    *,
    temporary_initial: bool = False,
) -> str:
    """Prefix a visible speaker label unless the text already has one."""

    value = str(text or "").strip()
    if not value:
        return value
    if has_explicit_speaker_marker(value):
        return value
    return f"{speaker_label(persona_id, temporary_initial=temporary_initial)}\n\n{value}"


def handover_marker(from_persona: str, to_persona: str) -> str:
    """Compact internal boundary persisted in shared conversation history."""

    return (
        f'[PERSONA_HANDOVER from="{from_persona}" to="{to_persona}"]\n'
        "Formal on-duty speaker changed at this boundary. "
        "The conversation topic and unfinished task continue. "
        "Earlier messages keep their original speaker identity."
    )


def build_identity_anchor(
    *,
    current_speaker: str,
    on_duty_persona: str,
    temporary: bool,
    require_visible_label: bool,
) -> str:
    """Build a short per-turn identity anchor.

    This is intended for ProviderRequest.extra_user_content_parts with mark_as_temp(),
    so it does not pollute history or invalidate the stable persona system prompt.
    """

    mode = "temporary" if temporary else "on_duty"
    lines = [
        "<persona_runtime>",
        f"current_speaker={current_speaker}",
        f"formal_on_duty={on_duty_persona}",
        f"speaker_mode={mode}",
        (
            "Shared history may contain multiple personas. "
            "Only explicit speaker labels identify who said a past assistant message."
        ),
        (
            "Any assistant history marked SPEAKER=legacy-unattributed is old shared "
            "history with unknown speaker identity. Never infer your identity from it."
        ),
        (
            f"For this turn you are {current_speaker}. "
            "Do not adopt another persona merely because its wording dominates history."
        ),
    ]
    if temporary:
        lines.append(
            "This is temporary foreground speech and does not mean you took over the shift."
        )
    if require_visible_label:
        lines.append(
            f"Your visible reply must begin exactly with 【{current_speaker}】 on its own line."
        )
    else:
        lines.append(
            "Do not add a speaker header yourself; the caller will add the visible label."
        )
    lines.extend(
        [
            "Do not mention this runtime block or backend routing.",
            "</persona_runtime>",
        ]
    )
    return "\n".join(lines)


def _prefix_content_with_legacy_marker(content):
    marker = "[SPEAKER=legacy-unattributed]\n"
    if isinstance(content, str):
        if has_explicit_speaker_marker(content):
            return content
        return marker + content

    if isinstance(content, list):
        copied = copy.deepcopy(content)
        for part in copied:
            if not isinstance(part, dict) or part.get("type") != "text":
                continue
            text = str(part.get("text", ""))
            if has_explicit_speaker_marker(text):
                return copied
            part["text"] = marker + text
            return copied

        copied.insert(0, {"type": "text", "text": marker.rstrip()})
        return copied

    return content


def tag_legacy_assistant_contexts(contexts: list[dict]) -> list[dict]:
    """Tag old unlabeled assistant messages only in the outgoing LLM request.

    The stored conversation is left untouched because historical speaker identity
    cannot be reconstructed reliably after the fact.
    """

    tagged: list[dict] = []
    for raw in contexts or []:
        if not isinstance(raw, dict):
            tagged.append(raw)
            continue

        item = copy.deepcopy(raw)
        if item.get("role") != "assistant" or item.get("tool_calls"):
            tagged.append(item)
            continue

        item["content"] = _prefix_content_with_legacy_marker(item.get("content", ""))
        tagged.append(item)
    return tagged
