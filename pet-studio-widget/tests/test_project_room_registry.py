from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WIDGET_DIR = ROOT / "pet-studio-widget"
WIDGET_SCRIPT = WIDGET_DIR / "pet_studio_widget.py"
STATE_SCRIPT = WIDGET_DIR / "set_pet_studio_state.py"
ADAPTER_SCRIPT = WIDGET_DIR / "pet_studio_event_adapter.py"
HOOK_SCRIPT = WIDGET_DIR / "codex_pet_hook.py"
ACTIVE_SCRIPT = WIDGET_DIR / "set_active_pet_studio.py"
TOOLS_DIR = ROOT / "tools"
PREFLIGHT_SCRIPT = TOOLS_DIR / "pet_studio_preflight.py"
PYTHON_CMD_WRAPPER = TOOLS_DIR / "pet_studio_python.cmd"
WIDGET_CMD_WRAPPER = TOOLS_DIR / "pet_studio_widget.cmd"
MODEL_CMD_WRAPPER = TOOLS_DIR / "pet_studio_model.cmd"
WORK_CMD_WRAPPER = TOOLS_DIR / "pet_studio_work.cmd"
DEMO_KIT = ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "project-room.json"
README_SCREENSHOT = ROOT / "docs" / "images" / "gakju-widget-bubble-example.png"
if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def relative_to_or_relpath(path: Path, start: Path) -> Path:
    try:
        return path.resolve().relative_to(start.resolve())
    except ValueError:
        return Path(os.path.relpath(path.resolve(), start.resolve()))


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

        self.assertEqual(
            [entity.id for entity in entities], ["room", "desk", "main-owner", "book-stack", "helper-prop-creature"]
        )
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
        helper_layer = next(layer for layer in kit["layers"] if layer["id"] == "helper-prop-creature")
        original_anchor = dict(kit["anchors"][helper_layer["anchor"]])
        layout = {"anchors": {"helper-prop-creature": {"x": -1050, "y": 611}}}

        entities = scene_entities_from_kit(kit, layout)
        helper = next(entity for entity in entities if entity.id == "helper-prop-creature")

        self.assertEqual(helper.anchor, original_anchor)

    def test_bubble_style_ignores_main_pet_sidecar_outside_kit_dir(self) -> None:
        from project_room_scene import BUBBLE_STYLE, resolve_bubble_style

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_dir = work / "kit"
            outside = work / "outside"
            kit_dir.mkdir()
            outside.mkdir()
            write_json(
                outside / "spritesheet.asset.json",
                {"bubbleStyle": {"fill": "#010203", "outline": "#040506", "shadow": "#070809", "text": "#0a0b0c"}},
            )
            kit = {
                "layers": [
                    {
                        "id": "main-owner",
                        "role": "mainPet",
                        "path": "../outside/spritesheet.webp",
                    }
                ]
            }

            style = resolve_bubble_style(kit, kit_dir)

        self.assertEqual(style["fill"], BUBBLE_STYLE["fill"])
        self.assertNotEqual(style["fill"], "#010203")

    def test_clamp_anchor_to_source_canvas_bounds_saved_drag_positions(self) -> None:
        from project_room_scene import clamp_anchor_to_source_canvas

        kit = self.load_demo_kit()

        self.assertEqual(clamp_anchor_to_source_canvas(kit, {"x": -1050, "y": 611}), {"x": 0, "y": 240})
        self.assertEqual(clamp_anchor_to_source_canvas(kit, {"x": 302, "y": 204}), {"x": 302, "y": 204})

    def test_widget_clamps_entity_anchor_using_rendered_sprite_bounds(self) -> None:
        import project_room_widget

        kit = self.load_demo_kit()
        image = Image.new("RGBA", (64, 87), (80, 130, 170, 255))

        anchor = project_room_widget.clamp_anchor_to_visible_image_bounds(
            kit,
            {"x": 380, "y": 0},
            image,
            widget_scale=1.25,
        )

        bounds = project_room_widget.image_bounds_for_anchor(anchor, image, widget_scale=1.25)
        self.assertGreaterEqual(bounds[0], 0)
        self.assertGreaterEqual(bounds[1], 0)
        self.assertLessEqual(bounds[2], 480)
        self.assertLessEqual(bounds[3], 300)
        self.assertNotEqual(anchor, {"x": 380, "y": 0})

    def test_widget_keeps_visible_entity_anchor_when_sprite_bounds_fit(self) -> None:
        import project_room_widget

        kit = self.load_demo_kit()
        image = Image.new("RGBA", (64, 87), (80, 130, 170, 255))

        anchor = project_room_widget.clamp_anchor_to_visible_image_bounds(
            kit,
            {"x": 302, "y": 204},
            image,
            widget_scale=1.25,
        )

        self.assertEqual(anchor, {"x": 302, "y": 204})

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

    def test_widget_prefers_installed_noto_fonts_for_multilingual_bubbles(self) -> None:
        import project_room_widget

        self.assertEqual(
            project_room_widget.bubble_font_family("한글 bubble 확인", {"Segoe UI", "Noto Sans CJK KR"}),
            "Noto Sans CJK KR",
        )
        self.assertEqual(
            project_room_widget.bubble_font_family("مرحبا", {"Segoe UI", "Noto Sans Arabic"}),
            "Noto Sans Arabic",
        )
        self.assertEqual(
            project_room_widget.bubble_font_family("Working", {"Segoe UI", "Noto Sans"}),
            "Noto Sans",
        )
        self.assertEqual(project_room_widget.bubble_font_family("Working", set()), "Segoe UI")

    def test_widget_uses_platform_fallback_when_noto_font_is_missing(self) -> None:
        import project_room_widget

        self.assertEqual(
            project_room_widget.bubble_font_family("한글 bubble 확인", {"Segoe UI", "Malgun Gothic"}),
            "Malgun Gothic",
        )
        self.assertEqual(
            project_room_widget.bubble_font_family("नमस्ते", {"Segoe UI", "Nirmala UI"}),
            "Nirmala UI",
        )

    def test_public_demo_helper_pet_is_visible_in_all_states(self) -> None:
        from project_room_scene import scene_entities_from_kit, visible_scene_entities

        kit = self.load_demo_kit()
        entities = scene_entities_from_kit(kit)

        for state in ("idle", "running", "waiting", "review", "failed", "jumping"):
            with self.subTest(state=state):
                visible_ids = [entity.id for entity in visible_scene_entities(kit, entities, state)]
                self.assertIn("helper-prop-creature", visible_ids)
                self.assertEqual(kit["states"][state]["helperPetRow"], "review")

    def test_public_demo_review_render_contains_helper_pet_pixels(self) -> None:
        import project_room_widget

        kit = self.load_demo_kit()
        kit_without_helper = json.loads(json.dumps(kit))
        kit_without_helper["states"]["review"]["visibleLayers"] = [
            layer_id
            for layer_id in kit_without_helper["states"]["review"]["visibleLayers"]
            if layer_id != "helper-prop-creature"
        ]
        layer_assets = project_room_widget.load_layer_assets(DEMO_KIT.parent, kit["layers"], [])

        with_helper = project_room_widget.build_source_frame(DEMO_KIT.parent, kit, "review", 0, layer_assets, [])
        without_helper = project_room_widget.build_source_frame(
            DEMO_KIT.parent, kit_without_helper, "review", 0, layer_assets, []
        )
        diff_pixels = sum(
            1
            for left, right in zip(rgba_pixels(with_helper), rgba_pixels(without_helper), strict=True)
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
        self.assertEqual(
            Path(project_room_widget.scale_visible_layer.__code__.co_filename).resolve().parents[1],
            ROOT / "pet-studio-kit",
        )

    def test_widget_tool_path_preference_does_not_delete_imported_modules(self) -> None:
        import project_room_widget

        module_name = "localized_messages"
        sentinel = object()
        original_module = sys.modules.get(module_name, sentinel)
        original_path = list(sys.path)
        original_local = project_room_widget.LOCAL_TOOLS
        original_installed = project_room_widget.INSTALLED_TOOLS

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            local_tools = work / "local"
            installed_tools = work / "installed"
            local_tools.mkdir()
            installed_tools.mkdir()
            module = type(sys)(module_name)
            module.__file__ = str(installed_tools / "localized_messages.py")
            sys.modules[module_name] = module
            project_room_widget.LOCAL_TOOLS = local_tools
            project_room_widget.INSTALLED_TOOLS = installed_tools

            try:
                project_room_widget.prefer_local_room_kit_tools()

                self.assertIs(sys.modules[module_name], module)
                self.assertLess(sys.path.index(str(local_tools)), sys.path.index(str(installed_tools)))
            finally:
                sys.path[:] = original_path
                project_room_widget.LOCAL_TOOLS = original_local
                project_room_widget.INSTALLED_TOOLS = original_installed
                if original_module is sentinel:
                    sys.modules.pop(module_name, None)
                else:
                    sys.modules[module_name] = original_module

    def test_project_layout_reset_removes_saved_entity_anchors(self) -> None:
        from project_room_scene import (
            load_project_layout,
            reset_project_layout,
            save_project_anchor,
            save_project_z_order,
        )

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

    def test_workroom_window_file_round_trips_geometry(self) -> None:
        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            window_file = Path(tmp) / "project-room-workroom.json"

            project_room_widget.save_workroom_window(
                window_file,
                {"x": 100, "y": 200, "width": 900, "height": 640},
            )
            window = project_room_widget.load_workroom_window(window_file)

            self.assertEqual(window, {"x": 100, "y": 200, "width": 900, "height": 640})

    def test_project_session_file_round_trips_widget_state(self) -> None:
        from project_room_scene import load_project_session, save_project_session

        with tempfile.TemporaryDirectory() as tmp:
            session_file = Path(tmp) / "project-room-session.json"

            save_project_session(
                session_file,
                "gakju-demo",
                {
                    "state": "review",
                    "message": "Working: restore check",
                    "bubbleVisible": False,
                    "window": {"x": 120, "y": 340, "scale": 1.25},
                    "stateSource": "manual",
                    "updatedAt": "2026-06-14T00:00:00Z",
                },
            )
            session = load_project_session(session_file, "gakju-demo")

        self.assertEqual(session["state"], "review")
        self.assertEqual(session["message"], "Working: restore check")
        self.assertFalse(session["bubbleVisible"])
        self.assertEqual(session["window"], {"x": 120, "y": 340, "scale": 1.25})
        self.assertEqual(session["stateSource"], "manual")

    def test_project_session_file_ignores_unknown_and_malformed_sessions(self) -> None:
        from project_room_scene import load_project_session

        with tempfile.TemporaryDirectory() as tmp:
            session_file = Path(tmp) / "project-room-session.json"
            session_file.write_text("{", encoding="utf-8")

            self.assertEqual(load_project_session(session_file, "gakju-demo"), {})

            write_json(session_file, {"schemaVersion": 1, "projects": {"other-demo": {"state": "review"}}})

            self.assertEqual(load_project_session(session_file, "gakju-demo"), {})

    def test_widget_startup_restores_session_state_window_and_bubble(self) -> None:
        import project_room_widget

        session = {
            "state": "review",
            "message": "Restored message",
            "bubbleVisible": False,
            "window": {"x": 88, "y": 99, "scale": 1.4},
            "stateSource": "manual",
        }

        state, message, source = project_room_widget.resolve_startup_state(
            "idle",
            None,
            None,
            "gakju-demo",
            session,
            restore_session=True,
        )
        scale, x, y = project_room_widget.resolve_startup_window(None, session, True, None, None, None)

        self.assertEqual((state, message, source), ("review", "Restored message", "manual"))
        self.assertEqual((scale, x, y), (1.4, 88, 99))

    def test_widget_startup_cli_values_override_session(self) -> None:
        import project_room_widget

        session = {
            "state": "review",
            "message": "Restored message",
            "window": {"x": 88, "y": 99, "scale": 1.4},
        }

        state, message, source = project_room_widget.resolve_startup_state(
            "idle",
            "failed",
            None,
            "gakju-demo",
            session,
            restore_session=True,
        )
        scale, x, y = project_room_widget.resolve_startup_window(
            {"x": 10, "y": 20, "scale": 1.1},
            session,
            True,
            1.25,
            120,
            620,
        )

        self.assertEqual((state, message, source), ("failed", None, "cli"))
        self.assertEqual((scale, x, y), (1.25, 120, 620))

    def test_widget_startup_fresh_bridge_overrides_session(self) -> None:
        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            write_json(
                state_file,
                {
                    "projectId": "gakju-demo",
                    "state": "running",
                    "message": "Working: fresh bridge",
                    "updatedAt": "2026-06-14T00:00:00Z",
                },
            )

            state, message, source = project_room_widget.resolve_startup_state(
                "idle",
                None,
                state_file,
                "gakju-demo",
                {"state": "review", "message": "Restored message"},
                restore_session=True,
                stale_after_ms=300000,
                now=datetime(2026, 6, 14, 0, 1, tzinfo=UTC),
            )

        self.assertEqual((state, message, source), ("running", "Working: fresh bridge", "bridge"))

    def test_widget_startup_ignores_stale_running_bridge_and_uses_session(self) -> None:
        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            write_json(
                state_file,
                {
                    "projectId": "gakju-demo",
                    "state": "running",
                    "message": "Working: old bridge",
                    "updatedAt": "2026-06-14T00:00:00Z",
                },
            )

            state, message, source = project_room_widget.resolve_startup_state(
                "idle",
                None,
                state_file,
                "gakju-demo",
                {"state": "review", "message": "Restored message", "stateSource": "manual"},
                restore_session=True,
                stale_after_ms=300000,
                now=datetime(2026, 6, 14, 0, 6, tzinfo=UTC),
            )

        self.assertEqual((state, message, source), ("review", "Restored message", "manual"))

    def test_widget_startup_no_restore_session_ignores_session_file_values(self) -> None:
        import project_room_widget

        session = {
            "state": "review",
            "message": "Restored message",
            "window": {"x": 88, "y": 99, "scale": 1.4},
        }

        state, message, source = project_room_widget.resolve_startup_state(
            "idle",
            None,
            None,
            "gakju-demo",
            session,
            restore_session=False,
        )
        scale, x, y = project_room_widget.resolve_startup_window(
            {"x": 10, "y": 20, "scale": 1.1},
            session,
            False,
            None,
            None,
            None,
        )

        self.assertEqual((state, message, source), ("idle", None, "default"))
        self.assertEqual((scale, x, y), (1.1, 10, 20))

    def test_widget_render_once_disables_session_restore(self) -> None:
        import project_room_widget

        self.assertFalse(project_room_widget.restore_session_enabled("gakju-demo", "runs/out.png", None))
        self.assertFalse(project_room_widget.restore_session_enabled(None, None, True))
        self.assertFalse(project_room_widget.restore_session_enabled("gakju-demo", None, False))
        self.assertTrue(project_room_widget.restore_session_enabled("gakju-demo", None, None))

    def test_widget_save_session_writes_current_visible_state(self) -> None:
        import project_room_widget
        from project_room_scene import load_project_session

        class FakeRoot:
            def winfo_x(self) -> int:
                return 321

            def winfo_y(self) -> int:
                return 654

        with tempfile.TemporaryDirectory() as tmp:
            widget = object.__new__(project_room_widget.ProjectRoomWidget)
            widget.project_id = "gakju-demo"
            widget.session_file = Path(tmp) / "project-room-session.json"
            widget.root = FakeRoot()
            widget.state = "failed"
            widget.message = "Need input"
            widget.bubble_visible = False
            widget.scale = 1.25
            widget.state_source = "manual"

            widget.save_session("manual")
            session = load_project_session(widget.session_file, "gakju-demo")

        self.assertEqual(session["state"], "failed")
        self.assertEqual(session["message"], "Need input")
        self.assertFalse(session["bubbleVisible"])
        self.assertEqual(session["window"], {"x": 321, "y": 654, "scale": 1.25})
        self.assertEqual(session["stateSource"], "manual")

    def test_bubble_text_prefers_state_message_and_uses_state_defaults(self) -> None:
        from project_room_scene import bubble_text_for_state

        self.assertEqual(bubble_text_for_state("running", "building room"), "building room")
        self.assertEqual(bubble_text_for_state("blocked", ""), "Need input")
        self.assertEqual(bubble_text_for_state("done", None), "Done")
        self.assertIsNone(bubble_text_for_state("idle", None, enabled=False))

    def test_bubble_text_normalizes_and_truncates_long_messages(self) -> None:
        from project_room_scene import MAX_BUBBLE_TEXT_LENGTH, bubble_text_for_state

        message = (
            "  Waiting\n\non   approval for the very long integration check before the widget can continue safely  "
        )

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

    def test_bubble_bounds_prefers_above_owner_when_overlapping_face(self) -> None:
        import project_room_widget

        dx, dy = project_room_widget.bubble_avoid_owner_shift(
            bubble_bounds=(110, 70, 260, 132),
            owner_bounds=(150, 95, 240, 230),
            canvas_width=480,
            canvas_height=300,
            margin=12,
            gap=8,
        )

        self.assertEqual(dx, 0)
        self.assertLess(dy, 0)
        shifted = (110 + dx, 70 + dy, 260 + dx, 132 + dy)
        self.assertLessEqual(shifted[3], 87)

    def test_bubble_bounds_shift_left_when_right_side_has_no_room(self) -> None:
        import project_room_widget

        dx, dy = project_room_widget.bubble_avoid_owner_shift(
            bubble_bounds=(240, 12, 390, 74),
            owner_bounds=(250, 20, 350, 230),
            canvas_width=420,
            canvas_height=300,
            margin=12,
            gap=8,
        )

        self.assertLess(dx, 0)
        self.assertEqual(dy, 0)
        shifted = (240 + dx, 12 + dy, 390 + dx, 74 + dy)
        self.assertLessEqual(shifted[2], 242)

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
                self.assertIn("pet_studio_widget_python", text)
                self.assertIn("pythonw", text)
                self.assertIn('start "pet studio widget"', text)
                self.assertIn("pet_studio_pythonw", text)

    def test_cmd_python_wrapper_avoids_broken_windows_python_shims(self) -> None:
        text = PYTHON_CMD_WRAPPER.read_text(encoding="utf-8").lower()

        self.assertIn("pet_studio_python", text)
        self.assertIn("codex-primary-runtime", text)
        self.assertIn("py -3 --version", text)
        self.assertIn("python --version", text)
        self.assertIn("no working python 3 runtime was found", text)
        self.assertIn("call exit /b %%errorlevel%%", text)
        self.assertNotIn("exit /b %errorlevel%", text)

    @unittest.skipIf(os.name != "nt", "Windows .cmd wrapper regression")
    def test_cmd_python_wrapper_propagates_python_failure(self) -> None:
        result = subprocess.run(
            [str(PYTHON_CMD_WRAPPER), "-m", "definitely_missing_pet_studio_module"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no module named definitely_missing_pet_studio_module", result.stderr.lower())

    def test_widget_cmd_wrapper_launches_widget_without_console_python(self) -> None:
        text = WIDGET_CMD_WRAPPER.read_text(encoding="utf-8").lower()
        ps1_text = (TOOLS_DIR / "pet_studio_widget.ps1").read_text(encoding="utf-8").lower()

        self.assertIn("powershell.exe", text)
        self.assertIn("-windowstyle hidden", text)
        self.assertIn("--foreground", text)
        self.assertIn("pet_studio_pythonw", text)
        self.assertIn("pythonw.exe", text)
        self.assertIn('start "pet studio widget"', text)
        self.assertIn("pet_studio_widget.py", text)
        self.assertIn("start-process", ps1_text)
        self.assertIn("-windowstyle hidden", ps1_text)
        self.assertIn("focus-petstudiowindow", ps1_text)
        self.assertIn("pet studio workroom", ps1_text)
        self.assertIn("findwindow", ps1_text)
        self.assertIn("setforegroundwindow", ps1_text)
        self.assertIn("project-room-widget.log", ps1_text)
        self.assertIn("project-room-widget.err.log", ps1_text)
        self.assertIn("python.exe", ps1_text)
        self.assertIn("& $python $script @args", ps1_text)
        self.assertIn("call exit /b %%errorlevel%%", text)
        self.assertNotIn("exit /b %errorlevel%", text)

    def test_model_cmd_wrapper_uses_widget_model_cli(self) -> None:
        text = MODEL_CMD_WRAPPER.read_text(encoding="utf-8").lower()

        self.assertIn("pet_studio_python.cmd", text)
        self.assertIn("pet_studio_widget.py", text)
        self.assertIn("%*", text)
        self.assertIn("rest", text)
        self.assertNotIn("\"%*\"", text)
        self.assertNotIn("%2 %3 %4 %5 %6 %7 %8 %9", text)
        self.assertIn("plan", text)
        self.assertIn("team", text)
        self.assertIn("save-credits", text)
        self.assertIn("all-local", text)
        self.assertIn("all-value", text)
        self.assertIn("lead-sota", text)
        self.assertIn("--team-model-preset", text)
        self.assertIn("reset-role", text)
        self.assertIn("clear-role", text)
        self.assertIn("--clear-role-model", text)
        self.assertIn("--print-team-model-env", text)
        self.assertIn("--print-role-model-env", text)
        self.assertIn("--set-role-model scout", text)
        self.assertIn("--set-role-model coordinator", text)
        self.assertIn("--set-role-model lead", text)
        self.assertIn("rest2", text)
        self.assertIn("call exit /b %%errorlevel%%", text)
        self.assertNotIn("exit /b %errorlevel%", text)

    @unittest.skipIf(os.name != "nt", "Windows .cmd wrapper regression")
    def test_model_cmd_wrapper_propagates_cli_failure(self) -> None:
        result = subprocess.run(
            [str(MODEL_CMD_WRAPPER), "--definitely-invalid-option"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("definitely-invalid-option", result.stderr.lower())

    @unittest.skipIf(os.name != "nt", "Windows .cmd wrapper regression")
    def test_model_cmd_env_team_preserves_options_after_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            saved = subprocess.run(
                [str(MODEL_CMD_WRAPPER), "coordinator", "local", "--state-file", str(state_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr + saved.stdout)

            env_plan = subprocess.run(
                [str(MODEL_CMD_WRAPPER), "env", "team", "--state-file", str(state_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            role_env = subprocess.run(
                [str(MODEL_CMD_WRAPPER), "env", "coordinator", "--state-file", str(state_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(env_plan.returncode, 0, env_plan.stderr + env_plan.stdout)
        self.assertIn("# coordinator: local/default", env_plan.stdout)
        self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", env_plan.stdout)
        self.assertEqual(role_env.returncode, 0, role_env.stderr + role_env.stdout)
        self.assertIn("$env:PET_STUDIO_MODEL_PROFILE = 'local/default'", role_env.stdout)
        self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", role_env.stdout)

    @unittest.skipIf(os.name != "nt", "Windows .cmd wrapper regression")
    def test_model_cmd_passthrough_preserves_parenthesized_model_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            saved = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "--state-file",
                    str(state_file),
                    "--set-model-profile",
                    "openrouter/test-model",
                    "--model-provider",
                    "openrouter",
                    "--model-name",
                    "test(model)",
                    "--model-cost",
                    "low",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(saved.returncode, 0, saved.stderr + saved.stdout)
        payload = json.loads(saved.stdout)
        profile = next(item for item in payload["profiles"] if item["id"] == "openrouter/test-model")
        self.assertEqual(profile["model"], "test(model)")
        self.assertEqual(profile["cost"], "low")

    def test_work_cmd_wrapper_uses_widget_work_cli(self) -> None:
        text = WORK_CMD_WRAPPER.read_text(encoding="utf-8").lower()

        self.assertIn("pet_studio_python.cmd", text)
        self.assertIn("pet_studio_widget.py", text)
        self.assertIn("rest", text)
        self.assertIn("--goal", text)
        self.assertIn("--mission", text)
        self.assertIn("--add-task", text)
        self.assertIn("--add-staff", text)
        self.assertIn("--assign-task", text)
        self.assertIn("--assign-staff", text)
        self.assertIn("--task-start", text)
        self.assertIn("--task-done", text)
        self.assertIn("--work-status", text)
        self.assertIn("pet_studio_workroom.cmd", text)
        self.assertIn('if /i "%cmd%"=="staff"', text)
        self.assertIn('if /i "%cmd%"=="assign-role"', text)
        self.assertIn('if /i "%cmd%"=="assign-staff"', text)
        self.assertIn('if /i "%cmd%"=="start"', text)
        self.assertIn('if /i "%cmd%"=="done"', text)
        self.assertNotIn("%2 %3 %4 %5 %6 %7 %8 %9", text)
        self.assertIn("call exit /b %%errorlevel%%", text)
        self.assertNotIn("exit /b %errorlevel%", text)

    def test_widget_script_relaunches_gui_runs_on_windows_python_exe(self) -> None:
        import argparse

        import project_room_widget

        args = argparse.Namespace(
            list_projects=False,
            render_once=None,
            render_project_once=None,
            foreground=False,
        )
        foreground_args = argparse.Namespace(
            list_projects=False,
            render_once=None,
            render_project_once=None,
            foreground=True,
        )
        render_args = argparse.Namespace(
            list_projects=False,
            render_once="out.png",
            render_project_once=None,
            foreground=False,
        )

        self.assertTrue(project_room_widget.should_relaunch_background(args, platform="win32", env={}))
        self.assertFalse(project_room_widget.should_relaunch_background(args, platform="linux", env={}))
        self.assertFalse(project_room_widget.should_relaunch_background(foreground_args, platform="win32", env={}))
        self.assertFalse(project_room_widget.should_relaunch_background(render_args, platform="win32", env={}))
        self.assertFalse(
            project_room_widget.should_relaunch_background(
                args,
                platform="win32",
                env={project_room_widget.BACKGROUND_CHILD_ENV: "1"},
            )
        )

    def test_widget_script_uses_local_lock_for_normal_gui_launches(self) -> None:
        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            lock_file = Path(tmp) / "project-room-widget.lock"

            first = project_room_widget.acquire_widget_lock(lock_file, platform="win32")
            self.assertIsNotNone(first)
            try:
                second = project_room_widget.acquire_widget_lock(lock_file, platform="win32")
                self.assertIsNone(second)
            finally:
                first.close()

    def test_widget_script_focus_existing_window_is_windows_only_by_default(self) -> None:
        import project_room_widget

        self.assertFalse(project_room_widget.focus_existing_widget_window(platform="linux"))

    def test_widget_script_relaunch_writes_stdout_and_stderr_to_log(self) -> None:
        text = (WIDGET_DIR / "project_room_widget.py").read_text(encoding="utf-8")

        self.assertIn("DEFAULT_WIDGET_LOG", text)
        self.assertIn("stdout=log_handle", text)
        self.assertIn("stderr=log_handle", text)
        self.assertNotIn("stderr=subprocess.DEVNULL", text)
        self.assertNotIn("Install Hook", text)
        self.assertNotIn("install_pet_studio_codex_integration", text)
        self.assertNotIn("add_team_room_menu", text)
        self.assertIn('"--workroom"', text)
        self.assertIn("WORKROOM_TITLE", text)
        self.assertIn("display_name=selected_project.display_name", text)
        self.assertIn("--test-model-profile", text)
        self.assertIn("--set-role-model", text)
        self.assertIn("--clear-role-model", text)
        self.assertIn("--team-model-preset", text)
        self.assertIn("--print-team-model-env", text)
        self.assertIn("--print-role-model-env", text)
        self.assertIn("roleModelPlan", text)
        self.assertIn("roleModelEnv", text)
        self.assertIn("roleModelEnvClear", text)
        self.assertIn("teamModelPreset", text)
        self.assertIn("teamModelSavings", text)
        self.assertIn("teamModelPresets", text)

    def test_project_hub_owns_team_room_view(self) -> None:
        text = (WIDGET_DIR / "ui" / "project_hub.py").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        preflight = PREFLIGHT_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('notebook.add(team_tab, text="Team Room")', text)
        self.assertIn("def _build_team_room_tab(", text)
        self.assertIn("Pet Studio Workroom", text)
        self.assertIn("Active model", text)
        self.assertIn("Team mode", text)
        self.assertIn("task_indexes", text)
        self.assertIn("update_project_queue_item", text)
        self.assertIn('text="Assign staff"', text)
        self.assertIn('text="Scout"', text)
        self.assertIn('text="Coordinator"', text)
        self.assertIn('text="Lead"', text)
        self.assertIn('text="Start"', text)
        self.assertIn('text="Done"', text)
        self.assertIn("Model Profiles (closed -> open-sota -> local -> value -> free)", text)
        self.assertIn("Credit Plan", text)
        self.assertIn("estimate_team_model_savings", text)
        self.assertIn("Lead-only estimate", text)
        self.assertIn("queue_indexes", text)
        self.assertIn("dequeue_roost", text)
        self.assertIn("remove_roost_queue_item", text)
        self.assertIn("route_roost_queue_item_to_project", text)
        self.assertIn("register_employee", text)
        self.assertIn('text="+ Staff"', text)
        self.assertIn('dialog.title("Add staff")', text)
        self.assertIn('text="Route to tasks"', text)
        self.assertIn('text="Dequeue next"', text)
        self.assertIn('text="Drop selected"', text)
        self.assertIn('text="Route"', text)
        self.assertIn("role_model_combos", text)
        self.assertIn("list_role_model_plan", text)
        self.assertIn("set_role_model_profile", text)
        self.assertIn("clear_role_model_profile", text)
        self.assertIn("Role model reset", text)
        self.assertIn("apply_team_model_preset", text)
        self.assertIn("get_team_model_preset_id", text)
        self.assertIn("프리셋이 적용되었습니다", text)
        self.assertIn("_save_team_model_preset", text)
        self.assertIn("_refresh_project_hub_credit_plan", text)
        self.assertIn("Preset: custom", text)
        self.assertIn("Save credits", text)
        self.assertIn("All local", text)
        self.assertIn("All value", text)
        self.assertIn("Lead SOTA", text)
        self.assertIn("역할이 저장되었습니다", text)
        self.assertIn("_select_model_tier", text)
        self.assertIn("Open SOTA", text)
        self.assertIn("Local", text)
        self.assertIn("Value", text)
        self.assertIn("Free", text)
        self.assertIn('"tier"', text)
        self.assertIn('text="Tier"', text)
        self.assertIn("closed", text)
        self.assertIn("open-sota", text)
        self.assertIn("list_model_profiles", text)
        self.assertIn("set_active_model_profile", text)
        self.assertIn("set_model_profile", text)
        self.assertIn("remove_model_profile", text)
        self.assertIn("model_profile_powershell_env_lines", text)
        self.assertIn("role_model_plan_powershell_env_lines", text)
        self.assertIn("Copy env", text)
        self.assertIn("Copy selected env", text)
        self.assertIn("Copy team env plan", text)
        self.assertIn("_powershell_env_lines_for_profile", text)
        self.assertIn("_powershell_env_lines_for_role_plan", text)
        self.assertIn("Test model", text)
        self.assertIn("_test_model_profile", text)
        self.assertIn("Export Work Packet", text)
        self.assertIn("Import Work Packet", text)
        self.assertIn("export_work_packet", text)
        self.assertIn("import_work_packet", text)
        self.assertIn("work-packets", text)
        self.assertIn("codex-packets", text)
        self.assertIn("project-room-workroom.json", gitignore)
        self.assertIn("pet-studio-widget/team_state.json", gitignore)
        self.assertIn("work-packets/", gitignore)
        self.assertIn("codex-packets/", gitignore)
        self.assertIn("pet-studio-widget/team_state.json", preflight)
        self.assertIn("work-packets/probe.json", preflight)
        self.assertIn("codex-packets/probe.json", preflight)

    def test_workroom_summary_includes_team_model_preset(self) -> None:
        from ui.project_hub import _summary_lines

        from roost.state import TeamState

        class Widget:
            project_id = "demo"
            _project_display_name = "Demo"
            state = "idle"

        with tempfile.TemporaryDirectory() as tmp:
            state = TeamState(Path(tmp) / "team_state.json")
            state.register_project("demo", "Demo", security_level=1, mission="Ship the room")
            widget = Widget()
            widget._team_state = state

            _summary, meta = _summary_lines(widget)

        self.assertIn("idle", meta)
        self.assertIn("open-sota openrouter/sota", meta)

    def test_project_hub_formats_profile_env_for_powershell(self) -> None:
        from ui.project_hub import _powershell_env_lines_for_profile, _powershell_env_lines_for_role_plan

        lines = _powershell_env_lines_for_profile(
            {
                "id": "openrouter/test",
                "provider": "openrouter",
                "model": "vendor/model's-fast",
            }
        )

        self.assertIn("$env:HERMES_MODEL = 'vendor/model''s-fast'", lines)
        self.assertIn("$env:OPENROUTER_MODEL = 'vendor/model''s-fast'", lines)
        self.assertIn("$env:PET_STUDIO_MODEL_PROFILE = 'openrouter/test'", lines)
        self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", lines)

        local_lines = _powershell_env_lines_for_profile(
            {
                "id": "local/default",
                "provider": "local",
                "model": "local",
            }
        )

        self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", local_lines)
        self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", local_lines)

        team_lines = _powershell_env_lines_for_role_plan(
            [
                {"role": "scout", "profile": {"id": "local/default", "provider": "local", "model": "local"}},
                {"role": "coordinator", "profile": {"id": "openrouter/fast", "provider": "openrouter", "model": "fast"}},
            ]
        )

        self.assertIn("# scout: local/default", team_lines)
        self.assertIn("# Copy one role section at a time; later sections reuse the same env variable names.", team_lines)
        self.assertIn("# coordinator: openrouter/fast", team_lines)
        self.assertIn("$env:OPENROUTER_MODEL = 'fast'", team_lines)
        self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", team_lines)

    def test_entity_hit_testing_ignores_transparent_image_pixels(self) -> None:
        import project_room_widget

        image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        image.putpixel((5, 8), (255, 120, 80, 255))

        self.assertFalse(project_room_widget.image_anchor_s_pixel_is_opaque(image, 100, 100, 95, 90))
        self.assertTrue(project_room_widget.image_anchor_s_pixel_is_opaque(image, 100, 100, 100, 98))

    def test_topmost_helper_sets_attribute_and_lifts_window(self) -> None:
        import project_room_widget

        class FakeRoot:
            def __init__(self) -> None:
                self.attributes: list[tuple[str, bool]] = []
                self.lift_count = 0

            def wm_attributes(self, key: str, value: bool) -> None:
                self.attributes.append((key, value))

            def lift(self) -> None:
                self.lift_count += 1

        root = FakeRoot()

        project_room_widget.apply_topmost(root, True)

        self.assertEqual(root.attributes, [("-topmost", True)])
        self.assertEqual(root.lift_count, 1)

    def test_fixed_window_geometry_keeps_widget_size_and_position(self) -> None:
        import project_room_widget

        self.assertEqual(project_room_widget.fixed_window_geometry(480, 320, 20, 40), "480x320+20+40")
        self.assertEqual(project_room_widget.fixed_window_geometry(0, -1), "1x1")

    def test_project_hub_uses_app_sized_shell_and_ttk_styles(self) -> None:
        text = (WIDGET_DIR / "ui" / "project_hub.py").read_text(encoding="utf-8")

        self.assertIn('hub.geometry("820x580")', text)
        self.assertIn("hub.minsize(760, 520)", text)
        self.assertIn('width = saved.get("width", 980)', text)
        self.assertIn('height = saved.get("height", 680)', text)
        self.assertIn("def _configure_hub_style", text)
        self.assertIn('"TNotebook.Tab"', text)
        self.assertIn('"Treeview"', text)

    def test_local_auth_file_is_ignored_and_wizard_is_clean(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        wizard = (WIDGET_DIR / "ui" / "api_key_wizard.py").read_text(encoding="utf-8")

        self.assertIn("pet-studio-widget/.pet_studio_keys.json", gitignore)
        self.assertIn("Connect Hermes / Codex", wizard)
        self.assertIn("HERMES_GATEWAY_URL", wizard)
        self.assertIn("CODEX_OAUTH_TOKEN", wizard)

    def test_done_state_resets_to_idle_after_reset_delay(self) -> None:
        from datetime import datetime

        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            write_json(
                state_file,
                {
                    "projectId": "gakju-demo",
                    "state": "done",
                    "message": "Done",
                    "updatedAt": "2026-06-13T00:00:00Z",
                    "resetAfterMs": 1500,
                    "resetToState": "idle",
                },
            )

            before_state, before_message = project_room_widget.read_project_state_payload(
                state_file,
                "gakju-demo",
                "idle",
                now=datetime(2026, 6, 13, 0, 0, 1, tzinfo=UTC),
            )
            after_state, after_message = project_room_widget.read_project_state_payload(
                state_file,
                "gakju-demo",
                "idle",
                now=datetime(2026, 6, 13, 0, 0, 2, tzinfo=UTC),
            )

        self.assertEqual(before_state, "jumping")
        self.assertEqual(before_message, "Done")
        self.assertEqual(after_state, "idle")
        self.assertIsNone(after_message)


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

    def test_project_room_registry_reexports_core_registry_api(self) -> None:
        import project_room_registry

        import pet_studio_core.registry as core_registry

        self.assertIs(project_room_registry.ProjectAssignment, core_registry.ProjectAssignment)
        self.assertIs(project_room_registry.ProjectRegistryError, core_registry.ProjectRegistryError)
        self.assertIs(project_room_registry.select_project, core_registry.select_project)
        self.assertEqual(project_room_registry.DEFAULT_REGISTRY, core_registry.DEFAULT_REGISTRY)

    def test_core_state_writer_preserves_bridge_payload_shape(self) -> None:
        from pet_studio_core.registry import read_project_state
        from pet_studio_core.state import write_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            payload = write_project_state(
                state_file,
                "gakju-demo",
                "done",
                "Done",
                updated_at="2026-06-15T00:00:00Z",
                reset_after_ms=1500,
                reset_to_state="idle",
            )

            self.assertEqual(
                payload,
                {
                    "projectId": "gakju-demo",
                    "state": "done",
                    "message": "Done",
                    "updatedAt": "2026-06-15T00:00:00Z",
                    "resetAfterMs": 1500,
                    "resetToState": "idle",
                },
            )
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "jumping")

    def test_core_package_has_no_codex_or_widget_host_imports(self) -> None:
        core_files = list((ROOT / "pet_studio_core").glob("*.py"))
        self.assertTrue(core_files)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in core_files)

        for forbidden in (
            "codex_",
            "tkinter",
            "codex_pet_hook",
            "install_pet_studio_codex_integration",
            "pet_studio_widget",
            "image_provider",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined)

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

    def test_widget_cli_manages_model_profiles_without_gui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            state_file = work / "project-room-state.json"

            listed = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--list-model-profiles",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr + listed.stdout)
            listed_payload = json.loads(listed.stdout)
            self.assertEqual(listed_payload["activeModelProfile"], "openrouter/sota")
            self.assertEqual(
                [profile["tier"] for profile in listed_payload["profiles"][:5]],
                ["closed", "closed", "open-sota", "local", "value"],
            )
            self.assertIn("closed/claude", [profile["id"] for profile in listed_payload["profiles"]])

            saved = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--set-model-profile",
                    "openrouter/test",
                    "--model-provider",
                    "openrouter",
                    "--model-name",
                    "test/model",
                    "--model-cost",
                    "low",
                    "--use-model-profile",
                    "openrouter/test",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr + saved.stdout)
            saved_payload = json.loads(saved.stdout)
            self.assertEqual(saved_payload["activeModelProfile"], "openrouter/test")
            self.assertTrue((work / "team_state.json").exists())

            env_print = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--print-model-env",
                    "openrouter/test",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(env_print.returncode, 0, env_print.stderr + env_print.stdout)
            self.assertIn("$env:OPENROUTER_MODEL = 'test/model'", env_print.stdout)
            self.assertIn("$env:PET_STUDIO_MODEL_PROFILE = 'openrouter/test'", env_print.stdout)

            codex_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "codex",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(codex_alias.returncode, 0, codex_alias.stderr + codex_alias.stdout)
            codex_payload = json.loads(codex_alias.stdout)
            self.assertEqual(codex_payload["activeModelProfile"], "codex/default")

            fast_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "fast",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(fast_alias.returncode, 0, fast_alias.stderr + fast_alias.stdout)
            fast_payload = json.loads(fast_alias.stdout)
            self.assertEqual(fast_payload["activeModelProfile"], "openrouter/fast")

            value_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "value",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(value_alias.returncode, 0, value_alias.stderr + value_alias.stdout)
            value_payload = json.loads(value_alias.stdout)
            self.assertEqual(value_payload["activeModelProfile"], "openrouter/fast")

            free_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "free",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(free_alias.returncode, 0, free_alias.stderr + free_alias.stdout)
            free_payload = json.loads(free_alias.stdout)
            self.assertEqual(free_payload["activeModelProfile"], "openrouter/cheap")

            claude_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "claude",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(claude_alias.returncode, 0, claude_alias.stderr + claude_alias.stdout)
            claude_payload = json.loads(claude_alias.stdout)
            self.assertEqual(claude_payload["activeModelProfile"], "closed/claude")

            local_alias = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model",
                    "local",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(local_alias.returncode, 0, local_alias.stderr + local_alias.stdout)
            local_payload = json.loads(local_alias.stdout)
            self.assertEqual(local_payload["activeModelProfile"], "local/default")

            wrapped_codex = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "codex",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_codex.returncode, 0, wrapped_codex.stderr + wrapped_codex.stdout)
            wrapped_codex_payload = json.loads(wrapped_codex.stdout)
            self.assertEqual(wrapped_codex_payload["activeModelProfile"], "codex/default")

            tested = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--set-model-profile",
                    "local/script-profile",
                    "--model-backend",
                    "script",
                    "--model-provider",
                    "local",
                    "--model-name",
                    "script",
                    "--use-model-profile",
                    "local/script-profile",
                    "--test-model-profile",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(tested.returncode, 0, tested.stderr + tested.stdout)
            tested_payload = json.loads(tested.stdout)
            self.assertTrue(tested_payload["ok"])
            self.assertEqual(tested_payload["profile"]["id"], "local/script-profile")
            self.assertEqual(tested_payload["diagnostics"]["env"]["PET_STUDIO_MODEL"], "script")
            self.assertIn("OPENROUTER_API_KEY", tested_payload["diagnostics"]["secrets"])

            status = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--model-status",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["activeModelProfile"], "local/script-profile")
            self.assertEqual(status_payload["teamModelPreset"], "save-credits")
            self.assertIn("teamModelSavings", status_payload)
            self.assertEqual(status_payload["roleModelEnv"]["coordinator"]["OPENROUTER_MODEL"], "fast")
            self.assertEqual(status_payload["roleModelEnvClear"]["scout"], ["OPENROUTER_MODEL", "CODEX_MODEL"])
            self.assertEqual(status_payload["roleModelEnvClear"]["coordinator"], ["CODEX_MODEL"])
            self.assertTrue(status_payload["test"]["ok"])
            role_plan = {item["role"]: item["profile"]["id"] for item in status_payload["roleModelPlan"]}
            self.assertEqual(role_plan["scout"], "local/default")
            self.assertEqual(role_plan["coordinator"], "openrouter/fast")
            self.assertEqual(role_plan["lead"], "local/script-profile")

            coordinator_env = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--print-role-model-env",
                    "coordinator",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(coordinator_env.returncode, 0, coordinator_env.stderr + coordinator_env.stdout)
            self.assertIn("$env:PET_STUDIO_MODEL_PROFILE = 'openrouter/fast'", coordinator_env.stdout)
            self.assertIn("$env:OPENROUTER_MODEL = 'fast'", coordinator_env.stdout)

            wrapped_lead_env = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "env",
                    "lead",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_lead_env.returncode, 0, wrapped_lead_env.stderr + wrapped_lead_env.stdout)
            self.assertIn("$env:PET_STUDIO_MODEL_PROFILE = 'local/script-profile'", wrapped_lead_env.stdout)
            self.assertIn("$env:HERMES_MODEL = 'script'", wrapped_lead_env.stdout)
            self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", wrapped_lead_env.stdout)
            self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", wrapped_lead_env.stdout)

            wrapped_team_env = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "env",
                    "team",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_team_env.returncode, 0, wrapped_team_env.stderr + wrapped_team_env.stdout)
            self.assertIn("# scout: local/default", wrapped_team_env.stdout)
            self.assertIn("# Copy one role section at a time", wrapped_team_env.stdout)
            self.assertIn("# coordinator: openrouter/fast", wrapped_team_env.stdout)
            self.assertIn("# lead: local/script-profile", wrapped_team_env.stdout)
            self.assertIn("$env:OPENROUTER_MODEL = 'fast'", wrapped_team_env.stdout)
            self.assertIn("Remove-Item Env:OPENROUTER_MODEL -ErrorAction SilentlyContinue", wrapped_team_env.stdout)
            self.assertIn("Remove-Item Env:CODEX_MODEL -ErrorAction SilentlyContinue", wrapped_team_env.stdout)

            set_role = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--set-role-model",
                    "coordinator",
                    "local",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(set_role.returncode, 0, set_role.stderr + set_role.stdout)
            set_role_payload = json.loads(set_role.stdout)
            role_plan = {item["role"]: item["profile"]["id"] for item in set_role_payload["roleModelPlan"]}
            self.assertEqual(role_plan["coordinator"], "local/default")

            clear_role = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--clear-role-model",
                    "coordinator",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(clear_role.returncode, 0, clear_role.stderr + clear_role.stdout)
            clear_role_payload = json.loads(clear_role.stdout)
            role_plan = {item["role"]: item["profile"]["id"] for item in clear_role_payload["roleModelPlan"]}
            self.assertEqual(role_plan["coordinator"], "openrouter/fast")

            wrapped_role = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "scout",
                    "free",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_role.returncode, 0, wrapped_role.stderr + wrapped_role.stdout)
            wrapped_role_payload = json.loads(wrapped_role.stdout)
            self.assertEqual(wrapped_role_payload["teamModelPreset"], "custom")
            role_plan = {item["role"]: item["profile"]["id"] for item in wrapped_role_payload["roleModelPlan"]}
            self.assertEqual(role_plan["scout"], "openrouter/cheap")

            wrapped_reset = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "reset-role",
                    "scout",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_reset.returncode, 0, wrapped_reset.stderr + wrapped_reset.stdout)
            wrapped_reset_payload = json.loads(wrapped_reset.stdout)
            role_plan = {item["role"]: item["profile"]["id"] for item in wrapped_reset_payload["roleModelPlan"]}
            self.assertEqual(role_plan["scout"], "local/default")

            wrapped_preset = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "all-local",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped_preset.returncode, 0, wrapped_preset.stderr + wrapped_preset.stdout)
            wrapped_preset_payload = json.loads(wrapped_preset.stdout)
            self.assertEqual(wrapped_preset_payload["teamModelPreset"], "all-local")
            role_plan = {item["role"]: item["profile"]["id"] for item in wrapped_preset_payload["roleModelPlan"]}
            self.assertEqual(role_plan["scout"], "local/default")
            self.assertEqual(role_plan["coordinator"], "local/default")
            self.assertEqual(role_plan["lead"], "local/default")

            wrapped = subprocess.run(
                [
                    str(MODEL_CMD_WRAPPER),
                    "--state-file",
                    str(state_file),
                    "--test-model-profile",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(wrapped.returncode, 0, wrapped.stderr + wrapped.stdout)
            wrapped_payload = json.loads(wrapped.stdout)
            self.assertTrue(wrapped_payload["ok"])
            self.assertEqual(wrapped_payload["profile"]["id"], "local/script-profile")
            self.assertEqual(wrapped_payload["diagnostics"]["env"]["PET_STUDIO_MODEL_PROFILE"], "local/script-profile")

    def test_widget_cli_team_state_path_follows_state_bridge_path(self) -> None:
        import project_room_widget

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "nested" / "project-room-state.json"

            self.assertEqual(project_room_widget.team_state_path_for_cli(str(state_file)), state_file.parent / "team_state.json")
            self.assertEqual(project_room_widget.team_state_path_for_cli(None), WIDGET_DIR / "team_state.json")

    def test_model_profile_failure_explains_broken_hermes_launcher(self) -> None:
        import project_room_widget

        diagnostics = {}
        reason = project_room_widget._explain_backend_version_failure(
            "hermes",
            101,
            (
                'Unable to create process using "C:\\Users\\USER\\AppData\\Roaming\\uv\\python\\'
                'cpython-3.11.11-windows-x86_64-none\\python.exe" '
                '"C:\\Users\\USER\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\hermes.exe" --version'
            ),
            diagnostics,
        )

        self.assertEqual(reason, "hermes launcher could not start its Python runtime")
        self.assertEqual(
            diagnostics["pythonRuntimePath"],
            "C:\\Users\\USER\\AppData\\Roaming\\uv\\python\\cpython-3.11.11-windows-x86_64-none\\python.exe",
        )
        self.assertIn("repairHint", diagnostics)
        self.assertNotIn("missing", reason)

    def test_model_profile_failure_explains_hermes_python_access_denied(self) -> None:
        import project_room_widget

        diagnostics = {}
        reason = project_room_widget._explain_backend_version_failure(
            "hermes",
            -1,
            (
                "[WinError 5] Access is denied: "
                "'C:\\Users\\USER\\AppData\\Roaming\\uv\\python\\"
                "cpython-3.11.11-windows-x86_64-none\\python.exe'"
            ),
            diagnostics,
        )

        self.assertEqual(reason, "hermes launcher could not start its Python runtime")
        self.assertEqual(
            diagnostics["pythonRuntimePath"],
            "C:\\Users\\USER\\AppData\\Roaming\\uv\\python\\cpython-3.11.11-windows-x86_64-none\\python.exe",
        )
        self.assertIn("repairHint", diagnostics)

    def test_widget_cli_manages_goal_and_task_cards_without_gui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            state_file = work / "project-room-state.json"

            goal = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                    "--goal",
                    "Ship a usable workroom",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(goal.returncode, 0, goal.stderr + goal.stdout)
            goal_payload = json.loads(goal.stdout)
            self.assertEqual(goal_payload["projectId"], "gakju-archive-demo")
            self.assertEqual(goal_payload["mission"], "Ship a usable workroom")
            self.assertEqual(goal_payload["tasks"][0]["task"], "Ship a usable workroom")
            self.assertEqual(goal_payload["tasks"][0]["source"], "goal")
            self.assertTrue((work / "team_state.json").exists())

            task = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "task",
                    "Review (model) workflow",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(task.returncode, 0, task.stderr + task.stdout)
            task_payload = json.loads(task.stdout)
            self.assertEqual(len(task_payload["tasks"]), 2)
            self.assertEqual(task_payload["tasks"][1]["task"], "Review (model) workflow")

            staff = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "staff",
                    "scout-1",
                    "Scout One",
                    "--staff-role",
                    "scout",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(staff.returncode, 0, staff.stderr + staff.stdout)
            staff_payload = json.loads(staff.stdout)
            self.assertEqual(staff_payload["employees"][0]["id"], "scout-1")
            self.assertEqual(staff_payload["employees"][0]["role"], "scout")

            assigned_role = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "assign-role",
                    "1",
                    "coordinator",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(assigned_role.returncode, 0, assigned_role.stderr + assigned_role.stdout)
            assigned_role_payload = json.loads(assigned_role.stdout)
            self.assertEqual(assigned_role_payload["tasks"][1]["assignedRole"], "coordinator")

            assigned_staff = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "assign-staff",
                    "1",
                    "scout-1",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(assigned_staff.returncode, 0, assigned_staff.stderr + assigned_staff.stdout)
            assigned_staff_payload = json.loads(assigned_staff.stdout)
            self.assertEqual(assigned_staff_payload["tasks"][1]["assignedEmployee"], "scout-1")
            self.assertEqual(assigned_staff_payload["tasks"][1]["assignedRole"], "scout")

            started = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "start",
                    "1",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
            started_payload = json.loads(started.stdout)
            self.assertEqual(started_payload["tasks"][1]["status"], "running")

            done = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "done",
                    "1",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            done_payload = json.loads(done.stdout)
            self.assertEqual(done_payload["tasks"][1]["status"], "done")

            status = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "status",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["mission"], "Ship a usable workroom")
            self.assertEqual(status_payload["teamModelPreset"], "save-credits")
            self.assertEqual(status_payload["roleModelEnv"]["coordinator"]["OPENROUTER_MODEL"], "fast")
            self.assertEqual(status_payload["roleModelEnvClear"]["scout"], ["OPENROUTER_MODEL", "CODEX_MODEL"])
            self.assertEqual(status_payload["teamModelSavings"]["savedUnits"], 5)
            self.assertEqual([item["task"] for item in status_payload["tasks"]], [
                "Ship a usable workroom",
                "Review (model) workflow",
            ])

            cleared = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "clear",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(cleared.returncode, 0, cleared.stderr + cleared.stdout)
            cleared_payload = json.loads(cleared.stdout)
            self.assertEqual(cleared_payload["clearedTasks"], 2)
            self.assertEqual(cleared_payload["tasks"], [])

            cleared_mission = subprocess.run(
                [
                    str(WORK_CMD_WRAPPER),
                    "clear-mission",
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(cleared_mission.returncode, 0, cleared_mission.stderr + cleared_mission.stdout)
            cleared_mission_payload = json.loads(cleared_mission.stdout)
            self.assertEqual(cleared_mission_payload["mission"], "")

    def test_workroom_model_profile_buttons_are_invokable(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        from ui.project_hub import show_project_hub

        from roost.state import TeamState

        def walk(widget):
            for child in widget.winfo_children():
                yield child
                yield from walk(child)

        with tempfile.TemporaryDirectory() as tmp:
            state = TeamState(Path(tmp) / "team_state.json")
            state.register_project("demo", display_name="Demo", security_level=0)
            state.set_model_profile(None, "openrouter/ui", "script", "openrouter", "ui/model", "low")
            state.set_active_model_profile(None, "openrouter/ui")

            try:
                root = tk.Tk()
            except tk.TclError as error:
                self.skipTest(f"Tk unavailable: {error}")

            root.withdraw()

            class FakeWidget:
                def __init__(self) -> None:
                    self.root = root
                    self.project_id = "demo"
                    self.state = "idle"
                    self._registry_path = None
                    self._project_display_name = "Demo"
                    self._hub_window = None
                    self._workroom_mode = True
                    self._workroom_window = None
                    self._team_state = state

                def save_workroom_window(self, hub) -> None:
                    return None

                def switch_project(self, project_id: str) -> None:
                    self.project_id = project_id

            fake = FakeWidget()
            try:
                show_project_hub(fake)
                root.update()
                hub = fake._hub_window
                self.assertIsNotNone(hub)

                notebook = next(child for child in walk(hub) if isinstance(child, ttk.Notebook))
                notebook.select(3)
                root.update()

                buttons = {
                    child.cget("text"): child
                    for child in walk(hub)
                    if isinstance(child, tk.Button) and child.cget("text") in {"Copy env", "Test model", "Local", "Value"}
                }
                self.assertEqual(set(buttons), {"Copy env", "Test model", "Local", "Value"})

                buttons["Copy env"].invoke()
                root.update()
                self.assertIn("$env:OPENROUTER_MODEL = 'ui/model'", root.clipboard_get())

                buttons["Test model"].invoke()
                root.update()
                labels = [child.cget("text") for child in walk(hub) if isinstance(child, tk.Label)]
                self.assertIn("[Test] openrouter/ui: OK local script", labels)

                buttons["Value"].invoke()
                root.update()
                self.assertEqual(state.get_active_model_profile()["tier"], "value")

                buttons["Local"].invoke()
                root.update()
                self.assertEqual(state.get_active_model_profile()["tier"], "local")

                preset_combo = next(
                    child
                    for child in walk(hub)
                    if isinstance(child, ttk.Combobox) and "all-value" in tuple(child.cget("values"))
                )
                preset_combo.set("all-value")
                preset_combo.event_generate("<<ComboboxSelected>>")
                root.update()
                self.assertEqual(state.get_team_model_preset_id(), "all-value")
            finally:
                root.destroy()

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
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            payload = json.dumps({"prompt": "Make the sub pet visible", "projectId": "gakju-demo"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
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
            log_entry = json.loads(log_file.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(log_entry["hook"], "user_prompt_submit")
            self.assertEqual(log_entry["event"], "start")
            self.assertEqual(log_entry["state"], "running")
            self.assertEqual(log_entry["projectId"], "gakju-demo")

    def test_codex_pet_hook_preserves_utf8_prompt_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            payload = json.dumps(
                {"prompt": "한글 bubble 확인", "projectId": "gakju-demo"},
                ensure_ascii=False,
            ).encode("utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
                    "--hook",
                    "user_prompt_submit",
                ],
                cwd=ROOT,
                input=payload,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                result.stderr.decode("utf-8", errors="replace") + result.stdout.decode("utf-8", errors="replace"),
            )
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["message"], "Working: 한글 bubble 확인")
            self.assertIn("한글 bubble 확인", state_file.read_text(encoding="utf-8"))

    def test_codex_pet_hook_stop_moves_bubble_to_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
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
            self.assertEqual(data["state"], "done")
            self.assertEqual(data["message"], "Done")
            self.assertEqual(data["resetAfterMs"], 1500)
            self.assertEqual(data["resetToState"], "idle")

    def test_codex_pet_hook_pre_tool_use_names_tool_without_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            payload = json.dumps({"tool_name": "apply_patch", "projectId": "gakju-demo"})

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
                    "--hook",
                    "pre_tool_use",
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
            self.assertEqual(data["message"], "Using apply_patch")

    def test_codex_pet_hook_post_tool_use_keeps_working_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
                    "--project-id",
                    "gakju-demo",
                    "--hook",
                    "post_tool_use",
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
            self.assertEqual(data["message"], "Working")

    def test_codex_pet_hook_refuses_unapproved_passthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            marker = Path(tmp) / "marker.txt"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
                    "--project-id",
                    "gakju-demo",
                    "--hook",
                    "notify",
                    "--passthrough",
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("passthrough requires --allow-passthrough", result.stderr + result.stdout)
            self.assertFalse(marker.exists())

    def test_codex_pet_hook_runs_approved_passthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            marker = Path(tmp) / "marker.txt"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HOOK_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--hook-log-file",
                    str(log_file),
                    "--project-id",
                    "gakju-demo",
                    "--hook",
                    "notify",
                    "--allow-passthrough",
                    "--passthrough",
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8"), "ran")


class PetStudioPreflightTests(unittest.TestCase):
    def test_preflight_renders_public_demo_with_skippable_local_install_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "preflight-render.png"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_SCRIPT),
                    "--skip-skill",
                    "--skip-hooks",
                    "--render-output",
                    str(output),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertTrue(data["ok"])
            self.assertEqual(data["projectId"], "gakju-archive-demo")
            self.assertEqual(Path(data["kitManifest"]).name, "project-room.json")
            self.assertIn("nextCommands", data)
            self.assertIn("launch", data["nextCommands"])
            self.assertIn("hookTrustHint", data)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)

    def test_preflight_validates_custom_registry_relative_project(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
            registry = Path(tmp) / "projects.json"
            kit_dir = ROOT / "runs" / "gakju-imagegen-room-v1" / "kit"
            write_json(
                registry,
                {
                    "schemaVersion": 1,
                    "projects": [
                        {
                            "projectId": "custom-demo",
                            "displayName": "Custom Demo",
                            "kitPath": str(relative_to_or_relpath(kit_dir, registry.parent)),
                            "petPackagePath": str(
                                (ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "pets" / "main-owner").resolve()
                            ),
                            "workspacePaths": [],
                            "defaultState": "idle",
                            "theme": "quiet archive nook",
                            "enabled": True,
                        }
                    ],
                },
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_SCRIPT),
                    "--skip-skill",
                    "--skip-hooks",
                    "--render-output",
                    str(Path(tmp) / "custom-render.png"),
                    "--json",
                    "--registry",
                    str(registry),
                    "--project-id",
                    "custom-demo",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertTrue(data["ok"])
            self.assertEqual(data["projectId"], "custom-demo")
            self.assertEqual(Path(data["kitManifest"]).resolve(), (kit_dir / "project-room.json").resolve())
            self.assertIn("--config", data["nextCommands"]["launch"])
            self.assertIn(str(registry), data["nextCommands"]["launch"])
            self.assertTrue(any(check["name"] == "kit-validation" and check["ok"] for check in data["checks"]))

    def test_preflight_reports_missing_skill_install_target(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            result = pet_studio_preflight.check_skill_install(Path(tmp) / "missing-skill")

        self.assertFalse(result.ok)
        self.assertIn("install_pet_studio_skill.py", result.message)

    def test_preflight_validates_project_registry_and_local_only_ignores(self) -> None:
        import pet_studio_preflight

        registry_result, project = pet_studio_preflight.check_project_registry(
            pet_studio_preflight.DEFAULT_REGISTRY,
            "gakju-archive-demo",
        )
        kit_result, manifest = pet_studio_preflight.check_project_kit(pet_studio_preflight.DEFAULT_REGISTRY, project)
        validation_result = pet_studio_preflight.validate_project_kit(ROOT, manifest)
        ignore_result = pet_studio_preflight.check_local_only_ignores(ROOT)
        team_model_result = pet_studio_preflight.check_team_model_plan()

        self.assertTrue(registry_result.ok, registry_result.message)
        self.assertTrue(kit_result.ok, kit_result.message)
        self.assertTrue(validation_result.ok, validation_result.message)
        self.assertTrue(ignore_result.ok, ignore_result.message)
        self.assertTrue(team_model_result.ok, team_model_result.message)
        self.assertIn("save-credits", team_model_result.message)
        self.assertIn("saved=5/9 units", team_model_result.message)
        self.assertIn("env=ok", team_model_result.message)

    def test_preflight_reports_registry_and_manifest_failures(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            missing_result, missing_project = pet_studio_preflight.check_project_registry(missing, "missing-demo")
            invalid = Path(tmp) / "invalid.json"
            invalid.write_text("{", encoding="utf-8")
            invalid_result, invalid_project = pet_studio_preflight.check_project_registry(invalid, "invalid-demo")
            no_projects = Path(tmp) / "no-projects.json"
            write_json(no_projects, {"schemaVersion": 1, "projects": {}})
            shape_result, shape_project = pet_studio_preflight.check_project_registry(no_projects, "shape-demo")
            disabled = Path(tmp) / "disabled.json"
            write_json(disabled, {"schemaVersion": 1, "projects": [{"projectId": "off", "enabled": False}]})
            disabled_result, disabled_project = pet_studio_preflight.check_project_registry(disabled, "off")
            missing_kit_path_result, _ = pet_studio_preflight.check_project_kit(
                disabled, {"projectId": "no-kit", "enabled": True}
            )
            missing_manifest_result, _ = pet_studio_preflight.check_project_kit(
                disabled,
                {"projectId": "missing-manifest", "enabled": True, "kitPath": "missing-kit"},
            )

        self.assertFalse(missing_result.ok)
        self.assertIsNone(missing_project)
        self.assertIn("Missing registry", missing_result.message)
        self.assertFalse(invalid_result.ok)
        self.assertIsNone(invalid_project)
        self.assertIn("Cannot read", invalid_result.message)
        self.assertFalse(shape_result.ok)
        self.assertIsNone(shape_project)
        self.assertIn("projects list", shape_result.message)
        self.assertIn('{"schemaVersion": 1, "projects": [...]', shape_result.message)
        self.assertFalse(disabled_result.ok)
        self.assertIsNotNone(disabled_project)
        self.assertIn("disabled", disabled_result.message)
        self.assertIn("enabled", disabled_result.message)
        self.assertFalse(missing_kit_path_result.ok)
        self.assertIn("kitPath", missing_kit_path_result.message)
        self.assertIn("project-room-projects.json", missing_kit_path_result.message)
        self.assertFalse(missing_manifest_result.ok)
        self.assertIn("Missing project manifest", missing_manifest_result.message)
        self.assertIn("Fix kitPath", missing_manifest_result.message)
        self.assertIn("tools\\pet_studio_create_room.py", missing_manifest_result.message)

    def test_preflight_unknown_project_message_has_register_and_list_hints(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(registry, {"schemaVersion": 1, "projects": []})

            result, project = pet_studio_preflight.check_project_registry(registry, "unknown-project")

        self.assertFalse(result.ok)
        self.assertIsNone(project)
        self.assertIn("tools\\pet_studio_create_room.py", result.message)
        self.assertIn("--list-projects", result.message)

    def test_preflight_cli_korean_lang_reports_unknown_project_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(registry, {"schemaVersion": 1, "projects": []})
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_SCRIPT),
                    "--project-id",
                    "unknown-project",
                    "--registry",
                    str(registry),
                    "--skip-render",
                    "--skip-hooks",
                    "--skip-skill",
                    "--lang",
                    "ko",
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                env=env,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("프로젝트가 registry에 등록되어 있지 않습니다", result.stdout + result.stderr)
        self.assertIn("해결:", result.stdout + result.stderr)
        self.assertIn("--list-projects", result.stdout + result.stderr)

    def test_preflight_cli_korean_lang_reports_missing_kitpath_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(registry, {"schemaVersion": 1, "projects": [{"projectId": "no-kit", "enabled": True}]})
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_SCRIPT),
                    "--project-id",
                    "no-kit",
                    "--registry",
                    str(registry),
                    "--skip-render",
                    "--skip-hooks",
                    "--skip-skill",
                    "--lang",
                    "ko",
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                env=env,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("프로젝트에 kitPath가 없습니다", result.stdout + result.stderr)
        self.assertIn("해결:", result.stdout + result.stderr)

    def test_preflight_json_output_remains_english_keyed_with_korean_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(registry, {"schemaVersion": 1, "projects": []})

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_SCRIPT),
                    "--project-id",
                    "unknown-project",
                    "--registry",
                    str(registry),
                    "--skip-render",
                    "--skip-hooks",
                    "--skip-skill",
                    "--json",
                    "--lang",
                    "ko",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            data = json.loads(result.stdout)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("projectId", data)
        self.assertIn("checks", data)
        registry_check = next(check for check in data["checks"] if check["name"] == "registry")
        self.assertIn("is not registered", registry_check["message"])
        self.assertNotIn("등록", registry_check["message"])

    def test_preflight_reports_validator_failure(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "kit" / "project-room.json"
            write_json(manifest, {"schemaVersion": 1, "layers": []})

            result = pet_studio_preflight.validate_project_kit(ROOT, manifest)

        self.assertFalse(result.ok)
        self.assertIn("Kit validation failed", result.message)

    def test_preflight_warns_for_incomplete_hook_config(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            hooks_file = Path(tmp) / "hooks.json"
            write_json(
                hooks_file,
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": f"{sys.executable} {HOOK_SCRIPT} --hook session_start",
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            result = pet_studio_preflight.check_hooks_config(hooks_file, "gakju-demo")

        self.assertTrue(result.ok)
        self.assertTrue(result.warning)
        self.assertIn("UserPromptSubmit", result.message)
        self.assertIn("Stop", result.message)
        self.assertIn("--project-id gakju-demo", result.message)
        self.assertIn("/hooks", result.message)

    def test_preflight_summarizes_hook_log_for_debugging(self) -> None:
        import pet_studio_preflight

        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "project-room-hook-events.jsonl"
            log_file.write_text(
                "\n".join(
                    [
                        json.dumps({"hook": "user_prompt_submit", "state": "running", "message": "Working"}),
                        json.dumps({"hook": "post_tool_use", "state": "running", "message": "Working"}),
                        json.dumps({"hook": "stop", "state": "done", "message": "Done"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = pet_studio_preflight.read_hook_log_summary(log_file, 2)

        self.assertEqual(summary, ["post_tool_use -> running: Working", "stop -> done: Done"])


class PetStudioDemoStateCyclerTests(unittest.TestCase):
    def test_demo_state_sequence_includes_expected_messages_and_final_idle(self) -> None:
        import pet_studio_demo_states

        steps = pet_studio_demo_states.build_demo_sequence()

        self.assertEqual(
            [step.state for step in steps], ["idle", "running", "waiting", "blocked", "review", "done", "idle"]
        )
        self.assertEqual(
            [step.message for step in steps],
            ["", "Working...", "Compacting context...", "Needs input", "Ready for review", "Done", ""],
        )

    def test_demo_state_payload_shape_uses_existing_bridge_contract(self) -> None:
        import pet_studio_demo_states

        payload = pet_studio_demo_states.payload_for_step(
            "gakju-archive-demo",
            pet_studio_demo_states.DemoStep("done", "Done"),
            updated_at="2026-06-15T00:00:00Z",
            delay_seconds=2.0,
        )

        self.assertEqual(
            payload,
            {
                "projectId": "gakju-archive-demo",
                "state": "done",
                "message": "Done",
                "updatedAt": "2026-06-15T00:00:00Z",
            },
        )

    def test_demo_state_dry_run_prints_json_and_does_not_write_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS_DIR / "pet_studio_demo_states.py"),
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertTrue(data["ok"])
            self.assertTrue(data["dryRun"])
            self.assertEqual(data["projectId"], "gakju-archive-demo")
            self.assertEqual(data["sequence"][1]["state"], "running")
            self.assertEqual(data["sequence"][1]["message"], "Working...")
            self.assertFalse(state_file.exists())

    def test_demo_state_once_writes_sequence_and_ends_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS_DIR / "pet_studio_demo_states.py"),
                    "--project-id",
                    "gakju-archive-demo",
                    "--state-file",
                    str(state_file),
                    "--once",
                    "--delay-seconds",
                    "0",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertTrue(data["ok"])
            self.assertFalse(data["dryRun"])
            self.assertEqual(data["cyclesCompleted"], 1)
            self.assertEqual(data["writes"], 7)
            payload = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["projectId"], "gakju-archive-demo")
            self.assertEqual(payload["state"], "idle")
            self.assertEqual(payload["message"], "")

    def test_demo_state_delay_alias_matches_delay_seconds(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS_DIR / "pet_studio_demo_states.py"),
                "--project-id",
                "gakju-archive-demo",
                "--delay",
                "1.5",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data["delaySeconds"], 1.5)
        done_payload = next(payload for payload in data["payloads"] if payload["state"] == "done")
        self.assertNotIn("resetAfterMs", done_payload)
        self.assertNotIn("resetToState", done_payload)


class PetStudioCodexIntegrationInstallerTests(unittest.TestCase):
    def test_hook_command_shell_args_quote_shell_metacharacters(self) -> None:
        from install_pet_studio_codex_integration import command_string

        command = command_string(
            [
                r"C:\Program Files\Python\python.exe",
                r"D:\pet & studio\pet-studio-widget\codex_pet_hook.py",
                "--hook",
                "stop",
            ]
        )

        self.assertIn('"D:\\\\pet & studio\\\\pet-studio-widget\\\\codex_pet_hook.py"', command)
        self.assertIn('"C:\\\\Program Files\\\\Python\\\\python.exe"', command)
        self.assertNotIn(r"D:\pet & studio\pet-studio-widget\codex_pet_hook.py --hook", command)

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
            stop_commands = [hook["command"] for group in data["hooks"]["Stop"] for hook in group["hooks"]]
            self.assertIn("python existing_stop.py", stop_commands)
            self.assertTrue(
                any("codex_pet_hook.py" in command and "--hook stop" in command for command in stop_commands)
            )
            prompt_hook = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]
            self.assertEqual(prompt_hook["type"], "command")
            self.assertIn("codex_pet_hook.py", prompt_hook["command"])
            self.assertIn("pet-studio-widget", prompt_hook["command"])
            self.assertIn("--hook user_prompt_submit", prompt_hook["command"])
            self.assertEqual(prompt_hook["timeout"], 30)
            self.assertEqual(
                result["events"],
                ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop"],
            )

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
            stop_commands = [hook["command"] for group in data["hooks"]["Stop"] for hook in group["hooks"]]
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

    def test_notify_bridge_marks_preserved_notify_as_approved_passthrough(self) -> None:
        from install_pet_studio_codex_integration import install_notify_bridge

        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / ".codex" / "config.toml"
            config_file.parent.mkdir(parents=True)
            config_file.write_text('notify = [ "python", "existing_notify.py" ]\n', encoding="utf-8")

            result = install_notify_bridge(config_file, dry_run=False)

            text = config_file.read_text(encoding="utf-8")
            self.assertIn("--allow-passthrough", text)
            self.assertIn("--passthrough", text)
            self.assertEqual(result["previousNotify"], ["python", "existing_notify.py"])
            self.assertIn("--allow-passthrough", result["nextNotify"])

    def test_default_hooks_file_is_project_local(self) -> None:
        from install_pet_studio_codex_integration import HOOKS_PATH

        self.assertEqual(HOOKS_PATH, ROOT / ".codex" / "hooks.json")

    def test_skill_installer_force_refuses_workspace_root_delete(self) -> None:
        from install_pet_studio_skill import install

        with self.assertRaises(SystemExit) as raised:
            install(ROOT, force=True)

        self.assertIn("Refusing to replace unsafe skill destination", str(raised.exception))
        self.assertTrue((ROOT / ".git").exists())

    def test_skill_installer_records_repo_location_for_widget_launcher(self) -> None:
        from install_pet_studio_skill import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "pet-studio"

            install(destination, force=False)

            location = json.loads((destination / "repo-location.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(location["repoRoot"]), ROOT)
            self.assertEqual(Path(location["widgetEntrypoint"]), WIDGET_SCRIPT)
            self.assertTrue((destination / "scripts" / "launch_pet_studio_widget.py").exists())

    def test_installed_skill_widget_launcher_uses_recorded_repo_runtime(self) -> None:
        from install_pet_studio_skill import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "pet-studio"
            install(destination, force=False)

            result = subprocess.run(
                [
                    sys.executable,
                    str(destination / "scripts" / "launch_pet_studio_widget.py"),
                    "--foreground",
                    "--list-projects",
                ],
                cwd=Path(tmp),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("gakju-archive-demo", result.stdout)
            self.assertNotIn("minimal widget", result.stderr.lower() + result.stdout.lower())

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
