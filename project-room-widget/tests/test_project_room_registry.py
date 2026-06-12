from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WIDGET_DIR = ROOT / "project-room-widget"
WIDGET_SCRIPT = WIDGET_DIR / "project_room_widget.py"
STATE_SCRIPT = WIDGET_DIR / "set_project_state.py"
ADAPTER_SCRIPT = WIDGET_DIR / "codex_state_adapter.py"
ACTIVE_SCRIPT = WIDGET_DIR / "set_active_project.py"
DEMO_KIT = ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "project-room.json"
if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class ProjectRoomSceneTests(unittest.TestCase):
    def load_demo_kit(self) -> dict:
        return json.loads(DEMO_KIT.read_text(encoding="utf-8"))

    def test_scene_entities_preserve_independent_layer_controls(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        entities = scene_entities_from_kit(kit)
        by_id = {entity.id: entity for entity in entities}

        self.assertEqual([entity.id for entity in entities], ["room", "desk", "helper-reviewer", "main-owner", "book-stack"])
        self.assertTrue(by_id["room"].locked)
        self.assertFalse(by_id["room"].draggable)
        self.assertTrue(by_id["desk"].draggable)
        self.assertFalse(by_id["desk"].locked)
        self.assertEqual(by_id["desk"].placement, "behindPet")
        self.assertEqual(by_id["book-stack"].placement, "foreground")

    def test_project_layout_overrides_entity_anchor_without_changing_kit(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        original_anchor = dict(kit["anchors"]["desk"])
        layout = {"anchors": {"desk": {"x": 260, "y": 210}}}

        entities = scene_entities_from_kit(kit, layout)
        desk = next(entity for entity in entities if entity.id == "desk")

        self.assertEqual(desk.anchor, {"x": 260, "y": 210})
        self.assertEqual(kit["anchors"]["desk"], original_anchor)

    def test_project_layout_file_round_trips_entity_anchor(self) -> None:
        from project_room_scene import load_project_layout, save_project_anchor

        with tempfile.TemporaryDirectory() as tmp:
            layout_file = Path(tmp) / "project-room-layouts.json"

            save_project_anchor(layout_file, "gakju-demo", "desk", {"x": 260, "y": 210})
            layout = load_project_layout(layout_file, "gakju-demo")

            self.assertEqual(layout["anchors"]["desk"], {"x": 260, "y": 210})

    def test_project_layout_reset_removes_saved_entity_anchors(self) -> None:
        from project_room_scene import load_project_layout, reset_project_layout, save_project_anchor

        with tempfile.TemporaryDirectory() as tmp:
            layout_file = Path(tmp) / "project-room-layouts.json"
            save_project_anchor(layout_file, "gakju-demo", "desk", {"x": 260, "y": 210})

            reset_project_layout(layout_file, "gakju-demo")
            layout = load_project_layout(layout_file, "gakju-demo")

            self.assertEqual(layout["anchors"], {})

    def test_project_window_file_round_trips_position_and_scale(self) -> None:
        from project_room_scene import load_project_window, save_project_window

        with tempfile.TemporaryDirectory() as tmp:
            window_file = Path(tmp) / "project-room-window.json"

            save_project_window(window_file, "gakju-demo", {"x": 120, "y": 340, "scale": 1.25})
            window = load_project_window(window_file, "gakju-demo")

            self.assertEqual(window, {"x": 120, "y": 340, "scale": 1.25})

    def test_bubble_text_prefers_state_message_and_uses_state_defaults(self) -> None:
        from project_room_scene import bubble_text_for_state

        self.assertEqual(bubble_text_for_state("running", "building room"), "building room")
        self.assertEqual(bubble_text_for_state("blocked", ""), "Need input")
        self.assertEqual(bubble_text_for_state("done", None), "Done")
        self.assertIsNone(bubble_text_for_state("idle", None, enabled=False))

    def test_bubble_text_normalizes_and_truncates_long_messages(self) -> None:
        from project_room_scene import MAX_BUBBLE_TEXT_LENGTH, bubble_text_for_state

        message = "  Waiting\n\non   approval for the very long integration check before the widget can continue safely  "

        text = bubble_text_for_state("blocked", message)

        self.assertIsNotNone(text)
        assert text is not None
        self.assertLessEqual(len(text), MAX_BUBBLE_TEXT_LENGTH)
        self.assertTrue(text.endswith("..."))
        self.assertNotIn("\n", text)
        self.assertNotIn("  ", text)

    def test_context_menu_labels_keep_close_as_explicit_action(self) -> None:
        from project_room_scene import context_menu_labels

        labels = context_menu_labels(project_id="gakju-demo")

        self.assertEqual(labels, ("Cycle state", "Reset layout", "Larger", "Smaller", "Reset size", "Hide bubble", "Close"))
        self.assertNotEqual(labels[0], "Close")


class ProjectRoomRegistryTests(unittest.TestCase):
    def make_config(self, path: Path, **overrides: object) -> Path:
        project = {
            "projectId": "gakju-demo",
            "displayName": "Gakju Demo",
            "kitPath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit"),
            "petPackagePath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "pets" / "main-owner"),
            "defaultState": "idle",
            "theme": "quiet archive nook",
            "enabled": True,
        }
        project.update(overrides)
        write_json(path, {"schemaVersion": 1, "projects": [project]})
        return path

    def test_selects_enabled_project_and_resolves_kit_path(self) -> None:
        from project_room_registry import select_project

        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "projects.json")

            project = select_project(config, "gakju-demo")

            self.assertEqual(project.project_id, "gakju-demo")
            self.assertEqual(project.display_name, "Gakju Demo")
            self.assertTrue(project.kit_manifest.exists())
            self.assertEqual(project.default_state, "idle")

    def test_rejects_disabled_unknown_and_missing_kit_projects(self) -> None:
        from project_room_registry import ProjectRegistryError, select_project

        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "projects.json", enabled=False)
            with self.assertRaisesRegex(ProjectRegistryError, "disabled"):
                select_project(config, "gakju-demo")

            missing_config = self.make_config(Path(tmp) / "missing.json", kitPath="missing-kit")
            with self.assertRaisesRegex(ProjectRegistryError, "Project Room Kit manifest not found"):
                select_project(missing_config, "gakju-demo")

            with self.assertRaisesRegex(ProjectRegistryError, "Unknown project id"):
                select_project(config, "nope")

    def test_state_file_maps_external_states_to_widget_rows(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            write_json(
                state_file,
                {
                    "projectId": "gakju-demo",
                    "state": "done",
                    "message": "done",
                    "updatedAt": "2026-06-12T00:00:00Z",
                },
            )

            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "jumping")

            write_json(state_file, {"projectId": "other", "state": "failed"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "idle")

            write_json(state_file, {"projectId": "gakju-demo", "state": "blocked"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "failed")

            write_json(state_file, {"projectId": "gakju-demo", "state": "handoff"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "review")

    def test_widget_cli_lists_and_renders_project_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json")
            output = work / "render.png"

            listed = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--list-projects",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr + listed.stdout)
            self.assertIn("gakju-demo", listed.stdout)

            rendered = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--project-id",
                    "gakju-demo",
                    "--layout-file",
                    str(work / "project-room-layouts.json"),
                    "--window-file",
                    str(work / "project-room-window.json"),
                    "--render-project-once",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr + rendered.stdout)
            self.assertTrue(output.exists())

            state_output = work / "render-done.png"
            rendered_done = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--project-id",
                    "gakju-demo",
                    "--state",
                    "done",
                    "--render-project-once",
                    str(state_output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered_done.returncode, 0, rendered_done.stderr + rendered_done.stdout)
            self.assertIn('"state": "jumping"', rendered_done.stdout)

    def test_infers_enabled_project_from_workspace_path(self) -> None:
        from project_room_registry import ProjectRegistryError, infer_project_for_workspace

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            workspace = work / "workspace"
            child = workspace / "src" / "feature"
            child.mkdir(parents=True)
            config = self.make_config(work / "projects.json", workspacePaths=[str(workspace)])

            project = infer_project_for_workspace(config, workspace)
            nested_project = infer_project_for_workspace(config, child)

            self.assertEqual(project.project_id, "gakju-demo")
            self.assertEqual(nested_project.project_id, "gakju-demo")

            disabled = self.make_config(work / "disabled.json", workspacePaths=[str(workspace)], enabled=False)
            with self.assertRaisesRegex(ProjectRegistryError, "Could not infer project id from workspace"):
                infer_project_for_workspace(disabled, workspace)

            missing = self.make_config(work / "missing-workspace.json", workspacePaths=[str(work / "other")])
            with self.assertRaisesRegex(ProjectRegistryError, "Could not infer project id from workspace"):
                infer_project_for_workspace(missing, workspace)

    def test_workspace_inference_prefers_longest_match_and_rejects_ambiguous_matches(self) -> None:
        from project_room_registry import ProjectRegistryError, infer_project_for_workspace

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            parent = work / "workspace"
            nested = parent / "nested"
            nested.mkdir(parents=True)
            config = work / "projects.json"
            base_project = {
                "displayName": "Demo",
                "kitPath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit"),
                "petPackagePath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "pets" / "main-owner"),
                "defaultState": "idle",
                "theme": "quiet archive nook",
                "enabled": True,
            }
            write_json(
                config,
                {
                    "schemaVersion": 1,
                    "projects": [
                        {"projectId": "parent", **base_project, "workspacePaths": [str(parent)]},
                        {"projectId": "nested", **base_project, "workspacePaths": [str(nested)]},
                    ],
                },
            )

            self.assertEqual(infer_project_for_workspace(config, nested).project_id, "nested")

            ambiguous = work / "ambiguous.json"
            write_json(
                ambiguous,
                {
                    "schemaVersion": 1,
                    "projects": [
                        {"projectId": "first", **base_project, "workspacePaths": [str(parent)]},
                        {"projectId": "second", **base_project, "workspacePaths": [str(parent)]},
                    ],
                },
            )
            with self.assertRaisesRegex(ProjectRegistryError, "Ambiguous workspace project match"):
                infer_project_for_workspace(ambiguous, parent)

    def test_set_project_state_cli_writes_external_state_bridge_file(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATE_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--project-id",
                    "gakju-demo",
                    "--state",
                    "blocked",
                    "--message",
                    "Waiting on review notes",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "blocked")
            self.assertEqual(data["message"], "Waiting on review notes")
            self.assertIn("updatedAt", data)
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "failed")

    def test_codex_state_adapter_maps_events_to_bridge_states(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            cases = [
                ("start", "running", "running"),
                ("block", "blocked", "failed"),
                ("done", "done", "jumping"),
            ]
            for event, stored_state, widget_state in cases:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ADAPTER_SCRIPT),
                        "--state-file",
                        str(state_file),
                        "--project-id",
                        "gakju-demo",
                        "--event",
                        event,
                        "--message",
                        f"event {event}",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                data = json.loads(state_file.read_text(encoding="utf-8"))
                self.assertEqual(data["projectId"], "gakju-demo")
                self.assertEqual(data["state"], stored_state)
                self.assertEqual(data["message"], f"event {event}")
                self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), widget_state)

    def test_codex_state_adapter_infers_project_from_workspace(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            workspace = work / "workspace"
            workspace.mkdir()
            config = self.make_config(work / "projects.json", workspacePaths=[str(workspace)])
            state_file = work / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--cwd",
                    str(workspace),
                    "--event",
                    "start",
                    "--message",
                    "inferred start",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "running")
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "running")

    def test_codex_state_adapter_project_id_overrides_workspace_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            workspace = work / "workspace"
            workspace.mkdir()
            config = self.make_config(work / "projects.json", workspacePaths=[str(workspace)])
            state_file = work / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--cwd",
                    str(work / "unmatched"),
                    "--project-id",
                    "manual-project",
                    "--event",
                    "done",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "manual-project")
            self.assertEqual(data["state"], "done")

    def test_codex_state_adapter_accepts_json_event_payload(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            state_file = work / "project-room-state.json"
            event_file = work / "event.json"
            write_json(
                event_file,
                {
                    "event": "block",
                    "message": "Waiting on approval",
                    "projectId": "gakju-demo",
                    "updatedAt": "2026-06-13T00:00:00Z",
                    "threadId": "thread-local",
                    "worktreeId": "worktree-local",
                },
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--event-json",
                    str(event_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "blocked")
            self.assertEqual(data["message"], "Waiting on approval")
            self.assertEqual(data["updatedAt"], "2026-06-13T00:00:00Z")
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "failed")

    def test_codex_state_adapter_accepts_stdin_event_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            state_file = work / "project-room-state.json"
            payload = json.dumps({"event": "done", "message": "Finished", "projectId": "gakju-demo"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--event-json",
                    "-",
                ],
                cwd=ROOT,
                input=payload,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "done")

    def test_codex_state_adapter_active_project_resolves_workspace_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            workspace = work / "workspace"
            workspace.mkdir()
            state_file = work / "project-room-state.json"
            active_file = work / "project-room-active.json"
            config = work / "projects.json"
            base_project = {
                "displayName": "Demo",
                "kitPath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit"),
                "petPackagePath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "pets" / "main-owner"),
                "defaultState": "idle",
                "theme": "quiet archive nook",
                "enabled": True,
                "workspacePaths": [str(workspace)],
            }
            write_json(
                config,
                {
                    "schemaVersion": 1,
                    "projects": [
                        {"projectId": "first", **base_project},
                        {"projectId": "second", **base_project},
                    ],
                },
            )
            write_json(active_file, {"schemaVersion": 1, "projectId": "second", "workspacePath": str(workspace)})

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--active-project-file",
                    str(active_file),
                    "--cwd",
                    str(workspace),
                    "--event",
                    "start",
                    "--message",
                    "Pinned project",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "second")
            self.assertEqual(data["state"], "running")

    def test_codex_state_adapter_payload_project_id_overrides_active_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            state_file = work / "project-room-state.json"
            active_file = work / "project-room-active.json"
            write_json(active_file, {"schemaVersion": 1, "projectId": "active-project"})
            payload = json.dumps({"event": "review", "message": "Manual override", "projectId": "payload-project"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--active-project-file",
                    str(active_file),
                    "--event-json",
                    "-",
                ],
                cwd=ROOT,
                input=payload,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "payload-project")
            self.assertEqual(data["state"], "review")

    def test_codex_state_adapter_rejects_unknown_active_project_without_writing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json")
            state_file = work / "project-room-state.json"
            active_file = work / "project-room-active.json"
            write_json(active_file, {"schemaVersion": 1, "projectId": "missing"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--active-project-file",
                    str(active_file),
                    "--event",
                    "start",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unknown project id", result.stderr + result.stdout)
            self.assertFalse(state_file.exists())

    def test_codex_state_adapter_rejects_disabled_active_project_without_writing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json", enabled=False)
            state_file = work / "project-room-state.json"
            active_file = work / "project-room-active.json"
            write_json(active_file, {"schemaVersion": 1, "projectId": "gakju-demo"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--active-project-file",
                    str(active_file),
                    "--event",
                    "start",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("disabled", result.stderr + result.stdout)
            self.assertFalse(state_file.exists())

    def test_set_active_project_cli_writes_enabled_project_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json")
            active_file = work / "project-room-active.json"
            workspace = work / "workspace"
            workspace.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(ACTIVE_SCRIPT),
                    "--config",
                    str(config),
                    "--active-project-file",
                    str(active_file),
                    "--project-id",
                    "gakju-demo",
                    "--cwd",
                    str(workspace),
                    "--updated-at",
                    "2026-06-13T00:00:00Z",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(active_file.read_text(encoding="utf-8"))
            self.assertEqual(data["schemaVersion"], 1)
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["workspacePath"], str(workspace.resolve()))
            self.assertEqual(data["updatedAt"], "2026-06-13T00:00:00Z")

    def test_codex_state_adapter_reports_workspace_inference_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json", workspacePaths=[str(work / "other")])
            state_file = work / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--config",
                    str(config),
                    "--state-file",
                    str(state_file),
                    "--cwd",
                    str(work / "unmatched"),
                    "--event",
                    "start",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Could not infer project id from workspace", result.stderr + result.stdout)
            self.assertFalse(state_file.exists())

    def test_codex_state_adapter_rejects_unknown_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--project-id",
                    "gakju-demo",
                    "--event",
                    "mystery",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported Codex event", result.stderr + result.stdout)
            self.assertFalse(state_file.exists())


if __name__ == "__main__":
    unittest.main()
