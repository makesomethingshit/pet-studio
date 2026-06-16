"""Launch the official Pet Studio widget runtime from an installed skill."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_repo_root(path: Path) -> bool:
    return (path / "pet-studio-widget" / "pet_studio_widget.py").exists()


def resolve_repo_root(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if os.environ.get("PET_STUDIO_REPO"):
        candidates.append(Path(os.environ["PET_STUDIO_REPO"]).expanduser())

    location_file = skill_root() / "repo-location.json"
    if location_file.exists():
        try:
            data = json.loads(location_file.read_text(encoding="utf-8"))
            if data.get("repoRoot"):
                candidates.append(Path(str(data["repoRoot"])).expanduser())
        except (OSError, json.JSONDecodeError):
            pass

    for base in (Path.cwd(), skill_root()):
        candidates.extend([base, *base.parents])

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if is_repo_root(resolved):
            return resolved

    raise SystemExit(
        "Official Pet Studio widget runtime was not found. "
        "Set PET_STUDIO_REPO to the cloned repo path, or reinstall the skill from the Pet Studio repo with "
        "`tools\\install_pet_studio_skill.py --force`."
    )


def should_run_foreground(widget_args: list[str], requested: bool) -> bool:
    if requested:
        return True
    foreground_flags = {"--list-projects", "--render-once", "--render-project-once"}
    return any(arg in foreground_flags for arg in widget_args)


def launch_widget(repo_root: Path, widget_args: list[str], foreground: bool) -> int:
    widget_script = repo_root / "pet-studio-widget" / "pet_studio_widget.py"
    if foreground:
        return subprocess.run([sys.executable, str(widget_script), *widget_args], cwd=repo_root, check=False).returncode

    launcher = repo_root / "tools" / "pet_studio_widget.cmd"
    if launcher.exists() and os.name == "nt":
        return subprocess.run([str(launcher), *widget_args], cwd=repo_root, check=False).returncode

    pythonw = os.environ.get("PET_STUDIO_PYTHONW") or "pythonw"
    return subprocess.Popen([pythonw, str(widget_script), *widget_args], cwd=repo_root).poll() or 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch the official Pet Studio widget runtime from an installed skill."
    )
    parser.add_argument("--repo", help="Path to the cloned Pet Studio repository")
    parser.add_argument("--foreground", action="store_true", help="Run in the current console for debugging")
    return parser


def main() -> None:
    parser = build_parser()
    args, widget_args = parser.parse_known_args()
    if not widget_args:
        parser.error("pass pet_studio_widget.py arguments, for example: --project-id gakju-archive-demo --scale 1.25")
    repo_root = resolve_repo_root(args.repo)
    raise SystemExit(launch_widget(repo_root, widget_args, should_run_foreground(widget_args, args.foreground)))


if __name__ == "__main__":
    main()
