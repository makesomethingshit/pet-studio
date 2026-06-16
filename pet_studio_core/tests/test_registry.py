"""Tests for pet_studio_core.registry module."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pet_studio_core.registry import (
    DEFAULT_ACTIVE_PROJECT_FILE,
    DEFAULT_REGISTRY,
    DEFAULT_STATE_FILE,
    STATE_ALIASES,
    WIDGET_STATES,
    ProjectAssignment,
    ProjectRegistryError,
    init_core,
    normalize_state,
    path_contains,
    project_to_summary,
    read_active_project_id,
    read_project_state,
)


class TestNormalizeState(unittest.TestCase):
    """Test state normalization and aliases."""

    def test_direct_states_preserved(self):
        for state in WIDGET_STATES:
            self.assertEqual(normalize_state(state), state)

    def test_aliases_mapped(self):
        self.assertEqual(normalize_state("done"), "jumping")
        self.assertEqual(normalize_state("blocked"), "failed")
        self.assertEqual(normalize_state("handoff"), "review")

    def test_none_returns_idle(self):
        self.assertEqual(normalize_state(None), "idle")

    def test_empty_string_returns_idle(self):
        self.assertEqual(normalize_state(""), "idle")

    def test_whitespace_returns_idle(self):
        self.assertEqual(normalize_state("   "), "idle")

    def test_unknown_state_returns_fallback(self):
        self.assertEqual(normalize_state("nonexistent", "running"), "running")

    def test_unknown_state_unknown_fallback_returns_idle(self):
        self.assertEqual(normalize_state("nonexistent", "alsobad"), "idle")

    def test_case_sensitive(self):
        # States are case-sensitive; "Running" != "running"
        self.assertEqual(normalize_state("Running"), "idle")


class TestStateAliases(unittest.TestCase):
    """Test STATE_ALIASES constant."""

    def test_all_alias_targets_in_widget_states(self):
        for alias, target in STATE_ALIASES.items():
            self.assertIn(target, WIDGET_STATES, f"alias {alias}->{target} not in WIDGET_STATES")

    def test_widget_states_is_superset_of_alias_values(self):
        for _alias, target in STATE_ALIASES.items():
            self.assertIn(target, WIDGET_STATES)


class TestPathContains(unittest.TestCase):
    """Test path containment check."""

    def test_same_path(self):
        p = Path("/tmp/test")
        self.assertTrue(path_contains(p, p))

    def test_child_path(self):
        parent = Path("/tmp/test")
        child = Path("/tmp/test/sub/deep")
        self.assertTrue(path_contains(parent, child))

    def test_unrelated_paths(self):
        a = Path("/tmp/test")
        b = Path("/tmp/other")
        self.assertFalse(path_contains(a, b))

    def test_parent_not_contains_child_reverse(self):
        parent = Path("/tmp/test")
        child = Path("/tmp/test/sub")
        self.assertFalse(path_contains(child, parent))


class TestInitCore(unittest.TestCase):
    """Test init_core() path overrides."""

    def setUp(self):
        # Save originals
        self._orig_registry = Path(str(DEFAULT_REGISTRY))
        self._orig_state = Path(str(DEFAULT_STATE_FILE))
        self._orig_active = Path(str(DEFAULT_ACTIVE_PROJECT_FILE))
        self._orig_aliases = dict(STATE_ALIASES)
        self._orig_widget_states = set(WIDGET_STATES)

    def tearDown(self):
        # Restore originals
        init_core(
            registry_path=self._orig_registry,
            state_file=self._orig_state,
            active_project_file=self._orig_active,
            state_aliases=self._orig_aliases,
            widget_states=self._orig_widget_states,
        )

    def test_override_registry_path(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            custom = Path(f.name)
        try:
            init_core(registry_path=custom)
            from pet_studio_core.registry import DEFAULT_REGISTRY as reg

            self.assertEqual(reg, custom)
        finally:
            custom.unlink(missing_ok=True)

    def test_override_state_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            custom = Path(f.name)
        try:
            init_core(state_file=custom)
            from pet_studio_core.registry import DEFAULT_STATE_FILE as sf

            self.assertEqual(sf, custom)
        finally:
            custom.unlink(missing_ok=True)

    def test_override_active_project_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            custom = Path(f.name)
        try:
            init_core(active_project_file=custom)
            from pet_studio_core.registry import DEFAULT_ACTIVE_PROJECT_FILE as apf

            self.assertEqual(apf, custom)
        finally:
            custom.unlink(missing_ok=True)

    def test_override_widget_states(self):
        custom_states = {"idle", "running"}
        init_core(widget_states=custom_states)
        from pet_studio_core.registry import WIDGET_STATES as ws

        self.assertEqual(ws, custom_states)

    def test_override_state_aliases(self):
        custom_aliases = {"custom_done": "jumping"}
        init_core(state_aliases=custom_aliases)
        from pet_studio_core.registry import STATE_ALIASES as sa

        self.assertEqual(sa, custom_aliases)

    def test_none_keeps_existing(self):
        """Passing None should not change the current value."""
        from pet_studio_core.registry import DEFAULT_REGISTRY as original

        init_core(registry_path=None)
        from pet_studio_core.registry import DEFAULT_REGISTRY as reg

        self.assertEqual(reg, original)


class TestReadActiveProject(unittest.TestCase):
    """Test read_active_project_id()."""

    def test_missing_file_returns_none(self):
        result = read_active_project_id("/nonexistent/path/active.json")
        self.assertIsNone(result)

    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"projectId": "test-proj"}, f)
            path = Path(f.name)
        try:
            result = read_active_project_id(path)
            self.assertEqual(result, "test-proj")
        finally:
            path.unlink(missing_ok=True)

    def test_missing_project_id_key(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"other": "value"}, f)
            path = Path(f.name)
        try:
            result = read_active_project_id(path)
            self.assertIsNone(result)
        finally:
            path.unlink(missing_ok=True)

    def test_empty_project_id_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"projectId": ""}, f)
            path = Path(f.name)
        try:
            with self.assertRaises(ProjectRegistryError):
                read_active_project_id(path)
        finally:
            path.unlink(missing_ok=True)


class TestReadProjectState(unittest.TestCase):
    """Test read_project_state()."""

    def test_missing_file_returns_fallback(self):
        result = read_project_state("/nonexistent/state.json", "proj", "idle")
        self.assertEqual(result, "idle")

    def test_matching_project(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"projectId": "myproj", "state": "running"}, f)
            path = Path(f.name)
        try:
            result = read_project_state(path, "myproj", "idle")
            self.assertEqual(result, "running")
        finally:
            path.unlink(missing_ok=True)

    def test_mismatched_project_returns_fallback(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"projectId": "other", "state": "running"}, f)
            path = Path(f.name)
        try:
            result = read_project_state(path, "myproj", "idle")
            self.assertEqual(result, "idle")
        finally:
            path.unlink(missing_ok=True)


class TestProjectToSummary(unittest.TestCase):
    """Test project_to_summary()."""

    def test_summary_keys(self):
        assignment = ProjectAssignment(
            project_id="test",
            display_name="Test Project",
            kit_manifest=Path("/tmp/kit.json"),
            kit_dir=Path("/tmp"),
            pet_package_path=None,
            workspace_paths=(Path("/tmp/ws"),),
            default_state="idle",
            theme="cozy",
            enabled=True,
            raw={},
        )
        summary = project_to_summary(assignment)
        self.assertEqual(summary["projectId"], "test")
        self.assertEqual(summary["displayName"], "Test Project")
        self.assertEqual(summary["defaultState"], "idle")
        self.assertEqual(summary["theme"], "cozy")
        self.assertTrue(summary["enabled"])
        self.assertIsNone(summary["petPackagePath"])
        self.assertIsInstance(summary["workspacePaths"], list)
