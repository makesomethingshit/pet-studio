"""Hermes Agent backend — subprocess-based event classification."""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class HermesBackend:
    """Hermes Agent backend — subprocess-based event classification.

    Uses `hermes -z` for one-shot classification via subprocess.
    Falls back to script rules if Hermes is not available.
    """

    name = "hermes"

    def __init__(self, hermes_cmd: str = "hermes", timeout: int = 10):
        self.hermes_cmd = hermes_cmd
        self.timeout = timeout

    def _run_hermes(self, prompt: str) -> str | None:
        try:
            result = subprocess.run(
                [self.hermes_cmd, "-z", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.warning("Hermes returned non-zero exit code: %s", result.returncode)
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.warning("Hermes subprocess failed: %s", e)
            return None

    def classify_event(self, event: dict[str, Any]) -> dict[str, Any]:
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
                text=True,
                timeout=5,
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

    def __repr__(self) -> str:
        return f"<HermesBackend name={self.name}>"
