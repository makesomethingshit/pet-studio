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

    _DEFAULT_ENDPOINTS: dict[str, dict[str, str]] = {
        "local/fast": {"backend": "script", "cost": "free"},
        "remote/sota": {"backend": "hermes", "cost": "high"},
    }
    _DEFAULT_ROLE_BACKENDS: dict[str, str] = {
        "scout": "local/fast",
        "coordinator": "remote/sota",
        "lead": "remote/sota",
    }
    _DEFAULT_SKILLS: dict[str, dict[str, Any]] = {
        "file-scan": {"enabled": True, "endpoint": "local/fast"},
        "log-summary": {"enabled": True, "endpoint": "local/fast"},
        "draft-packet": {"enabled": True, "endpoint": "local/fast"},
        "deploy": {"enabled": False, "endpoint": "remote/sota"},
        "team-reconfigure": {"enabled": False, "endpoint": "remote/sota"},
    }

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
            "employees": {"pool": []},
            "leads": {"pool": []},
            "trust": {},
            "approvals": [],
            "endpoints": self._copy_default_map(self._DEFAULT_ENDPOINTS),
            "role_backends": dict(self._DEFAULT_ROLE_BACKENDS),
            "skills": self._copy_default_map(self._DEFAULT_SKILLS),
        }

    def save(self) -> None:
        self._data["updatedAt"] = utc_now()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _copy_default_map(defaults: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in defaults.items()}

    def _check_reconfigure(self, project_id: str | None) -> None:
        if not project_id:
            return
        from roost.security import check_security

        check_security(project_id, "team.reconfigure", self)

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
        mission: str = "",
    ) -> None:
        projects = self._data.setdefault("projects", {})
        projects[project_id] = {
            "displayName": display_name or project_id,
            "status": "idle",
            "assignedEmployees": [],
            "lead": None,
            "securityLevel": security_level,
            "queue": [],
            "mission": mission,
            "tasks": [],
            "lastEvent": None,
            "eventLog": [],
        }
        self.save()

    def list_projects(self) -> list[dict[str, Any]]:
        """Return list of registered projects with id, displayName, status, mission."""
        projects = self._data.get("projects", {})
        return [
            {
                "id": pid,
                "displayName": p.get("displayName", pid),
                "status": p.get("status", "idle"),
                "mission": p.get("mission", ""),
            }
            for pid, p in projects.items()
        ]

    def set_project_mission(self, project_id: str, mission: str) -> bool:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        project = self._data.setdefault("projects", {}).get(project_id)
        if project:
            project["mission"] = mission
            self.save()
            return True
        return False

    def get_project_mission(self, project_id: str) -> str:
        project = self.get_project(project_id)
        if project:
            return project.get("mission", "")
        return ""

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

    def register_employee(
        self,
        employee_id: str,
        name: str,
        role: str = "worker",
    ) -> bool:
        """Register a new employee. Returns False if ID already exists."""
        pool = self._data.setdefault("employees", {}).setdefault("pool", [])
        if any(e.get("id") == employee_id for e in pool):
            return False
        pool.append({"id": employee_id, "name": name, "status": "idle", "role": role})
        self.save()
        return True

    def set_employee_status(self, employee_id: str, status: str) -> bool:
        pool = self._data.setdefault("employees", {}).setdefault("pool", [])
        for emp in pool:
            if emp.get("id") == employee_id:
                emp["status"] = status
                self.save()
                return True
        return False

    def get_employees_by_role(self, role: str) -> list[dict]:
        """Filter employees by role (scout, coordinator, lead)."""
        pool = self._data.get("employees", {}).get("pool", [])
        return [e for e in pool if e.get("role") == role]

    # --- Endpoints ---

    def _ensure_endpoints(self) -> dict[str, dict[str, Any]]:
        return self._data.setdefault("endpoints", self._copy_default_map(self._DEFAULT_ENDPOINTS))

    def list_endpoints(self) -> list[dict[str, Any]]:
        endpoints = self._ensure_endpoints()
        return [
            {"alias": alias, "backend": info.get("backend", ""), "cost": info.get("cost", "")}
            for alias, info in endpoints.items()
        ]

    def set_endpoint(self, project_id: str | None, alias: str, backend: str, cost: str) -> None:
        self._check_reconfigure(project_id)
        self._ensure_endpoints()[alias] = {"backend": backend, "cost": cost}
        self.save()

    def remove_endpoint(self, project_id: str | None, alias: str) -> bool:
        self._check_reconfigure(project_id)
        endpoints = self._ensure_endpoints()
        if alias not in endpoints:
            return False
        del endpoints[alias]
        self.save()
        return True

    def resolve_endpoint_backend(self, alias_or_backend: str) -> str:
        endpoints = self._ensure_endpoints()
        if alias_or_backend in endpoints:
            return endpoints[alias_or_backend].get("backend", alias_or_backend)
        return alias_or_backend

    # --- Role Backends (chosen lead agent) ---

    def get_role_backend(self, role: str) -> str:
        """Get the backend assigned to a role.

        Args:
            role: One of "scout", "coordinator", "lead".

        Returns:
            Endpoint alias or backend name string.
        """
        role_backends = self._data.setdefault("role_backends", dict(self._DEFAULT_ROLE_BACKENDS))
        return role_backends.get(role, self._DEFAULT_ROLE_BACKENDS.get(role, "remote/sota"))

    def set_role_backend(self, role: str, backend: str, project_id: str | None = None) -> None:
        """Set the backend for a role (called by Phase 2 UI).

        Args:
            role: One of "scout", "coordinator", "lead".
            backend: Endpoint alias or backend name.
            project_id: Optional project id for L0-L3 security checks.
        """
        self._check_reconfigure(project_id)
        role_backends = self._data.setdefault("role_backends", dict(self._DEFAULT_ROLE_BACKENDS))
        role_backends[role] = backend
        self.save()

    # --- Skills ---

    def _ensure_skills(self) -> dict[str, Any]:
        """Ensure skills section exists with defaults."""
        return self._data.setdefault("skills", self._copy_default_map(self._DEFAULT_SKILLS))

    def list_skills(self) -> list[dict[str, Any]]:
        """Return skills list with id, enabled, endpoint."""
        skills = self._ensure_skills()
        return [
            {"id": sid, "enabled": s.get("enabled", False), "endpoint": s.get("endpoint", "")}
            for sid, s in skills.items()
        ]

    def set_skill_enabled(self, skill_id: str, enabled: bool, project_id: str | None = None) -> None:
        """Toggle skill on/off."""
        self._check_reconfigure(project_id)
        skills = self._ensure_skills()
        if skill_id in skills:
            skills[skill_id]["enabled"] = enabled
            self.save()

    def get_skill_endpoint(self, skill_id: str) -> str:
        """Get the endpoint assigned to a skill."""
        skills = self._ensure_skills()
        if skill_id in skills:
            return skills[skill_id].get("endpoint", "")
        return ""

    def set_skill_endpoint(self, skill_id: str, endpoint: str, project_id: str | None = None) -> None:
        """Assign endpoint to skill."""
        self._check_reconfigure(project_id)
        skills = self._ensure_skills()
        if skill_id in skills:
            skills[skill_id]["endpoint"] = endpoint
            self.save()

    # --- Approvals ---

    def add_approval_request(
        self,
        project_id: str,
        action: str,
        requester: str = "system",
    ) -> str:
        """Add an approval request. Returns the approval ID."""
        approval_id = str(uuid.uuid4())
        approvals = self._data.setdefault("approvals", [])
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
