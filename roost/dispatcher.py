"""Role-based task dispatcher for Pet Studio.

Routes tasks to the right backend based on role:
- Scout (read-only) → script backend (free)
- Coordinator (compress/draft) → hermes backend (mid-cost)
- Lead (implement/deploy) → chosen lead agent (high-cost, configurable)

Hermes is the default lead agent. Other agents (Codex, OpenCode, etc.)
can be registered via BackendRegistry.register().
"""

from __future__ import annotations

import enum
import logging
from typing import Any

from roost.backend import RoostBackend
from roost.backend.hermes import HermesBackend
from roost.backend.script import ScriptBackend

logger = logging.getLogger(__name__)


class TaskRole(enum.Enum):
    """Internal role for token-optimized task routing."""

    SCOUT = "scout"
    COORDINATOR = "coordinator"
    LEAD = "lead"


# Task type keywords mapped to roles
_SCOUT_TYPES = {"scan", "read", "summarize_files", "log_summary", "file_scan"}
_COORDINATOR_TYPES = {"compress", "summarize", "draft_packet", "synthesize"}


def classify_task(task: dict[str, Any]) -> TaskRole:
    """Classify a task into a role based on its type.

    Args:
        task: Task dict with at least a "type" field.

    Returns:
        TaskRole enum value.
    """
    task_type = task.get("type", "").lower()
    if task_type in _SCOUT_TYPES:
        return TaskRole.SCOUT
    if task_type in _COORDINATOR_TYPES:
        return TaskRole.COORDINATOR
    return TaskRole.LEAD


class BackendRegistry:
    """Extensible backend registry — instance-based for test isolation.

    Default backends: script (free), hermes (subprocess).
    New backends (Codex, OpenCode, etc.) can be registered via register().
    """

    def __init__(self) -> None:
        self._backends: dict[str, type[RoostBackend]] = {
            "script": ScriptBackend,
            "hermes": HermesBackend,
        }

    def register(self, name: str, cls: type[RoostBackend]) -> None:
        """Register a new backend (e.g. Codex, OpenCode)."""
        self._backends[name] = cls
        logger.info("Backend registered: %s → %s", name, cls.__name__)

    def get(self, name: str) -> type[RoostBackend]:
        """Get backend class by name."""
        if name not in self._backends:
            raise ValueError(f"Unknown backend: {name!r}. Available: {list(self._backends.keys())}")
        return self._backends[name]

    def reset(self) -> None:
        """Reset to defaults (for test isolation)."""
        self._backends = {
            "script": ScriptBackend,
            "hermes": HermesBackend,
        }

    @property
    def available(self) -> list[str]:
        return list(self._backends.keys())


# Global default instance
default_registry = BackendRegistry()

# Default role → backend mapping
_DEFAULT_ROLE_BACKENDS: dict[TaskRole, str] = {
    TaskRole.SCOUT: "local/fast",
    TaskRole.COORDINATOR: "remote/sota",
    TaskRole.LEAD: "remote/sota",
}

# Task type → security action mapping
_TASK_ACTION_MAP: dict[str, str] = {
    "deploy": "deploy",
    "project.delete": "project.delete",
    "team.reconfigure": "team.reconfigure",
}


def _task_action(task: dict[str, Any]) -> str:
    """Map task type to security action string."""
    task_type = task.get("type", "").lower()
    return _TASK_ACTION_MAP.get(task_type, "state.write")


def _resolve_backend_for_role(
    role: TaskRole,
    team_state: Any,  # TeamState — avoid circular import
) -> str:
    """Resolve which backend to use for a role.

    Priority:
    1. User override in team_state.role_backends
    2. Auto-select based on cost optimization
    """
    # 1. Check user override
    role_target = team_state.get_role_backend(role.value)
    if role_target and role_target != _DEFAULT_ROLE_BACKENDS.get(role):
        # User has set a non-default override
        return team_state.resolve_endpoint_backend(role_target)
    # 2. Auto-select
    auto_alias = team_state.auto_select_endpoint(role.value)
    return team_state.resolve_endpoint_backend(auto_alias)


def dispatch(
    task: dict[str, Any],
    team_state: Any,  # TeamState
    registry: BackendRegistry | None = None,
) -> dict[str, Any]:
    """Dispatch a task to the appropriate backend based on role.

    Flow:
    1. Security check (project-level)
    2. Classify task → role
    3. Resolve backend for role (from team_state or default)
    4. Execute via backend.classify_event()

    Args:
        task: Task dict. Should have "type" and optionally "project_id".
        team_state: TeamState instance.
        registry: Optional BackendRegistry (for testing). Uses default if None.

    Returns:
        Classified event dict.

    Raises:
        SecurityError: If project security blocks the action.
        ValueError: If backend name is unknown.
    """
    if registry is None:
        registry = default_registry

    # 1. Security check
    project_id = task.get("project_id", "")
    if project_id:
        from roost.security import check_security

        action = _task_action(task)
        check_security(project_id, action, team_state)

    # 2. Classify
    role = classify_task(task)

    # 2b. Special case: deliver_packet → skip backend classification
    if task.get("type", "").lower() == "deliver_packet":
        from roost.delivery import deliver_packet

        return deliver_packet(
            project_id=project_id,
            team_state=team_state,
            agent=task.get("agent"),
        )

    # 3. Resolve backend
    backend_name = _resolve_backend_for_role(role, team_state)
    logger.debug("Backend resolved: role=%s → backend=%s", role.value, backend_name)

    # 4. Execute
    backend_cls = registry.get(backend_name)
    backend = backend_cls()
    context = team_state.get_context_history()
    return backend.classify_event(task, context)
