"""File-based Pet Studio state bridge primitives."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .registry import DEFAULT_STATE_FILE, STATE_ALIASES, WIDGET_STATES


EXTERNAL_STATES = WIDGET_STATES | set(STATE_ALIASES)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_project_state(
    state_file: Path,
    project_id: str,
    state: str,
    message: str,
    updated_at: str | None = None,
    reset_after_ms: int | None = None,
    reset_to_state: str = "idle",
) -> dict:
    state = state.strip()
    if state not in EXTERNAL_STATES:
        supported = ", ".join(sorted(EXTERNAL_STATES))
        raise SystemExit(f"Unsupported project state `{state}`. Supported states: {supported}")
    if reset_to_state not in EXTERNAL_STATES:
        supported = ", ".join(sorted(EXTERNAL_STATES))
        raise SystemExit(f"Unsupported reset state `{reset_to_state}`. Supported states: {supported}")
    if reset_after_ms is not None and reset_after_ms < 0:
        raise SystemExit("resetAfterMs must be zero or greater")

    payload = {
        "projectId": project_id,
        "state": state,
        "message": message,
        "updatedAt": updated_at or utc_now(),
    }
    if reset_after_ms is not None:
        payload["resetAfterMs"] = int(reset_after_ms)
        payload["resetToState"] = reset_to_state
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


__all__ = ["DEFAULT_STATE_FILE", "EXTERNAL_STATES", "utc_now", "write_project_state"]
