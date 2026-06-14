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


def demo_launch_command(project_id: str, registry: Path) -> str:
    command = [".\\tools\\pet_studio_widget.cmd", "--project-id", project_id, "--scale", "1.25"]
    if registry.expanduser().resolve() != DEFAULT_REGISTRY.resolve():
        command[1:1] = ["--config", str(registry.expanduser())]
    return command_preview(command)


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


def check_demo_registry(registry: Path, project_id: str) -> tuple[CheckResult, dict[str, Any] | None]:
    if not registry.exists():
        return fail_check("registry", f"Missing registry: {display_path(registry)}"), None
    try:
        project = find_project(registry, project_id)
    except (json.JSONDecodeError, OSError) as error:
        return fail_check("registry", f"Cannot read {display_path(registry)}: {error}"), None
    if project is None:
        return fail_check("registry", f"Project {project_id!r} is not registered in {display_path(registry)}"), None
    if project.get("enabled") is not True:
        return fail_check("registry", f"Project {project_id!r} is registered but disabled"), project
    return pass_check("registry", f"{project_id} is enabled"), project


def check_sample_kit(registry: Path, project: dict[str, Any] | None) -> CheckResult:
    if not project:
        return fail_check("sample-kit", "Cannot check sample kit because the demo project was not resolved")
    raw_kit_path = project.get("kitPath")
    if not isinstance(raw_kit_path, str) or not raw_kit_path.strip():
        return fail_check("sample-kit", "Demo project has no kitPath")
    kit_dir = resolve_registry_path(registry, raw_kit_path)
    manifest = kit_dir / "project-room.json"
    if not manifest.exists():
        return fail_check("sample-kit", f"Missing sample manifest: {display_path(manifest)}")
    try:
        kit = load_json(manifest)
    except (json.JSONDecodeError, OSError) as error:
        return fail_check("sample-kit", f"Cannot read {display_path(manifest)}: {error}")
    layers = kit.get("layers")
    if not isinstance(layers, list) or not layers:
        return fail_check("sample-kit", f"Sample manifest has no layers: {display_path(manifest)}")
    return pass_check("sample-kit", f"found {display_path(manifest)}")


def hook_command_has_event(command: str, hook_name: str) -> bool:
    return "codex_pet_hook.py" in command and f"--hook {hook_name}" in command


def check_hooks_config(hooks_file: Path) -> CheckResult:
    if not hooks_file.exists():
        return warn_check(
            "hooks",
            f"Missing hooks file: {display_path(hooks_file)}. Run tools\\install_pet_studio_codex_integration.py.",
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
        return warn_check("hooks", "Missing Pet Studio hook entries: " + ", ".join(missing))
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


def render_demo(root: Path, registry: Path, project_id: str, output: Path) -> CheckResult:
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
        return fail_check("render", f"Demo render failed: {detail}")
    if not output.exists() or output.stat().st_size == 0:
        return fail_check("render", f"Demo render did not create {display_path(output)}")
    return pass_check("render", f"wrote {display_path(output)}")


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


def run_checks(args: argparse.Namespace) -> list[CheckResult]:
    registry = Path(args.registry).expanduser()
    skill_dir = Path(args.skill_dir).expanduser()
    hooks_file = Path(args.hooks_file).expanduser()
    render_output = Path(args.render_output).expanduser()

    results: list[CheckResult] = [check_python_environment()]
    if not args.skip_skill:
        results.append(check_skill_install(skill_dir))
    registry_result, project = check_demo_registry(registry, args.project_id)
    results.append(registry_result)
    results.append(check_sample_kit(registry, project))
    if not args.skip_hooks:
        results.append(check_hooks_config(hooks_file))
    results.append(check_local_only_ignores(ROOT))
    if not args.skip_render:
        results.append(render_demo(ROOT, registry, args.project_id, render_output))
    return results


def print_text_report(results: list[CheckResult], args: argparse.Namespace) -> None:
    for result in results:
        marker = "WARN" if result.warning else ("OK" if result.ok else "FAIL")
        print(f"[{marker}] {result.name}: {result.message}")
    if all(result.ok for result in results):
        print()
        print("Demo launch command:")
        print(demo_launch_command(args.project_id, Path(args.registry)))
        print(f"Render output: {display_path(Path(args.render_output).expanduser())}")
        print("Hook trust hint: restart Codex or open /hooks if Codex asks you to trust the commands.")
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
    results = run_checks(args)
    ok = all(result.ok for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "checks": [result.__dict__ for result in results]}, indent=2))
    else:
        print_text_report(results, args)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
