"""Tests for pet_studio_core.state module."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pet_studio_core.state import EXTERNAL_STATES, utc_now, write_project_state


class TestUtcNow(unittest.TestCase):
    """Test utc_now()."""

    def test_returns_string(self):
        result = utc_now()
        self.assertIsInstance(result, str)

    def test_ends_with_z(self):
        result = utc_now()
        self.assertTrue(result.endswith("Z"))

    def test_no_microseconds(self):
        result = utc_now()
        # Should not have microseconds: 2026-01-01T00:00:00Z
        self.assertNotIn(".", result.split("T")[1])


class TestExternalStates(unittest.TestCase):
    """Test EXTERNAL_STATES constant."""

    def test_includes_all_widget_states(self):
        for state in [
            "idle",
            "running",
            "waiting",
            "review",
            "failed",
            "jumping",
            "waving",
            "running-right",
            "running-left",
        ]:
            self.assertIn(state, EXTERNAL_STATES)

    def test_includes_aliases(self):
        for alias in ["done", "blocked", "handoff"]:
            self.assertIn(alias, EXTERNAL_STATES)


class TestWriteProjectState(unittest.TestCase):
    """Test write_project_state()."""

    def _tmp_file(self):
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        path = Path(f.name)
        f.close()
        return path

    def test_basic_write(self):
        path = self._tmp_file()
        try:
            payload = write_project_state(path, "proj1", "running", "Working...")
            self.assertEqual(payload["projectId"], "proj1")
            self.assertEqual(payload["state"], "running")
            self.assertEqual(payload["message"], "Working...")
            self.assertIn("updatedAt", payload)
        finally:
            path.unlink(missing_ok=True)

    def test_file_is_written(self):
        path = self._tmp_file()
        try:
            write_project_state(path, "proj1", "idle", "")
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["state"], "idle")
        finally:
            path.unlink(missing_ok=True)

    def test_metadata_preserved(self):
        path = self._tmp_file()
        try:
            meta = {"source": "test", "count": 42}
            payload = write_project_state(path, "proj1", "running", "", metadata=meta)
            self.assertEqual(payload["metadata"], meta)
        finally:
            path.unlink(missing_ok=True)

    def test_reset_after_ms(self):
        path = self._tmp_file()
        try:
            payload = write_project_state(path, "proj1", "running", "", reset_after_ms=5000, reset_to_state="idle")
            self.assertEqual(payload["resetAfterMs"], 5000)
            self.assertEqual(payload["resetToState"], "idle")
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_state_raises(self):
        path = self._tmp_file()
        try:
            with self.assertRaises(SystemExit):
                write_project_state(path, "proj1", "invalid_state", "")
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_reset_state_raises(self):
        path = self._tmp_file()
        try:
            with self.assertRaises(SystemExit):
                write_project_state(path, "proj1", "running", "", reset_after_ms=1000, reset_to_state="bad")
        finally:
            path.unlink(missing_ok=True)

    def test_negative_reset_after_ms_raises(self):
        path = self._tmp_file()
        try:
            with self.assertRaises(SystemExit):
                write_project_state(path, "proj1", "running", "", reset_after_ms=-1)
        finally:
            path.unlink(missing_ok=True)

    def test_custom_timestamp(self):
        path = self._tmp_file()
        try:
            custom_ts = "2026-01-01T00:00:00Z"
            payload = write_project_state(path, "proj1", "idle", "", updated_at=custom_ts)
            self.assertEqual(payload["updatedAt"], custom_ts)
        finally:
            path.unlink(missing_ok=True)

    def test_creates_parent_dirs(self):
        path = Path(tempfile.gettempdir()) / "pet_studio_test_subdir" / "state.json"
        try:
            write_project_state(path, "proj1", "idle", "")
            self.assertTrue(path.exists())
        finally:
            path.unlink(missing_ok=True)
            path.parent.rmdir()
