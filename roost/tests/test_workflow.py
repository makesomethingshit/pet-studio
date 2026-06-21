"""Mission workflow tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roost.state import TeamState


class MissionWorkflowTests(unittest.TestCase):
    def test_start_mission_workflow_creates_role_handoff_tasks(self) -> None:
        from roost.workflow import start_mission_workflow

        with tempfile.TemporaryDirectory() as tmp:
            state = TeamState(Path(tmp) / "team_state.json")
            state.register_project("demo", "Demo")

            with patch(
                "roost.workflow.dispatch",
                side_effect=[
                    {"classification": {"source": "scout", "priority": "normal"}},
                    {"classification": {"source": "coordinator", "priority": "normal"}},
                ],
            ) as dispatch:
                ok, message = start_mission_workflow(state, "demo", "Ship the room")

            self.assertTrue(ok)
            self.assertEqual(message, "Workflow ready: Scout -> Coordinator -> Lead")
            queue = state.get_project_queue("demo")
            self.assertEqual([task["workflowStep"] for task in queue], ["scout", "coordinator", "lead"])
            self.assertEqual([task["assignedRole"] for task in queue], ["scout", "coordinator", "lead"])
            self.assertEqual(queue[0]["task"], "Scout: Ship the room")
            self.assertEqual(queue[1]["parentTaskId"], queue[0]["id"])
            self.assertEqual(queue[1]["inputFrom"], queue[0]["dispatchMessage"])
            self.assertEqual(queue[2]["parentTaskId"], queue[1]["id"])
            self.assertEqual(queue[2]["status"], "waiting")
            self.assertEqual(queue[2]["dispatchMessage"], "Ready for Lead. Start manually.")
            self.assertEqual(dispatch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
