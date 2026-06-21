"""Small mission workflow helpers."""

from __future__ import annotations

import uuid
from typing import Any

from roost.dispatcher import dispatch


def _task_id(role: str) -> str:
    return f"{role}-{uuid.uuid4().hex[:8]}"


def _dispatch_step(team_state: Any, project_id: str, index: int) -> tuple[bool, str]:
    queue = team_state.get_project_queue(project_id)
    if index < 0 or index >= len(queue):
        return False, "Workflow task is missing."
    team_state.update_project_queue_item(project_id, index, {"status": "running"})
    task = dict(queue[index])
    task["project_id"] = project_id
    try:
        result = dispatch(task, team_state)
    except Exception as error:  # noqa: BLE001
        message = str(error) or "Workflow dispatch failed."
        team_state.update_project_queue_item(
            project_id,
            index,
            {"status": "waiting", "dispatchError": message, "dispatchMessage": message},
        )
        return False, message
    classification = result.get("classification", {}) if isinstance(result, dict) else {}
    source = str(classification.get("source") or task.get("assignedRole") or "workflow")
    priority = classification.get("priority", "normal")
    message = f"AI connected: {source} / {priority}"
    team_state.update_project_queue_item(
        project_id,
        index,
        {
            "classification": classification,
            "lastDispatch": result,
            "dispatchSource": source,
            "dispatchMessage": message,
        },
    )
    return True, message


def start_mission_workflow(team_state: Any, project_id: str, mission: str) -> tuple[bool, str]:
    mission = mission.strip()
    if not mission:
        return False, "Enter a mission first."
    workflow_id = f"workflow-{uuid.uuid4().hex[:8]}"
    queue_start = len(team_state.get_project_queue(project_id))
    scout_id = _task_id("scout")
    coordinator_id = _task_id("coordinator")
    lead_id = _task_id("lead")
    team_state.set_project_mission(project_id, mission)
    tasks = [
        {
            "id": scout_id,
            "workflowId": workflow_id,
            "workflowStep": "scout",
            "type": "scan",
            "task": f"Scout: {mission}",
            "status": "waiting",
            "source": "mission",
            "assignedRole": "scout",
            "dispatchMessage": "Waiting for Scout.",
            "dispatchSource": "scout",
        },
        {
            "id": coordinator_id,
            "workflowId": workflow_id,
            "workflowStep": "coordinator",
            "parentTaskId": scout_id,
            "type": "synthesize",
            "task": f"Coordinator: {mission}",
            "status": "waiting",
            "source": "mission",
            "assignedRole": "coordinator",
            "dispatchMessage": "Waiting for Coordinator.",
            "dispatchSource": "coordinator",
        },
        {
            "id": lead_id,
            "workflowId": workflow_id,
            "workflowStep": "lead",
            "parentTaskId": coordinator_id,
            "type": "implement",
            "task": f"Lead: {mission}",
            "status": "waiting",
            "source": "mission",
            "assignedRole": "lead",
            "dispatchMessage": "Ready for Lead. Start manually.",
            "dispatchSource": "lead",
        },
    ]
    for task in tasks:
        team_state.enqueue_project(project_id, task)
    ok, message = _dispatch_step(team_state, project_id, queue_start)
    if not ok:
        return False, message
    scout_task = team_state.get_project_queue(project_id)[queue_start]
    team_state.update_project_queue_item(
        project_id,
        queue_start + 1,
        {"inputFrom": scout_task.get("dispatchMessage", ""), "parentTaskId": scout_task.get("id", scout_id)},
    )
    ok, message = _dispatch_step(team_state, project_id, queue_start + 1)
    if not ok:
        return False, message
    return True, "Workflow ready: Scout -> Coordinator -> Lead"
