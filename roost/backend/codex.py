"""Codex CLI backend for users who already authenticated Codex locally."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from roost.model_profile import build_model_profile_env
from roost.auth_config import apply_auth_config_env

logger = logging.getLogger(__name__)


class CodexBackend:
    """Run a minimal Codex CLI task using local OAuth or configured env.

    The default command is `codex`; set CODEX_CMD in env or local auth config
    when the executable lives elsewhere.
    """

    name = "codex"

    def __init__(self, codex_cmd: str | None = None, timeout: int = 30) -> None:
        auth_env = apply_auth_config_env(os.environ)
        self.codex_cmd = codex_cmd or auth_env.get("CODEX_CMD", "codex")
        self.timeout = timeout
        self.model_profile: dict[str, Any] | None = None

    def set_model_profile(self, profile: dict[str, Any]) -> None:
        self.model_profile = dict(profile)

    def _env(self) -> dict[str, str]:
        return build_model_profile_env(self.model_profile)

    def _run_codex(self, prompt: str) -> str | None:
        try:
            result = subprocess.run(
                [self.codex_cmd, "exec", prompt],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                text=True,
                timeout=self.timeout,
                env=self._env(),
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.warning("Codex returned non-zero exit code: %s", result.returncode)
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as error:
            logger.warning("Codex subprocess failed: %s", error)
            return None

    def classify_event(
        self,
        event: dict[str, Any],
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prompt = (
            "Classify this event by priority (high/normal/low). Reply with ONE word only.\n"
            f"Event: {json.dumps(event)}"
        )
        output = self._run_codex(prompt)
        priority = self._parse_priority(output) if output else None
        if priority:
            event["classification"] = {"priority": priority, "source": "codex"}
        else:
            event["classification"] = {"priority": "normal", "source": "codex (no response)"}
        return event

    def health_check(self) -> bool:
        try:
            result = subprocess.run(
                [self.codex_cmd, "--version"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                text=True,
                timeout=5,
                env=self._env(),
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    @staticmethod
    def _parse_priority(output: str | None) -> str | None:
        text = (output or "").strip().lower()
        for word in ("high", "normal", "low"):
            if word in text:
                return word
        return None

    def deliver_packet(self, packet: dict[str, Any]) -> dict[str, Any]:
        output = self._run_codex(f"Execute this Pet Studio Work Packet:\n{json.dumps(packet)}")
        return {
            "agent": "codex",
            "status": "delivered" if output else "failed",
            "output": output or "(no output)",
        }

    def __repr__(self) -> str:
        return f"<CodexBackend name={self.name}>"
