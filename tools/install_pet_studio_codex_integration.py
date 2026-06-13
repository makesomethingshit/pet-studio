"""Install Pet Studio skill and Codex notify bridge for local development."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from install_project_room_skill import install as install_skill


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe"
CONFIG_PATH = Path.home() / ".codex" / "config.toml"
SKILL_DESTINATION = Path.home() / ".codex" / "skills" / "pet-studio"
PROJECT_ID = "fresh-custom-pet-room"


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
        str(ROOT / "project-room-widget" / "codex_pet_hook.py"),
        "--hook",
        "notify",
    ]
    if previous_notify and not is_pet_studio_notify(previous_notify):
        command.extend(["--passthrough", *previous_notify])
    return command


def is_pet_studio_notify(values: list[str]) -> bool:
    return any(value.endswith("codex_pet_hook.py") for value in values)


def install_notify_bridge(config_path: Path, dry_run: bool = False) -> dict:
    if not config_path.exists():
        raise SystemExit(f"Codex config not found: {config_path}")
    text = config_path.read_text(encoding="utf-8")
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
    active_file = ROOT / "project-room-widget" / "project-room-active.json"
    if dry_run:
        return {"activeProjectFile": str(active_file), "projectId": project_id, "dryRun": True}
    widget_dir = ROOT / "project-room-widget"
    if str(widget_dir) not in sys.path:
        sys.path.insert(0, str(widget_dir))
    from set_active_project import write_active_project as write_project_pin

    payload = write_project_pin(active_file, project_id, ROOT)
    return {"activeProjectFile": str(active_file), "activeProject": payload, "dryRun": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--skill-dest", default=str(SKILL_DESTINATION))
    parser.add_argument("--project-id", default=PROJECT_ID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-skill", action="store_true")
    parser.add_argument("--skip-notify", action="store_true")
    parser.add_argument("--skip-active-project", action="store_true")
    args = parser.parse_args()

    results: dict[str, object] = {}
    if not args.skip_skill:
        if not args.dry_run:
            install_skill(Path(args.skill_dest).expanduser(), force=True)
        results["skill"] = {"destination": str(Path(args.skill_dest).expanduser()), "dryRun": args.dry_run}
    if not args.skip_notify:
        results["notify"] = install_notify_bridge(Path(args.config).expanduser(), dry_run=args.dry_run)
    if not args.skip_active_project:
        results["activeProject"] = write_active_project(args.project_id, dry_run=args.dry_run)
    print(json.dumps({"ok": True, **results}, indent=2))


if __name__ == "__main__":
    main()
