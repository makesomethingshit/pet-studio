"""Guided public wrapper for creating a first Pet Studio room."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "pet-studio-widget" / "project-room-projects.json"
CREATE_KIT_SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "create_project_room_kit.py"
KIT_SCRIPTS = ROOT / "pet-studio-kit" / "scripts"
if str(KIT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(KIT_SCRIPTS))

from asset_guardrails import AssetInput, format_guardrail_failure, is_safe_id, run_asset_guardrails  # noqa: E402


def slug_to_title(value: str) -> str:
    words = [word for word in value.replace("_", "-").split("-") if word]
    return " ".join(word[:1].upper() + word[1:] for word in words) or "Pet Studio Room"


def validate_project_id(project_id: str) -> None:
    if not is_safe_id(project_id):
        raise SystemExit(
            f"Project id `{project_id}` is not safe for generated file paths. "
            "Use letters, numbers, underscore, and hyphen only; start with a letter or number."
        )


def resolve_existing_path(raw: str, label: str) -> Path:
    path = Path(raw).expanduser()
    if not path.exists():
        raise SystemExit(f"{label} not found: {path}")
    return path


def default_out_dir(project_id: str) -> Path:
    return ROOT / "runs" / project_id


def selected_out_dir(args: argparse.Namespace) -> Path:
    return Path(args.out_dir).expanduser() if args.out_dir else default_out_dir(args.project_id)


def is_unsafe_replace_target(path: Path) -> bool:
    resolved = path.resolve()
    protected = {ROOT.resolve(), ROOT.parent.resolve(), Path.home().resolve()}
    anchor = Path(resolved.anchor).resolve()
    if resolved in protected or resolved == anchor:
        return True
    runs_root = (ROOT / "runs").resolve()
    if resolved == runs_root:
        return True
    if ROOT.resolve() in resolved.parents and runs_root not in resolved.parents:
        return True
    if (resolved / ".git").exists() or (resolved / ".codex").exists():
        return True
    return False


def ensure_output_dir_available(out_dir: Path, force: bool) -> None:
    if not out_dir.exists():
        return
    if force:
        if is_unsafe_replace_target(out_dir):
            raise SystemExit(f"Refusing to replace unsafe output directory: {out_dir}")
        shutil.rmtree(out_dir)
        return
    raise SystemExit(f"Output directory already exists: {out_dir}\nRe-run with --force to replace it.")


def build_create_command(args: argparse.Namespace) -> list[str]:
    project_id = args.project_id
    display_name = args.display_name or slug_to_title(project_id)
    out_dir = selected_out_dir(args)
    registry = Path(args.registry).expanduser()
    workspace_paths = args.workspace_path or [str(Path.cwd())]

    command = [
        sys.executable,
        str(CREATE_KIT_SCRIPT),
        "--out-dir",
        str(out_dir),
        "--pet-package",
        str(resolve_existing_path(args.pet_package, "Pet package")),
        "--room-image",
        str(resolve_existing_path(args.room_image, "Room image")),
        "--room-alpha-mode",
        args.room_alpha_mode,
        "--guardrail-mode",
        args.guardrail_mode,
        "--theme",
        args.theme,
        "--display-name",
        display_name,
        "--render-preview",
        "--render-contact",
        "--register-project",
        "--project-id",
        project_id,
        "--registry",
        str(registry),
    ]
    for prop in args.prop:
        prop_id, prop_path = parse_id_path(prop, "Prop")
        command.extend(["--prop", f"{prop_id}={prop_path}"])
    for placement in args.prop_placement:
        command.extend(["--prop-placement", placement])
    for helper in args.helper_package:
        helper_id, helper_path = parse_id_path(helper, "Helper package")
        command.extend(["--helper-package", f"{helper_id}={helper_path}"])
    for workspace_path in workspace_paths:
        command.extend(["--workspace-path", str(Path(workspace_path).expanduser())])
    if args.bake_fallback:
        command.append("--bake-fallback")
    return command


def parse_id_path(value: str, label: str) -> tuple[str, Path]:
    if "=" not in value:
        raise SystemExit(f"{label} must use id=path format: {value}")
    item_id, raw_path = value.split("=", 1)
    item_id = item_id.strip()
    if not item_id:
        raise SystemExit(f"{label} id cannot be empty: {value}")
    return item_id, resolve_existing_path(raw_path.strip(), label)


def command_preview(command: list[str]) -> str:
    return " ".join(json.dumps(part) if any(char.isspace() for char in part) else part for part in command)


def next_commands(project_id: str, registry: Path | None = None) -> dict[str, str]:
    registry = registry.expanduser() if registry else DEFAULT_REGISTRY
    uses_default_registry = registry.resolve() == DEFAULT_REGISTRY.resolve()
    preflight = [
        ".\\tools\\pet_studio_python.cmd",
        "tools\\pet_studio_preflight.py",
        "--project-id",
        project_id,
    ]
    launch = [
        ".\\tools\\pet_studio_widget.cmd",
        "--project-id",
        project_id,
        "--scale",
        "1.25",
    ]
    render = [
        ".\\tools\\pet_studio_python.cmd",
        "pet-studio-widget\\pet_studio_widget.py",
        "--project-id",
        project_id,
        "--render-project-once",
        f"runs\\{project_id}\\widget-render.png",
    ]
    qa_pack = [
        ".\\tools\\pet_studio_python.cmd",
        "tools\\pet_studio_create_qa_pack.py",
        "--project-id",
        project_id,
    ]
    if not uses_default_registry:
        registry_arg = str(registry)
        preflight.extend(["--registry", registry_arg])
        launch[1:1] = ["--config", registry_arg]
        render[2:2] = ["--config", registry_arg]
        qa_pack.extend(["--registry", registry_arg])
    return {
        "preflight": command_preview(preflight),
        "launch": command_preview(launch),
        "render": command_preview(render),
        "qaPack": command_preview(qa_pack),
    }


def load_report(out_dir: Path) -> dict:
    report_path = out_dir / "production-report.json"
    if not report_path.exists():
        return {}
    return json.loads(report_path.read_text(encoding="utf-8-sig"))


def success_summary(project_id: str, out_dir: Path, registry: Path) -> dict:
    report = load_report(out_dir)
    return {
        "ok": True,
        "projectId": project_id,
        "artifacts": {
            "kit": str(out_dir / "kit" / "project-room.json"),
            "validation": str(out_dir / "kit-validation.json"),
            "preview": str(out_dir / "room-preview.png"),
            "contact": str(out_dir / "room-contact.png"),
            "productionReport": str(out_dir / "production-report.json"),
            "generationBrief": str(out_dir / "generation-brief.json"),
        },
        "registeredProject": report.get("registeredProject"),
        "guardrails": report.get("guardrails"),
        "nextCommands": next_commands(project_id, registry),
    }


def guardrails_for_args(args: argparse.Namespace) -> dict:
    props = [AssetInput(prop_id, path) for prop_id, path in (parse_id_path(value, "Prop") for value in args.prop)]
    helpers = [AssetInput(helper_id, path) for helper_id, path in (parse_id_path(value, "Helper package") for value in args.helper_package)]
    return run_asset_guardrails(
        pet_package=resolve_existing_path(args.pet_package, "Pet package"),
        room_image=resolve_existing_path(args.room_image, "Room image"),
        props=props,
        helpers=helpers,
        prop_placements=args.prop_placement,
        mode=args.guardrail_mode,
        room_alpha_mode=args.room_alpha_mode,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and register a Pet Studio room with first-run defaults.")
    parser.add_argument("--project-id", required=True, help="Local Pet Studio project id, e.g. archive-nook")
    parser.add_argument("--pet-package", required=True, help="Existing hatch-pet package directory")
    parser.add_argument("--room-image", required=True, help="384x240 room PNG")
    parser.add_argument("--out-dir", default=None, help="Output directory; defaults to runs/<project-id>")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--workspace-path", action="append", default=[], help="Workspace path to link; defaults to current directory")
    parser.add_argument("--prop", action="append", default=[], help="Prop asset in id=path format; may be repeated")
    parser.add_argument("--prop-placement", action="append", default=[], help="Prop placement in id=background|behind-pet|front-of-pet|foreground format")
    parser.add_argument("--helper-package", action="append", default=[], help="Helper pet package in id=path format; may be repeated")
    parser.add_argument("--theme", default="pet studio room")
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--room-alpha-mode", choices=("safe", "balanced", "aggressive"), default="balanced")
    parser.add_argument("--guardrail-mode", choices=("basic", "strict", "off"), default="basic")
    parser.add_argument("--bake-fallback", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory")
    parser.add_argument("--verbose", action="store_true", help="Print the underlying kit creation output")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned command without creating files")
    args = parser.parse_args()

    out_dir = selected_out_dir(args)
    registry = Path(args.registry).expanduser()
    validate_project_id(args.project_id)
    if not args.dry_run:
        ensure_output_dir_available(out_dir, args.force)
    command = build_create_command(args)
    project_id = args.project_id
    guardrails = guardrails_for_args(args)
    if not guardrails["ok"]:
        raise SystemExit(format_guardrail_failure(guardrails))
    plan = {
        "ok": True,
        "projectId": project_id,
        "command": command,
        "commandPreview": command_preview(command),
        "guardrails": guardrails,
        "nextCommands": next_commands(project_id, registry),
        "dryRun": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return

    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if args.verbose and completed.stdout:
        print(completed.stdout, end="")
    if args.verbose and completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise SystemExit(completed.returncode)
    print(json.dumps(success_summary(project_id, out_dir, registry), indent=2))


if __name__ == "__main__":
    main()
