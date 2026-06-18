"""Roost — shared state manager for Pet Studio team orchestration.

Manages team_state.json: project queues, employee/lead status, event logs.
Works without any LLM (script mode). LLM backends add smarter event classification.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path("team_state.json")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class TeamState:
    """Read/write team_state.json with validation."""

    def __init__(self, state_file: str | Path | None = None):
        self.state_file = Path(state_file) if state_file else DEFAULT_STATE_FILE
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self.state_file.exists():
            try:
                self._data = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load team state: %s", e)
                self._data = self._default_state()
        else:
            self._data = self._default_state()

    def _default_state(self) -> dict[str, Any]:
        return {
            "version": "0.6.0",
            "updatedAt": utc_now(),
            "roost": {
                "status": "idle",
                "backend": "script",
                "model": None,
                "lastActive": None,
                "queue": [],
                "context": {"history": [], "patterns": {}, "projectInsights": {}},
            },
            "projects": {},
            "employees": {
                "pool": [
                    {"id": "emp-1", "name": "Codex", "status": "idle", "role": "worker"},
                    {"id": "emp-2", "name": "Claude", "status": "idle", "role": "worker"},
                ]
            },
            "leads": {"pool": []},
            "trust": {},
            "approvals": [],
        }

    def save(self) -> None:
        self._data["updatedAt"] = utc_now()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Roost ---

    @property
    def roost_status(self) -> str:
        return self._data.get("roost", {}).get("status", "idle")

    @roost_status.setter
    def roost_status(self, value: str) -> None:
        self._data.setdefault("roost", {})["status"] = value
        self.save()

    @property
    def roost_backend(self) -> str:
        return self._data.get("roost", {}).get("backend", "script")

    def get_roost_queue(self) -> list[dict]:
        return self._data.get("roost", {}).get("queue", [])

    def enqueue_roost(self, event: dict[str, Any]) -> None:
        queue = self._data.setdefault("roost", {}).setdefault("queue", [])
        event["enqueuedAt"] = utc_now()
        queue.append(event)
        self.save()

    def dequeue_roost(self) -> dict[str, Any] | None:
        queue = self._data.setdefault("roost", {}).setdefault("queue", [])
        if queue:
            item = queue.pop(0)
            self.save()
            return item
        return None

    # --- Projects ---

    def register_project(
        self,
        project_id: str,
        display_name: str | None = None,
        security_level: int = 1,
    ) -> None:
        projects = self._data.setdefault("projects", {})
        projects[project_id] = {
            "displayName": display_name or project_id,
            "status": "idle",
            "assignedEmployees": [],
            "lead": None,
            "securityLevel": security_level,
            "queue": [],
            "lastEvent": None,
            "eventLog": [],
        }
        self.save()

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        return self._data.get("projects", {}).get(project_id)

    def set_project_status(self, project_id: str, status: str) -> None:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        project = self._data.setdefault("projects", {}).get(project_id)
        if project:
            project["status"] = status
            self.save()

    def get_project_queue(self, project_id: str) -> list[dict]:
        project = self.get_project(project_id)
        if project:
            return project.get("queue", [])
        return []

    def enqueue_project(self, project_id: str, task: dict[str, Any]) -> None:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        project = self._data.setdefault("projects", {}).get(project_id)
        if project:
            queue = project.setdefault("queue", [])
            task["enqueuedAt"] = utc_now()
            queue.append(task)
            self.save()

    def log_event(self, project_id: str, event: dict[str, Any]) -> None:
        project = self._data.setdefault("projects", {}).get(project_id)
        if project:
            event["timestamp"] = utc_now()
            project["lastEvent"] = event
            log = project.setdefault("eventLog", [])
            log.append(event)
            if len(log) > 100:
                log.pop(0)
            self.save()
            # Context accumulation
            self.add_context_history(
                {
                    "project_id": project_id,
                    "action": event.get("type", "unknown"),
                    "priority": event.get("priority", "normal"),
                }
            )

    # --- Context accumulation ---

    def add_context_history(self, entry: dict[str, Any]) -> None:
        history = self._data.setdefault("roost", {}).setdefault("context", {}).setdefault("history", [])  # noqa: E501
        entry["timestamp"] = utc_now()
        history.append(entry)
        if len(history) > 200:
            history.pop(0)
        self.save()

    def get_context_history(self, limit: int = 50) -> list[dict]:
        return self._data.get("roost", {}).get("context", {}).get("history", [])[-limit:]

    def add_project_insight(self, project_id: str, key: str, value: Any) -> None:
        insights = (
            self._data.setdefault("roost", {})
            .setdefault("context", {})
            .setdefault("projectInsights", {})
            .setdefault(project_id, {})
        )
        insights[key] = value
        self.save()

    # --- Employees ---

    def get_employees(self) -> list[dict]:
        return self._data.get("employees", {}).get("pool", [])

    def set_employee_status(self, employee_id: str, status: str) -> bool:
        pool = self._data.setdefault("employees", {}).setdefault("pool", [])
        for emp in pool:
            if emp.get("id") == employee_id:
                emp["status"] = status
                self.save()
                return True
        return False

    # --- Approvals ---

    def add_approval_request(
        self,
        project_id: str,
        action: str,
        requester: str = "system",
    ) -> str:
        """Add an approval request. Returns the approval ID."""
        approvals = self._data.setdefault("approvals", [])
        # Generate unique ID (check for collisions)
        existing_ids = {a.get("id") for a in approvals}
        for _ in range(10):
            approval_id = str(uuid.uuid4())
            if approval_id not in existing_ids:
                break
        else:
            raise RuntimeError("Failed to generate unique approval ID after 10 attempts")
        approvals.append(
            {
                "id": approval_id,
                "projectId": project_id,
                "action": action,
                "requester": requester,
                "timestamp": utc_now(),
                "status": "pending",
            }
        )
        # Trim to last 50
        if len(approvals) > 50:
            self._data["approvals"] = approvals[-50:]
        self.save()
        return approval_id

    def resolve_approval(self, approval_id: str, approved: bool) -> bool:
        """Resolve an approval request. Returns True if found and resolved."""
        approvals = self._data.get("approvals", [])
        for a in approvals:
            if a.get("id") == approval_id:
                a["status"] = "approved" if approved else "rejected"
                a["resolvedAt"] = utc_now()
                self.save()
                return True
        return False

    def get_pending_approvals(self) -> list[dict]:
        return [a for a in self._data.get("approvals", []) if a.get("status") == "pending"]
