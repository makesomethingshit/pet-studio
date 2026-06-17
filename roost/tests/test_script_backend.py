"""Tests for roost script backend — context-aware classification."""

from __future__ import annotations

import unittest

from roost.backend.script import ScriptBackend


class TestScriptBackend(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = ScriptBackend()

    # --- Keyword classification ---

    def test_error_keyword_is_high(self) -> None:
        event = {"type": "build", "status": "error", "message": "Build failed"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "high")

    def test_done_keyword_is_low(self) -> None:
        event = {"type": "build", "status": "done", "message": "Build complete"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "low")

    def test_unknown_is_normal(self) -> None:
        event = {"type": "info", "message": "Something happened"}
        result = self.backend.classify_event(event)
        self.assertEqual(result["classification"]["priority"], "normal")

    # --- Context adjustment ---

    def test_context_none_uses_keyword_only(self) -> None:
        event = {"type": "info", "message": "Something", "project_id": "p1"}
        result = self.backend.classify_event(event, context=None)
        self.assertEqual(result["classification"]["priority"], "normal")

    def test_context_empty_list_no_change(self) -> None:
        event = {"type": "info", "message": "Something", "project_id": "p1"}
        result = self.backend.classify_event(event, context=[])
        self.assertEqual(result["classification"]["priority"], "normal")

    def test_3_high_events_keeps_priority_high(self) -> None:
        context = [
            {"project_id": "p1", "priority": "high"},
            {"project_id": "p1", "priority": "high"},
            {"project_id": "p1", "priority": "high"},
        ]
        event = {"type": "info", "message": "no keyword", "project_id": "p1"}
        result = self.backend.classify_event(event, context=context)
        self.assertEqual(result["classification"]["priority"], "high")

    def test_2_high_events_does_not_change(self) -> None:
        context = [
            {"project_id": "p1", "priority": "high"},
            {"project_id": "p1", "priority": "high"},
        ]
        event = {"type": "info", "message": "no keyword", "project_id": "p1"}
        result = self.backend.classify_event(event, context=context)
        self.assertEqual(result["classification"]["priority"], "normal")

    def test_context_other_project_does_not_affect(self) -> None:
        context = [
            {"project_id": "p2", "priority": "high"},
            {"project_id": "p2", "priority": "high"},
            {"project_id": "p2", "priority": "high"},
        ]
        event = {"type": "info", "message": "no keyword", "project_id": "p1"}
        result = self.backend.classify_event(event, context=context)
        self.assertEqual(result["classification"]["priority"], "normal")

    # --- health_check ---

    def test_health_check_always_true(self) -> None:
        self.assertTrue(self.backend.health_check())

    # --- repr ---

    def test_repr(self) -> None:
        self.assertEqual(repr(self.backend), "<ScriptBackend name=script>")
