"""Create local QA evidence for a registered Pet Studio project."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WIDGET_DIR = ROOT / "pet-studio-widget"
KIT_SCRIPTS = ROOT / "pet-studio-kit" / "scripts"
DEFAULT_REGISTRY = WIDGET_DIR / "project-room-projects.json"
VALIDATOR = KIT_SCRIPTS / "validate_project_room_kit.py"
KIT_RENDERER = KIT_SCRIPTS / "render_project_room_preview.py"
WIDGET_RENDERER = WIDGET_DIR / "pet_studio_widget.py"

if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))

from project_room_registry import ProjectRegistryError, select_project  # noqa: E402


def default_out_dir(project_id: str) -> Path:
    return ROOT / "runs" / project_id / "qa-pack"


def command_preview(command: list[str]) -> str:
    return " ".join(json.dumps(part) if any(char.isspace() for char in part) else part for part in command)


def run_step(name: str, command: list[str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise SystemExit(f"Step `{name}` failed: {detail}\nCommand: {command_preview(command)}")
    return completed.stdout


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_validation(kit_manifest: Path, output: Path) -> dict[str, Any]:
    run_step(
        "validation",
        [
            sys.executable,
            str(VALIDATOR),
            "--kit",
            str(kit_manifest),
            "--json-out",
            str(output),
        ],
    )
    return load_json(output)


def render_kit_state(kit_manifest: Path, state: str, output: Path) -> dict[str, Any]:
    stdout = run_step(
        f"kit render {state}",
        [
            sys.executable,
            str(KIT_RENDERER),
            "--kit",
            str(kit_manifest),
            "--state",
            state,
            "--out",
            str(output),
        ],
    )
    return json.loads(stdout)


def render_widget(registry: Path, project_id: str, output: Path) -> dict[str, Any]:
    stdout = run_step(
        "widget render",
        [
            sys.executable,
            str(WIDGET_RENDERER),
            "--config",
            str(registry),
            "--project-id",
            project_id,
            "--render-project-once",
            str(output),
        ],
    )
    return json.loads(stdout)


def write_coder_to_qa(
    path: Path,
    *,
    project_id: str,
    display_name: str,
    theme: str,
    registry: Path,
    kit_manifest: Path,
    artifacts: dict[str, str],
    warnings: list[str],
) -> None:
    warning_text = "\n".join(f"- {warning}" for warning in warnings) if warnings else "- None"
    body = f"""# CODER_TO_QA - Pet Studio QA Pack

## Project
- Project ID: `{project_id}`
- Display name: `{display_name}`
- Theme: `{theme or "unspecified"}`
- Registry: `{registry}`
- Kit manifest: `{kit_manifest}`

## Evidence
- Validation JSON: `{artifacts["validation"]}`
- Idle render: `{artifacts["idleRender"]}`
- All-state contact sheet: `{artifacts["allStatesContact"]}`
- Widget render: `{artifacts["widgetRender"]}`
- Summary JSON: `{artifacts["summary"]}`

## QA Focus
- Style consistency between room, props, main pet, and helper/sub-pet if present.
- Alpha cleanup, edge residue, halos, and transparent RGB residue.
- All-state contact sheet label readability and state coverage.
- Widget render composition, scale, bubble-safe room spacing, and project selection.
- Helper/sub-pet presence only when expected by the kit.

## Warnings
{warning_text}

## Notes
- This is local QA evidence for internal review.
- Do not edit `QA_REPORT.md` from this handoff.
- Do not include this QA pack in public git commits unless explicitly requested.
"""
    path.write_text(body, encoding="utf-8")


def create_qa_pack(project_id: str, registry: Path, out_dir: Path, state: str) -> dict[str, Any]:
    project = select_project(registry, project_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "validation": str(out_dir / "validation.json"),
        "idleRender": str(out_dir / "idle-render.png"),
        "allStatesContact": str(out_dir / "all-states-contact.png"),
        "widgetRender": str(out_dir / "widget-render.png"),
        "coderToQa": str(out_dir / "CODER_TO_QA.md"),
        "summary": str(out_dir / "qa-pack-summary.json"),
    }

    validation = render_validation(project.kit_manifest, Path(artifacts["validation"]))
    idle_render = render_kit_state(project.kit_manifest, state, Path(artifacts["idleRender"]))
    contact_render = render_kit_state(project.kit_manifest, "all", Path(artifacts["allStatesContact"]))
    widget_render = render_widget(registry, project_id, Path(artifacts["widgetRender"]))

    warnings = sorted(
        {
            *validation.get("warnings", []),
            *idle_render.get("warnings", []),
            *contact_render.get("warnings", []),
        }
    )

    write_coder_to_qa(
        Path(artifacts["coderToQa"]),
        project_id=project.project_id,
        display_name=project.display_name,
        theme=project.theme,
        registry=registry,
        kit_manifest=project.kit_manifest,
        artifacts=artifacts,
        warnings=warnings,
    )

    summary = {
        "ok": True,
        "projectId": project.project_id,
        "displayName": project.display_name,
        "theme": project.theme,
        "registry": str(registry),
        "kit": str(project.kit_manifest),
        "outDir": str(out_dir),
        "state": state,
        "artifacts": artifacts,
        "warnings": warnings,
        "widgetRender": widget_render,
    }
    Path(artifacts["summary"]).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Create local QA evidence for a registered Pet Studio project.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--out-dir", default=None, help="Output directory; defaults to runs/<project-id>/qa-pack")
    parser.add_argument("--state", default="idle", help="Kit state for the single-state render")
    args = parser.parse_args()

    registry = Path(args.registry).expanduser()
    out_dir = Path(args.out_dir).expanduser() if args.out_dir else default_out_dir(args.project_id)
    try:
        summary = create_qa_pack(args.project_id, registry, out_dir, args.state)
    except ProjectRegistryError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
