"""Install the Pet Studio skill into a local Codex skills directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pet-studio-kit"
DEFAULT_DESTINATION = Path.home() / ".codex" / "skills" / "pet-studio"
INCLUDED = [
    "SKILL.md",
    "agents",
    "generation-workflow.json",
    "kit",
    "scripts",
]


def is_unsafe_replace_target(path: Path) -> bool:
    resolved = path.resolve()
    protected = {ROOT.resolve(), ROOT.parent.resolve(), Path.home().resolve()}
    codex_home = (Path.home() / ".codex").resolve()
    skills_root = (codex_home / "skills").resolve()
    anchor = Path(resolved.anchor).resolve()
    if resolved in protected or resolved in {codex_home, skills_root} or resolved == anchor:
        return True
    if resolved == ROOT.resolve() or ROOT.resolve() in resolved.parents:
        return True
    if (resolved / ".git").exists() or (resolved / ".codex").exists():
        return True
    return False


def copy_item(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def install(destination: Path, force: bool) -> None:
    if not (SOURCE / "SKILL.md").exists():
        raise SystemExit(f"Skill source is missing SKILL.md: {SOURCE}")
    if destination.exists():
        if not force:
            raise SystemExit(f"Destination already exists: {destination}\nRe-run with --force to replace it.")
        if is_unsafe_replace_target(destination):
            raise SystemExit(f"Refusing to replace unsafe skill destination: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in INCLUDED:
        copy_item(SOURCE / name, destination / name)
    print(f"Installed Pet Studio skill to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default=str(DEFAULT_DESTINATION), help="Destination skill directory")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed skill")
    args = parser.parse_args()
    install(Path(args.dest).expanduser(), args.force)


if __name__ == "__main__":
    main()
