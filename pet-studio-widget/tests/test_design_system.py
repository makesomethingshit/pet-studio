"""Design system smoke tests for the Project Hub UI."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN_SYSTEM_PATH = ROOT / "ui" / "design_system.py"
PROJECT_HUB_PATH = ROOT / "ui" / "project_hub.py"


def _load_design_system():
    spec = importlib.util.spec_from_file_location("pet_studio_widget_ui_design_system", DESIGN_SYSTEM_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DesignSystemTests(unittest.TestCase):
    def test_design_system_tokens_are_small_and_stable(self) -> None:
        module = _load_design_system()

        self.assertEqual(
            module.DS_SPACING,
            {
                "hair": 4,
                "tight": 8,
                "cluster": 12,
                "section": 16,
                "block": 24,
                "panel": 32,
            },
        )
        self.assertEqual(module.hub_colors()["bg"], module.DS_COLORS["page"])
        self.assertEqual(module.hub_colors()["accent"], module.DS_COLORS["accent"])
        self.assertEqual(module.status_color("failed"), module.DS_COLORS["danger"])
        self.assertEqual(module.role_color("lead"), module.DS_COLORS["success"])

    def test_project_hub_uses_design_system_entrypoint(self) -> None:
        source = PROJECT_HUB_PATH.read_text(encoding="utf-8")

        self.assertIn("from ui.design_system import", source)
        self.assertIn("HUB_COLORS = hub_colors()", source)
        self.assertIn("configure_hub_ttk(hub)", source)


if __name__ == "__main__":
    unittest.main()
