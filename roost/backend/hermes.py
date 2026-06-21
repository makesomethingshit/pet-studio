"""Hermes Agent backend - subprocess-based event classification."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

from roost.model_profile import build_model_profile_env
from roost.auth_config import apply_auth_config_env

logger = logging.getLogger(__name__)


class HermesBackend:
    """Hermes Agent backend - subprocess-based event classification.

    Uses `hermes -z` for one-shot classification via subprocess.
    Falls back to script rules if Hermes is not available.
    """

    name = "hermes"

    def __init__(self, hermes_cmd: str | None = None, timeout: int = 10):
        auth_env = apply_auth_config_env(os.environ)
        self.hermes_cmd = hermes_cmd or auth_env.get("HERMES_CMD", "hermes")
        self.timeout = timeout
        self.model_profile: dict[str, Any] | None = None

    def set_model_profile(self, profile: dict[str, Any]) -> None:
        self.model_profile = dict(profile)

    def _env(self) -> dict[str, str]:
        return build_model_profile_env(self.model_profile)

    def _run_hermes(self, prompt: str) -> str | None:
        try:
            result = subprocess.run(
                [self.hermes_cmd, "-z", prompt],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                text=True,
                timeout=self.timeout,
                env=self._env(),
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.warning("Hermes returned non-zero exit code: %s", result.returncode)
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.warning("Hermes subprocess failed: %s", e)
            return None

    def classify_event(
        self,
        event: dict[str, Any],
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prompt = (
            f"Classify this event by priority (high/normal/low). Reply with ONE word only.\nEvent: {json.dumps(event)}"
        )
        output = self._run_hermes(prompt)
        priority = self._parse_priority(output) if output else None
        if priority:
            event["classification"] = {"priority": priority, "source": "hermes"}
        else:
            event["classification"] = {"priority": "normal", "source": "hermes (no response)"}
        return event

    def health_check(self) -> bool:
        try:
            result = subprocess.run(
                [self.hermes_cmd, "--version"],
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
    def _parse_priority(output: str) -> str | None:
        text = output.strip().lower()
        for word in ("high", "normal", "low"):
            if word in text:
                return word
        return None

    def deliver_packet(self, packet: dict[str, Any]) -> dict[str, Any]:
        """Deliver a packet to Hermes subprocess.

        Writes packet to temp file, then runs:
            hermes -z "Execute this packet: <file_path>"
        """
        import json
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
            tmp_path = f.name

        try:
            result = self._run_hermes(f"Execute this packet: {tmp_path}")
            return {
                "status": "delivered" if result else "failed",
                "output": result or "(no output)",
            }
        except (OSError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Hermes delivery failed: {e}") from e
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def __repr__(self) -> str:
        return f"<HermesBackend name={self.name}>"
