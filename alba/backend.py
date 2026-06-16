"""Alba backend adapter interface.

All backends implement:
  - classify_event(event: dict) -> dict: classify an event, return enriched event
  - health_check() -> bool: check if backend is available
"""

from __future__ import annotations

import logging
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


# Import json for ScriptBackend
import json  # noqa: E402
