"""Tests for roost packet delivery."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from roost.delivery import DeliveryError, _deliver_to_script, deliver_packet
from roost.packet import build_codex_packet, build_work_packet, export_work_packet, import_work_packet
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

    @patch("roost.delivery.subprocess.run")
    def test_deliver_default_logs_without_subprocess(self, mock_run):
        """When agent=None, delivery should log locally instead of launching Hermes."""
        self.state.set_role_backend("lead", "remote/sota")
        result = deliver_packet("test-proj", self.state, agent=None)
        self.assertEqual(result["agent"], "script")
        self.assertEqual(result["status"], "logged")
        mock_run.assert_not_called()

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
    def test_deliver_to_hermes_passes_model_profile_env(self, mock_run):
        self.state.set_active_model_profile(None, "openrouter/cheap")
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        deliver_packet("test-proj", self.state, agent="hermes")

        env = mock_run.call_args.kwargs["env"]
        self.assertEqual(env["PET_STUDIO_MODEL_PROFILE"], "openrouter/cheap")
        self.assertEqual(env["PET_STUDIO_MODEL_PROVIDER"], "openrouter")
        self.assertEqual(env["PET_STUDIO_MODEL"], "cheap")
        self.assertEqual(env["OPENROUTER_MODEL"], "cheap")

    @patch("roost.delivery.subprocess.run")
    def test_deliver_to_hermes_uses_requested_role_model_profile(self, mock_run):
        self.state.set_active_model_profile(None, "openrouter/sota")
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

        deliver_packet("test-proj", self.state, agent="hermes", role="coordinator")

        env = mock_run.call_args.kwargs["env"]
        self.assertEqual(env["PET_STUDIO_MODEL_PROFILE"], "openrouter/fast")
        self.assertEqual(env["OPENROUTER_MODEL"], "fast")

    def test_work_packet_includes_model_profile_and_compat_marker(self):
        self.state.set_active_model_profile(None, "openrouter/fast")
        self.state.register_employee("scout-1", "Scout One", role="scout")
        self.state.enqueue_project(
            "test-proj",
            {
                "id": "task-1",
                "type": "scan",
                "status": "waiting",
                "assignedRole": "scout",
                "assignedEmployee": "scout-1",
            },
        )

        packet = build_work_packet("test-proj", self.state)

        self.assertEqual(packet["work_packet"], "v1")
        self.assertEqual(packet["codex_packet"], "v1")
        self.assertEqual(packet["model_profile"]["id"], "openrouter/fast")
        self.assertEqual(packet["model_profile"]["provider"], "openrouter")
        self.assertEqual(packet["team_model_preset"], "save-credits")
        self.assertEqual(packet["team_model_savings"]["baseline"], "lead-only")
        self.assertEqual(packet["team_model_savings"]["baselineUnits"], 3)
        self.assertEqual(packet["team_model_savings"]["planUnits"], 2)
        self.assertEqual(packet["team_model_savings"]["savedUnits"], 1)
        plan = {item["role"]: item["profile"]["id"] for item in packet["role_model_plan"]}
        self.assertEqual(plan["scout"], "local/default")
        self.assertEqual(plan["coordinator"], "openrouter/fast")
        self.assertEqual(plan["lead"], "openrouter/fast")
        self.assertEqual(packet["role_model_env"]["scout"]["PET_STUDIO_MODEL_PROFILE"], "local/default")
        self.assertEqual(packet["role_model_env"]["coordinator"]["OPENROUTER_MODEL"], "fast")
        self.assertEqual(packet["role_model_env"]["lead"]["OPENROUTER_MODEL"], "fast")
        self.assertEqual(packet["role_model_env_clear"]["scout"], ["OPENROUTER_MODEL", "CODEX_MODEL"])
        self.assertEqual(packet["role_model_env_clear"]["coordinator"], ["CODEX_MODEL"])
        self.assertEqual(packet["role_model_env_clear"]["lead"], ["CODEX_MODEL"])
        self.assertEqual(packet["employees"][0]["id"], "scout-1")
        self.assertEqual(packet["employees"][0]["role"], "scout")
        self.assertEqual(packet["tasks"][0]["payload"]["assignedRole"], "scout")
        self.assertEqual(packet["tasks"][0]["payload"]["assignedEmployee"], "scout-1")

    def test_legacy_codex_packet_builder_still_works(self):
        packet = build_codex_packet("test-proj", self.state)

        self.assertEqual(packet["work_packet"], "v1")
        self.assertEqual(packet["codex_packet"], "v1")

    def test_export_work_packet_uses_work_packet_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = export_work_packet("test-proj", self.state, out_dir=tmp)
            packet = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(out_path.name, "test-proj-work-packet.json")
        self.assertEqual(packet["work_packet"], "v1")
        self.assertEqual(packet["codex_packet"], "v1")

    def test_import_work_packet_accepts_legacy_codex_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "legacy-codex-packet.json"
            packet_path.write_text(
                json.dumps(
                    {
                        "codex_packet": "v1",
                        "project": {"id": "legacy-proj", "name": "Legacy Project"},
                        "mission": "Keep compatibility",
                        "tasks": [],
                    }
                ),
                encoding="utf-8",
            )

            packet = import_work_packet(packet_path, self.state)

        self.assertEqual(packet["codex_packet"], "v1")
        self.assertEqual(self.state.get_project_mission("legacy-proj"), "Keep compatibility")

    def test_import_work_packet_restores_model_profile_and_team_preset(self):
        self.state.set_active_model_profile(None, "openrouter/cheap")
        self.state.apply_team_model_preset("all-value")
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = export_work_packet("test-proj", self.state, out_dir=tmp)
            imported = TeamState(Path(tmp) / "imported-team-state.json")

            import_work_packet(packet_path, imported)

        self.assertEqual(imported.get_active_model_profile_id(), "openrouter/cheap")
        self.assertEqual(imported.get_team_model_preset_id(), "all-value")
        self.assertEqual(imported.estimate_team_model_savings()["baseline"], "lead-only")

    def test_import_work_packet_restores_custom_role_model_plan(self):
        self.state.set_model_profile(
            None,
            "openrouter/scout-custom",
            "hermes",
            "openrouter",
            "custom/scout",
            "low",
            "value",
        )
        self.state.set_role_model_profile("scout", "openrouter/scout-custom")
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = export_work_packet("test-proj", self.state, out_dir=tmp)
            imported = TeamState(Path(tmp) / "imported-team-state.json")

            import_work_packet(packet_path, imported)

        self.assertEqual(imported.get_team_model_preset_id(), "custom")
        scout_profile = imported.get_role_model_profile("scout")
        self.assertEqual(scout_profile["id"], "openrouter/scout-custom")
        self.assertEqual(scout_profile["model"], "custom/scout")

    def test_import_work_packet_restores_employees_and_task_assignments(self):
        self.state.register_employee("scout-1", "Scout One", role="scout")
        self.state.set_employee_status("scout-1", "busy")
        self.state.enqueue_project(
            "test-proj",
            {
                "id": "task-1",
                "type": "scan",
                "status": "running",
                "assignedRole": "scout",
                "assignedEmployee": "scout-1",
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = export_work_packet("test-proj", self.state, out_dir=tmp)
            imported = TeamState(Path(tmp) / "imported-team-state.json")

            import_work_packet(packet_path, imported)

        employee = imported.get_employees()[0]
        self.assertEqual(employee["id"], "scout-1")
        self.assertEqual(employee["name"], "Scout One")
        self.assertEqual(employee["role"], "scout")
        self.assertEqual(employee["status"], "busy")
        task = imported.get_project_queue("test-proj")[0]
        self.assertEqual(task["id"], "task-1")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["assignedRole"], "scout")
        self.assertEqual(task["assignedEmployee"], "scout-1")
        self.assertIn("enqueuedAt", task)
        self.assertNotIn("enqueued_at", task)

    def test_import_work_packet_merges_existing_task_payload(self):
        self.state.enqueue_project(
            "test-proj",
            {
                "id": "task-1",
                "type": "scan",
                "status": "running",
                "assignedRole": "scout",
                "assignedEmployee": "scout-1",
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = export_work_packet("test-proj", self.state, out_dir=tmp)
            imported = TeamState(Path(tmp) / "imported-team-state.json")
            imported.register_project("test-proj")
            imported.enqueue_project(
                "test-proj",
                {
                    "id": "task-1",
                    "type": "scan",
                    "status": "waiting",
                },
            )

            import_work_packet(packet_path, imported)

            reloaded = TeamState(Path(tmp) / "imported-team-state.json")

        task = reloaded.get_project_queue("test-proj")[0]
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["assignedRole"], "scout")
        self.assertEqual(task["assignedEmployee"], "scout-1")
        self.assertIn("enqueuedAt", task)
        self.assertNotIn("enqueued_at", task)

    def test_import_work_packet_skips_incomplete_unknown_role_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "incomplete-work-packet.json"
            packet_path.write_text(
                json.dumps(
                    {
                        "work_packet": "v1",
                        "project": {"id": "import-proj", "name": "Import Project"},
                        "role_model_plan": [
                            {
                                "role": "scout",
                                "profile": {"id": "openrouter/missing-model"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            imported = TeamState(Path(tmp) / "imported-team-state.json")

            import_work_packet(packet_path, imported)

        self.assertEqual(imported.get_role_model_profile("scout")["id"], "local/default")

    @patch("roost.delivery.subprocess.run")
    def test_deliver_resolves_agent_alias(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = deliver_packet("test-proj", self.state, agent="remote/sota")
        self.assertEqual(result["agent"], "hermes")
        self.assertEqual(result["status"], "delivered")

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
