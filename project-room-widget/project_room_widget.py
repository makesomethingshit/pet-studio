from __future__ import annotations

import runpy
import sys
from pathlib import Path

target_dir = Path(__file__).resolve().parents[1] / "pet-studio-widget"
sys.path.insert(0, str(target_dir))
target = target_dir / Path(__file__).name
runpy.run_path(str(target), run_name="__main__")
