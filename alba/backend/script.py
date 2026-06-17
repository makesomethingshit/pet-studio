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

    def classify_event(
        self,
        event: dict[str, Any],
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        text = json.dumps(event).lower()
        priority = "normal"
        for keyword, p in self.KEYWORD_PRIORITY.items():
            if keyword in text:
                priority = p
                break
        if context:
            priority = self._adjust_by_context(event, priority, context)
        event["classification"] = {"priority": priority, "source": "script"}
        return event

    def _adjust_by_context(
        self,
        event: dict[str, Any],
        current_priority: str,
        context: list[dict[str, Any]],
    ) -> str:
        """Adjust priority based on recent history.

        If the same project had 3+ high-priority events in the last 10,
        keep priority at high even if current keywords say otherwise.
        """
        project_id = event.get("project_id")
        if not project_id:
            return current_priority
        recent = [e for e in context[-10:] if e.get("project_id") == project_id]
        high_count = sum(1 for e in recent if e.get("priority") == "high")
        if high_count >= 3 and current_priority != "high":
            return "high"
        return current_priority

    def health_check(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<ScriptBackend name={self.name}>"
