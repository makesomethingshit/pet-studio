"""Packet delivery - send prepared packets to the chosen lead agent.

Extensible: new agents implement deliver_packet() on their backend class,
or register via BackendRegistry.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from roost.model_profile import build_model_profile_env
from roost.packet import build_work_packet
from roost.auth_config import apply_auth_config_env

logger = logging.getLogger(__name__)


class DeliveryError(Exception):
    """Raised when packet delivery fails."""

    pass


def deliver_packet(
    project_id: str,
    team_state: Any,  # TeamState
    agent: str | None = None,
    role: str = "lead",
) -> dict[str, Any]:
    """Build and deliver a packet to the chosen lead agent.

    Flow:
    1. Resolve agent (default "script" for local packet logging)
    2. Build work packet from team_state
    3. Deliver via agent-specific method

    Args:
        project_id: Project identifier.
        team_state: TeamState instance.
        agent: Override agent name. If None, logs locally through script.
        role: Team role whose model profile should be used for remote delivery.

    Returns:
        Dict with delivery result: {"agent": str, "status": str, "output": str}

    Raises:
        DeliveryError: If delivery fails.
        SecurityError: If project security blocks delivery.
    """
    # 0. Security check - delivery is a "deploy" action
    from roost.security import check_security

    check_security(project_id, "deploy", team_state)

    # 1. Resolve agent
    if agent is None:
        agent = "script"
    else:
        agent = team_state.resolve_endpoint_backend(agent)
    logger.info("Delivering packet: project=%s -> agent=%s", project_id, agent)

    # 2. Build packet
    packet = build_work_packet(project_id, team_state)

    # 3. Deliver
    if agent == "script":
        return _deliver_to_script(packet)
    if agent == "hermes":
        profile = (
            team_state.get_role_model_profile(role)
            if hasattr(team_state, "get_role_model_profile")
            else team_state.get_active_model_profile()
        )
        return _deliver_to_hermes(packet, profile)

    # Extensible: try registered backend with deliver_packet method
    from roost.dispatcher import default_registry

    try:
        backend_cls = default_registry.get(agent)
        backend = backend_cls()
        if hasattr(backend, "set_model_profile"):
            profile = (
                team_state.get_role_model_profile(role)
                if hasattr(team_state, "get_role_model_profile")
                else team_state.get_active_model_profile()
            )
            backend.set_model_profile(profile)
        if hasattr(backend, "deliver_packet"):
            return backend.deliver_packet(packet)
        raise DeliveryError(f"Agent {agent!r} does not support packet delivery")
    except ValueError as e:
        raise DeliveryError(f"Unknown agent: {agent!r}") from e


def _deliver_to_hermes(packet: dict[str, Any], model_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Deliver packet to Hermes via subprocess.

    Writes packet to temp file, then runs:
        hermes -z "Execute this packet: <file_path>"
    """
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
            tmp_path = f.name

        env = build_model_profile_env(model_profile) if model_profile else apply_auth_config_env()
        hermes_cmd = env.get("HERMES_CMD", "hermes")
        result = subprocess.run(
            [hermes_cmd, "-z", f"Execute this packet: {tmp_path}"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            text=True,
            timeout=30,
            env=env,
        )

        return {
            "agent": "hermes",
            "status": "delivered" if result.returncode == 0 else "failed",
            "output": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        raise DeliveryError(f"Hermes delivery failed: {e}") from e
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)


def _deliver_to_script(packet: dict[str, Any]) -> dict[str, Any]:
    """Script backend - no-op delivery (logs only)."""
    logger.info("Script backend: packet delivery is no-op (packet logged)")
    return {
        "agent": "script",
        "status": "logged",
        "output": json.dumps(packet, indent=2, ensure_ascii=False),
    }
