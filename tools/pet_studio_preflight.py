"""Public release preflight checks for Pet Studio."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ID = "gakju-archive-demo"
DEFAULT_REGISTRY = ROOT / "pet-studio-widget" / "project-room-projects.json"
DEFAULT_HOOKS_FILE = ROOT / ".codex" / "hooks.json"
DEFAULT_HOOK_LOG = ROOT / "pet-studio-widget" / "project-room-hook-events.jsonl"
DEFAULT_SKILL_DIR = Path.home() / ".codex" / "skills" / "pet-studio"
DEFAULT_RENDER_OUTPUT = ROOT / "runs" / "pet-studio-preflight-render.png"
VALIDATOR_SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "validate_project_room_kit.py"
EXPECTED_HOOKS = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "user_prompt_submit",
    "PreToolUse": "pre_tool_use",
    "PostToolUse": "post_tool_use",
    "PreCompact": "pre_compact",
    "Stop": "stop",
}
LOCAL_ONLY_PATHS = [
    "tester/README.md",
    "runs/fresh-custom-pet-room/README.md",
    "runs/example-room/qa-pack/CODER_TO_QA.md",
    "runs/pet-studio-preflight-render.png",
    "pet-studio-widget/project-room-active.json",
    "pet-studio-widget/project-room-hook-events.jsonl",
    "pet-studio-widget/project-room-layouts.json",
    "pet-studio-widget/project-room-session.json",
    "pet-studio-widget/project-room-state.json",
    "pet-studio-widget/project-room-window.json",
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str
    warning: bool = False


def pass_check(name: str, message: str) -> CheckResult:
    return CheckResult(name=name, ok=True, message=message)


def fail_check(name: str, message: str) -> CheckResult:
    return CheckResult(name=name, ok=False, message=message)


def warn_check(name: str, message: str) -> CheckResult:
    return CheckResult(name=name, ok=True, message=message, warning=True)


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def command_preview(command: list[str]) -> str:
    return " ".join(json.dumps(part) if any(char.isspace() for char in part) else part for part in command)


def uses_default_registry(registry: Path) -> bool:
    return registry.expanduser().resolve() == DEFAULT_REGISTRY.resolve()


def project_launch_command(project_id: str, registry: Path) -> str:
    command = [".\\tools\\pet_studio_widget.cmd", "--project-id", project_id, "--scale", "1.25"]
    if not uses_default_registry(registry):
        command[1:1] = ["--config", str(registry.expanduser())]
    return command_preview(command)


def project_render_command(project_id: str, registry: Path, output: Path) -> str:
    command = [
        ".\\tools\\pet_studio_python.cmd",
        "pet-studio-widget\\pet_studio_widget.py",
        "--project-id",
        project_id,
        "--render-project-once",
        str(output),
    ]
    if not uses_default_registry(registry):
        command[2:2] = ["--config", str(registry.expanduser())]
    return command_preview(command)


def project_qa_pack_command(project_id: str, registry: Path) -> str:
    command = [".\\tools\\pet_studio_python.cmd", "tools\\pet_studio_create_qa_pack.py", "--project-id", project_id]
    if not uses_default_registry(registry):
        command.extend(["--registry", str(registry.expanduser())])
    return command_preview(command)


def install_hooks_command(project_id: str) -> str:
    return command_preview(
        [
            ".\\tools\\pet_studio_python.cmd",
            "tools\\install_pet_studio_codex_integration.py",
            "--project-id",
            project_id,
        ]
    )


def hook_trust_hint(project_id: str) -> str:
    return f"Run {install_hooks_command(project_id)}, then restart Codex or open /hooks to trust the commands if prompted."


def registry_schema_hint() -> str:
    return 'Expected {"schemaVersion": 1, "projects": [...]}; recreate or repair the registry file.'


def register_project_hint(project_id: str, registry: Path) -> str:
    return (
        f"Register it with tools\\pet_studio_create_room.py --project-id {project_id} --registry {registry}, "
        "or inspect available ids with pet-studio-widget\\pet_studio_widget.py --list-projects."
    )


def kit_repair_hint(project_id: str, registry: Path) -> str:
    return (
        f"Fix kitPath for {project_id!r} in {display_path(registry)}, restore the missing kit, "
        f"or regenerate it with tools\\pet_studio_create_room.py --project-id {project_id} --registry {registry}."
    )


def next_commands(project_id: str, registry: Path, render_output: Path) -> dict[str, str]:
    return {
        "launch": project_launch_command(project_id, registry),
        "render": project_render_command(project_id, registry, render_output),
        "qaPack": project_qa_pack_command(project_id, registry),
        "installHooks": install_hooks_command(project_id),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_registry_path(registry: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (registry.parent / path).resolve()


def find_project(registry: Path, project_id: str) -> dict[str, Any] | None:
    data = load_json(registry)
    projects = data.get("projects")
    if not isinstance(projects, list):
        return None
    for project in projects:
        if isinstance(project, dict) and project.get("projectId") == project_id:
            return project
    return None


def check_python_environment() -> CheckResult:
    if sys.version_info < (3, 11):
        return fail_check("python", f"Python 3.11+ is required; found {sys.version.split()[0]}")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return fail_check("python", "Pillow is missing. Install it or use tools\\pet_studio_python.cmd.")
    return pass_check("python", f"{sys.version.split()[0]} with Pillow")


def check_skill_install(skill_dir: Path) -> CheckResult:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return fail_check(
            "skill",
            f"Pet Studio skill is not installed at {skill_file}. Run tools\\install_pet_studio_skill.py.",
        )
    return pass_check("skill", f"installed at {skill_file}")


def check_project_registry(registry: Path, project_id: str) -> tuple[CheckResult, dict[str, Any] | None]:
    if not registry.exists():
        return fail_check("registry", f"Missing registry: {display_path(registry)}"), None
    try:
        data = load_json(registry)
    except (json.JSONDecodeError, OSError) as error:
        return fail_check("registry", f"Cannot read {display_path(registry)}: {error}"), None
    if not isinstance(data, dict):
        return fail_check("registry", f"{display_path(registry)} must contain a JSON object. {registry_schema_hint()}"), None
    projects = data.get("projects")
    if not isinstance(projects, list):
        return fail_check("registry", f"{display_path(registry)} must contain a projects list. {registry_schema_hint()}"), None
    project = None
    for item in projects:
        if isinstance(item, dict) and item.get("projectId") == project_id:
            project = item
            break
    if project is None:
        return fail_check(
            "registry",
            f"Project {project_id!r} is not registered in {display_path(registry)}. {register_project_hint(project_id, registry)}",
        ), None
    if project.get("enabled") is not True:
        return fail_check("registry", f"Project {project_id!r} is registered but disabled. Set enabled to true in {display_path(registry)} or choose another project id."), project
    return pass_check("registry", f"{project_id} is enabled"), project


def check_demo_registry(registry: Path, project_id: str) -> tuple[CheckResult, dict[str, Any] | None]:
    return check_project_registry(registry, project_id)


def check_project_kit(registry: Path, project: dict[str, Any] | None) -> tuple[CheckResult, Path | None]:
    if not project:
        return fail_check("project-kit", "Cannot check project kit because the project was not resolved"), None
    raw_kit_path = project.get("kitPath")
    project_id = str(project.get("projectId", "?"))
    if not isinstance(raw_kit_path, str) or not raw_kit_path.strip():
        return fail_check(
            "project-kit",
            f"Project {project_id!r} has no kitPath. Add kitPath in project-room-projects.json or {register_project_hint(project_id, registry)}",
        ), None
    kit_path = resolve_registry_path(registry, raw_kit_path)
    manifest = kit_path if kit_path.name == "project-room.json" else kit_path / "project-room.json"
    if not manifest.exists():
        return fail_check("project-kit", f"Missing project manifest: {display_path(manifest)}. {kit_repair_hint(project_id, registry)}"), manifest
    try:
        kit = load_json(manifest)
    except (json.JSONDecodeError, OSError) as error:
        return fail_check("project-kit", f"Cannot read {display_path(manifest)}: {error}"), manifest
    layers = kit.get("layers")
    if not isinstance(layers, list) or not layers:
        return fail_check("project-kit", f"Project manifest has no layers: {display_path(manifest)}"), manifest
    return pass_check("project-kit", f"found {display_path(manifest)}"), manifest


def check_sample_kit(registry: Path, project: dict[str, Any] | None) -> CheckResult:
    result, _ = check_project_kit(registry, project)
    return result


def validate_project_kit(root: Path, manifest: Path | None) -> CheckResult:
    if manifest is None:
        return fail_check("kit-validation", "Cannot validate kit because the project manifest was not resolved")
    command = [sys.executable, str(VALIDATOR_SCRIPT), "--kit", str(manifest)]
    completed = subprocess.run(command, cwd=root, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if len(detail) > 800:
            detail = detail[:797] + "..."
        return fail_check("kit-validation", f"Kit validation failed for {display_path(manifest)}: {detail}")
    return pass_check("kit-validation", f"validated {display_path(manifest)}")


def hook_command_has_event(command: str, hook_name: str) -> bool:
    return "codex_pet_hook.py" in command and f"--hook {hook_name}" in command


def check_hooks_config(hooks_file: Path, project_id: str = DEFAULT_PROJECT_ID) -> CheckResult:
    if not hooks_file.exists():
        return warn_check(
            "hooks",
            f"Missing hooks file: {display_path(hooks_file)}. {hook_trust_hint(project_id)}",
        )
    try:
        data = load_json(hooks_file)
    except (json.JSONDecodeError, OSError) as error:
        return fail_check("hooks", f"Cannot read {display_path(hooks_file)}: {error}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return fail_check("hooks", f"{display_path(hooks_file)} has no hooks object")

    missing: list[str] = []
    for event, hook_name in EXPECTED_HOOKS.items():
        groups = hooks.get(event)
        found = False
        if isinstance(groups, list):
            for group in groups:
                handlers = group.get("hooks") if isinstance(group, dict) else None
                if not isinstance(handlers, list):
                    continue
                for handler in handlers:
                    command = handler.get("command") if isinstance(handler, dict) else None
                    if isinstance(command, str) and hook_command_has_event(command, hook_name):
                        found = True
                        break
                if found:
                    break
        if not found:
            missing.append(event)

    if missing:
        return warn_check(
            "hooks",
            "Missing Pet Studio hook entries: "
            + ", ".join(missing)
            + f". {hook_trust_hint(project_id)}",
        )
    return pass_check("hooks", "project-local Codex lifecycle hooks are installed; trust them in /hooks if prompted")


def git_check_ignore(root: Path, relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative_path],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    return completed.returncode == 0


def check_local_only_ignores(root: Path) -> CheckResult:
    missing = [path for path in LOCAL_ONLY_PATHS if not git_check_ignore(root, path)]
    if missing:
        return fail_check("local-only", "These local-only paths are not ignored by git: " + ", ".join(missing))
    return pass_check("local-only", "QA output, preflight render, hook logs, and runtime state are ignored")


def render_project(root: Path, registry: Path, project_id: str, output: Path) -> CheckResult:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(root / "pet-studio-widget" / "pet_studio_widget.py"),
        "--config",
        str(registry),
        "--project-id",
        project_id,
        "--render-project-once",
        str(output),
    ]
    completed = subprocess.run(command, cwd=root, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        return fail_check("render", f"Project render failed: {detail}")
    if not output.exists() or output.stat().st_size == 0:
        return fail_check("render", f"Project render did not create {display_path(output)}")
    return pass_check("render", f"wrote {display_path(output)}")


def render_demo(root: Path, registry: Path, project_id: str, output: Path) -> CheckResult:
    return render_project(root, registry, project_id, output)


def read_hook_log_summary(log_file: Path, max_lines: int) -> list[str]:
    if not log_file.exists():
        return [f"No hook log found at {display_path(log_file)}"]
    lines = log_file.read_text(encoding="utf-8").splitlines()[-max_lines:]
    summary: list[str] = []
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        hook = entry.get("hook", "?")
        state = entry.get("state", "?")
        message = entry.get("message", "")
        summary.append(f"{hook} -> {state}: {message}")
    return summary or [f"No readable hook entries in {display_path(log_file)}"]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    registry = Path(args.registry).expanduser()
    skill_dir = Path(args.skill_dir).expanduser()
    hooks_file = Path(args.hooks_file).expanduser()
    render_output = Path(args.render_output).expanduser()

    results: list[CheckResult] = [check_python_environment()]
    if not args.skip_skill:
        results.append(check_skill_install(skill_dir))
    registry_result, project = check_project_registry(registry, args.project_id)
    results.append(registry_result)
    kit_result, manifest = check_project_kit(registry, project)
    results.append(kit_result)
    if kit_result.ok:
        results.append(validate_project_kit(ROOT, manifest))
    if not args.skip_hooks:
        results.append(check_hooks_config(hooks_file, args.project_id))
    results.append(check_local_only_ignores(ROOT))
    if not args.skip_render:
        results.append(render_project(ROOT, registry, args.project_id, render_output))
    return {
        "ok": all(result.ok for result in results),
        "projectId": args.project_id,
        "registry": str(registry),
        "kitManifest": str(manifest) if manifest is not None else None,
        "nextCommands": next_commands(args.project_id, registry, render_output),
        "renderOutput": str(render_output),
        "hookTrustHint": hook_trust_hint(args.project_id),
        "checks": [result.__dict__ for result in results],
    }


def run_checks(args: argparse.Namespace) -> list[CheckResult]:
    return [CheckResult(**result) for result in build_report(args)["checks"]]


def print_text_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    results = [CheckResult(**result) for result in report["checks"]]
    for result in results:
        marker = "WARN" if result.warning else ("OK" if result.ok else "FAIL")
        print(f"[{marker}] {result.name}: {result.message}")
    if all(result.ok for result in results):
        print()
        print("Project launch command:")
        print(report["nextCommands"]["launch"])
        print(f"Render output: {display_path(Path(report['renderOutput']).expanduser())}")
        print("Hook trust hint:")
        print(report["hookTrustHint"])
    if args.show_hook_log:
        print()
        print("Recent hook log:")
        for line in read_hook_log_summary(Path(args.hook_log).expanduser(), args.hook_log_lines):
            print(f"- {line}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Pet Studio public release preflight checks.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--hooks-file", default=str(DEFAULT_HOOKS_FILE))
    parser.add_argument("--hook-log", default=str(DEFAULT_HOOK_LOG))
    parser.add_argument("--hook-log-lines", type=int, default=10)
    parser.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR))
    parser.add_argument("--render-output", default=str(DEFAULT_RENDER_OUTPUT))
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-skill", action="store_true")
    parser.add_argument("--skip-hooks", action="store_true")
    parser.add_argument("--show-hook-log", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable check results")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report, args)
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
