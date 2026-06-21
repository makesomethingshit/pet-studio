"""Roost backend adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class RoostBackend(ABC):
    """Base class for roost LLM backends."""

    name: str = "base"

    @abstractmethod
    def classify_event(self, event: dict[str, Any], context: list[dict[str, Any]] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"


from roost.backend.codex import CodexBackend  # noqa: E402
from roost.backend.gateway import GatewayBackend  # noqa: E402
from roost.backend.hermes import HermesBackend  # noqa: E402
from roost.backend.script import ScriptBackend  # noqa: E402

__all__ = ["RoostBackend", "ScriptBackend", "HermesBackend", "CodexBackend", "GatewayBackend"]
