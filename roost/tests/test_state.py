"""Tests for roost state manager."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roost.state import TEAM_STATE_VERSION, TeamState


class TestTeamState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state = TeamState(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_default_state(self):
        self.assertEqual(self.state._data["version"], TEAM_STATE_VERSION)
        self.assertEqual(self.state.roost_status, "idle")
        self.assertEqual(self.state.roost_backend, "script")

    def test_team_state_schema_example_tracks_model_contract(self):
        schema_path = Path(__file__).resolve().parents[1] / "team_state.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        for key in (
            "trust",
            "approvals",
            "endpoints",
            "model_profiles",
            "active_model_profile",
            "role_model_profiles",
            "role_backends",
            "skills",
        ):
            self.assertIn(key, schema)

        self.assertEqual(schema["version"], TEAM_STATE_VERSION)
        self.assertEqual(schema["active_model_profile"], self.state.get_active_model_profile_id())
        self.assertEqual(set(schema["model_profiles"]), {profile["id"] for profile in self.state.list_model_profiles()})
        self.assertEqual(schema["role_model_profiles"], {"scout": "local/default", "coordinator": "openrouter/fast"})
        self.assertEqual(
            schema["role_backends"],
            {"scout": "local/fast", "coordinator": "remote/sota", "lead": "remote/sota"},
        )

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

    def test_remove_roost_queue_item(self):
        self.state.enqueue_roost({"type": "first"})
        self.state.enqueue_roost({"type": "second"})

        removed = self.state.remove_roost_queue_item(1)

        self.assertEqual(removed["type"], "second")
        self.assertEqual([item["type"] for item in self.state.get_roost_queue()], ["first"])
        self.assertIsNone(self.state.remove_roost_queue_item(4))

    def test_route_roost_queue_item_to_project(self):
        self.state.register_project("test-proj")
        self.state.enqueue_roost({"type": "scan", "path": "README.md"})
        self.state.enqueue_roost({"type": "review"})

        routed = self.state.route_roost_queue_item_to_project(0, "test-proj")

        self.assertEqual(routed["type"], "scan")
        self.assertEqual(routed["task"], "scan")
        self.assertEqual(routed["source"], "roost")
        self.assertEqual(routed["status"], "waiting")
        self.assertIn("routedAt", routed)
        self.assertEqual([item["type"] for item in self.state.get_roost_queue()], ["review"])
        self.assertEqual([item["type"] for item in self.state.get_project_queue("test-proj")], ["scan"])

    def test_route_roost_queue_item_to_missing_project_keeps_queue(self):
        self.state.enqueue_roost({"type": "scan"})

        routed = self.state.route_roost_queue_item_to_project(0, "missing-proj")

        self.assertIsNone(routed)
        self.assertEqual([item["type"] for item in self.state.get_roost_queue()], ["scan"])

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

    def test_update_project_queue_item_assigns_and_changes_status(self):
        self.state.register_project("test-proj")
        self.state.enqueue_project("test-proj", {"task": "lint"})

        updated = self.state.update_project_queue_item(
            "test-proj",
            0,
            {"assignedRole": "scout", "assignedEmployee": "emp-1", "status": "running"},
        )

        self.assertEqual(updated["assignedRole"], "scout")
        self.assertEqual(updated["assignedEmployee"], "emp-1")
        self.assertEqual(updated["status"], "running")
        self.assertIn("updatedAt", updated)
        self.assertIsNone(self.state.update_project_queue_item("test-proj", 5, {"status": "done"}))

    def test_update_project_queue_item_can_clear_assignment(self):
        self.state.register_project("test-proj")
        self.state.enqueue_project("test-proj", {"task": "lint", "assignedRole": "lead"})

        updated = self.state.update_project_queue_item("test-proj", 0, {"assignedRole": None})

        self.assertNotIn("assignedRole", updated)

    def test_project_queue_clear_removes_tasks(self):
        self.state.register_project("test-proj")
        self.state.enqueue_project("test-proj", {"task": "lint"})
        self.state.enqueue_project("test-proj", {"task": "review"})

        cleared = self.state.clear_project_queue("test-proj")

        self.assertEqual(cleared, 2)
        self.assertEqual(self.state.get_project_queue("test-proj"), [])

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
        """Default role_backends should map scout to script and coordinator/lead to hermes."""
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

    def test_active_model_profile_round_trips(self):
        self.assertEqual(self.state.get_active_model_profile_id(), "openrouter/sota")
        self.assertEqual(
            [profile["tier"] for profile in self.state.list_model_profiles()[:5]],
            ["closed", "closed", "open-sota", "local", "value"],
        )

        self.state.set_active_model_profile(None, "openrouter/fast")
        profile = self.state.get_active_model_profile()

        self.assertEqual(profile["id"], "openrouter/fast")
        self.assertEqual(profile["provider"], "openrouter")
        self.assertEqual(profile["model"], "fast")
        self.assertEqual(profile["tier"], "value")

    def test_role_model_plan_defaults_save_credits(self):
        plan = {item["role"]: item for item in self.state.list_role_model_plan()}

        self.assertEqual(plan["scout"]["profile"]["id"], "local/default")
        self.assertEqual(plan["scout"]["endpoint"], "local/default")
        self.assertEqual(plan["coordinator"]["profile"]["id"], "openrouter/fast")
        self.assertEqual(plan["coordinator"]["endpoint"], "openrouter/fast")
        self.assertEqual(plan["lead"]["profile"]["id"], "openrouter/sota")
        self.assertEqual(plan["lead"]["endpoint"], "openrouter/sota")

    def test_team_model_savings_defaults_compare_against_lead_only(self):
        savings = self.state.estimate_team_model_savings()

        self.assertEqual(savings["baseline"], "lead-only")
        self.assertEqual(savings["baselineUnits"], 9)
        self.assertEqual(savings["planUnits"], 4)
        self.assertEqual(savings["savedUnits"], 5)
        self.assertEqual(savings["savedPercent"], 56)

    def test_lead_role_model_follows_active_profile_by_default(self):
        self.state.set_active_model_profile(None, "openrouter/cheap")

        self.assertEqual(self.state.get_role_model_profile("lead")["id"], "openrouter/cheap")
        self.assertEqual(self.state.get_role_model_profile("lead")["tier"], "free")
        self.assertEqual(self.state.get_role_model_profile("scout")["id"], "local/default")

    def test_lead_role_model_follows_active_profile_after_reload(self):
        self.state.set_active_model_profile(None, "openrouter/cheap")

        reloaded = TeamState(self.tmp.name)

        self.assertEqual(reloaded.get_role_model_profile("lead")["id"], "openrouter/cheap")
        self.assertEqual(reloaded.get_role_model_profile("scout")["id"], "local/default")

    def test_set_role_model_profile_persists_override(self):
        self.state.set_role_model_profile("coordinator", "openrouter/sota")

        self.assertEqual(self.state.get_role_model_profile("coordinator")["id"], "openrouter/sota")

    def test_role_backend_uses_model_profile_backend_without_endpoint_override(self):
        self.state.set_role_model_profile("coordinator", "local/default")

        self.assertEqual(self.state.resolve_role_backend("coordinator"), "script")

    def test_role_backend_explicit_endpoint_override_wins(self):
        self.state.set_role_backend("scout", "remote/sota")

        self.assertEqual(self.state.resolve_role_backend("scout"), "hermes")

    def test_role_model_plan_shows_explicit_endpoint_override(self):
        self.state.set_role_backend("scout", "remote/sota")

        plan = {item["role"]: item for item in self.state.list_role_model_plan()}

        self.assertEqual(plan["scout"]["endpoint"], "remote/sota")
        self.assertEqual(plan["scout"]["backend"], "hermes")

    def test_role_model_plan_shows_model_profile_route_without_endpoint_override(self):
        self.state.set_role_model_profile("scout", "openrouter/fast")

        plan = {item["role"]: item for item in self.state.list_role_model_plan()}

        self.assertEqual(plan["scout"]["profile"]["id"], "openrouter/fast")
        self.assertEqual(plan["scout"]["endpoint"], "openrouter/fast")
        self.assertEqual(plan["scout"]["backend"], "hermes")

    def test_clear_role_model_profile_restores_team_defaults(self):
        self.state.set_active_model_profile(None, "openrouter/cheap")
        self.state.set_role_model_profile("lead", "local/default")
        self.state.set_role_model_profile("scout", "openrouter/fast")

        self.assertTrue(self.state.clear_role_model_profile("lead"))
        self.assertTrue(self.state.clear_role_model_profile("scout"))

        self.assertEqual(self.state.get_role_model_profile("lead")["id"], "openrouter/cheap")
        self.assertEqual(self.state.get_role_model_profile("scout")["id"], "local/default")

    def test_clear_role_model_profile_returns_false_without_override(self):
        self.assertFalse(self.state.clear_role_model_profile("lead"))

    def test_apply_team_model_preset_sets_all_roles(self):
        self.state.apply_team_model_preset("all-local")

        plan = {item["role"]: item["profile"]["id"] for item in self.state.list_role_model_plan()}

        self.assertEqual(self.state.get_team_model_preset_id(), "all-local")
        self.assertEqual(plan["scout"], "local/default")
        self.assertEqual(plan["coordinator"], "local/default")
        self.assertEqual(plan["lead"], "local/default")

    def test_save_credits_preset_keeps_lead_on_active_profile(self):
        self.state.set_active_model_profile(None, "openrouter/cheap")
        self.state.set_role_model_profile("lead", "local/default")

        self.state.apply_team_model_preset("save-credits")

        plan = {item["role"]: item["profile"]["id"] for item in self.state.list_role_model_plan()}
        self.assertEqual(self.state.get_team_model_preset_id(), "save-credits")
        self.assertEqual(plan["scout"], "local/default")
        self.assertEqual(plan["coordinator"], "openrouter/fast")
        self.assertEqual(plan["lead"], "openrouter/cheap")

    def test_team_model_preset_aliases(self):
        self.state.apply_team_model_preset("value")

        plan = {item["role"]: item["profile"]["id"] for item in self.state.list_role_model_plan()}

        self.assertEqual(self.state.get_team_model_preset_id(), "all-value")
        self.assertEqual(plan["scout"], "openrouter/fast")
        self.assertEqual(plan["coordinator"], "openrouter/fast")
        self.assertEqual(plan["lead"], "openrouter/fast")

    def test_team_model_preset_reports_custom(self):
        self.state.set_role_model_profile("scout", "openrouter/sota")

        self.assertEqual(self.state.get_team_model_preset_id(), "custom")

    def test_unknown_team_model_preset_rejected(self):
        with self.assertRaises(ValueError):
            self.state.apply_team_model_preset("missing")

    def test_unknown_model_profile_rejected(self):
        with self.assertRaises(ValueError):
            self.state.set_active_model_profile(None, "missing/profile")

    def test_custom_model_profile_round_trips(self):
        self.state.set_model_profile(
            None,
            "openrouter/claude",
            "hermes",
            "openrouter",
            "anthropic/claude-3.5-sonnet",
            "high",
            "closed",
        )
        self.state.set_active_model_profile(None, "openrouter/claude")

        profile = self.state.get_active_model_profile()

        self.assertEqual(profile["id"], "openrouter/claude")
        self.assertEqual(profile["backend"], "hermes")
        self.assertEqual(profile["provider"], "openrouter")
        self.assertEqual(profile["model"], "anthropic/claude-3.5-sonnet")
        self.assertEqual(profile["tier"], "closed")

    def test_model_profile_requires_provider_and_model(self):
        with self.assertRaises(ValueError):
            self.state.set_model_profile(None, "bad/profile", "hermes", "", "model", "high")
        with self.assertRaises(ValueError):
            self.state.set_model_profile(None, "bad/profile", "hermes", "openrouter", "", "high")

    def test_active_model_profile_cannot_be_removed(self):
        with self.assertRaises(ValueError):
            self.state.remove_model_profile(None, "openrouter/sota")

    def test_model_profile_can_be_removed(self):
        self.state.set_model_profile(None, "openrouter/temp", "hermes", "openrouter", "temp/model", "low")

        self.assertTrue(self.state.remove_model_profile(None, "openrouter/temp"))
        self.assertFalse(self.state.remove_model_profile(None, "openrouter/temp"))

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
        with self.assertRaises(SecurityError):
            self.state.set_active_model_profile("locked", "openrouter/fast")
        with self.assertRaises(SecurityError):
            self.state.set_model_profile("locked", "custom/model", "hermes", "openrouter", "custom", "high")
        with self.assertRaises(SecurityError):
            self.state.remove_model_profile("locked", "openrouter/fast")
        with self.assertRaises(SecurityError):
            self.state.set_role_model_profile("scout", "openrouter/fast", project_id="locked")
        with self.assertRaises(SecurityError):
            self.state.clear_role_model_profile("scout", project_id="locked")
        with self.assertRaises(SecurityError):
            self.state.apply_team_model_preset("all-local", project_id="locked")

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
