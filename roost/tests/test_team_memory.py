"""Tests for Roost team memory approval flow."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roost.packet import build_work_packet
from roost.state import TeamState
from roost.team_memory import (
    add_memory_candidate,
    approve_memory_candidate,
    list_memory_candidates,
    load_memory_context,
    reject_memory_candidate,
)


class TestTeamMemory(unittest.TestCase):
    def test_candidate_approval_promotes_team_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = add_memory_candidate(root, "Check release drift", scope="team", kind="rule")

            approved = approve_memory_candidate(root, candidate["id"])
            context = load_memory_context(root, project_id="pet-studio")

            self.assertEqual(approved["status"], "approved")
            self.assertEqual(context["team_memory"][0]["summary"], "Check release drift")
            self.assertEqual(context["project_culture"], [])

    def test_candidate_approval_promotes_project_culture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = add_memory_candidate(
                root,
                "Keep Codex as an optional adapter",
                scope="project",
                project_id="pet-studio",
                kind="preference",
            )

            approve_memory_candidate(root, candidate["id"])
            context = load_memory_context(root, project_id="pet-studio")

            self.assertEqual(context["team_memory"], [])
            self.assertEqual(context["project_culture"][0]["summary"], "Keep Codex as an optional adapter")

    def test_rejected_candidate_is_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = add_memory_candidate(root, "Noisy candidate")

            rejected = reject_memory_candidate(root, candidate["id"])
            candidates = list_memory_candidates(root)
            context = load_memory_context(root, project_id="pet-studio")

            self.assertEqual(rejected["status"], "rejected")
            self.assertEqual(candidates[0]["status"], "rejected")
            self.assertEqual(context["team_memory"], [])
            self.assertEqual(context["project_culture"], [])

    def test_log_event_collects_memory_candidate_next_to_team_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = TeamState(Path(tmp) / "team_state.json")
            state.register_project("pet-studio")

            state.log_event(
                "pet-studio",
                {
                    "type": "handoff",
                    "memoryCandidate": {
                        "summary": "Handoff should mention the next agent",
                        "scope": "project",
                        "kind": "lesson",
                        "evidence": ["handoff"],
                    },
                },
            )

            candidates = list_memory_candidates(Path(tmp))

            self.assertEqual(candidates[0]["projectId"], "pet-studio")
            self.assertEqual(candidates[0]["summary"], "Handoff should mention the next agent")

    def test_work_packet_includes_only_approved_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = TeamState(root / "team_state.json")
            state.register_project("pet-studio")
            team_candidate = add_memory_candidate(root, "Run boundary checks", scope="team")
            add_memory_candidate(root, "Pending noise", scope="team")
            project_candidate = add_memory_candidate(
                root,
                "Use local workroom wording",
                scope="project",
                project_id="pet-studio",
            )
            approve_memory_candidate(root, team_candidate["id"])
            approve_memory_candidate(root, project_candidate["id"])

            packet = build_work_packet("pet-studio", state)

            self.assertEqual([item["summary"] for item in packet["team_memory"]], ["Run boundary checks"])
            self.assertEqual([item["summary"] for item in packet["project_culture"]], ["Use local workroom wording"])
            self.assertNotIn("Pending noise", json.dumps(packet, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
