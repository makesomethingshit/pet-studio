"""Auto-detect project from current workspace and activate it.

Usage:
    python tools/auto_detect_project.py [--cwd <path>]

If --cwd is omitted, uses the current directory.
Prints the detected project ID and updates the active project pin.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "pet_studio_core"
ACTIVE_PROJECT_FILE = ROOT / "pet-studio-widget" / "project-room-active.json"
DEFAULT_REGISTRY = ROOT / "pet-studio-widget" / "project-room-projects.json"

if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from registry import infer_project_for_workspace, ProjectRegistryError  # noqa: E402


def detect(cwd: Path | None = None) -> str:
    """Detect project ID from workspace path."""
    workspace = (cwd or Path.cwd()).resolve()
    try:
        project = infer_project_for_workspace(str(DEFAULT_REGISTRY), str(workspace))
        return project.project_id
    except ProjectRegistryError:
        return ""


def activate(project_id: str, workspace: Path) -> bool:
    """Set the active project pin."""
    cmd = [
        sys.executable,
        str(ROOT / "pet-studio-widget" / "set_active_project.py"),
        "--project-id", project_id,
        "--cwd", str(workspace),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-detect project from workspace")
    parser.add_argument("--cwd", default=None, help="Workspace directory (default: current dir)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    workspace = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd().resolve()
    project_id = detect(workspace)

    if not project_id:
        if args.json:
            print(json.dumps({"ok": False, "error": f"No project registered for workspace: {workspace}"}))
        else:
            print(f"  No project registered for: {workspace}")
            print(f"  Register one with: python tools\\create_room_interactive.py")
        sys.exit(1)

    ok = activate(project_id, workspace)

    if args.json:
        print(json.dumps({"ok": ok, "projectId": project_id, "workspace": str(workspace)}))
    else:
        if ok:
            print(f"  Detected: {project_id}")
            print(f"  Workspace: {workspace}")
            print(f"  Active project pin updated.")
            print()
            print(f"  Launch widget:")
            print(f"    .\\tools\\pet_studio_widget.cmd --project-id {project_id} --scale 1.25")
        else:
            print(f"  [ERROR] Failed to activate {project_id}")
            sys.exit(1)


if __name__ == "__main__":
    main()
