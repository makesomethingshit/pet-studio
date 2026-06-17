"""Alba backend adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class AlbaBackend(ABC):
    """Base class for alba LLM backends."""

    name: str = "base"

    @abstractmethod
    def classify_event(self, event: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"


from alba.backend.hermes import HermesBackend  # noqa: E402
from alba.backend.script import ScriptBackend  # noqa: E402

__all__ = ["AlbaBackend", "ScriptBackend", "HermesBackend"]
