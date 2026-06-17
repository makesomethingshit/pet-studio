"""Tests for alba state manager."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from alba.state import TeamState


class TestTeamState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_default_state(self):
        self.assertEqual(self.state.alba_status, "idle")
        self.assertEqual(self.state.alba_backend, "script")

    def test_alba_status_set(self):
        self.state.alba_status = "active"
        self.assertEqual(self.state.alba_status, "active")
        self.state._load()
        self.assertEqual(self.state.alba_status, "active")

    def test_enqueue_dequeue_alba(self):
        event = {"type": "file_change", "path": "test.py"}
        self.state.enqueue_alba(event)
        queue = self.state.get_alba_queue()
        self.assertEqual(len(queue), 1)
        item = self.state.dequeue_alba()
        self.assertEqual(item["type"], "file_change")

    def test_register_project(self):
        self.state.register_project("test-proj", "Test Project", security_level=2)
        project = self.state.get_project("test-proj")
        self.assertIsNotNone(project)
        self.assertEqual(project["displayName"], "Test Project")
        self.assertEqual(project["securityLevel"], 2)

    def test_project_queue(self):
        self.state.register_project("test-proj")
        self.state.enqueue_project("test-proj", {"task": "lint"})
        queue = self.state.get_project_queue("test-proj")
        self.assertEqual(len(queue), 1)

    def test_log_event(self):
        self.state.register_project("test-proj")
        self.state.log_event("test-proj", {"type": "build", "status": "pass"})
        project = self.state.get_project("test-proj")
        self.assertEqual(len(project["eventLog"]), 1)
        self.assertEqual(project["lastEvent"]["type"], "build")

    def test_context_history(self):
        self.state.add_context_history({"action": "commit", "files": 3})
        self.state.add_context_history({"action": "push", "success": True})
        history = self.state.get_context_history()
        self.assertEqual(len(history), 2)

    def test_project_insight(self):
        self.state.register_project("test-proj")
        self.state.add_project_insight("test-proj", "lastBuild", "pass")
        self.state.get_context_history(limit=1)


if __name__ == "__main__":
    unittest.main()
