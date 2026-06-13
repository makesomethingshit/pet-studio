"""Install Pet Studio skill and Codex lifecycle bridges for local development."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from install_pet_studio_skill import install as install_skill


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = Path(sys.executable)
CONFIG_PATH = Path.home() / ".codex" / "config.toml"
HOOKS_PATH = ROOT / ".codex" / "hooks.json"
SKILL_DESTINATION = Path.home() / ".codex" / "skills" / "pet-studio"
HOOK_EVENTS = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop"]


def toml_string(value: str) -> str:
    return json.dumps(value)


def toml_array(values: list[str]) -> str:
    return "[ " + ", ".join(toml_string(value) for value in values) + " ]"


def parse_notify_line(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("notify"):
        return None
    if "=" not in stripped:
        return None
    raw = stripped.split("=", 1)[1].strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


def build_notify_command(previous_notify: list[str] | None) -> list[str]:
    command = [
        str(PYTHON_EXE),
        str(ROOT / "pet-studio-widget" / "codex_pet_hook.py"),
        "--hook",
        "notify",
    ]
    if previous_notify and not is_pet_studio_notify(previous_notify):
        command.extend(["--passthrough", *previous_notify])
    return command


def is_pet_studio_notify(values: list[str]) -> bool:
    return any(value.endswith("codex_pet_hook.py") for value in values)


def shell_arg(value: str) -> str:
    if not value or any(char.isspace() for char in value) or '"' in value:
        return toml_string(value)
    return value


def command_string(values: list[str]) -> str:
    return " ".join(shell_arg(value) for value in values)


def build_hook_command(hook_name: str) -> str:
    return command_string(
        [
            str(PYTHON_EXE),
            str(ROOT / "pet-studio-widget" / "codex_pet_hook.py"),
            "--hook",
            hook_name,
        ]
    )


def is_pet_studio_hook(handler: dict) -> bool:
    command = handler.get("command")
    return isinstance(command, str) and "codex_pet_hook.py" in command


def pet_studio_hook_group(event: str, hook_name: str, status_message: str | None = None) -> dict:
    handler: dict[str, object] = {
        "type": "command",
        "command": build_hook_command(hook_name),
        "timeout": 30,
    }
    if status_message:
        handler["statusMessage"] = status_message
    group: dict[str, object] = {"hooks": [handler]}
    if event in {"SessionStart", "PreCompact"}:
        group["matcher"] = "*"
    return group


def pet_studio_hook_groups() -> dict[str, list[dict]]:
    return {
        "SessionStart": [pet_studio_hook_group("SessionStart", "session_start", "pet-studio: ready")],
        "UserPromptSubmit": [pet_studio_hook_group("UserPromptSubmit", "user_prompt_submit", "pet-studio: updating bubble")],
        "PreToolUse": [pet_studio_hook_group("PreToolUse", "pre_tool_use")],
        "PostToolUse": [pet_studio_hook_group("PostToolUse", "post_tool_use")],
        "PreCompact": [pet_studio_hook_group("PreCompact", "pre_compact")],
        "Stop": [pet_studio_hook_group("Stop", "stop", "pet-studio: done")],
    }


def load_hooks_file(hooks_file: Path) -> dict:
    if not hooks_file.exists():
        return {"hooks": {}}
    try:
        data = json.loads(hooks_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid Codex hooks JSON: {hooks_file}: {error}") from error
    if not isinstance(data, dict):
        raise SystemExit(f"Codex hooks JSON must be an object: {hooks_file}")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"Codex hooks JSON `hooks` must be an object: {hooks_file}")
    return data


def without_pet_studio_groups(groups: object) -> list[dict]:
    if not isinstance(groups, list):
        return []
    retained: list[dict] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            retained.append(group)
            continue
        next_handlers = [
            handler
            for handler in handlers
            if not (isinstance(handler, dict) and is_pet_studio_hook(handler))
        ]
        if not next_handlers:
            continue
        next_group = dict(group)
        next_group["hooks"] = next_handlers
        retained.append(next_group)
    return retained


def install_hooks_bridge(hooks_file: Path, dry_run: bool = False) -> dict:
    data = load_hooks_file(hooks_file)
    hooks = data["hooks"]
    next_groups = pet_studio_hook_groups()
    for event, groups in next_groups.items():
        hooks[event] = without_pet_studio_groups(hooks.get(event)) + groups

    if not dry_run:
        hooks_file.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if hooks_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup = hooks_file.with_name(hooks_file.name + f".bak-pet-studio-{timestamp}")
            shutil.copy2(hooks_file, backup)
        hooks_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        backup = None

    return {
        "hooksFile": str(hooks_file),
        "backup": str(backup) if backup else None,
        "events": HOOK_EVENTS,
        "dryRun": dry_run,
    }


def install_notify_bridge(config_path: Path, dry_run: bool = False) -> dict:
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    lines = text.splitlines()
    previous_notify: list[str] | None = None
    notify_index: int | None = None
    for index, line in enumerate(lines):
        parsed = parse_notify_line(line)
        if parsed is not None:
            previous_notify = parsed
            notify_index = index
            break

    next_notify = build_notify_command(previous_notify)
    next_line = "notify = " + toml_array(next_notify)
    if notify_index is None:
        lines.insert(0, next_line)
    else:
        lines[notify_index] = next_line

    if not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup = config_path.with_name(config_path.name + f".bak-pet-studio-{timestamp}")
            shutil.copy2(config_path, backup)
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        backup = None

    return {
        "config": str(config_path),
        "backup": str(backup) if backup else None,
        "previousNotify": previous_notify,
        "nextNotify": next_notify,
        "dryRun": dry_run,
    }


def write_active_project(project_id: str, dry_run: bool = False) -> dict:
    active_file = ROOT / "pet-studio-widget" / "project-room-active.json"
    if dry_run:
        return {"activeProjectFile": str(active_file), "projectId": project_id, "dryRun": True}
    widget_dir = ROOT / "pet-studio-widget"
    if str(widget_dir) not in sys.path:
        sys.path.insert(0, str(widget_dir))
    from set_active_project import write_active_project as write_project_pin

    payload = write_project_pin(active_file, project_id, ROOT)
    return {"activeProjectFile": str(active_file), "activeProject": payload, "dryRun": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--hooks-file", default=str(HOOKS_PATH))
    parser.add_argument("--skill-dest", default=str(SKILL_DESTINATION))
    parser.add_argument("--project-id", default=None, help="Optional project id to pin as the active Pet Studio room")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-skill", action="store_true")
    parser.add_argument("--install-notify", action="store_true", help="Also wrap the user-level Codex notify command")
    parser.add_argument("--skip-notify", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-hooks", action="store_true")
    parser.add_argument("--skip-active-project", action="store_true")
    args = parser.parse_args()

    results: dict[str, object] = {}
    if not args.skip_skill:
        if not args.dry_run:
            install_skill(Path(args.skill_dest).expanduser(), force=True)
        results["skill"] = {"destination": str(Path(args.skill_dest).expanduser()), "dryRun": args.dry_run}
    if args.install_notify and not args.skip_notify:
        results["notify"] = install_notify_bridge(Path(args.config).expanduser(), dry_run=args.dry_run)
    if not args.skip_hooks:
        results["hooks"] = install_hooks_bridge(Path(args.hooks_file).expanduser(), dry_run=args.dry_run)
    if not args.skip_active_project and args.project_id:
        results["activeProject"] = write_active_project(args.project_id, dry_run=args.dry_run)
    print(json.dumps({"ok": True, **results}, indent=2))


if __name__ == "__main__":
    main()
