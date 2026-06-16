"""Tests for alba backend adapters."""

from __future__ import annotations

import unittest

from alba.backend import ScriptBackend


class TestScriptBackend(unittest.TestCase):
    def setUp(self):
        self.backend = ScriptBackend()

    def test_health_check(self):
        self.assertTrue(self.backend.health_check())

    def test_classify_event_error(self):
        event = {"type": "build", "status": "failed", "message": "error in module"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "high")
        self.assertEqual(result["classification"]["source"], "script")

    def test_classify_event_idle(self):
        event = {"type": "status", "state": "idle"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "low")

    def test_classify_event_normal(self):
        event = {"type": "build", "state": "running"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "normal")


if __name__ == "__main__":
    unittest.main()
