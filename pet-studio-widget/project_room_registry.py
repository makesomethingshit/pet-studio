"""Compatibility imports for Pet Studio project registry helpers."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pet_studio_core.registry import *  # noqa: F401,F403,E402
