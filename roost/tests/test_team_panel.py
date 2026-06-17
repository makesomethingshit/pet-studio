"""Tests for TeamRoomPanel logic (non-GUI).

We test the data-binding and state resolution paths by mocking tkinter.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from roost.state import TeamState


class TestTeamRoomPanelLogic(unittest.TestCase):
    """Test panel data resolution through TeamState."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)
        self.state.register_project("test-proj", "Test Project", security_level=2)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_panel_shows_pending_approvals(self):
        """Panel should display pending approval count."""
        self.state.add_approval_request("test-proj", "deploy")
        self.state.add_approval_request("test-proj", "layout.reset")
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 2)

    def test_panel_approve_resolves(self):
        """Approve button should resolve approval."""
        aid = self.state.add_approval_request("test-proj", "deploy")
        self.state.resolve_approval(aid, True)
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 0)

    def test_panel_reject_resolves(self):
        """Reject button should resolve approval."""
        aid = self.state.add_approval_request("test-proj", "deploy")
        self.state.resolve_approval(aid, False)
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 0)

    def test_panel_employee_list(self):
        """Panel should show default employees."""
        emps = self.state.get_employees()
        self.assertEqual(len(emps), 2)
        names = [e["name"] for e in emps]
        self.assertIn("Codex", names)
        self.assertIn("Claude", names)

    def test_panel_employee_status_change(self):
        """Panel should reflect employee status changes."""
        self.state.set_employee_status("emp-1", "running")
        emps = self.state.get_employees()
        codex = next(e for e in emps if e["id"] == "emp-1")
        self.assertEqual(codex["status"], "running")

    def test_panel_queue_count(self):
        """Panel should show roost queue count."""
        self.state.enqueue_roost({"type": "file_change", "path": "test.py"})
        self.state.enqueue_roost({"type": "build", "status": "pass"})
        queue = self.state.get_roost_queue()
        self.assertEqual(len(queue), 2)

    def test_panel_approval_trim_at_50(self):
        """Panel should handle approval trim at 50."""
        for i in range(55):
            self.state.add_approval_request("test-proj", f"action-{i}")
        approvals = self.state._data["approvals"]
        self.assertEqual(len(approvals), 50)

    def test_panel_security_l2_enqueues_approval(self):
        """L2 ASK action should auto-enqueue approval request."""
        from roost.security import SecurityError, check_security

        with self.assertRaises(SecurityError):
            check_security("test-proj", "deploy", self.state)
        pending = self.state.get_pending_approvals()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["action"], "deploy")

    def test_panel_state_persistence(self):
        """Panel state should persist across TeamState instances."""
        aid = self.state.add_approval_request("test-proj", "deploy")
        # Reload from disk
        state2 = TeamState(self.tmp.name)
        pending = state2.get_pending_approvals()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], aid)


if __name__ == "__main__":
    unittest.main()
