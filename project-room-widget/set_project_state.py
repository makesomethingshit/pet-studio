"""Write the Pet Studio widget file-based state bridge."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from project_room_registry import DEFAULT_STATE_FILE, STATE_ALIASES, WIDGET_STATES


EXTERNAL_STATES = WIDGET_STATES | set(STATE_ALIASES)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_project_state(
    state_file: Path,
    project_id: str,
    state: str,
    message: str,
    updated_at: str | None = None,
) -> dict:
    state = state.strip()
    if state not in EXTERNAL_STATES:
        supported = ", ".join(sorted(EXTERNAL_STATES))
        raise SystemExit(f"Unsupported project state `{state}`. Supported states: {supported}")

    payload = {
        "projectId": project_id,
        "state": state,
        "message": message,
        "updatedAt": updated_at or utc_now(),
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Pet Studio state JSON path")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state", required=True, help="External Pet Studio state to publish")
    parser.add_argument("--message", default="")
    parser.add_argument("--updated-at", default=None, help="Override updatedAt; mainly useful for deterministic tests")
    args = parser.parse_args()

    state_file = Path(args.state_file).expanduser()
    payload = write_project_state(state_file, args.project_id, args.state, args.message, args.updated_at)
    print(json.dumps({"ok": True, "stateFile": str(state_file), "state": payload}, indent=2))


if __name__ == "__main__":
    main()
