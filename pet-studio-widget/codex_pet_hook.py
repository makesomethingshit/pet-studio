"""Codex hook/notify bridge for Pet Studio widget bubbles."""

from __future__ import annotations

import argparse
import json
import locale
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codex_state_adapter import publish_codex_event, resolve_project_id
from project_room_registry import DEFAULT_ACTIVE_PROJECT_FILE, DEFAULT_REGISTRY, DEFAULT_STATE_FILE, ProjectRegistryError


DONE_RESET_AFTER_MS = 1500
DEFAULT_HOOK_LOG_FILE = Path(__file__).with_name("project-room-hook-events.jsonl")
HOOK_TO_EVENT = {
    "session_start": ("idle", "Pet Studio ready"),
    "user_prompt_submit": ("start", "Working"),
    "pre_tool_use": ("start", "Using tool"),
    "post_tool_use": ("start", "Working"),
    "pre_compact": ("wait", "Compacting context"),
    "stop": ("done", "Done"),
    "notify": ("done", "Turn ended"),
}


def reset_options_for_hook(hook: str) -> dict[str, object]:
    if hook in {"stop", "notify"}:
        return {"reset_after_ms": DONE_RESET_AFTER_MS, "reset_to_state": "idle"}
    return {}


def decode_stdin_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", sys.stdin.encoding, locale.getpreferredencoding(False)):
        if not encoding:
            continue
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def load_stdin_payload() -> dict[str, Any]:
    if sys.stdin is None or sys.stdin.closed or sys.stdin.isatty():
        return {}
    try:
        raw_bytes = sys.stdin.buffer.read()
    except OSError:
        return {}
    raw = decode_stdin_bytes(raw_bytes)
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw.strip()}
    return payload if isinstance(payload, dict) else {"payload": payload}


def first_string(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def compact_message(text: str, limit: int = 80) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def message_for_hook(hook: str, payload: dict[str, Any], fallback: str) -> str:
    if hook == "user_prompt_submit":
        prompt = first_string(payload, ("prompt", "userPrompt", "message", "raw"))
        return compact_message(f"Working: {prompt}") if prompt else fallback
    if hook == "pre_tool_use":
        tool_name = first_string(payload, ("toolName", "tool_name", "name"))
        return compact_message(f"Using {tool_name}") if tool_name else fallback
    if hook == "pre_compact":
        return fallback
    if hook == "stop":
        error = first_string(payload, ("error", "lastError"))
        return compact_message(f"Needs review: {error}") if error else fallback
    notify_text = first_string(payload, ("message", "summary", "raw"))
    return compact_message(notify_text) if notify_text else fallback


def run_passthrough(command: list[str]) -> int:
    if not command:
        return 0
    try:
        completed = subprocess.run(command, check=False)
    except OSError:
        return 1
    return int(completed.returncode)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_hook_log(log_file: Path | None, entry: dict[str, Any]) -> None:
    if log_file is None:
        return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook", choices=sorted(HOOK_TO_EVENT), default="notify")
    parser.add_argument("--config", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--active-project-file", default=str(DEFAULT_ACTIVE_PROJECT_FILE))
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--message", default=None)
    parser.add_argument("--hook-log-file", default=str(DEFAULT_HOOK_LOG_FILE))
    parser.add_argument("--allow-passthrough", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--passthrough", nargs=argparse.REMAINDER, help="Optional command to run after updating the pet state")
    args = parser.parse_args()

    payload = load_stdin_payload()
    event, fallback_message = HOOK_TO_EVENT[args.hook]
    message = args.message or message_for_hook(args.hook, payload, fallback_message)

    project_id_arg = args.project_id or first_string(payload, ("projectId", "project_id"))
    cwd = args.cwd or first_string(payload, ("cwd", "workspace", "workspacePath"))
    try:
        project_id = resolve_project_id(project_id_arg, args.config, cwd, args.active_project_file)
    except ProjectRegistryError as error:
        print(f"pet-studio hook skipped: {error}", file=sys.stderr)
        project_id = None

    state_payload = None
    if project_id:
        state_payload = publish_codex_event(Path(args.state_file).expanduser(), project_id, event, message, **reset_options_for_hook(args.hook))
    append_hook_log(
        Path(args.hook_log_file).expanduser() if args.hook_log_file else None,
        {
            "timestamp": utc_now(),
            "hook": args.hook,
            "event": event,
            "projectId": project_id,
            "state": state_payload.get("state") if state_payload else None,
            "message": message,
            "cwd": cwd,
            "payloadKeys": sorted(payload.keys()),
            "skipped": project_id is None,
        },
    )

    passthrough = args.passthrough or []
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    if passthrough and not args.allow_passthrough:
        raise SystemExit("passthrough requires --allow-passthrough")
    raise SystemExit(run_passthrough(passthrough))


if __name__ == "__main__":
    main()
