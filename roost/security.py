"""Security level enforcement for Pet Studio team orchestration.

L0 ALLOW → all actions allowed
L1 WARN  → dangerous actions logged but allowed (default)
L2 ASK   → dangerous actions require user approval
L3 DENY  → dangerous actions fully blocked
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security check blocks an action."""

    def __init__(self, action: str, level: int, reason: str = "") -> None:
        self.action = action
        self.level = level
        self.reason = reason or f"L{level} blocks {action}"
        super().__init__(self.reason)


class SecurityLevel:
    """Security level constants."""

    ALLOW = 0
    WARN = 1
    ASK = 2
    DENY = 3


# Action risk level: 0=safe, 1=moderate, 3=critical
ACTION_RISK: dict[str, int] = {
    "state.read": 0,
    "state.write": 0,
    "preset.export": 0,
    "preset.import": 1,
    "layout.reset": 1,
    "project.delete": 3,
    "team.reconfigure": 3,
    "deploy": 3,
}


def check_security(
    project_id: str,
    action: str,
    team_state: Any,  # TeamState — avoid circular import
) -> dict[str, Any]:
    """Check whether an action is allowed under the project's security level.

    Returns:
        {"allowed": bool, "reason": str, "level": int, "risk": int}

    Raises:
        SecurityError: If the action is blocked (L2 ASK or L3 DENY).
    """
    project = team_state.get_project(project_id)
    if project is None:
        return {
            "allowed": False,
            "reason": f"Project not found: {project_id}",
            "level": -1,
            "risk": -1,
        }

    level: int = project.get("securityLevel", SecurityLevel.WARN)
    risk: int = ACTION_RISK.get(action, 1)

    # L0: allow everything
    if level == SecurityLevel.ALLOW:
        return {"allowed": True, "reason": "L0 allow-all", "level": level, "risk": risk}

    # Risk 0: always safe
    if risk == 0:
        return {
            "allowed": True,
            "reason": "Low-risk action",
            "level": level,
            "risk": risk,
        }

    # L3: deny all risky actions
    if level == SecurityLevel.DENY:
        raise SecurityError(
            action=action,
            level=level,
            reason=f"L3 DENY: {action} blocked for project {project_id}",
        )

    # L2: risky actions (risk >= 2) require approval
    if level == SecurityLevel.ASK and risk >= 2:
        # Auto-add to approval queue
        try:
            team_state.add_approval_request(project_id, action, requester="security")
        except Exception:  # noqa: BLE001
            logger.warning("Failed to enqueue approval for %s/%s", project_id, action)
        raise SecurityError(
            action=action,
            level=level,
            reason=f"L2 ASK: {action} requires approval for project {project_id}",
        )

    # L1 (default): warn but allow
    logger.warning("L1 WARN: action=%s risk=%d project=%s", action, risk, project_id)
    return {
        "allowed": True,
        "reason": f"L1 WARN: {action} allowed with warning",
        "level": level,
        "risk": risk,
    }
