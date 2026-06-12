"""Run the full Project Room Kit compatibility experiment."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_step(name: str, command: list[str], cwd: Path) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "name": name,
        "command": command,
        "startedAt": started,
        "exitCode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def copytree_clean(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-kit-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--hatch-pet-dir", default=r"C:\Users\USER\.codex\skills\hatch-pet")
    parser.add_argument("--pet-id", default="project-room-full-experiment")
    parser.add_argument("--display-name", default="Project Room Full Experiment")
    args = parser.parse_args()

    source_kit_dir = Path(args.source_kit_dir)
    out_dir = Path(args.out_dir)
    experiment_kit_dir = out_dir / "kit"
    package_dir = out_dir / "package"
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parents[1]
    hatch_pet_dir = Path(args.hatch_pet_dir)
    report_path = out_dir / "full-experiment-report.json"

    out_dir.mkdir(parents=True, exist_ok=True)
    copytree_clean(source_kit_dir, experiment_kit_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        run_step(
            "create sample assets",
            [args.python, str(scripts_dir / "create_sample_assets.py"), "--kit-dir", str(experiment_kit_dir)],
            repo_root,
        ),
        run_step(
            "style-lock validation",
            [
                args.python,
                str(scripts_dir / "validate_project_room_kit.py"),
                "--kit",
                str(experiment_kit_dir / "project-room.json"),
                "--json-out",
                str(out_dir / "kit-style-validation.json"),
            ],
            repo_root,
        ),
        run_step(
            "bake pet package",
            [
                args.python,
                str(scripts_dir / "bake_project_room_pet.py"),
                "--kit",
                str(experiment_kit_dir / "project-room.json"),
                "--out-dir",
                str(package_dir),
                "--pet-id",
                args.pet_id,
                "--display-name",
                args.display_name,
            ],
            repo_root,
        ),
        run_step(
            "hatch-pet atlas validation",
            [
                args.python,
                str(hatch_pet_dir / "scripts" / "validate_atlas.py"),
                str(package_dir / "spritesheet.webp"),
                "--json-out",
                str(out_dir / "atlas-validation.json"),
            ],
            repo_root,
        ),
        run_step(
            "contact sheet generation",
            [
                args.python,
                str(hatch_pet_dir / "scripts" / "make_contact_sheet.py"),
                str(package_dir / "spritesheet.webp"),
                "--output",
                str(out_dir / "contact-sheet.png"),
            ],
            repo_root,
        ),
    ]

    ok = all(step["ok"] for step in steps)
    report = {
        "ok": ok,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceKitDir": str(source_kit_dir),
        "experimentKitDir": str(experiment_kit_dir),
        "packageDir": str(package_dir),
        "outputs": {
            "petJson": str(package_dir / "pet.json"),
            "spritesheet": str(package_dir / "spritesheet.webp"),
            "styleValidation": str(out_dir / "kit-style-validation.json"),
            "atlasValidation": str(out_dir / "atlas-validation.json"),
            "contactSheet": str(out_dir / "contact-sheet.png"),
        },
        "steps": steps,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
