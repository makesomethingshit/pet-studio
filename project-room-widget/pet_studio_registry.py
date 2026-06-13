from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

target = Path(__file__).resolve().parents[1] / "pet-studio-widget" / Path(__file__).name
spec = importlib.util.spec_from_file_location("_pet_studio_registry", target)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load Pet Studio registry alias: {target}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
globals().update({name: value for name, value in vars(module).items() if not name.startswith("__")})
