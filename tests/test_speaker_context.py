from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.speaker_context import (
    build_identity_anchor,
    ensure_speaker_label,
    handover_marker,
    tag_legacy_assistant_contexts,
)


def test_formal_speaker_label_is_added_once():
    text = ensure_speaker_label("Arona", "老师，收到！")
    assert text == "【Arona】\n\n老师，收到！"
    assert ensure_speaker_label("Arona", text) == text


def test_wrong_model_generated_label_is_corrected():
    text = ensure_speaker_label("Arona", "【Plana】\n\n收到，老师。")
    assert text == "【Arona】\n\n收到，老师。"

    temporary = ensure_speaker_label(
        "Plana",
        "【Plana】\n\n在，老师。",
        temporary_initial=True,
    )
    assert temporary == "【Plana｜临时插话】\n\n在，老师。"


def test_runtime_anchor_separates_speaker_and_on_duty_persona():
    formal = build_identity_anchor(
        current_speaker="Arona",
        on_duty_persona="Arona",
        temporary=False,
        require_visible_label=True,
    )
    assert "current_speaker=Arona" in formal
    assert "formal_on_duty=Arona" in formal
    assert "speaker_mode=on_duty" in formal
    assert "【Arona】" in formal
    assert "legacy-unattributed" in formal

    temporary = build_identity_anchor(
        current_speaker="Plana",
        on_duty_persona="Arona",
        temporary=True,
        require_visible_label=False,
    )
    assert "current_speaker=Plana" in temporary
    assert "formal_on_duty=Arona" in temporary
    assert "speaker_mode=temporary" in temporary
    assert "does not mean you took over the shift" in temporary


def test_legacy_assistant_history_is_tagged_without_touching_labeled_messages():
    contexts = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "旧的未标注回答"},
        {"role": "assistant", "content": "【Plana】\n\n已有标签"},
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "旧多模态文本"}],
        },
        {
            "role": "assistant",
            "content": "工具调用不应改",
            "tool_calls": [{"id": "x"}],
        },
    ]

    tagged = tag_legacy_assistant_contexts(contexts)

    assert tagged[0]["content"] == "你好"
    assert tagged[1]["content"].startswith("[SPEAKER=legacy-unattributed]")
    assert tagged[2]["content"] == "【Plana】\n\n已有标签"
    assert tagged[3]["content"][0]["text"].startswith(
        "[SPEAKER=legacy-unattributed]"
    )
    assert tagged[4]["content"] == "工具调用不应改"

    # The original history object must remain untouched.
    assert contexts[1]["content"] == "旧的未标注回答"
    assert contexts[3]["content"][0]["text"] == "旧多模态文本"


def test_legacy_tagging_is_idempotent():
    contexts = [{"role": "assistant", "content": "old"}]
    once = tag_legacy_assistant_contexts(contexts)
    twice = tag_legacy_assistant_contexts(once)
    assert once == twice


def test_handover_marker_is_compact_and_preserves_task_continuity():
    marker = handover_marker("Arona", "Plana")
    assert marker.startswith('[PERSONA_HANDOVER from="Arona" to="Plana"]')
    assert "unfinished task continue" in marker
    assert "Earlier messages keep their original speaker identity" in marker
