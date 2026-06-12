"""Translate Codex-like task events into Project Room Widget state updates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_room_registry import DEFAULT_STATE_FILE
from set_project_state import write_project_state


EVENT_TO_STATE = {
    "start": "running",
    "wait": "waiting",
    "review": "review",
    "block": "blocked",
    "fail": "failed",
    "done": "done",
    "idle": "idle",
}


def bridge_state_for_event(event: str) -> str:
    value = event.strip().lower()
    try:
        return EVENT_TO_STATE[value]
    except KeyError as error:
        supported = ", ".join(sorted(EVENT_TO_STATE))
        raise SystemExit(f"Unsupported Codex event `{event}`. Supported events: {supported}") from error


def publish_codex_event(
    state_file: Path,
    project_id: str,
    event: str,
    message: str,
    updated_at: str | None = None,
) -> dict:
    state = bridge_state_for_event(event)
    return write_project_state(state_file, project_id, state, message, updated_at)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Project room state JSON path")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--event", required=True, help="Codex task event to publish")
    parser.add_argument("--message", default="")
    parser.add_argument("--updated-at", default=None, help="Override updatedAt; mainly useful for deterministic tests")
    args = parser.parse_args()

    state_file = Path(args.state_file).expanduser()
    payload = publish_codex_event(state_file, args.project_id, args.event, args.message, args.updated_at)
    print(
        json.dumps(
            {
                "ok": True,
                "stateFile": str(state_file),
                "event": args.event,
                "state": payload,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
