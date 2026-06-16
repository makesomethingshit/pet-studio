"""Alba backend adapter interface.

All backends implement:
  - classify_event(event: dict) -> dict: classify an event, return enriched event
  - health_check() -> bool: check if backend is available
"""

from __future__ import annotations

import json
import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class AlbaBackend(ABC):
    """Base class for alba LLM backends."""

    name: str = "base"

    @abstractmethod
    def classify_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Classify an event and return enriched event with 'classification' and 'priority'."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"


class ScriptBackend(AlbaBackend):
    """Pure script backend — no LLM. Rule-based classification only."""

    name = "script"

    # Simple keyword-based priority
    KEYWORD_PRIORITY = {
        "error": "high",
        "failed": "high",
        "blocked": "high",
        "done": "low",
        "idle": "low",
        "running": "normal",
        "waiting": "normal",
        "review": "normal",
    }

    def classify_event(self, event: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(event).lower()
        priority = "normal"
        for keyword, p in self.KEYWORD_PRIORITY.items():
            if keyword in text:
                priority = p
                break
        event["classification"] = {"priority": priority, "source": "script"}
        return event

    def health_check(self) -> bool:
        return True  # Always available


class HermesBackend(AlbaBackend):
    """Hermes Agent backend — subprocess-based event classification.

    Uses `hermes -z` for one-shot classification via subprocess.
    Falls back to script rules if Hermes is not available.
    """

    name = "hermes"

    def __init__(self, hermes_cmd: str = "hermes", timeout: int = 10):
        self.hermes_cmd = hermes_cmd
        self.timeout = timeout
        self._script_fallback = ScriptBackend()

    def _run_hermes(self, prompt: str) -> str | None:
        """Run hermes -z and return stdout, or None on failure."""
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
            f"Classify this event by priority (high/normal/low). "
            f"Reply with ONE word only.\n"
            f"Event: {json.dumps(event)}"
        )
        output = self._run_hermes(prompt)
        priority = self._parse_priority(output) if output else None
        if priority:
            event["classification"] = {"priority": priority, "source": "hermes"}
        else:
            # Fallback to script rules
            event = self._script_fallback.classify_event(event)
            event["classification"]["source"] = "script (hermes fallback)"
        return event

    def health_check(self) -> bool:
        result = self._run_hermes("--version")
        return result is not None

    @staticmethod
    def _parse_priority(output: str) -> str | None:
        text = output.strip().lower()
        for word in ("high", "normal", "low"):
            if word in text:
                return word
        return None
