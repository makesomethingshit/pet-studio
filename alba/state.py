"""Alba (알바생) — shared state manager for Pet Studio team orchestration.

Manages team_state.json: project queues, employee/lead status, event logs.
Works without any LLM (script mode). LLM backends add smarter event classification.
"""

from __future__ import annotations

import json
import logging
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
            "version": "0.5.0",
            "updatedAt": utc_now(),
            "alba": {
                "status": "idle",
                "backend": "script",
                "model": None,
                "lastActive": None,
                "queue": [],
                "context": {"history": [], "patterns": {}, "projectInsights": {}},
            },
            "projects": {},
            "employees": {"pool": []},
            "leads": {"pool": []},
            "trust": {},
        }

    def save(self) -> None:
        self._data["updatedAt"] = utc_now()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Alba ---

    @property
    def alba_status(self) -> str:
        return self._data.get("alba", {}).get("status", "idle")

    @alba_status.setter
    def alba_status(self, value: str) -> None:
        self._data.setdefault("alba", {})["status"] = value
        self.save()

    @property
    def alba_backend(self) -> str:
        return self._data.get("alba", {}).get("backend", "script")

    def get_alba_queue(self) -> list[dict]:
        return self._data.get("alba", {}).get("queue", [])

    def enqueue_alba(self, event: dict[str, Any]) -> None:
        queue = self._data.setdefault("alba", {}).setdefault("queue", [])
        event["enqueuedAt"] = utc_now()
        queue.append(event)
        self.save()

    def dequeue_alba(self) -> dict[str, Any] | None:
        queue = self._data.setdefault("alba", {}).setdefault("queue", [])
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
        from alba.security import SecurityError, check_security

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
        from alba.security import SecurityError, check_security

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
            self.add_context_history({
                "project_id": project_id,
                "action": event.get("type", "unknown"),
                "priority": event.get("priority", "normal"),
            })

    # --- Context accumulation ---

    def add_context_history(self, entry: dict[str, Any]) -> None:
        history = self._data.setdefault("alba", {}).setdefault("context", {}).setdefault("history", [])  # noqa: E501
        entry["timestamp"] = utc_now()
        history.append(entry)
        if len(history) > 200:
            history.pop(0)
        self.save()

    def get_context_history(self, limit: int = 50) -> list[dict]:
        return self._data.get("alba", {}).get("context", {}).get("history", [])[-limit:]

    def add_project_insight(self, project_id: str, key: str, value: Any) -> None:
        insights = (
            self._data.setdefault("alba", {})
            .setdefault("context", {})
            .setdefault("projectInsights", {})
            .setdefault(project_id, {})
        )
        insights[key] = value
        self.save()
