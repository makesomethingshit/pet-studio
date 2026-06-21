"""Tests for roost backend adapters."""

from __future__ import annotations

import json
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from roost.backend import CodexBackend, GatewayBackend, HermesBackend, ScriptBackend
from roost.model_profile import build_model_profile_env


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
    def test_classify_passes_local_auth_config_env(self, mock_run):
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / ".pet_studio_keys.json"
            auth_path.write_text(
                '{"HERMES_GATEWAY_URL":"https://gateway.test","HERMES_GATEWAY_TOKEN":"secret"}',
                encoding="utf-8",
            )
            old_config = os.environ.get("PET_STUDIO_AUTH_CONFIG")
            os.environ["PET_STUDIO_AUTH_CONFIG"] = str(auth_path)
            try:
                mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "normal"})()
                self.backend.classify_event({"type": "build"})
            finally:
                if old_config is None:
                    os.environ.pop("PET_STUDIO_AUTH_CONFIG", None)
                else:
                    os.environ["PET_STUDIO_AUTH_CONFIG"] = old_config

        env = mock_run.call_args.kwargs["env"]
        self.assertEqual(env["HERMES_GATEWAY_URL"], "https://gateway.test")
        self.assertEqual(env["HERMES_GATEWAY_TOKEN"], "secret")

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


class TestCodexBackend(unittest.TestCase):
    @patch("roost.backend.codex.subprocess.run")
    def test_health_check_uses_codex_command_and_auth_env(self, mock_run):
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / ".pet_studio_keys.json"
            auth_path.write_text(
                '{"CODEX_CMD":"codex-local","CODEX_OAUTH_TOKEN":"oauth-token"}',
                encoding="utf-8",
            )
            old_config = os.environ.get("PET_STUDIO_AUTH_CONFIG")
            os.environ["PET_STUDIO_AUTH_CONFIG"] = str(auth_path)
            try:
                backend = CodexBackend()
                mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "codex 1.0"})()
                self.assertTrue(backend.health_check())
            finally:
                if old_config is None:
                    os.environ.pop("PET_STUDIO_AUTH_CONFIG", None)
                else:
                    os.environ["PET_STUDIO_AUTH_CONFIG"] = old_config

        self.assertEqual(mock_run.call_args.args[0], ["codex-local", "--version"])
        self.assertEqual(mock_run.call_args.kwargs["env"]["CODEX_OAUTH_TOKEN"], "oauth-token")

    def test_model_profile_env_loads_auth_config_without_overriding_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / ".pet_studio_keys.json"
            auth_path.write_text(
                '{"OPENROUTER_API_KEY":"stored","CODEX_OAUTH_TOKEN":"stored-oauth"}',
                encoding="utf-8",
            )
            env = build_model_profile_env(
                None,
                {
                    "PET_STUDIO_AUTH_CONFIG": str(auth_path),
                    "OPENROUTER_API_KEY": "env-key",
                },
            )

        self.assertEqual(env["OPENROUTER_API_KEY"], "env-key")
        self.assertEqual(env["CODEX_OAUTH_TOKEN"], "stored-oauth")


class TestGatewayBackend(unittest.TestCase):
    def test_defaults_to_local_fusion_gateway(self):
        backend = GatewayBackend()
        self.assertEqual(backend.gateway_url, "http://127.0.0.1:8787/v1")

    @patch("roost.backend.gateway.urllib.request.urlopen")
    def test_classify_posts_openai_compatible_payload(self, mock_urlopen):
        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / ".pet_studio_keys.json"
            auth_path.write_text(
                '{"HERMES_GATEWAY_URL":"http://gateway.local/v1","HERMES_GATEWAY_TOKEN":"secret"}',
                encoding="utf-8",
            )
            old_config = os.environ.get("PET_STUDIO_AUTH_CONFIG")
            os.environ["PET_STUDIO_AUTH_CONFIG"] = str(auth_path)
            try:
                response = mock_urlopen.return_value.__enter__.return_value
                response.read.return_value = b'{"choices":[{"message":{"content":"high"}}]}'
                backend = GatewayBackend()
                backend.set_model_profile({"id": "fusion/local", "provider": "openrouter", "model": "fusion"})
                result = backend.classify_event({"type": "build", "status": "failed"})
            finally:
                if old_config is None:
                    os.environ.pop("PET_STUDIO_AUTH_CONFIG", None)
                else:
                    os.environ["PET_STUDIO_AUTH_CONFIG"] = old_config

        self.assertEqual(result["classification"]["source"], "gateway")
        self.assertEqual(result["classification"]["priority"], "high")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://gateway.local/v1/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "fusion")
        self.assertFalse(payload["stream"])

    @patch("roost.backend.gateway.urllib.request.urlopen")
    def test_gateway_health_check_uses_models_endpoint(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.status = 200

        self.assertTrue(GatewayBackend().health_check())

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8787/v1/models")


if __name__ == "__main__":
    unittest.main()
