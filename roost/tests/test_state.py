"""Tests for roost state manager."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from roost.state import TeamState


class TestTeamState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_default_state(self):
        self.assertEqual(self.state.roost_status, "idle")
        self.assertEqual(self.state.roost_backend, "script")

    def test_roost_status_set(self):
        self.state.roost_status = "active"
        self.assertEqual(self.state.roost_status, "active")
        self.state._load()
        self.assertEqual(self.state.roost_status, "active")

    def test_enqueue_dequeue_roost(self):
        event = {"type": "file_change", "path": "test.py"}
        self.state.enqueue_roost(event)
        queue = self.state.get_roost_queue()
        self.assertEqual(len(queue), 1)
        item = self.state.dequeue_roost()
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

    def test_context_history_truncated_to_200(self):
        for i in range(210):
            self.state.add_context_history({"action": f"act-{i}"})
        history = self.state.get_context_history(limit=500)
        self.assertEqual(len(history), 200)

    def test_trust_field_in_default_state(self):
        self.assertIn("trust", self.state._data)
        self.assertEqual(self.state._data["trust"], {})

    def test_log_event_accumulates_context(self):
        self.state.register_project("ctx-proj")
        self.state.log_event("ctx-proj", {"type": "build", "priority": "high"})
        self.state.log_event("ctx-proj", {"type": "test", "priority": "high"})
        history = self.state.get_context_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["project_id"], "ctx-proj")

    # --- Employees ---

    def test_default_employees_empty(self):
        emps = self.state.get_employees()
        self.assertEqual(len(emps), 0)

    def test_register_employee(self):
        result = self.state.register_employee("emp-1", "Codex")
        self.assertTrue(result)
        emps = self.state.get_employees()
        self.assertEqual(len(emps), 1)
        self.assertEqual(emps[0]["name"], "Codex")
        self.assertEqual(emps[0]["status"], "idle")

    def test_register_employee_duplicate(self):
        self.state.register_employee("emp-1", "Codex")
        result = self.state.register_employee("emp-1", "Duplicate")
        self.assertFalse(result)
        emps = self.state.get_employees()
        self.assertEqual(len(emps), 1)

    def test_set_employee_status(self):
        self.state.register_employee("emp-1", "Codex")
        result = self.state.set_employee_status("emp-1", "running")
        self.assertTrue(result)
        emps = self.state.get_employees()
        self.assertEqual(emps[0]["status"], "running")

    def test_set_employee_status_not_found(self):
        result = self.state.set_employee_status("emp-999", "running")
        self.assertFalse(result)

    # --- Approvals ---

    def test_add_approval_request(self):
        self.state.register_project("test-proj")
        aid = self.state.add_approval_request("test-proj", "deploy")
        self.assertIsInstance(aid, str)
        self.assertTrue(len(aid) > 0)

    def test_get_pending_approvals(self):
        self.state.register_project("test-proj")
        self.state.add_approval_request("test-proj", "deploy")
        self.state.add_approval_request("test-proj", "layout.reset")
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 2)

    def test_resolve_approval(self):
        self.state.register_project("test-proj")
        aid = self.state.add_approval_request("test-proj", "deploy")
        result = self.state.resolve_approval(aid, approved=True)
        self.assertTrue(result)
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 0)

    def test_resolve_approval_reject(self):
        self.state.register_project("test-proj")
        aid = self.state.add_approval_request("test-proj", "deploy")
        self.state.resolve_approval(aid, approved=False)
        approvals = self.state._data["approvals"]
        self.assertEqual(approvals[0]["status"], "rejected")
        self.assertIn("resolvedAt", approvals[0])

    def test_resolve_approval_not_found(self):
        result = self.state.resolve_approval("nonexistent", approved=True)
        self.assertFalse(result)

    def test_approvals_trimmed_to_50(self):
        self.state.register_project("test-proj")
        for i in range(55):
            self.state.add_approval_request("test-proj", f"action-{i}")
        approvals = self.state._data["approvals"]
        self.assertEqual(len(approvals), 50)

    def test_approval_id_is_full_uuid(self):
        """Approval ID should be a full UUID (36 chars), not truncated."""
        self.state.register_project("test-proj")
        aid = self.state.add_approval_request("test-proj", "deploy")
        self.assertEqual(len(aid), 36)
        self.assertIn("-", aid)

    def test_approval_ids_unique(self):
        """Multiple approvals should never share the same ID."""
        self.state.register_project("test-proj")
        ids = set()
        for i in range(20):
            aid = self.state.add_approval_request("test-proj", f"action-{i}")
            self.assertNotIn(aid, ids)
            ids.add(aid)
        self.assertEqual(len(ids), 20)

    # --- Role backends ---

    def test_default_role_backends(self):
        """Default role_backends should map scout→script, coordinator→hermes, lead→hermes."""
        self.assertEqual(self.state.get_role_backend("scout"), "local/fast")
        self.assertEqual(self.state.get_role_backend("coordinator"), "remote/sota")
        self.assertEqual(self.state.get_role_backend("lead"), "remote/sota")

    def test_set_role_backend(self):
        """set_role_backend should persist the change."""
        self.state.set_role_backend("lead", "codex")
        self.assertEqual(self.state.get_role_backend("lead"), "codex")
        # Other roles unchanged
        self.assertEqual(self.state.get_role_backend("scout"), "local/fast")

    def test_role_backends_in_default_state(self):
        """_default_state should include role_backends section."""
        data = self.state._default_state()
        self.assertIn("role_backends", data)
        self.assertEqual(data["role_backends"]["scout"], "local/fast")
        self.assertEqual(data["role_backends"]["lead"], "remote/sota")

    def test_endpoint_alias_resolves_to_backend(self):
        self.assertEqual(self.state.resolve_endpoint_backend("local/fast"), "script")
        self.assertEqual(self.state.resolve_endpoint_backend("remote/sota"), "hermes")
        self.assertEqual(self.state.resolve_endpoint_backend("script"), "script")

    def test_l3_blocks_reconfigure_writes(self):
        from roost.security import SecurityError

        self.state.register_project("locked", security_level=3)
        with self.assertRaises(SecurityError):
            self.state.set_endpoint("locked", "custom/fast", "script", "low")
        with self.assertRaises(SecurityError):
            self.state.remove_endpoint("locked", "local/fast")
        with self.assertRaises(SecurityError):
            self.state.set_role_backend("lead", "local/fast", project_id="locked")
        with self.assertRaises(SecurityError):
            self.state.set_skill_enabled("deploy", True, project_id="locked")

    def test_get_employees_by_role(self):
        """get_employees_by_role should filter by role field."""
        self.state.register_employee("e1", "Alice", role="scout")
        self.state.register_employee("e2", "Bob", role="lead")
        self.state.register_employee("e3", "Charlie", role="scout")
        scouts = self.state.get_employees_by_role("scout")
        leads = self.state.get_employees_by_role("lead")
        self.assertEqual(len(scouts), 2)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["name"], "Bob")


if __name__ == "__main__":
    unittest.main()
