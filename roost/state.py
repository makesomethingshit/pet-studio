"""Roost - shared state manager for Pet Studio team orchestration.

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
TEAM_STATE_VERSION = "0.8.0-dev"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class TeamState:
    """Read/write team_state.json with validation."""

    _DEFAULT_ENDPOINTS: dict[str, dict[str, str]] = {
        "local/fast": {"backend": "script", "cost": "free"},
        "remote/sota": {"backend": "hermes", "cost": "high"},
        "fusion/local": {"backend": "gateway", "cost": "low"},
    }
    _DEFAULT_MODEL_PROFILES: dict[str, dict[str, str]] = {
        "codex/default": {
            "backend": "codex",
            "provider": "codex",
            "model": "default",
            "cost": "high",
            "tier": "closed",
        },
        "closed/claude": {
            "backend": "hermes",
            "provider": "openrouter",
            "model": "claude",
            "cost": "high",
            "tier": "closed",
        },
        "openrouter/fast": {
            "backend": "hermes",
            "provider": "openrouter",
            "model": "fast",
            "cost": "low",
            "tier": "value",
        },
        "openrouter/sota": {
            "backend": "hermes",
            "provider": "openrouter",
            "model": "sota",
            "cost": "high",
            "tier": "open-sota",
        },
        "local/default": {
            "backend": "script",
            "provider": "local",
            "model": "local",
            "cost": "free",
            "tier": "local",
        },
        "openrouter/cheap": {
            "backend": "hermes",
            "provider": "openrouter",
            "model": "cheap",
            "cost": "free",
            "tier": "free",
        },
        "fusion/local": {
            "backend": "gateway",
            "provider": "openrouter",
            "model": "fusion",
            "cost": "low",
            "tier": "value",
        },
    }
    _DEFAULT_ROLE_BACKENDS: dict[str, str] = {
        "scout": "local/fast",
        "coordinator": "remote/sota",
        "lead": "remote/sota",
    }
    _DEFAULT_ROLE_MODEL_PROFILES: dict[str, str] = {
        "scout": "local/default",
        "coordinator": "openrouter/fast",
    }
    _TEAM_MODEL_PRESETS: dict[str, dict[str, str | None]] = {
        "save-credits": {
            "scout": "local/default",
            "coordinator": "openrouter/fast",
            "lead": None,
        },
        "all-local": {
            "scout": "local/default",
            "coordinator": "local/default",
            "lead": "local/default",
        },
        "all-value": {
            "scout": "openrouter/fast",
            "coordinator": "openrouter/fast",
            "lead": "openrouter/fast",
        },
        "lead-sota": {
            "scout": "local/default",
            "coordinator": "openrouter/fast",
            "lead": "openrouter/sota",
        },
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
            "version": TEAM_STATE_VERSION,
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
            "model_profiles": self._copy_default_map(self._DEFAULT_MODEL_PROFILES),
            "active_model_profile": "openrouter/sota",
            "role_model_profiles": dict(self._DEFAULT_ROLE_MODEL_PROFILES),
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

    def remove_roost_queue_item(self, index: int) -> dict[str, Any] | None:
        queue = self._data.setdefault("roost", {}).setdefault("queue", [])
        if index < 0 or index >= len(queue):
            return None
        item = queue.pop(index)
        self.save()
        return item

    def route_roost_queue_item_to_project(
        self,
        index: int,
        project_id: str,
        status: str = "waiting",
    ) -> dict[str, Any] | None:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        projects = self._data.setdefault("projects", {})
        project = projects.get(project_id)
        if not project:
            return None
        roost_queue = self._data.setdefault("roost", {}).setdefault("queue", [])
        if index < 0 or index >= len(roost_queue):
            return None

        item = dict(roost_queue.pop(index))
        task_type = item.get("type", item.get("task", "unknown"))
        item.setdefault("type", task_type)
        item.setdefault("task", task_type)
        item.setdefault("source", "roost")
        item["status"] = status
        item["routedAt"] = utc_now()
        project.setdefault("queue", []).append(item)
        self.save()
        return item

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

    def update_project_queue_item(
        self,
        project_id: str,
        index: int,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        project = self._data.setdefault("projects", {}).get(project_id)
        if not project:
            return None
        queue = project.setdefault("queue", [])
        if index < 0 or index >= len(queue):
            return None
        item = queue[index]
        for key, value in updates.items():
            if value is None:
                item.pop(key, None)
            else:
                item[key] = value
        item["updatedAt"] = utc_now()
        self.save()
        return item

    def clear_project_queue(self, project_id: str) -> int:
        from roost.security import SecurityError, check_security

        try:
            check_security(project_id, "state.write", self)
        except SecurityError:
            raise
        project = self._data.setdefault("projects", {}).get(project_id)
        if not project:
            return 0
        queue = project.setdefault("queue", [])
        count = len(queue)
        project["queue"] = []
        self.save()
        return count

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
            candidate = event.get("memoryCandidate")
            if isinstance(candidate, dict):
                try:
                    from roost.team_memory import add_memory_candidate

                    add_memory_candidate(
                        self.state_file.parent,
                        str(candidate.get("summary", "")),
                        scope=str(candidate.get("scope", "project")),
                        project_id=str(candidate.get("projectId") or project_id),
                        kind=str(candidate.get("kind", "lesson")),
                        evidence=[str(item) for item in candidate.get("evidence", [])],
                        source="event",
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to record memory candidate: %s", e)

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
        endpoints = self._data.setdefault("endpoints", self._copy_default_map(self._DEFAULT_ENDPOINTS))
        for alias, info in self._DEFAULT_ENDPOINTS.items():
            endpoints.setdefault(alias, dict(info))
        return endpoints

    def _ensure_model_profiles(self) -> dict[str, dict[str, Any]]:
        profiles = self._data.setdefault("model_profiles", self._copy_default_map(self._DEFAULT_MODEL_PROFILES))
        for profile_id, info in self._DEFAULT_MODEL_PROFILES.items():
            profiles.setdefault(profile_id, dict(info))
        return profiles

    def list_model_profiles(self) -> list[dict[str, Any]]:
        from roost.model_profile import model_profile_sort_key, model_profile_tier

        profiles = self._ensure_model_profiles()
        results = []
        for profile_id, info in profiles.items():
            profile = {
                "id": profile_id,
                "backend": info.get("backend", ""),
                "provider": info.get("provider", ""),
                "model": info.get("model", ""),
                "cost": info.get("cost", ""),
                "tier": info.get("tier") or model_profile_tier({"id": profile_id, **info}),
            }
            results.append(profile)
        return sorted(results, key=model_profile_sort_key)

    def get_active_model_profile_id(self) -> str:
        profile_id = self._data.get("active_model_profile", "openrouter/sota")
        profiles = self._ensure_model_profiles()
        return profile_id if profile_id in profiles else "openrouter/sota"

    def get_active_model_profile(self) -> dict[str, Any]:
        from roost.model_profile import model_profile_tier

        profile_id = self.get_active_model_profile_id()
        profile = dict(self._ensure_model_profiles().get(profile_id, {}))
        profile["id"] = profile_id
        profile["tier"] = profile.get("tier") or model_profile_tier(profile)
        return profile

    def _ensure_role_model_profiles(self) -> dict[str, str]:
        role_profiles = self._data.setdefault("role_model_profiles", dict(self._DEFAULT_ROLE_MODEL_PROFILES))
        for role, profile_id in self._DEFAULT_ROLE_MODEL_PROFILES.items():
            role_profiles.setdefault(role, profile_id)
        return role_profiles

    def get_role_model_profile_id(self, role: str) -> str:
        """Return the model profile assigned to a team role.

        Lead follows the active profile unless it is explicitly overridden, so
        the user can switch the main expensive model without pushing Scout or
        Coordinator onto that route.
        """
        role = role.strip().lower()
        profiles = self._ensure_model_profiles()
        profile_id = self._ensure_role_model_profiles().get(role)
        if role == "lead" and not profile_id:
            return self.get_active_model_profile_id()
        if profile_id in profiles:
            return str(profile_id)
        fallback = self._DEFAULT_ROLE_MODEL_PROFILES.get(role)
        if fallback in profiles:
            return str(fallback)
        return self.get_active_model_profile_id()

    def get_role_model_profile(self, role: str) -> dict[str, Any]:
        from roost.model_profile import model_profile_tier

        profile_id = self.get_role_model_profile_id(role)
        profile = dict(self._ensure_model_profiles().get(profile_id, {}))
        profile["id"] = profile_id
        profile["tier"] = profile.get("tier") or model_profile_tier(profile)
        return profile

    def set_role_model_profile(self, role: str, profile_id: str, project_id: str | None = None) -> None:
        self._check_reconfigure(project_id)
        role = role.strip().lower()
        if role not in {"scout", "coordinator", "lead"}:
            raise ValueError(f"Unknown role: {role!r}")
        if profile_id not in self._ensure_model_profiles():
            raise ValueError(f"Unknown model profile: {profile_id!r}")
        self._ensure_role_model_profiles()[role] = profile_id
        self.save()

    def clear_role_model_profile(self, role: str, project_id: str | None = None) -> bool:
        self._check_reconfigure(project_id)
        role = role.strip().lower()
        if role not in {"scout", "coordinator", "lead"}:
            raise ValueError(f"Unknown role: {role!r}")
        role_profiles = self._ensure_role_model_profiles()
        if role not in role_profiles:
            return False
        del role_profiles[role]
        self.save()
        return True

    def list_team_model_presets(self) -> list[dict[str, Any]]:
        return [
            {"id": preset_id, "roles": dict(roles)}
            for preset_id, roles in sorted(self._TEAM_MODEL_PRESETS.items())
        ]

    def get_team_model_preset_id(self) -> str:
        role_profiles = self._ensure_role_model_profiles()
        for preset_id, roles in self._TEAM_MODEL_PRESETS.items():
            explicit_roles_match = all(
                role_profiles.get(role) == profile_id
                for role, profile_id in roles.items()
                if profile_id is not None
            )
            follow_active_roles_match = all(
                role not in role_profiles
                for role, profile_id in roles.items()
                if profile_id is None
            )
            if explicit_roles_match and follow_active_roles_match:
                return preset_id
        return "custom"

    def apply_team_model_preset(self, preset_id: str, project_id: str | None = None) -> None:
        self._check_reconfigure(project_id)
        preset_id = preset_id.strip().lower()
        aliases = {
            "credits": "save-credits",
            "cheap": "save-credits",
            "local": "all-local",
            "value": "all-value",
            "sota": "lead-sota",
        }
        preset_id = aliases.get(preset_id, preset_id)
        if preset_id not in self._TEAM_MODEL_PRESETS:
            raise ValueError(f"Unknown team model preset: {preset_id!r}")

        profiles = self._ensure_model_profiles()
        role_profiles = self._ensure_role_model_profiles()
        for role, profile_id in self._TEAM_MODEL_PRESETS[preset_id].items():
            if profile_id is None:
                role_profiles.pop(role, None)
                continue
            if profile_id not in profiles:
                raise ValueError(f"Unknown model profile: {profile_id!r}")
            role_profiles[role] = profile_id
        self.save()

    def resolve_role_backend(self, role: str) -> str:
        role = role.strip().lower()
        role_target = self.get_role_backend(role)
        if role_target and role_target != self._DEFAULT_ROLE_BACKENDS.get(role):
            return self.resolve_endpoint_backend(role_target)
        profile_backend = self.get_role_model_profile(role).get("backend")
        if profile_backend:
            return str(profile_backend)
        return self.resolve_endpoint_backend(self.auto_select_endpoint(role))

    def list_role_model_plan(self) -> list[dict[str, Any]]:
        """Return the credit-aware model plan for Scout, Coordinator, Lead."""
        plan = []
        for role in ("scout", "coordinator", "lead"):
            role_target = self.get_role_backend(role)
            profile = self.get_role_model_profile(role)
            endpoint = (
                role_target
                if role_target and role_target != self._DEFAULT_ROLE_BACKENDS.get(role)
                else profile["id"]
            )
            plan.append(
                {
                    "role": role,
                    "profile": profile,
                    "endpoint": endpoint,
                    "backend": self.resolve_role_backend(role),
                }
            )
        return plan

    def estimate_team_model_savings(self) -> dict[str, Any]:
        """Estimate relative credit savings versus routing all roles to Lead."""
        from roost.model_profile import estimate_role_model_plan_savings

        return estimate_role_model_plan_savings(
            self.list_role_model_plan(),
            self.get_role_model_profile("lead"),
        )

    def set_active_model_profile(self, project_id: str | None, profile_id: str) -> None:
        self._check_reconfigure(project_id)
        if profile_id not in self._ensure_model_profiles():
            raise ValueError(f"Unknown model profile: {profile_id!r}")
        self._data["active_model_profile"] = profile_id
        self.save()

    def set_model_profile(
        self,
        project_id: str | None,
        profile_id: str,
        backend: str,
        provider: str,
        model: str,
        cost: str,
        tier: str | None = None,
    ) -> None:
        from roost.model_profile import model_profile_tier

        self._check_reconfigure(project_id)
        profile_id = profile_id.strip()
        provider = provider.strip()
        model = model.strip()
        if not profile_id:
            raise ValueError("Model profile id is required")
        if not provider:
            raise ValueError("Model provider is required")
        if not model:
            raise ValueError("Model name is required")
        self._ensure_model_profiles()[profile_id] = {
            "backend": backend.strip() or "hermes",
            "provider": provider,
            "model": model,
            "cost": cost.strip() or "high",
            "tier": tier or model_profile_tier(
                {"id": profile_id, "provider": provider, "model": model, "cost": cost}
            ),
        }
        self.save()

    def remove_model_profile(self, project_id: str | None, profile_id: str) -> bool:
        self._check_reconfigure(project_id)
        profiles = self._ensure_model_profiles()
        if profile_id not in profiles:
            return False
        if profile_id == self.get_active_model_profile_id():
            raise ValueError("Cannot remove the active model profile")
        del profiles[profile_id]
        self.save()
        return True

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

    def auto_select_endpoint(self, role: str) -> str:
        """Automatically select the best endpoint for a role.

        Cost-optimized selection:
        - Scout -> cheapest available (free > low > high)
        - Coordinator -> mid-cost (low > free > high)
        - Lead -> user's chosen lead agent (default: remote/sota)

        Returns:
            Endpoint alias string.
        """
        endpoints = self._ensure_endpoints()
        cost_order = {"free": 0, "low": 1, "high": 2}

        def _sort_key(item):
            alias, info = item
            cost = info.get("cost", "high")
            return cost_order.get(cost, 2)

        sorted_eps = sorted(endpoints.items(), key=_sort_key)

        if role == "scout":
            # Cheapest
            return sorted_eps[0][0] if sorted_eps else "local/fast"
        if role == "coordinator":
            # Mid-cost: prefer "low", otherwise keep the configured coordinator endpoint.
            for alias, info in sorted_eps:
                if info.get("cost") == "low":
                    return alias
            return self.get_role_backend(role)
        # Lead: user's choice (stored in role_backends)
        return self.get_role_backend(role)

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
