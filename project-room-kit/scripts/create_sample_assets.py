from __future__ import annotations

import runpy
import sys
from pathlib import Path

target_dir = Path(__file__).resolve().parents[2] / "pet-studio-kit" / "scripts"
sys.path.insert(0, str(target_dir))
runpy.run_path(str(target_dir / Path(__file__).name), run_name="__main__")
