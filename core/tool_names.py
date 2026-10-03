from __future__ import annotations

from collections.abc import Iterable


def build_persona_management_tool_names(tool_names: Iterable[str]) -> set[str]:
    """Return current and legacy Persona+ management tool names.

    Work on immutable snapshots instead of mutating a set while iterating it.
    """

    current_names = {str(name).strip() for name in tool_names if str(name).strip()}
    legacy_names = {
        name.replace("persona_", "persona_plus_", 1)
        for name in current_names
        if name.startswith("persona_")
    }
    return (
        current_names
        | legacy_names
        | {"persona_switch", "persona_plus_switch"}
    )
