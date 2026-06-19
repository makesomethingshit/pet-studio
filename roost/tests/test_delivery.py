"""Tests for roost packet delivery."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from roost.delivery import DeliveryError, _deliver_to_script, deliver_packet
from roost.state import TeamState


class TestDeliverToScript(unittest.TestCase):
    def test_script_returns_logged(self):
        packet = {"codex_packet": "v1", "project": {"id": "test"}}
        result = _deliver_to_script(packet)
        self.assertEqual(result["agent"], "script")
        self.assertEqual(result["status"], "logged")
        self.assertIn("codex_packet", result["output"])


class TestDeliverPacket(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)
        self.state.register_project("test-proj", security_level=0)  # L0 = allow all

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_deliver_to_script(self):
        """Script agent should return logged status."""
        result = deliver_packet("test-proj", self.state, agent="script")
        self.assertEqual(result["agent"], "script")
        self.assertEqual(result["status"], "logged")

    def test_deliver_to_unknown_agent(self):
        """Unknown agent should raise DeliveryError."""
        with self.assertRaises(DeliveryError):
            deliver_packet("test-proj", self.state, agent="nonexistent")

    def test_deliver_resolves_lead_from_state(self):
        """When agent=None, should use team_state's lead backend."""
        # Default lead is "hermes", but hermes subprocess will fail in test
        # So set lead to "script" for testing
        self.state.set_role_backend("lead", "script")
        result = deliver_packet("test-proj", self.state, agent=None)
        self.assertEqual(result["agent"], "script")
        self.assertEqual(result["status"], "logged")

    def test_deliver_l3_deny_blocks(self):
        """L3 DENY project should raise SecurityError."""
        self.state.register_project("denied-proj", security_level=3)
        from roost.security import SecurityError

        with self.assertRaises(SecurityError):
            deliver_packet("denied-proj", self.state, agent="script")

    @patch("roost.delivery.subprocess.run")
    def test_deliver_to_hermes_success(self, mock_run):
        """Hermes delivery should call subprocess with packet."""
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = deliver_packet("test-proj", self.state, agent="hermes")
        self.assertEqual(result["agent"], "hermes")
        self.assertEqual(result["status"], "delivered")
        mock_run.assert_called_once()

    @patch("roost.delivery.subprocess.run")
    def test_deliver_to_hermes_failure(self, mock_run):
        """Hermes delivery failure should return failed status."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = deliver_packet("test-proj", self.state, agent="hermes")
        self.assertEqual(result["status"], "failed")

    def test_deliver_to_hermes_not_installed(self):
        """Hermes not installed should raise DeliveryError."""
        with patch("roost.delivery.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(DeliveryError):
                deliver_packet("test-proj", self.state, agent="hermes")


class TestBackendDeliverPacket(unittest.TestCase):
    def test_script_backend_deliver(self):
        from roost.backend.script import ScriptBackend

        backend = ScriptBackend()
        result = backend.deliver_packet({"test": True})
        self.assertEqual(result["status"], "logged")

    @patch("roost.backend.hermes.subprocess.run")
    def test_hermes_backend_deliver(self, mock_run):
        from roost.backend.hermes import HermesBackend

        backend = HermesBackend()
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = backend.deliver_packet({"test": True})
        self.assertEqual(result["status"], "delivered")


if __name__ == "__main__":
    unittest.main()
