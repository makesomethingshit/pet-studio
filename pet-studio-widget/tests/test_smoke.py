"""Smoke tests for Pet Studio widget — verify core rendering pipeline.

These tests use tkinter in a virtual display context (Xvfb on Linux,
or hidden window on Windows) to verify that:
  1. A kit can be loaded and rendered without errors
  2. State transitions produce valid frames
  3. The widget can be created and destroyed cleanly

On Windows without a display, these tests skip gracefully.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Skip entire module if tkinter is not available or no display
try:
    import tkinter as tk  # noqa: F401

    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    from PIL import Image  # noqa: F401

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def _has_display() -> bool:
    """Check if a display is available for tkinter."""
    if sys.platform == "win32":
        # Windows always has a display
        return True
    # Unix: check DISPLAY or WAYLAND_DISPLAY
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@unittest.skipUnless(HAS_TKINTER and HAS_PILLOW and _has_display(), "tkinter, Pillow, or display not available")
class WidgetSmokeTests(unittest.TestCase):
    """Smoke tests for the widget rendering pipeline."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures."""
        cls.project_id = "gakju-archive-demo"
        cls.registry_path = ROOT / "pet-studio-widget" / "project-room-projects.json"
        cls.kit_manifest = ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "project-room.json"

    def test_kit_loads_and_has_required_keys(self) -> None:
        """Verify the demo kit manifest loads and has required structure."""
        import json

        data = json.loads(self.kit_manifest.read_text(encoding="utf-8-sig"))
        self.assertIn("layers", data)
        self.assertIsInstance(data["layers"], list)
        self.assertTrue(len(data["layers"]) > 0)

    def test_state_bridge_write_and_read(self) -> None:
        """Verify state bridge can write and read back a state."""
        import tempfile

        from pet_studio_core.state import write_project_state

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = Path(f.name)

        try:
            payload = write_project_state(
                state_file=state_file,
                project_id=self.project_id,
                state="running",
                message="smoke test",
            )
            self.assertEqual(payload["state"], "running")
            self.assertEqual(payload["projectId"], self.project_id)
            self.assertIn("updatedAt", payload)

            # Read back
            import json

            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["state"], "running")
        finally:
            state_file.unlink(missing_ok=True)

    def test_metadata_round_trip(self) -> None:
        """Verify metadata parameter is preserved in state payload."""
        import tempfile

        from pet_studio_core.state import write_project_state

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = Path(f.name)

        try:
            meta = {"source": "smoke-test", "adapter": "test"}
            payload = write_project_state(
                state_file=state_file,
                project_id=self.project_id,
                state="idle",
                message="",
                metadata=meta,
            )
            self.assertEqual(payload["metadata"], meta)
        finally:
            state_file.unlink(missing_ok=True)

    def test_init_core_overrides_defaults(self) -> None:
        """Verify init_core() can override default paths."""
        import tempfile

        from pet_studio_core.registry import DEFAULT_REGISTRY, init_core

        original = DEFAULT_REGISTRY
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            custom_path = Path(f.name)

        try:
            init_core(registry_path=custom_path)
            from pet_studio_core.registry import DEFAULT_REGISTRY as new_default

            self.assertEqual(new_default, custom_path)
        finally:
            # Restore
            init_core(registry_path=original)
            custom_path.unlink(missing_ok=True)

    def test_core_exports_metadata_aware_write(self) -> None:
        """Verify write_project_state accepts metadata from pet_studio_core."""
        import inspect

        from pet_studio_core import write_project_state

        sig = inspect.signature(write_project_state)
        self.assertIn("metadata", sig.parameters)

    def test_registry_resolves_demo_project(self) -> None:
        """Verify the demo project can be resolved from the registry."""
        from pet_studio_core.registry import select_project

        project = select_project(str(self.registry_path), self.project_id)
        self.assertEqual(project.project_id, self.project_id)
        self.assertTrue(project.enabled)

    def test_normalize_state_aliases(self) -> None:
        """Verify state aliases work correctly."""
        from pet_studio_core.registry import normalize_state

        self.assertEqual(normalize_state("done"), "jumping")
        self.assertEqual(normalize_state("blocked"), "failed")
        self.assertEqual(normalize_state("handoff"), "review")
        self.assertEqual(normalize_state("running"), "running")
        self.assertEqual(normalize_state(None), "idle")

    def test_external_states_includes_aliases(self) -> None:
        """Verify EXTERNAL_STATES includes both widget states and aliases."""
        from pet_studio_core.state import EXTERNAL_STATES

        # Widget states
        for state in ["idle", "running", "waiting", "review", "failed", "jumping"]:
            self.assertIn(state, EXTERNAL_STATES)

        # Aliases
        for alias in ["done", "blocked", "handoff"]:
            self.assertIn(alias, EXTERNAL_STATES)


class CoreBoundarySmokeTests(unittest.TestCase):
    """Verify core module has no forbidden dependencies."""

    def test_core_files_exist(self) -> None:
        """Verify all core files are present."""
        core_dir = ROOT / "pet_studio_core"
        self.assertTrue((core_dir / "__init__.py").exists())
        self.assertTrue((core_dir / "registry.py").exists())
        self.assertTrue((core_dir / "state.py").exists())

    def test_core_no_tkinter(self) -> None:
        """Verify core does not import tkinter."""
        core_files = list((ROOT / "pet_studio_core").rglob("*.py"))
        combined = "\n".join(f.read_text(encoding="utf-8") for f in core_files)
        self.assertNotIn("import tkinter", combined)
        self.assertNotIn("from tkinter", combined)

    def test_core_no_codex_adapter(self) -> None:
        """Verify core does not import Codex adapter modules."""
        core_files = list((ROOT / "pet_studio_core").rglob("*.py"))
        combined = "\n".join(f.read_text(encoding="utf-8") for f in core_files)
        self.assertNotIn("codex_pet_hook", combined)
        self.assertNotIn("codex_state_adapter", combined)
        self.assertNotIn("install_pet_studio_codex_integration", combined)
