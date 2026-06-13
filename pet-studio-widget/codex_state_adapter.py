"""Translate Codex-like task events into Pet Studio widget state updates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_room_registry import (
    DEFAULT_ACTIVE_PROJECT_FILE,
    DEFAULT_REGISTRY,
    DEFAULT_STATE_FILE,
    ProjectRegistryError,
    infer_project_for_workspace,
    select_active_project,
)
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


def load_event_payload(path_value: str) -> dict:
    if path_value == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path_value).expanduser().read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid Codex event JSON: {error}") from error
    if not isinstance(data, dict):
        raise SystemExit("Codex event JSON must be an object")
    return data


def optional_payload_string(payload: dict, key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise SystemExit(f"Codex event JSON `{key}` must be a string")
    return value


def resolve_project_id(
    project_id: str | None,
    config: str | Path | None,
    cwd: str | Path | None,
    active_project_file: str | Path | None,
) -> str:
    if project_id:
        return project_id
    active_project = select_active_project(config, active_project_file)
    if active_project:
        return active_project.project_id
    workspace = Path(cwd).expanduser() if cwd else Path.cwd()
    return infer_project_for_workspace(config, workspace).project_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_REGISTRY), help="Project assignment registry path")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Project room state JSON path")
    parser.add_argument("--active-project-file", default=str(DEFAULT_ACTIVE_PROJECT_FILE), help="Active project pin JSON path")
    parser.add_argument("--project-id", default=None, help="Project id override; inferred from workspace when omitted")
    parser.add_argument("--cwd", default=None, help="Workspace directory for project inference; defaults to current directory")
    parser.add_argument("--event", default=None, help="Codex task event to publish")
    parser.add_argument("--event-json", default=None, help="Codex event JSON path, or `-` to read stdin")
    parser.add_argument("--message", default=None)
    parser.add_argument("--updated-at", default=None, help="Override updatedAt; mainly useful for deterministic tests")
    args = parser.parse_args()

    payload = load_event_payload(args.event_json) if args.event_json else {}
    event = args.event or optional_payload_string(payload, "event")
    if not event:
        raise SystemExit("--event is required unless --event-json provides `event`")
    message = args.message if args.message is not None else optional_payload_string(payload, "message") or ""
    project_id_arg = args.project_id or optional_payload_string(payload, "projectId")
    cwd = args.cwd or optional_payload_string(payload, "cwd")
    updated_at = args.updated_at or optional_payload_string(payload, "updatedAt")

    state_file = Path(args.state_file).expanduser()
    try:
        project_id = resolve_project_id(project_id_arg, args.config, cwd, args.active_project_file)
    except ProjectRegistryError as error:
        raise SystemExit(str(error)) from error
    state_payload = publish_codex_event(state_file, project_id, event, message, updated_at)
    print(
        json.dumps(
            {
                "ok": True,
                "stateFile": str(state_file),
                "event": event,
                "projectId": project_id,
                "state": state_payload,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
