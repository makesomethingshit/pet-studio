"""Tests for roost dispatcher role-based task routing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from roost.dispatcher import (
    BackendRegistry,
    TaskRole,
    _resolve_backend_for_role,
    classify_task,
    dispatch,
)
from roost.state import TeamState


class TestClassifyTask(unittest.TestCase):
    def test_scout_types(self):
        for t in ("scan", "read", "summarize_files", "log_summary", "file_scan"):
            self.assertEqual(classify_task({"type": t}), TaskRole.SCOUT)

    def test_coordinator_types(self):
        for t in ("compress", "summarize", "draft_packet", "synthesize"):
            self.assertEqual(classify_task({"type": t}), TaskRole.COORDINATOR)

    def test_lead_default(self):
        """Unknown types should default to LEAD."""
        self.assertEqual(classify_task({"type": "implement"}), TaskRole.LEAD)
        self.assertEqual(classify_task({"type": "deploy"}), TaskRole.LEAD)
        self.assertEqual(classify_task({}), TaskRole.LEAD)

    def test_assigned_role_overrides_type(self):
        self.assertEqual(classify_task({"type": "implement", "assignedRole": "coordinator"}), TaskRole.COORDINATOR)
        self.assertEqual(classify_task({"type": "summarize", "assignedRole": "lead"}), TaskRole.LEAD)
        self.assertEqual(classify_task({"type": "deploy", "assigned_role": "scout"}), TaskRole.SCOUT)

    def test_case_insensitive(self):
        self.assertEqual(classify_task({"type": "SCAN"}), TaskRole.SCOUT)
        self.assertEqual(classify_task({"type": "Compress"}), TaskRole.COORDINATOR)


class TestBackendRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = BackendRegistry()

    def test_default_backends(self):
        self.assertIn("script", self.registry.available)
        self.assertIn("hermes", self.registry.available)

    def test_register_new(self):
        mock_cls = MagicMock()
        mock_cls.__name__ = "FakeBackend"
        self.registry.register("codex", mock_cls)
        self.assertIn("codex", self.registry.available)
        self.assertEqual(self.registry.get("codex"), mock_cls)

    def test_get_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.registry.get("nonexistent")

    def test_reset(self):
        mock_cls = MagicMock()
        mock_cls.__name__ = "FakeBackend"
        self.registry.register("codex", mock_cls)
        self.registry.reset()
        self.assertNotIn("codex", self.registry.available)
        self.assertEqual(set(self.registry.available), {"script", "hermes"})


class TestResolveBackendForRole(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_defaults(self):
        self.assertEqual(_resolve_backend_for_role(TaskRole.SCOUT, self.state), "script")
        self.assertEqual(_resolve_backend_for_role(TaskRole.COORDINATOR, self.state), "hermes")
        self.assertEqual(_resolve_backend_for_role(TaskRole.LEAD, self.state), "hermes")

    def test_custom_lead(self):
        self.state.set_role_backend("lead", "codex")
        self.assertEqual(_resolve_backend_for_role(TaskRole.LEAD, self.state), "codex")
        # Others unchanged
        self.assertEqual(_resolve_backend_for_role(TaskRole.SCOUT, self.state), "script")


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)
        self.state.register_project("test-proj")
        self.registry = BackendRegistry()

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_dispatch_scout(self):
        """Scout task should use script backend (free)."""
        task = {"type": "scan", "project_id": "test-proj"}
        result = dispatch(task, self.state, registry=self.registry)
        self.assertIn("classification", result)
        self.assertEqual(result["classification"]["source"], "script")

    def test_dispatch_resolves_endpoint_alias(self):
        """Endpoint aliases should resolve before BackendRegistry lookup."""
        self.state.set_role_backend("scout", "local/fast")
        task = {"type": "scan", "project_id": "test-proj"}
        result = dispatch(task, self.state, registry=self.registry)
        self.assertEqual(result["classification"]["source"], "script")

    def test_dispatch_unknown_endpoint_alias_raises(self):
        self.state.set_role_backend("scout", "missing/alias")
        task = {"type": "scan", "project_id": "test-proj"}
        with self.assertRaises(ValueError):
            dispatch(task, self.state, registry=self.registry)

    def test_dispatch_lead(self):
        """Lead task should use hermes backend (default)."""
        task = {"type": "implement", "project_id": "test-proj"}
        # Mock hermes to avoid subprocess
        with patch("roost.dispatcher.HermesBackend") as MockHermes:
            mock_instance = MagicMock()
            mock_instance.classify_event.return_value = {
                "type": "implement",
                "classification": {"priority": "normal", "source": "hermes"},
            }
            MockHermes.return_value = mock_instance
            result = dispatch(task, self.state, registry=self.registry)
        self.assertIn("classification", result)

    def test_dispatch_with_custom_registry(self):
        """Custom registry should be used when passed."""
        task = {"type": "scan", "project_id": "test-proj"}
        custom_registry = BackendRegistry()
        mock_cls = MagicMock(spec=object)
        mock_cls.__name__ = "MockBackend"
        mock_instance = MagicMock()
        mock_instance.classify_event.return_value = {
            "type": "scan",
            "classification": {"priority": "low", "source": "mock"},
        }
        mock_cls.return_value = mock_instance
        custom_registry.register("mock_backend", mock_cls)
        # Override scout to use mock
        self.state.set_role_backend("scout", "mock_backend")
        result = dispatch(task, self.state, registry=custom_registry)
        self.assertEqual(result["classification"]["source"], "mock")

    def test_dispatch_passes_active_model_profile_to_backend(self):
        task = {"type": "implement", "project_id": "test-proj"}
        self.state.set_active_model_profile(None, "openrouter/fast")
        custom_registry = BackendRegistry()
        mock_cls = MagicMock(spec=object)
        mock_cls.__name__ = "MockHermes"
        mock_instance = MagicMock()
        mock_instance.classify_event.return_value = {
            "type": "implement",
            "classification": {"priority": "normal", "source": "mock"},
        }
        mock_cls.return_value = mock_instance
        custom_registry.register("hermes", mock_cls)

        dispatch(task, self.state, registry=custom_registry)

        mock_instance.set_model_profile.assert_called_once()
        profile = mock_instance.set_model_profile.call_args.args[0]
        self.assertEqual(profile["id"], "openrouter/fast")

    def test_dispatch_passes_role_model_profile_to_backend(self):
        task = {"type": "summarize", "project_id": "test-proj"}
        self.state.set_active_model_profile(None, "openrouter/sota")
        custom_registry = BackendRegistry()
        mock_cls = MagicMock(spec=object)
        mock_cls.__name__ = "MockHermes"
        mock_instance = MagicMock()
        mock_instance.classify_event.return_value = {
            "type": "summarize",
            "classification": {"priority": "normal", "source": "mock"},
        }
        mock_cls.return_value = mock_instance
        custom_registry.register("hermes", mock_cls)

        dispatch(task, self.state, registry=custom_registry)

        mock_instance.set_model_profile.assert_called_once()
        profile = mock_instance.set_model_profile.call_args.args[0]
        self.assertEqual(profile["id"], "openrouter/fast")

    def test_dispatch_uses_assigned_role_model_profile(self):
        task = {"type": "implement", "project_id": "test-proj", "assignedRole": "coordinator"}
        self.state.set_active_model_profile(None, "openrouter/sota")
        custom_registry = BackendRegistry()
        mock_cls = MagicMock(spec=object)
        mock_cls.__name__ = "MockHermes"
        mock_instance = MagicMock()
        mock_instance.classify_event.return_value = {
            "type": "implement",
            "classification": {"priority": "normal", "source": "mock"},
        }
        mock_cls.return_value = mock_instance
        custom_registry.register("hermes", mock_cls)

        dispatch(task, self.state, registry=custom_registry)

        mock_instance.set_model_profile.assert_called_once()
        profile = mock_instance.set_model_profile.call_args.args[0]
        self.assertEqual(profile["id"], "openrouter/fast")

    def test_dispatch_security_blocks(self):
        """L3 DENY project should raise SecurityError for risky actions."""
        self.state.register_project("denied-proj", security_level=3)
        # "deploy" has risk=3 (critical), which L3 blocks
        task = {"type": "deploy", "project_id": "denied-proj"}
        from roost.security import SecurityError

        with self.assertRaises(SecurityError):
            dispatch(task, self.state, registry=self.registry)

    def test_dispatch_no_project_id_skips_security(self):
        """Task without project_id should skip security check."""
        task = {"type": "scan"}
        result = dispatch(task, self.state, registry=self.registry)
        self.assertIn("classification", result)


if __name__ == "__main__":
    unittest.main()
