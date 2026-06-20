"""Tests for roost backend adapters."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from roost.backend import HermesBackend, ScriptBackend


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


class TestHermesBackend(unittest.TestCase):
    def setUp(self):
        self.backend = HermesBackend()

    def test_name(self):
        self.assertEqual(self.backend.name, "hermes")

    def test_parse_priority_high(self):
        self.assertEqual(HermesBackend._parse_priority("high"), "high")

    def test_parse_priority_normal(self):
        self.assertEqual(HermesBackend._parse_priority("normal"), "normal")

    def test_parse_priority_low(self):
        self.assertEqual(HermesBackend._parse_priority("low"), "low")

    def test_parse_priority_unknown(self):
        self.assertIsNone(HermesBackend._parse_priority("something else"))

    @patch("roost.backend.hermes.subprocess.run")
    def test_classify_with_hermes_response(self, mock_run):
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "high"})()
        event = {"type": "build", "status": "failed"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "high")
        self.assertEqual(result["classification"]["source"], "hermes")

    @patch("roost.backend.hermes.subprocess.run")
    def test_classify_passes_model_profile_env(self, mock_run):
        self.backend.set_model_profile(
            {
                "id": "openrouter/fast",
                "provider": "openrouter",
                "model": "fast",
            }
        )
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "normal"})()

        self.backend.classify_event({"type": "build"})

        env = mock_run.call_args.kwargs["env"]
        self.assertEqual(env["PET_STUDIO_MODEL_PROFILE"], "openrouter/fast")
        self.assertEqual(env["PET_STUDIO_MODEL_PROVIDER"], "openrouter")
        self.assertEqual(env["PET_STUDIO_MODEL"], "fast")
        self.assertEqual(env["OPENROUTER_MODEL"], "fast")

    @patch("roost.backend.hermes.subprocess.run")
    def test_classify_no_response(self, mock_run):
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": ""})()
        event = {"type": "build", "status": "failed"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["source"], "hermes (no response)")

    @patch("roost.backend.hermes.subprocess.run")
    def test_classify_fallback_on_error(self, mock_run):
        mock_run.return_value = type("R", (), {"returncode": 1, "stdout": ""})()
        event = {"type": "build", "status": "failed"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["source"], "hermes (no response)")

    @patch("roost.backend.hermes.subprocess.run")
    def test_classify_fallback_on_missing_cmd(self, mock_run):
        mock_run.side_effect = FileNotFoundError("hermes not found")
        event = {"type": "status", "state": "idle"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["source"], "hermes (no response)")

    @patch("roost.backend.hermes.subprocess.run")
    def test_health_check_ok(self, mock_run):
        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "hermes 1.0"})()
        self.assertTrue(self.backend.health_check())

    @patch("roost.backend.hermes.subprocess.run")
    def test_health_check_fail(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(self.backend.health_check())

    def test_repr(self):
        self.assertIn("HermesBackend", repr(self.backend))


if __name__ == "__main__":
    unittest.main()
