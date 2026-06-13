from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "project-room-kit" / "scripts" / "create_project_room_kit.py"
VALIDATOR = ROOT / "project-room-kit" / "scripts" / "validate_project_room_kit.py"
ASSET_HELPERS = ROOT / "project-room-kit" / "scripts" / "project_room_assets.py"
BAKE_SCRIPT = ROOT / "project-room-kit" / "scripts" / "bake_project_room_pet.py"


STATE_FRAMES = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def make_pet_package(path: Path, *, size: tuple[int, int] = (1536, 1872)) -> None:
    path.mkdir(parents=True, exist_ok=True)
    write_json(
        path / "pet.json",
        {
            "id": "sample-pet",
            "displayName": "Sample Pet",
            "description": "A test hatch-pet package.",
            "spritesheetPath": "spritesheet.webp",
        },
    )
    atlas = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(atlas)
    for row, state in enumerate(STATE_FRAMES):
        for frame in range(STATE_FRAMES[state]):
            x = frame * 192 + 70
            y = row * 208 + 94
            draw.rounded_rectangle((x, y, x + 44, y + 62), radius=14, fill=(80, 130, 170, 255))
    atlas.save(path / "spritesheet.webp", "WEBP", lossless=True, quality=100)


def make_room(path: Path, *, size: tuple[int, int] = (384, 240)) -> None:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, size[0] - 5, size[1] - 5), radius=12, fill=(248, 252, 247, 255))
    if size == (384, 240):
        draw.line((18, 182, 366, 182), fill=(36, 49, 58, 255), width=2)
        draw.rounded_rectangle((12, 84, 54, 184), radius=7, fill=(220, 230, 225, 255))
        draw.rounded_rectangle((330, 84, 372, 184), radius=7, fill=(220, 230, 225, 255))
    img.save(path)


def make_room_with_edge_margin(path: Path) -> None:
    img = Image.new("RGBA", (384, 240), (248, 246, 245, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 22, 383, 216), radius=10, fill=(248, 252, 247, 255), outline=(36, 49, 58, 255), width=3)
    draw.rectangle((24, 76, 92, 180), fill=(238, 242, 236, 255))
    img.save(path)


def make_room_with_soft_edge_halo(path: Path) -> None:
    img = Image.new("RGBA", (384, 240), (232, 236, 230, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((20, 20, 363, 219), outline=(36, 49, 58, 255), width=3)
    draw.rectangle((24, 24, 359, 215), fill=(232, 236, 230, 255))
    draw.line((24, 182, 359, 182), fill=(36, 49, 58, 255), width=2)
    img.save(path)


def make_room_with_pastel_edge_halo(path: Path) -> None:
    img = Image.new("RGBA", (384, 240), (224, 232, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((20, 20, 363, 219), outline=(36, 49, 58, 255), width=3)
    draw.rectangle((24, 24, 359, 215), fill=(224, 232, 255, 255))
    draw.line((24, 182, 359, 182), fill=(36, 49, 58, 255), width=2)
    img.save(path)


def make_prop(path: Path) -> None:
    img = Image.new("RGBA", (96, 54), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((5, 20, 91, 42), radius=5, fill=(170, 120, 80, 255))
    draw.rectangle((16, 42, 24, 53), fill=(120, 80, 55, 255))
    draw.rectangle((72, 42, 80, 53), fill=(120, 80, 55, 255))
    img.save(path)


class ProjectRoomPipelineTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creates_kit_prompts_validation_and_previews_from_pet_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--theme",
                "quiet archive nook",
                "--display-name",
                "Archive Nook",
                "--render-preview",
                "--render-contact",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            kit_dir = out / "kit"
            manifest = json.loads((kit_dir / "project-room.json").read_text(encoding="utf-8"))
            style = json.loads((kit_dir / "style-lock.json").read_text(encoding="utf-8"))
            prop_meta = json.loads((kit_dir / "props" / "desk.asset.json").read_text(encoding="utf-8"))
            report = json.loads((out / "production-report.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["displayName"], "Archive Nook")
            self.assertEqual(manifest["sourceCanvas"], {"width": 384, "height": 240, "purpose": "layered Pet Studio widget canvas"})
            self.assertEqual(style["sourcePolicy"]["selectedSource"]["type"], "existing hatch-pet pet package")
            self.assertEqual(style["sourcePolicy"]["selectedSource"]["petId"], "sample-pet")
            self.assertEqual(prop_meta["role"], "prop")
            self.assertEqual(prop_meta["assetType"], "prop")
            self.assertIn("desk", manifest["anchors"])
            layers = {layer["id"]: layer for layer in manifest["layers"]}
            self.assertEqual(layers["desk"]["placement"], "behindPet")
            self.assertLess(layers["desk"]["z"], layers["main-owner"]["z"])
            self.assertTrue(layers["desk"]["draggable"])
            self.assertFalse(layers["desk"]["locked"])
            self.assertFalse(layers["room"]["draggable"])
            self.assertTrue(layers["room"]["locked"])
            self.assertTrue((out / "generation-brief.json").exists())
            self.assertIn("SD/chibi dollhouse room", (out / "prompts" / "room-prompt.txt").read_text(encoding="utf-8"))
            self.assertTrue((out / "room-preview.png").exists())
            self.assertTrue((out / "room-contact.png").exists())
            self.assertTrue(report["validation"]["ok"])

            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--kit",
                    str(kit_dir / "project-room.json"),
                    "--json-out",
                    str(out / "kit-validation-rerun.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)

    def test_room_margin_cleanup_makes_edge_connected_near_white_transparent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room-with-margin.png"
            out = work / "out"
            make_pet_package(pet)
            make_room_with_edge_margin(room)

            result = self.run_cli("--out-dir", str(out), "--pet-package", str(pet), "--room-image", str(room))

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            cleaned = Image.open(out / "kit" / "rooms" / "default-room.png").convert("RGBA")
            self.assertEqual(cleaned.size, (384, 240))
            self.assertEqual(cleaned.getpixel((10, 10))[3], 0)
            self.assertEqual(cleaned.getpixel((192, 230))[3], 0)
            self.assertEqual(cleaned.getpixel((192, 60))[3], 255)
            self.assertEqual(cleaned.getpixel((30, 90))[3], 255)

            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--kit",
                    str(out / "kit" / "project-room.json"),
                    "--json-out",
                    str(out / "cleaned-validation.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)

    def test_room_margin_detector_warns_on_uncleaned_edge_connected_near_white(self) -> None:
        spec = importlib.util.spec_from_file_location("project_room_assets", ASSET_HELPERS)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            room = Path(tmp) / "room-with-margin.png"
            make_room_with_edge_margin(room)

            self.assertGreater(module.room_edge_margin_pixel_count(room), 0)

    def test_room_alpha_modes_have_distinct_cleanup_strengths(self) -> None:
        spec = importlib.util.spec_from_file_location("project_room_assets", ASSET_HELPERS)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            soft = work / "soft-halo.png"
            pastel = work / "pastel-halo.png"
            make_room_with_soft_edge_halo(soft)
            make_room_with_pastel_edge_halo(pastel)

            with Image.open(soft) as image:
                safe = module.remove_room_edge_margin(image, mode="safe")
                balanced = module.remove_room_edge_margin(image, mode="balanced")
            self.assertEqual(safe.getpixel((5, 5))[3], 255)
            self.assertEqual(balanced.getpixel((5, 5))[3], 0)
            self.assertEqual(balanced.getpixel((192, 120))[3], 255)

            with Image.open(pastel) as image:
                balanced_pastel = module.remove_room_edge_margin(image, mode="balanced")
                aggressive = module.remove_room_edge_margin(image, mode="aggressive")
            self.assertEqual(balanced_pastel.getpixel((5, 5))[3], 255)
            self.assertEqual(aggressive.getpixel((5, 5))[3], 0)
            self.assertEqual(aggressive.getpixel((192, 120))[3], 255)

    def test_create_kit_uses_balanced_room_alpha_cleanup_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "soft-halo.png"
            out = work / "out"
            make_pet_package(pet)
            make_room_with_soft_edge_halo(room)

            result = self.run_cli("--out-dir", str(out), "--pet-package", str(pet), "--room-image", str(room))

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            cleaned = Image.open(out / "kit" / "rooms" / "default-room.png").convert("RGBA")
            self.assertEqual(cleaned.getpixel((5, 5))[3], 0)
            self.assertEqual(cleaned.getpixel((192, 120))[3], 255)

    def test_create_kit_can_use_safe_room_alpha_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "soft-halo.png"
            out = work / "out"
            make_pet_package(pet)
            make_room_with_soft_edge_halo(room)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--room-alpha-mode",
                "safe",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            cleaned = Image.open(out / "kit" / "rooms" / "default-room.png").convert("RGBA")
            self.assertEqual(cleaned.getpixel((5, 5))[3], 255)

    def test_registers_created_kit_in_project_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            registry = work / "project-room-projects.json"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--theme",
                "quiet archive nook",
                "--display-name",
                "Archive Nook",
                "--register-project",
                "--project-id",
                "archive-nook",
                "--registry",
                str(registry),
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(data["schemaVersion"], 1)
            self.assertEqual(len(data["projects"]), 1)
            project = data["projects"][0]
            self.assertEqual(project["projectId"], "archive-nook")
            self.assertEqual(project["displayName"], "Archive Nook")
            self.assertEqual(project["defaultState"], "idle")
            self.assertEqual(project["theme"], "quiet archive nook")
            self.assertTrue(project["enabled"])
            self.assertEqual((registry.parent / project["kitPath"]).resolve(), (out / "kit").resolve())
            report = json.loads((out / "production-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["projectLink"]["projectId"], "archive-nook")
            self.assertEqual(Path(report["projectLink"]["registryPath"]), registry.resolve())

    def test_registers_workspace_path_with_created_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            registry = work / "project-room-projects.json"
            workspace = work / "workspace"
            workspace.mkdir()
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--register-project",
                "--project-id",
                "archive-nook",
                "--registry",
                str(registry),
                "--workspace-path",
                str(workspace),
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(registry.read_text(encoding="utf-8"))
            project = data["projects"][0]
            self.assertEqual(project["workspacePaths"], [str(workspace.resolve())])
            report = json.loads((out / "production-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["projectLink"]["workspacePaths"], [str(workspace.resolve())])

    def test_prop_placement_controls_layer_order_relative_to_main_pet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            plant = work / "plant.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)
            make_prop(plant)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--prop",
                f"plant={plant}",
                "--prop-placement",
                "desk=behind-pet",
                "--prop-placement",
                "plant=front-of-pet",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((out / "kit" / "project-room.json").read_text(encoding="utf-8"))
            layers = {layer["id"]: layer for layer in manifest["layers"]}
            self.assertEqual(layers["desk"]["placement"], "behindPet")
            self.assertEqual(layers["plant"]["placement"], "frontOfPet")
            self.assertLess(layers["desk"]["z"], layers["main-owner"]["z"])
            self.assertGreater(layers["plant"]["z"], layers["main-owner"]["z"])

    def test_foreground_props_default_to_pet_clear_right_floor_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            book_stack = work / "book-stack.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)
            make_prop(book_stack)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--prop",
                f"book-stack={book_stack}",
                "--prop-placement",
                "book-stack=foreground",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((out / "kit" / "project-room.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["anchors"]["owner"], {"x": 96, "y": 206})
            self.assertGreaterEqual(manifest["anchors"]["book-stack"]["x"], 320)
            self.assertGreaterEqual(manifest["anchors"]["book-stack"]["y"], 216)

    def test_contact_sheet_reserves_left_gutter_for_state_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--render-contact",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            with Image.open(out / "room-contact.png") as image:
                self.assertEqual(image.size[0], 3 * (384 + 92) + 2 * 10)
                first_label_gutter = image.crop((0, 0, 92, 28))
                first_frame_area = image.crop((92, 28, 92 + 384, 28 + 240))
                self.assertIsNotNone(first_label_gutter.getbbox())
                self.assertIsNotNone(first_frame_area.getbbox())

    def test_scale_visible_layer_can_flip_asymmetric_layer(self) -> None:
        spec = importlib.util.spec_from_file_location("bake_project_room_pet", BAKE_SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        layer = Image.new("RGBA", (4, 2), (0, 0, 0, 0))
        layer.putpixel((0, 0), (255, 0, 0, 255))
        layer.putpixel((3, 0), (0, 0, 255, 255))

        flipped = module.scale_visible_layer(layer, 1.0, flip_x=True)

        self.assertEqual(flipped.getpixel((0, 0)), (0, 0, 255, 255))
        self.assertEqual(flipped.getpixel((3, 0)), (255, 0, 0, 255))

    def test_validator_rejects_non_boolean_flip_x(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)

            result = self.run_cli("--out-dir", str(out), "--pet-package", str(pet), "--room-image", str(room))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            manifest_path = out / "kit" / "project-room.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["layers"][0]["flipX"] = "yes"
            write_json(manifest_path, manifest)

            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--kit",
                    str(manifest_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(validation.returncode, 0)
            self.assertIn("invalid flipX", validation.stderr + validation.stdout)

    def test_rejects_unknown_prop_placement_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--prop-placement",
                "unknown=front-of-pet",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Prop placement references unknown prop id", result.stderr + result.stdout)

    def test_helper_pet_is_mapped_for_review_and_blocked_scenes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            helper = work / "helper"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            make_pet_package(pet)
            make_pet_package(helper)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
                "--helper-package",
                f"reviewer={helper}",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((out / "kit" / "project-room.json").read_text(encoding="utf-8"))
            helper_layer = next(layer for layer in manifest["layers"] if layer["id"] == "reviewer")
            self.assertEqual(helper_layer["visibleWhen"], ["review", "failed"])
            self.assertIn("reviewer", manifest["states"]["review"]["visibleLayers"])
            self.assertIn("reviewer", manifest["states"]["failed"]["visibleLayers"])
            self.assertEqual(manifest["states"]["review"]["helperPetRow"], "review")
            self.assertEqual(manifest["states"]["failed"]["helperPetRow"], "review")

    def test_rejects_bad_pet_atlas_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            make_pet_package(pet, size=(192, 208))
            make_room(room)

            result = self.run_cli("--out-dir", str(out), "--pet-package", str(pet), "--room-image", str(room))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected 1536x1872", result.stderr + result.stdout)

    def test_rejects_bad_room_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room, size=(192, 208))

            result = self.run_cli("--out-dir", str(out), "--pet-package", str(pet), "--room-image", str(room))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected 384x240", result.stderr + result.stdout)

    def test_validator_rejects_transparent_rgb_residue_in_registered_props(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"desk={desk}",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            prop_path = out / "kit" / "props" / "desk.png"
            dirty = Image.new("RGBA", (96, 54), (255, 0, 0, 0))
            dirty.save(prop_path)

            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--kit",
                    str(out / "kit" / "project-room.json"),
                    "--json-out",
                    str(out / "dirty-validation.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(validation.returncode, 0)
            self.assertIn("transparent RGB residue", validation.stderr + validation.stdout)

    def test_asset_cleanup_removes_low_alpha_chroma_fringe(self) -> None:
        spec = importlib.util.spec_from_file_location("project_room_assets", ASSET_HELPERS)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        image = Image.new("RGBA", (3, 1), (0, 0, 0, 0))
        image.putpixel((0, 0), (255, 0, 255, 12))
        image.putpixel((1, 0), (255, 0, 255, 96))
        image.putpixel((2, 0), (200, 80, 160, 12))

        cleaned = module.clear_transparent_rgb(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(cleaned.getpixel((1, 0)), (255, 0, 255, 96))
        self.assertEqual(cleaned.getpixel((2, 0)), (200, 80, 160, 12))

    def test_bake_cleanup_removes_low_alpha_chroma_fringe(self) -> None:
        spec = importlib.util.spec_from_file_location("bake_project_room_pet", BAKE_SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        image = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
        image.putpixel((0, 0), (255, 0, 255, 12))
        image.putpixel((1, 0), (255, 0, 255, 96))

        cleaned = module.clear_transparent_rgb(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(cleaned.getpixel((1, 0)), (255, 0, 255, 96))


if __name__ == "__main__":
    unittest.main()
