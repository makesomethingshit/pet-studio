"""Tests for alba security level enforcement."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from alba.security import (
    SecurityError,
    check_security,
)
from alba.state import TeamState


class TestSecurityLevel(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)
        self.state.register_project("proj-A", "Project A")
        self.state.register_project("proj-B", "Project B", security_level=2)
        self.state.register_project("proj-C", "Project C", security_level=3)

    def tearDown(self) -> None:
        Path(self.tmp.name).unlink(missing_ok=True)

    # --- L0 ALLOW ---

    def test_l0_allows_all_actions(self) -> None:
        self.state.register_project("proj-L0", "L0 Project", security_level=0)
        result = check_security("proj-L0", "deploy", self.state)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["level"], 0)

    # --- L1 WARN (default) ---

    def test_l1_allows_low_risk(self) -> None:
        result = check_security("proj-A", "state.read", self.state)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["risk"], 0)

    def test_l1_warns_but_allows_moderate_risk(self) -> None:
        result = check_security("proj-A", "preset.import", self.state)
        self.assertTrue(result["allowed"])
        self.assertIn("WARN", result["reason"])

    def test_l1_allows_critical_risk_with_warning(self) -> None:
        result = check_security("proj-A", "deploy", self.state)
        self.assertTrue(result["allowed"])

    # --- L2 ASK ---

    def test_l2_allows_low_risk(self) -> None:
        result = check_security("proj-B", "state.read", self.state)
        self.assertTrue(result["allowed"])

    def test_l2_allows_moderate_risk(self) -> None:
        result = check_security("proj-B", "preset.import", self.state)
        self.assertTrue(result["allowed"])

    def test_l2_blocks_critical_risk(self) -> None:
        with self.assertRaises(SecurityError):
            check_security("proj-B", "project.delete", self.state)

    def test_l2_blocks_deploy(self) -> None:
        with self.assertRaises(SecurityError):
            check_security("proj-B", "deploy", self.state)

    # --- L3 DENY ---

    def test_l3_blocks_all_risky_actions(self) -> None:
        with self.assertRaises(SecurityError):
            check_security("proj-C", "preset.import", self.state)

    def test_l3_allows_only_safe_actions(self) -> None:
        result = check_security("proj-C", "state.read", self.state)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["risk"], 0)

    # --- Edge cases ---

    def test_unknown_project_returns_not_found(self) -> None:
        result = check_security("nonexistent", "state.read", self.state)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["level"], -1)

    def test_default_security_level_is_warn(self) -> None:
        project = self.state.get_project("proj-A")
        self.assertEqual(project.get("securityLevel"), 1)

    def test_security_error_message(self) -> None:
        with self.assertRaises(SecurityError) as ctx:
            check_security("proj-C", "deploy", self.state)
        self.assertIn("L3", str(ctx.exception))
        self.assertIn("deploy", str(ctx.exception))


class TestActionRiskLevels(unittest.TestCase):
    def test_safe_actions_are_risk_zero(self) -> None:
        from alba.security import ACTION_RISK

        self.assertEqual(ACTION_RISK["state.read"], 0)
        self.assertEqual(ACTION_RISK["state.write"], 0)
        self.assertEqual(ACTION_RISK["preset.export"], 0)

    def test_moderate_actions_are_risk_one(self) -> None:
        from alba.security import ACTION_RISK

        self.assertEqual(ACTION_RISK["preset.import"], 1)
        self.assertEqual(ACTION_RISK["layout.reset"], 1)

    def test_critical_actions_are_risk_three(self) -> None:
        from alba.security import ACTION_RISK

        self.assertEqual(ACTION_RISK["project.delete"], 3)
        self.assertEqual(ACTION_RISK["team.reconfigure"], 3)
        self.assertEqual(ACTION_RISK["deploy"], 3)
