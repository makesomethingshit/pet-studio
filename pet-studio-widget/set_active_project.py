"""Pin the active Pet Studio project for Codex event adapters."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from project_room_registry import DEFAULT_ACTIVE_PROJECT_FILE, DEFAULT_REGISTRY, ProjectRegistryError, select_project


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_active_project(
    active_project_file: Path,
    project_id: str,
    workspace_path: Path | None = None,
    updated_at: str | None = None,
) -> dict:
    payload = {
        "schemaVersion": 1,
        "projectId": project_id,
        "workspacePath": str(workspace_path.resolve()) if workspace_path else None,
        "updatedAt": updated_at or utc_now(),
    }
    active_project_file.parent.mkdir(parents=True, exist_ok=True)
    active_project_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_REGISTRY), help="Project assignment registry path")
    parser.add_argument("--active-project-file", default=str(DEFAULT_ACTIVE_PROJECT_FILE), help="Active project pin JSON path")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--cwd", default=None, help="Workspace directory to record with the active project")
    parser.add_argument("--updated-at", default=None, help="Override updatedAt; mainly useful for deterministic tests")
    args = parser.parse_args()

    try:
        project = select_project(args.config, args.project_id)
    except ProjectRegistryError as error:
        raise SystemExit(str(error)) from error

    workspace_path = Path(args.cwd).expanduser() if args.cwd else None
    active_file = Path(args.active_project_file).expanduser()
    payload = write_active_project(active_file, project.project_id, workspace_path, args.updated_at)
    print(json.dumps({"ok": True, "activeProjectFile": str(active_file), "activeProject": payload}, indent=2))


if __name__ == "__main__":
    main()
