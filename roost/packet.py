"""Work packet export for Pet Studio.

Converts team_state.json project data into a compact packet for the selected
agent. The older codex_packet marker and function names are kept for
compatibility with existing exports and integrations.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from roost.model_profile import role_model_env_clear, role_model_env_overrides

_SLUG_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


def _safe_project_filename(project_id: str) -> str:
    """Return a safe filename slug for the given project ID.

    Raises:
        ValueError: If project_id contains path-unsafe characters.
    """
    if not _SLUG_RE.match(project_id):
        raise ValueError(
            f"Unsafe project_id for file export: {project_id!r}. "
            "Use only alphanumeric, dots, hyphens, underscores (1-64 chars)."
        )
    return project_id


def build_codex_packet(
    project_id: str,
    team_state: Any,
    state: str = "idle",
) -> dict[str, Any]:
    """Build a work packet from team state.

    Args:
        project_id: Project identifier.
        team_state: TeamState instance.
        state: Current widget state string.

    Returns:
        Dict in work packet v1 format.
    """
    project = team_state.get_project(project_id) if team_state else None
    mission = team_state.get_project_mission(project_id) if team_state else ""
    queue: list[dict] = []
    if team_state:
        queue = team_state.get_project_queue(project_id)
    model_profile = (
        team_state.get_active_model_profile()
        if team_state and hasattr(team_state, "get_active_model_profile")
        else {}
    )
    role_model_plan = (
        team_state.list_role_model_plan()
        if team_state and hasattr(team_state, "list_role_model_plan")
        else []
    )
    team_model_preset = (
        team_state.get_team_model_preset_id()
        if team_state and hasattr(team_state, "get_team_model_preset_id")
        else "custom"
    )
    team_model_savings = (
        team_state.estimate_team_model_savings()
        if team_state and hasattr(team_state, "estimate_team_model_savings")
        else {}
    )
    employees = team_state.get_employees() if team_state and hasattr(team_state, "get_employees") else []

    tasks = []
    for item in queue:
        tasks.append(
            {
                "id": item.get("id", ""),
                "type": item.get("type", item.get("task", "unknown")),
                "status": item.get("status", "waiting"),
                "enqueued_at": item.get("enqueuedAt", ""),
                "payload": {
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "type", "task", "status", "enqueuedAt")
                },
            }
        )

    return {
        "work_packet": "v1",
        "codex_packet": "v1",
        "project": {
            "id": project_id,
            "name": (project.get("displayName", project_id) if project else project_id),
            "state": state,
        },
        "mission": mission,
        "model_profile": model_profile,
        "team_model_preset": team_model_preset,
        "role_model_plan": role_model_plan,
        "role_model_env": role_model_env_overrides(role_model_plan),
        "role_model_env_clear": role_model_env_clear(role_model_plan),
        "team_model_savings": team_model_savings,
        "employees": employees,
        "tasks": tasks,
        "state": {
            "current": state,
            "blocked_by": None,
        },
    }


def export_codex_packet(
    project_id: str,
    team_state: Any,
    out_dir: str | Path = "codex-packets",
    state: str = "idle",
) -> Path:
    """Build and write a legacy-compatible packet JSON file.

    Args:
        project_id: Project identifier.
        team_state: TeamState instance.
        out_dir: Output directory for packet files.
        state: Current widget state string.

    Returns:
        Path to the written packet file.
    """
    packet = build_codex_packet(project_id, team_state, state)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_project_filename(project_id)
    file_path = out_path / f"{safe_name}-codex-packet.json"
    file_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return file_path


def build_work_packet(
    project_id: str,
    team_state: Any,
    state: str = "idle",
    context_budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a work packet from team state."""
    packet = build_codex_packet(project_id, team_state, state)
    if team_state and hasattr(team_state, "state_file"):
        from roost.team_memory import load_memory_context

        memory_context = load_memory_context(team_state.state_file.parent, project_id)
        packet["team_memory"] = memory_context["team_memory"]
        packet["project_culture"] = memory_context["project_culture"]
    if context_budget is not None:
        packet["context_budget"] = context_budget
    return packet


def export_work_packet(
    project_id: str,
    team_state: Any,
    out_dir: str | Path = "work-packets",
    state: str = "idle",
    context_budget: dict[str, Any] | None = None,
) -> Path:
    """Build and write a work packet JSON file."""
    packet = build_work_packet(project_id, team_state, state, context_budget)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_project_filename(project_id)
    file_path = out_path / f"{safe_name}-work-packet.json"
    file_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return file_path


def _known_model_profile_ids(team_state: Any) -> set[str]:
    if not team_state or not hasattr(team_state, "list_model_profiles"):
        return set()
    return {str(profile.get("id", "")) for profile in team_state.list_model_profiles()}


def _ensure_packet_model_profile(project_id: str, team_state: Any, profile: dict[str, Any]) -> str:
    profile_id = str(profile.get("id", ""))
    if not profile_id:
        return ""
    known_profiles = _known_model_profile_ids(team_state)
    if profile_id in known_profiles or not hasattr(team_state, "set_model_profile"):
        return profile_id
    provider = str(profile.get("provider", ""))
    model = str(profile.get("model", ""))
    if not provider or not model:
        return ""
    team_state.set_model_profile(
        project_id,
        profile_id,
        str(profile.get("backend", "hermes")),
        provider,
        model,
        str(profile.get("cost", "unknown")),
        str(profile.get("tier", "")),
    )
    return profile_id


def _import_model_profile(packet: dict[str, Any], project_id: str, team_state: Any) -> None:
    if not team_state:
        return
    profile = packet.get("model_profile")
    if not isinstance(profile, dict):
        return
    profile_id = _ensure_packet_model_profile(project_id, team_state, profile)
    if not profile_id:
        return
    if hasattr(team_state, "set_active_model_profile"):
        team_state.set_active_model_profile(project_id, profile_id)


def _import_team_model_policy(packet: dict[str, Any], project_id: str, team_state: Any) -> None:
    if not team_state:
        return
    preset = str(packet.get("team_model_preset", ""))
    if preset and preset != "custom" and hasattr(team_state, "apply_team_model_preset"):
        team_state.apply_team_model_preset(preset, project_id=project_id)
        return
    if not hasattr(team_state, "set_role_model_profile"):
        return
    role_model_plan = packet.get("role_model_plan", [])
    if not isinstance(role_model_plan, list):
        return
    for item in role_model_plan:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", ""))
        profile = item.get("profile", {})
        if not role or not isinstance(profile, dict):
            continue
        profile_id = _ensure_packet_model_profile(project_id, team_state, profile)
        if profile_id:
            team_state.set_role_model_profile(role, profile_id, project_id=project_id)


def _import_employees(packet: dict[str, Any], team_state: Any) -> None:
    if not team_state or not hasattr(team_state, "register_employee"):
        return
    employees = packet.get("employees", [])
    if not isinstance(employees, list):
        return
    existing_ids = {
        str(employee.get("id", ""))
        for employee in team_state.get_employees()
        if isinstance(employee, dict) and employee.get("id")
    }
    for employee in employees:
        if not isinstance(employee, dict):
            continue
        employee_id = str(employee.get("id", "")).strip()
        if not employee_id or employee_id in existing_ids:
            continue
        name = str(employee.get("name") or employee_id)
        role = str(employee.get("role") or "worker")
        team_state.register_employee(employee_id, name, role=role)
        existing_ids.add(employee_id)
        status = str(employee.get("status") or "")
        if status and status != "idle" and hasattr(team_state, "set_employee_status"):
            team_state.set_employee_status(employee_id, status)


def _merge_task_payload(queue_item: dict[str, Any], task: dict[str, Any]) -> None:
    queue_item["status"] = task.get("status", queue_item.get("status", "waiting"))
    task_type = task.get("type")
    if task_type:
        queue_item["type"] = task_type
    # Packet uses snake_case enqueued_at; normalize to internal camelCase enqueuedAt
    enqueued_at = task.get("enqueued_at") or task.get("enqueuedAt")
    if enqueued_at:
        queue_item["enqueuedAt"] = enqueued_at
    payload = task.get("payload", {})
    if isinstance(payload, dict):
        queue_item.update(payload)


def import_codex_packet(
    packet_file: str | Path,
    team_state: Any,
) -> dict[str, Any]:
    """Import a work packet JSON file into team state.

    Reads a packet and updates the project's mission and tasks
    in team_state. Does NOT modify widget state; caller must refresh.

    Args:
        packet_file: Path to the packet JSON file.
        team_state: TeamState instance.

    Returns:
        The parsed packet dict.

    Raises:
        FileNotFoundError: If packet_file does not exist.
        ValueError: If packet format is invalid.
    """
    path = Path(packet_file)
    if not path.exists():
        raise FileNotFoundError(f"Work packet not found: {path}")
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Invalid work packet JSON: {e}") from e

    if not isinstance(packet, dict) or (packet.get("work_packet") != "v1" and packet.get("codex_packet") != "v1"):
        raise ValueError("Unsupported work packet format (expected v1)")

    project = packet.get("project", {})
    project_id = project.get("id", "")
    if not project_id:
        raise ValueError("Work packet missing project.id")

    # Ensure project exists
    existing = team_state.get_project(project_id) if team_state else None
    if team_state and existing is None:
        team_state.register_project(
            project_id,
            display_name=project.get("name", project_id),
        )

    # Update mission
    mission = packet.get("mission", "")
    if mission and team_state:
        team_state.set_project_mission(project_id, mission)

    _import_model_profile(packet, project_id, team_state)
    _import_team_model_policy(packet, project_id, team_state)
    _import_employees(packet, team_state)

    # Merge tasks into project queue
    tasks = packet.get("tasks", [])
    if team_state and tasks:
        existing_queue = team_state.get_project_queue(project_id)
        existing_ids = {t.get("id") for t in existing_queue if t.get("id")}
        updated_existing = False
        for task in tasks:
            task_id = task.get("id", "")
            if task_id and task_id in existing_ids:
                # Update existing task status
                for q_item in existing_queue:
                    if q_item.get("id") == task_id:
                        _merge_task_payload(q_item, task)
                        updated_existing = True
                        break
            else:
                # Enqueue new task
                team_state.enqueue_project(
                    project_id,
                    {
                        "id": task_id or None,
                        "type": task.get("type", "unknown"),
                        "status": task.get("status", "waiting"),
                        "enqueuedAt": task.get("enqueued_at", ""),
                        **task.get("payload", {}),
                    },
                )
        if updated_existing and hasattr(team_state, "save"):
            team_state.save()

    return packet


def import_work_packet(
    packet_file: str | Path,
    team_state: Any,
) -> dict[str, Any]:
    """Import a work packet JSON file into team state."""
    return import_codex_packet(packet_file, team_state)
