"""Codex hook bridge status and diagnostics for Pet Studio.

Quick health check for the Codex <-> Pet Studio integration layer.
Answers: Are hooks installed? Is the bridge reachable? Are events flowing?
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WIDGET_DIR = ROOT / "pet-studio-widget"
CODEX_DIR = ROOT / ".codex"

DEFAULT_REGISTRY = WIDGET_DIR / "project-room-projects.json"
DEFAULT_HOOKS_FILE = CODEX_DIR / "hooks.json"
DEFAULT_HOOK_LOG = WIDGET_DIR / "project-room-hook-events.jsonl"
DEFAULT_STATE_FILE = WIDGET_DIR / "project-room-state.json"
DEFAULT_ACTIVE_FILE = WIDGET_DIR / "project-room-active.json"
DEFAULT_SKILL_DIR = Path.home() / ".codex" / "skills" / "pet-studio"

EXPECTED_HOOKS = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "user_prompt_submit",
    "PreToolUse": "pre_tool_use",
    "PostToolUse": "post_tool_use",
    "PreCompact": "pre_compact",
    "Stop": "stop",
}


@dataclass
class StatusItem:
    name: str
    ok: bool
    message: str
    warning: bool = False
    detail: str | None = None


def pass_item(name: str, message: str, detail: str | None = None) -> StatusItem:
    return StatusItem(name=name, ok=True, message=message, detail=detail)


def fail_item(name: str, message: str, detail: str | None = None) -> StatusItem:
    return StatusItem(name=name, ok=False, message=message, detail=detail)


def warn_item(name: str, message: str, detail: str | None = None) -> StatusItem:
    return StatusItem(name=name, ok=True, message=message, warning=True, detail=detail)


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def check_hooks_installed(hooks_file: Path) -> StatusItem:
    if not hooks_file.exists():
        return fail_item("hooks-installed", f"hooks.json not found at {rel_path(hooks_file)}")
    try:
        data = json.loads(hooks_file.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as error:
        return fail_item("hooks-installed", f"Cannot read hooks.json: {error}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return fail_item("hooks-installed", "hooks.json has no 'hooks' object")

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
                    if isinstance(command, str) and "codex_pet_hook.py" in command and f"--hook {hook_name}" in command:
                        found = True
                        break
                if found:
                    break
        if not found:
            missing.append(event)

    if missing:
        return warn_item(
            "hooks-installed",
            f"Missing hooks: {', '.join(missing)}",
            detail="Run: .\\tools\\pet_studio_python.cmd tools\\install_pet_studio_codex_integration.py --project-id <id>",
        )
    return pass_item("hooks-installed", f"All {len(EXPECTED_HOOKS)} lifecycle hooks registered")


def check_skill_installed(skill_dir: Path) -> StatusItem:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return fail_item("skill-installed", f"Skill not found at {rel_path(skill_file)}")
    return pass_item("skill-installed", f"Installed at {rel_path(skill_file)}")


def check_hook_log_activity(log_file: Path, max_lines: int = 20) -> StatusItem:
    if not log_file.exists():
        return warn_item(
            "hook-activity",
            f"No hook log at {rel_path(log_file)}",
            detail="Hooks may not have fired yet. Run a Codex session to generate events.",
        )

    lines = log_file.read_text(encoding="utf-8").splitlines()
    if not lines:
        return warn_item("hook-activity", "Hook log is empty")

    # Parse last N entries
    recent: list[dict[str, Any]] = []
    for raw in reversed(lines[-max_lines:]):
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        recent.append(entry)

    if not recent:
        return warn_item("hook-activity", "No readable JSON entries in hook log")

    # Check timestamps for staleness
    last_entry = recent[0]
    last_ts = last_entry.get("timestamp", "")
    last_hook = last_entry.get("hook", "?")
    last_state = last_entry.get("state", "?")
    last_skipped = last_entry.get("skipped", False)

    # Count by hook type
    hook_counts: dict[str, int] = {}
    for entry in recent:
        h = entry.get("hook", "unknown")
        hook_counts[h] = hook_counts.get(h, 0) + 1

    detail_parts = [f"Last: {last_hook} -> {last_state} at {last_ts}"]
    if last_skipped:
        detail_parts.append("WARNING: last event was SKIPPED (no project resolved)")
    detail_parts.append(f"Recent events by type: {json.dumps(hook_counts)}")

    # Check for skipped events
    skipped = sum(1 for e in recent if e.get("skipped", False))
    if skipped > 0:
        return warn_item(
            "hook-activity",
            f"{skipped}/{len(recent)} recent events were skipped",
            detail="; ".join(detail_parts),
        )

    return pass_item(
        "hook-activity",
        f"{len(recent)} recent events, last: {last_hook} -> {last_state}",
        detail="; ".join(detail_parts),
    )


def check_state_bridge(state_file: Path) -> StatusItem:
    if not state_file.exists():
        return warn_item("state-bridge", f"No state file at {rel_path(state_file)}")
    try:
        data = json.loads(state_file.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as error:
        return fail_item("state-bridge", f"Cannot read state file: {error}")

    state = data.get("state", "?")
    project_id = data.get("projectId", "?")
    updated_at = data.get("updatedAt", "unknown")

    # Check staleness
    stale = False
    if updated_at and updated_at != "unknown":
        try:
            ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            age_s = (datetime.now(timezone.utc) - ts).total_seconds()
            if state in {"running", "waiting", "review", "failed", "blocked", "handoff"}:
                if age_s > 300:
                    stale = True
        except (ValueError, TypeError):
            pass

    if stale:
        return warn_item(
            "state-bridge",
            f"State '{state}' for '{project_id}' may be stale (updated {updated_at})",
            detail="Widget may need restart or explicit state reset",
        )
    return pass_item(
        "state-bridge",
        f"State: {state} for project '{project_id}' (updated {updated_at})",
    )


def check_active_project(active_file: Path) -> StatusItem:
    if not active_file.exists():
        return pass_item("active-project", "No active project pin (uses workspace matching)")
    try:
        data = json.loads(active_file.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as error:
        return warn_item("active-project", f"Cannot read active project file: {error}")
    project_id = data.get("projectId", "?")
    return pass_item("active-project", f"Pinned to '{project_id}'")


def check_project_registry(registry: Path, project_id: str) -> StatusItem:
    if not registry.exists():
        return fail_item("registry", f"Registry not found at {rel_path(registry)}")
    try:
        data = json.loads(registry.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as error:
        return fail_item("registry", f"Cannot read registry: {error}")
    projects = data.get("projects", [])
    for p in projects:
        if isinstance(p, dict) and p.get("projectId") == project_id:
            if p.get("enabled") is not True:
                return warn_item("registry", f"Project '{project_id}' exists but is disabled")
            return pass_item("registry", f"Project '{project_id}' registered and enabled")
    return warn_item("registry", f"Project '{project_id}' not found in registry")


def build_status_report(args: argparse.Namespace) -> dict[str, Any]:
    hooks_file = Path(args.hooks_file).expanduser()
    log_file = Path(args.hook_log).expanduser()
    state_file = Path(args.state_file).expanduser()
    active_file = Path(args.active_file).expanduser()
    registry = Path(args.registry).expanduser()
    skill_dir = Path(args.skill_dir).expanduser()

    items: list[StatusItem] = [
        check_hooks_installed(hooks_file),
        check_skill_installed(skill_dir),
        check_hook_log_activity(log_file, args.hook_log_lines),
        check_state_bridge(state_file),
        check_active_project(active_file),
        check_project_registry(registry, args.project_id),
    ]

    # Overall verdict
    critical_fails = [i for i in items if not i.ok and not i.warning]
    warnings = [i for i in items if i.warning]

    if critical_fails:
        verdict = "FAIL"
        verdict_message = f"{len(critical_fails)} critical issue(s) found"
    elif warnings:
        verdict = "WARN"
        verdict_message = f"{len(warnings)} warning(s), no critical issues"
    else:
        verdict = "OK"
        verdict_message = "Codex bridge is healthy"

    report = {
        "verdict": verdict,
        "verdictMessage": verdict_message,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "projectId": args.project_id,
        "hooksFile": str(hooks_file),
        "hookLog": str(log_file),
        "stateFile": str(state_file),
        "checks": [
            {
                "name": i.name,
                "ok": i.ok,
                "warning": i.warning,
                "message": i.message,
                "detail": i.detail,
            }
            for i in items
        ],
    }
    return report


def print_report(report: dict[str, Any], human: bool = True) -> None:
    if human:
        verdict = report["verdict"]
        marker = {"OK": "OK", "WARN": "WARN", "FAIL": "FAIL"}.get(verdict, "???")
        print(f"[{marker}] {report['verdictMessage']}")
        print(f"  Project: {report['projectId']}")
        print(f"  Time:    {report['timestamp']}")
        print()
        for check in report["checks"]:
            icon = "WARN" if check["warning"] else ("OK" if check["ok"] else "FAIL")
            print(f"  [{icon}] {check['name']}: {check['message']}")
            if check.get("detail"):
                print(f"         {check['detail']}")
    else:
        print(json.dumps(report, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex hook bridge status and diagnostics")
    parser.add_argument("--project-id", default="gakju-archive-demo")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--hooks-file", default=str(DEFAULT_HOOKS_FILE))
    parser.add_argument("--hook-log", default=str(DEFAULT_HOOK_LOG))
    parser.add_argument("--hook-log-lines", type=int, default=20)
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--active-file", default=str(DEFAULT_ACTIVE_FILE))
    parser.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR))
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    report = build_status_report(args)
    print_report(report, human=not args.json)
    raise SystemExit(0 if report["verdict"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
