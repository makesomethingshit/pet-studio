"""Script backend — pure rule-based, no LLM."""

from __future__ import annotations

import json
from typing import Any


class ScriptBackend:
    """Pure script backend — no LLM. Rule-based classification only."""

    name = "script"

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
        return True

    def __repr__(self) -> str:
        return f"<ScriptBackend name={self.name}>"
