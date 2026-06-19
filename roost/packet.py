"""Codex packet export for Pet Studio.

Converts team_state.json project data into Codex CLI-compatible packet format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_codex_packet(
    project_id: str,
    team_state: Any,
    state: str = "idle",
) -> dict[str, Any]:
    """Build a codex packet from team state.

    Args:
        project_id: Project identifier.
        team_state: TeamState instance.
        state: Current widget state string.

    Returns:
        Dict in codex packet v1 format.
    """
    project = team_state.get_project(project_id) if team_state else None
    mission = team_state.get_project_mission(project_id) if team_state else ""
    queue: list[dict] = []
    if team_state:
        try:
            queue = team_state.get_project_queue(project_id)
        except Exception:
            queue = []

    tasks = []
    for item in queue:
        tasks.append(
            {
                "id": item.get("id", ""),
                "type": item.get("type", item.get("task", "unknown")),
                "status": item.get("status", "waiting"),
                "enqueued_at": item.get("enqueuedAt", ""),
                "payload": {k: v for k, v in item.items() if k not in ("id", "type", "task", "status", "enqueuedAt")},
            }
        )

    return {
        "codex_packet": "v1",
        "project": {
            "id": project_id,
            "name": (project.get("displayName", project_id) if project else project_id),
            "state": state,
        },
        "mission": mission,
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
    """Build and write a codex packet JSON file.

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
    file_path = out_path / f"{project_id}-codex-packet.json"
    file_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return file_path
