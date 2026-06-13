from __future__ import annotations

import json
import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
WIDGET_DIR = ROOT / "project-room-widget"
WIDGET_SCRIPT = WIDGET_DIR / "pet_studio_widget.py"
STATE_SCRIPT = WIDGET_DIR / "set_pet_studio_state.py"
ADAPTER_SCRIPT = WIDGET_DIR / "pet_studio_event_adapter.py"
HOOK_SCRIPT = WIDGET_DIR / "codex_pet_hook.py"
ACTIVE_SCRIPT = WIDGET_DIR / "set_active_pet_studio.py"
TOOLS_DIR = ROOT / "tools"
DEMO_KIT = ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "project-room.json"
README_SCREENSHOT = ROOT / "docs" / "images" / "gakju-widget-bubble-example.png"
if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def rgba_pixels(image: Image.Image):
    rgba = image.convert("RGBA")
    data = rgba.tobytes()
    for index in range(0, len(data), 4):
        yield data[index], data[index + 1], data[index + 2], data[index + 3]


class ProjectRoomSceneTests(unittest.TestCase):
    def load_demo_kit(self) -> dict:
        return json.loads(DEMO_KIT.read_text(encoding="utf-8"))

    def test_scene_entities_preserve_independent_layer_controls(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        entities = scene_entities_from_kit(kit)
        by_id = {entity.id: entity for entity in entities}

        self.assertEqual([entity.id for entity in entities], ["room", "desk", "main-owner", "book-stack", "helper-reviewer"])
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

    def test_project_layout_ignores_entity_anchor_outside_source_canvas(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        helper_layer = next(layer for layer in kit["layers"] if layer["id"] == "helper-reviewer")
        original_anchor = dict(kit["anchors"][helper_layer["anchor"]])
        layout = {"anchors": {"helper-reviewer": {"x": -1050, "y": 611}}}

        entities = scene_entities_from_kit(kit, layout)
        helper = next(entity for entity in entities if entity.id == "helper-reviewer")

        self.assertEqual(helper.anchor, original_anchor)

    def test_clamp_anchor_to_source_canvas_bounds_saved_drag_positions(self) -> None:
        from project_room_scene import clamp_anchor_to_source_canvas

        kit = self.load_demo_kit()

        self.assertEqual(clamp_anchor_to_source_canvas(kit, {"x": -1050, "y": 611}), {"x": 0, "y": 240})
        self.assertEqual(clamp_anchor_to_source_canvas(kit, {"x": 302, "y": 204}), {"x": 302, "y": 204})

    def test_project_layout_file_round_trips_entity_anchor(self) -> None:
        from project_room_scene import load_project_layout, save_project_anchor

        with tempfile.TemporaryDirectory() as tmp:
            layout_file = Path(tmp) / "project-room-layouts.json"

            save_project_anchor(layout_file, "gakju-demo", "desk", {"x": 260, "y": 210})
            layout = load_project_layout(layout_file, "gakju-demo")

            self.assertEqual(layout["anchors"]["desk"], {"x": 260, "y": 210})

    def test_project_layout_file_round_trips_entity_z_order(self) -> None:
        from project_room_scene import load_project_layout, save_project_z_order

        with tempfile.TemporaryDirectory() as tmp:
            layout_file = Path(tmp) / "project-room-layouts.json"

            save_project_z_order(layout_file, "gakju-demo", "desk", 27)
            layout = load_project_layout(layout_file, "gakju-demo")

            self.assertEqual(layout["zOrder"]["desk"], 27)

    def test_project_layout_z_order_overrides_entity_sorting_without_changing_kit(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        original_desk_z = next(layer for layer in kit["layers"] if layer["id"] == "desk")["z"]
        layout = {"anchors": {}, "zOrder": {"desk": 99}}

        entities = scene_entities_from_kit(kit, layout)
        desk = next(entity for entity in entities if entity.id == "desk")

        self.assertEqual(desk.z, 99)
        self.assertEqual(entities[-1].id, "desk")
        self.assertEqual(next(layer for layer in kit["layers"] if layer["id"] == "desk")["z"], original_desk_z)

    def test_scene_entities_read_layer_flip_x(self) -> None:
        from project_room_scene import scene_entities_from_kit

        kit = self.load_demo_kit()
        desk_layer = next(layer for layer in kit["layers"] if layer["id"] == "desk")
        desk_layer["flipX"] = True

        entities = scene_entities_from_kit(kit)
        desk = next(entity for entity in entities if entity.id == "desk")

        self.assertTrue(desk.flip_x)

    def test_public_demo_helper_pet_is_visible_only_in_review_states(self) -> None:
        from project_room_scene import scene_entities_from_kit, visible_scene_entities

        kit = self.load_demo_kit()
        entities = scene_entities_from_kit(kit)

        idle_ids = [entity.id for entity in visible_scene_entities(kit, entities, "idle")]
        review_ids = [entity.id for entity in visible_scene_entities(kit, entities, "review")]
        failed_ids = [entity.id for entity in visible_scene_entities(kit, entities, "failed")]

        self.assertNotIn("helper-reviewer", idle_ids)
        self.assertIn("helper-reviewer", review_ids)
        self.assertIn("helper-reviewer", failed_ids)

    def test_public_demo_review_render_contains_helper_pet_pixels(self) -> None:
        import project_room_widget

        kit = self.load_demo_kit()
        kit_without_helper = json.loads(json.dumps(kit))
        kit_without_helper["states"]["review"]["visibleLayers"] = [
            layer_id
            for layer_id in kit_without_helper["states"]["review"]["visibleLayers"]
            if layer_id != "helper-reviewer"
        ]
        layer_assets = project_room_widget.load_layer_assets(DEMO_KIT.parent, kit["layers"], [])

        with_helper = project_room_widget.build_source_frame(DEMO_KIT.parent, kit, "review", 0, layer_assets, [])
        without_helper = project_room_widget.build_source_frame(DEMO_KIT.parent, kit_without_helper, "review", 0, layer_assets, [])
        diff_pixels = sum(
            1
            for left, right in zip(rgba_pixels(with_helper), rgba_pixels(without_helper))
            if left != right
        )

        self.assertGreater(diff_pixels, 1000)

    def test_readme_screenshot_has_no_visible_magenta_chroma_key(self) -> None:
        with Image.open(README_SCREENSHOT) as image:
            rgba = image.convert("RGBA")
            visible_chroma = sum(
                1
                for red, green, blue, alpha in rgba_pixels(rgba)
                if alpha > 0 and red >= 220 and green <= 70 and blue >= 220
            )

        self.assertEqual(visible_chroma, 0)

    def test_widget_imports_local_room_kit_tools_before_installed_skill(self) -> None:
        import project_room_widget

        signature = inspect.signature(project_room_widget.scale_visible_layer)

        self.assertIn("flip_x", signature.parameters)
        self.assertEqual(Path(project_room_widget.scale_visible_layer.__code__.co_filename).resolve().parents[1], ROOT / "project-room-kit")

    def test_project_layout_reset_removes_saved_entity_anchors(self) -> None:
        from project_room_scene import load_project_layout, reset_project_layout, save_project_anchor, save_project_z_order

        with tempfile.TemporaryDirectory() as tmp:
            layout_file = Path(tmp) / "project-room-layouts.json"
            save_project_anchor(layout_file, "gakju-demo", "desk", {"x": 260, "y": 210})
            save_project_z_order(layout_file, "gakju-demo", "desk", 27)

            reset_project_layout(layout_file, "gakju-demo")
            layout = load_project_layout(layout_file, "gakju-demo")

            self.assertEqual(layout["anchors"], {})
            self.assertEqual(layout["zOrder"], {})

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

    def test_bubble_visual_style_uses_soft_room_palette(self) -> None:
        from project_room_scene import BUBBLE_STYLE

        self.assertEqual(BUBBLE_STYLE["fill"], "#fffaf1")
        self.assertEqual(BUBBLE_STYLE["outline"], "#7a6554")
        self.assertEqual(BUBBLE_STYLE["shadow"], "#d8c0a1")
        self.assertEqual(BUBBLE_STYLE["text"], "#2d241e")

    def test_rounded_rectangle_points_create_curved_bubble_body(self) -> None:
        from project_room_scene import rounded_rectangle_points

        points = rounded_rectangle_points(10, 20, 110, 70, 12, steps=5)

        self.assertGreater(len(points), 8)
        self.assertAlmostEqual(min(points[0::2]), 10)
        self.assertAlmostEqual(max(points[0::2]), 110)
        self.assertAlmostEqual(min(points[1::2]), 20)
        self.assertAlmostEqual(max(points[1::2]), 70)
        self.assertNotEqual(points, [10, 20, 110, 20, 110, 70, 10, 70])

    def test_bubble_style_prefers_kit_manifest_over_pet_sidecar_and_image(self) -> None:
        from project_room_scene import resolve_bubble_style

        with tempfile.TemporaryDirectory() as tmp:
            kit_dir = Path(tmp)
            pet_dir = kit_dir / "pets" / "main-owner"
            pet_dir.mkdir(parents=True)
            Image.new("RGBA", (8, 8), (20, 160, 120, 255)).save(pet_dir / "spritesheet.webp")
            write_json(pet_dir / "spritesheet.asset.json", {"bubbleStyle": {"fill": "#eeeeee", "outline": "#111111"}})
            kit = {
                "bubbleStyle": {"fill": "#fdf4d8", "outline": "#35524a", "shadow": "#c8a66a", "text": "#1b211f"},
                "layers": [{"id": "main-owner", "role": "mainPet", "path": "pets/main-owner/spritesheet.webp"}],
            }

            style = resolve_bubble_style(kit, kit_dir)

            self.assertEqual(style["fill"], "#fdf4d8")
            self.assertEqual(style["outline"], "#35524a")
            self.assertEqual(style["shadow"], "#c8a66a")
            self.assertEqual(style["text"], "#1b211f")

    def test_bubble_style_reads_main_pet_sidecar_when_manifest_has_no_style(self) -> None:
        from project_room_scene import resolve_bubble_style

        with tempfile.TemporaryDirectory() as tmp:
            kit_dir = Path(tmp)
            pet_dir = kit_dir / "pets" / "main-owner"
            pet_dir.mkdir(parents=True)
            Image.new("RGBA", (8, 8), (20, 160, 120, 255)).save(pet_dir / "spritesheet.webp")
            write_json(
                pet_dir / "spritesheet.asset.json",
                {"bubbleStyle": {"fill": "#e8fbf5", "outline": "#247667", "shadow": "#a5d4c9", "text": "#1d2d2a"}},
            )
            kit = {"layers": [{"id": "main-owner", "role": "mainPet", "path": "pets/main-owner/spritesheet.webp"}]}

            style = resolve_bubble_style(kit, kit_dir)

            self.assertEqual(style["fill"], "#e8fbf5")
            self.assertEqual(style["outline"], "#247667")
            self.assertEqual(style["shadow"], "#a5d4c9")
            self.assertEqual(style["text"], "#1d2d2a")

    def test_bubble_style_can_be_inferred_from_main_pet_pixels(self) -> None:
        from project_room_scene import BUBBLE_STYLE, resolve_bubble_style

        with tempfile.TemporaryDirectory() as tmp:
            kit_dir = Path(tmp)
            pet_dir = kit_dir / "pets" / "main-owner"
            pet_dir.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (80, 130, 170, 255)).save(pet_dir / "spritesheet.webp")
            kit = {"layers": [{"id": "main-owner", "role": "mainPet", "path": "pets/main-owner/spritesheet.webp"}]}

            style = resolve_bubble_style(kit, kit_dir)

            self.assertNotEqual(style["fill"], BUBBLE_STYLE["fill"])
            self.assertTrue(style["fill"].startswith("#"))
            self.assertTrue(style["outline"].startswith("#"))
            self.assertTrue(style["shadow"].startswith("#"))
            self.assertEqual(style["text"], BUBBLE_STYLE["text"])

    def test_context_menu_labels_keep_close_as_explicit_action(self) -> None:
        from project_room_scene import context_menu_labels

        labels = context_menu_labels(project_id="gakju-demo", entity_selected=True)

        self.assertEqual(
            labels,
            (
                "Cycle state",
                "Reset layout",
                "Bring forward",
                "Send backward",
                "Bring to front",
                "Send to back",
                "Larger",
                "Smaller",
                "Reset size",
                "Hide bubble",
                "Close",
            ),
        )
        self.assertNotEqual(labels[0], "Close")

    def test_sample_launchers_start_widget_without_console_python(self) -> None:
        for launcher in WIDGET_DIR.glob("run-*.bat"):
            with self.subTest(launcher=launcher.name):
                text = launcher.read_text(encoding="utf-8").lower()
                self.assertIn("pythonw", text)
                self.assertIn("start \"pet studio widget\"", text)
                self.assertNotIn("\\python.exe", text)


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
            with self.assertRaisesRegex(ProjectRegistryError, "Pet Studio kit manifest not found"):
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
                    "--active-project-file",
                    str(work / "missing-active.json"),
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
                    "--active-project-file",
                    str(work / "missing-active.json"),
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
                    "--active-project-file",
                    str(work / "missing-active.json"),
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

    def test_codex_pet_hook_user_prompt_updates_bubble_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            payload = json.dumps({"prompt": "Make the sub pet visible", "projectId": "gakju-demo"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook",
                    "user_prompt_submit",
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
            self.assertEqual(data["state"], "running")
            self.assertEqual(data["message"], "Working: Make the sub pet visible")

    def test_codex_pet_hook_stop_moves_bubble_to_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--project-id",
                    "gakju-demo",
                    "--hook",
                    "stop",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "review")
            self.assertEqual(data["message"], "Ready for review")


class PetStudioCodexIntegrationInstallerTests(unittest.TestCase):
    def test_installs_lifecycle_hooks_json_without_dropping_existing_hooks(self) -> None:
        from install_pet_studio_codex_integration import install_hooks_bridge

        with tempfile.TemporaryDirectory() as tmp:
            hooks_file = Path(tmp) / "hooks.json"
            write_json(
                hooks_file,
                {
                    "hooks": {
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python existing_stop.py",
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            result = install_hooks_bridge(hooks_file, dry_run=False)

            data = json.loads(hooks_file.read_text(encoding="utf-8"))
            self.assertIn("UserPromptSubmit", data["hooks"])
            self.assertIn("PreToolUse", data["hooks"])
            self.assertIn("PostToolUse", data["hooks"])
            self.assertIn("PreCompact", data["hooks"])
            self.assertIn("Stop", data["hooks"])
            stop_commands = [
                hook["command"]
                for group in data["hooks"]["Stop"]
                for hook in group["hooks"]
            ]
            self.assertIn("python existing_stop.py", stop_commands)
            self.assertTrue(any("codex_pet_hook.py" in command and "--hook stop" in command for command in stop_commands))
            prompt_hook = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]
            self.assertEqual(prompt_hook["type"], "command")
            self.assertIn("codex_pet_hook.py", prompt_hook["command"])
            self.assertIn("--hook user_prompt_submit", prompt_hook["command"])
            self.assertEqual(prompt_hook["timeout"], 30)
            self.assertEqual(result["events"], ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop"])

    def test_installing_lifecycle_hooks_twice_is_idempotent(self) -> None:
        from install_pet_studio_codex_integration import install_hooks_bridge

        with tempfile.TemporaryDirectory() as tmp:
            hooks_file = Path(tmp) / "hooks.json"

            install_hooks_bridge(hooks_file, dry_run=False)
            install_hooks_bridge(hooks_file, dry_run=False)

            data = json.loads(hooks_file.read_text(encoding="utf-8"))
            prompt_commands = [
                hook["command"]
                for group in data["hooks"]["UserPromptSubmit"]
                for hook in group["hooks"]
                if "codex_pet_hook.py" in hook["command"]
            ]
            self.assertEqual(len(prompt_commands), 1)

    def test_reinstalling_hooks_preserves_non_pet_studio_sibling_handlers(self) -> None:
        from install_pet_studio_codex_integration import install_hooks_bridge

        with tempfile.TemporaryDirectory() as tmp:
            hooks_file = Path(tmp) / "hooks.json"
            write_json(
                hooks_file,
                {
                    "hooks": {
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python old_codex_pet_hook.py --hook stop",
                                    },
                                    {
                                        "type": "command",
                                        "command": "python keep_me.py",
                                    },
                                ]
                            }
                        ]
                    }
                },
            )

            install_hooks_bridge(hooks_file, dry_run=False)

            data = json.loads(hooks_file.read_text(encoding="utf-8"))
            stop_commands = [
                hook["command"]
                for group in data["hooks"]["Stop"]
                for hook in group["hooks"]
            ]
            self.assertIn("python keep_me.py", stop_commands)
            self.assertNotIn("python old_codex_pet_hook.py --hook stop", stop_commands)

    def test_notify_bridge_creates_config_when_missing(self) -> None:
        from install_pet_studio_codex_integration import install_notify_bridge

        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / ".codex" / "config.toml"

            result = install_notify_bridge(config_file, dry_run=False)

            text = config_file.read_text(encoding="utf-8")
            self.assertIn("notify = [", text)
            self.assertIn("codex_pet_hook.py", text)
            self.assertIsNone(result["backup"])

    def test_default_hooks_file_is_project_local(self) -> None:
        from install_pet_studio_codex_integration import HOOKS_PATH

        self.assertEqual(HOOKS_PATH, ROOT / ".codex" / "hooks.json")

    def test_installer_does_not_wrap_global_notify_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS_DIR / "install_pet_studio_codex_integration.py"),
                    "--dry-run",
                    "--skip-skill",
                    "--skip-hooks",
                    "--config",
                    str(Path(tmp) / "config.toml"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertNotIn("notify", data)

    def test_installer_wraps_global_notify_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS_DIR / "install_pet_studio_codex_integration.py"),
                    "--dry-run",
                    "--skip-skill",
                    "--skip-hooks",
                    "--install-notify",
                    "--config",
                    str(Path(tmp) / "config.toml"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertIn("notify", data)


if __name__ == "__main__":
    unittest.main()
