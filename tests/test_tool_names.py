from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.tool_names import build_persona_management_tool_names


def test_build_persona_management_tool_names_includes_current_and_legacy_names():
    names = build_persona_management_tool_names(
        ["persona_delegate", "persona_list", "persona_view"]
    )

    assert "persona_delegate" in names
    assert "persona_list" in names
    assert "persona_view" in names

    assert "persona_plus_delegate" in names
    assert "persona_plus_list" in names
    assert "persona_plus_view" in names

    assert "persona_switch" in names
    assert "persona_plus_switch" in names


def test_build_persona_management_tool_names_does_not_generate_double_plus_alias():
    names = build_persona_management_tool_names(
        ["persona_delegate", "persona_plus_switch"]
    )

    assert "persona_plus_plus_switch" not in names
