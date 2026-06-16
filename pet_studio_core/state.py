"""File-based Pet Studio state bridge primitives."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .registry import DEFAULT_STATE_FILE, STATE_ALIASES, WIDGET_STATES

EXTERNAL_STATES = WIDGET_STATES | set(STATE_ALIASES)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_project_state(
    state_file: Path,
    project_id: str,
    state: str,
    message: str,
    updated_at: str | None = None,
    reset_after_ms: int | None = None,
    reset_to_state: str = "idle",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a state bridge payload.

    Parameters
    ----------
    state_file:
        Path to the JSON state file.
    project_id:
        Project identifier written into the payload.
    state:
        Pet Studio state. Must be in ``EXTERNAL_STATES``.
    message:
        Human-readable status message for speech bubbles.
    updated_at:
        ISO-8601 timestamp. Defaults to current UTC time.
    reset_after_ms:
        Optional auto-reset interval in milliseconds.
    reset_to_state:
        State to reset to after ``reset_after_ms`` elapses.
    metadata:
        Optional opaque metadata dict preserved in the payload under the
        ``metadata`` key.  Future envelopes (Workroom, adapters) can store
        adapter-specific data without changing the core schema.

    Returns
    -------
    dict
        The written payload.
    """
    state = state.strip()
    if state not in EXTERNAL_STATES:
        supported = ", ".join(sorted(EXTERNAL_STATES))
        raise SystemExit(f"Unsupported project state `{state}`. Supported states: {supported}")
    if reset_to_state not in EXTERNAL_STATES:
        supported = ", ".join(sorted(EXTERNAL_STATES))
        raise SystemExit(f"Unsupported reset state `{reset_to_state}`. Supported states: {supported}")
    if reset_after_ms is not None and reset_after_ms < 0:
        raise SystemExit("resetAfterMs must be zero or greater")

    payload: dict[str, Any] = {
        "projectId": project_id,
        "state": state,
        "message": message,
        "updatedAt": updated_at or utc_now(),
    }
    if reset_after_ms is not None:
        payload["resetAfterMs"] = int(reset_after_ms)
        payload["resetToState"] = reset_to_state
    if metadata:
        payload["metadata"] = metadata

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


__all__ = ["DEFAULT_STATE_FILE", "EXTERNAL_STATES", "utc_now", "write_project_state"]
