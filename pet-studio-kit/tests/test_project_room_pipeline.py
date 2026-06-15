from __future__ import annotations

import json
import importlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "create_project_room_kit.py"
VALIDATOR = ROOT / "pet-studio-kit" / "scripts" / "validate_project_room_kit.py"
ASSET_HELPERS = ROOT / "pet-studio-kit" / "scripts" / "project_room_assets.py"
BAKE_SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "bake_project_room_pet.py"
RENDER_SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "render_project_room_preview.py"
GUIDED_CREATE_SCRIPT = ROOT / "tools" / "pet_studio_create_room.py"
QA_PACK_SCRIPT = ROOT / "tools" / "pet_studio_create_qa_pack.py"


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


def make_empty_prop(path: Path) -> None:
    Image.new("RGBA", (96, 54), (0, 0, 0, 0)).save(path)


def make_oversized_prop(path: Path) -> None:
    img = Image.new("RGBA", (385, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((8, 20, 376, 108), radius=8, fill=(170, 120, 80, 255))
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

    def create_basic_kit(self, work: Path) -> Path:
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
            "security check",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return out / "kit" / "project-room.json"

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

    def test_guided_create_room_dry_run_uses_first_room_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            command = data["command"]
            self.assertTrue(data["dryRun"])
            self.assertIn("--render-preview", command)
            self.assertIn("--render-contact", command)
            self.assertIn("--register-project", command)
            self.assertIn("--workspace-path", command)
            self.assertIn(str(ROOT / "runs" / "first-room"), command)
            self.assertEqual(data["nextCommands"]["launch"], ".\\tools\\pet_studio_widget.cmd --project-id first-room --scale 1.25")

    def test_guided_create_room_creates_registered_kit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            desk = work / "desk.png"
            out = work / "out"
            registry = work / "projects.json"
            workspace = work / "workspace"
            workspace.mkdir()
            make_pet_package(pet)
            make_room(room)
            make_prop(desk)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--prop",
                    f"desk={desk}",
                    "--prop-placement",
                    "desk=behind-pet",
                    "--out-dir",
                    str(out),
                    "--registry",
                    str(registry),
                    "--workspace-path",
                    str(workspace),
                    "--theme",
                    "quiet archive nook",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((out / "kit" / "project-room.json").exists())
            self.assertTrue((out / "room-preview.png").exists())
            self.assertTrue((out / "room-contact.png").exists())
            config = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(config["projects"][0]["projectId"], "first-room")
            self.assertEqual(config["projects"][0]["workspacePaths"], [str(workspace.resolve())])
            summary = json.loads(result.stdout)
            self.assertIn("pet_studio_widget.cmd --config", summary["nextCommands"]["launch"])
            self.assertIn(str(registry), summary["nextCommands"]["launch"])
            self.assertIn("--project-id first-room --scale 1.25", summary["nextCommands"]["launch"])

    def test_guided_create_room_prints_concise_summary_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            registry = work / "projects.json"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(out),
                    "--registry",
                    str(registry),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertTrue(data["ok"])
            self.assertEqual(data["projectId"], "first-room")
            self.assertEqual(data["artifacts"]["kit"], str(out / "kit" / "project-room.json"))
            self.assertEqual(data["artifacts"]["validation"], str(out / "kit-validation.json"))
            self.assertEqual(data["artifacts"]["preview"], str(out / "room-preview.png"))
            self.assertEqual(data["artifacts"]["contact"], str(out / "room-contact.png"))

    def test_guided_create_room_next_commands_include_custom_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            registry = work / "projects.json"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--registry",
                    str(registry),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            commands = data["nextCommands"]
            self.assertIn("--registry", commands["preflight"])
            self.assertIn(str(registry), commands["preflight"])
            self.assertIn("--config", commands["launch"])
            self.assertIn(str(registry), commands["launch"])
            self.assertIn("--config", commands["render"])
            self.assertIn(str(registry), commands["render"])
            self.assertIn("--registry", commands["qaPack"])
            self.assertIn(str(registry), commands["qaPack"])

    def test_guided_create_room_refuses_existing_output_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            out = work / "out"
            out.mkdir()
            (out / "keep.txt").write_text("existing work", encoding="utf-8")
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--force", result.stderr + result.stdout)
            self.assertEqual((out / "keep.txt").read_text(encoding="utf-8"), "existing work")

    def test_guided_create_room_force_refuses_workspace_root_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "danger-demo",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(ROOT),
                    "--force",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to replace unsafe output directory", result.stderr + result.stdout)
            self.assertTrue((ROOT / ".git").exists())

    def test_guided_create_room_force_refuses_workspace_code_dir_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "danger-demo",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(ROOT / "pet-studio-kit"),
                    "--force",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to replace unsafe output directory", result.stderr + result.stdout)
            self.assertTrue((ROOT / "pet-studio-kit" / "SKILL.md").exists())

    def test_qa_pack_creates_local_evidence_from_custom_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            kit_out = work / "room-output"
            registry = work / "projects.json"
            qa_out = work / "qa-pack"
            make_pet_package(pet)
            make_room(room)

            create = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "qa-demo",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(kit_out),
                    "--registry",
                    str(registry),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(create.returncode, 0, create.stderr + create.stdout)

            result = subprocess.run(
                [
                    sys.executable,
                    str(QA_PACK_SCRIPT),
                    "--project-id",
                    "qa-demo",
                    "--registry",
                    str(registry),
                    "--out-dir",
                    str(qa_out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["ok"])
            self.assertEqual(summary["projectId"], "qa-demo")
            self.assertEqual(summary["outDir"], str(qa_out))
            for name in (
                "validation",
                "idleRender",
                "allStatesContact",
                "widgetRender",
                "coderToQa",
                "summary",
            ):
                self.assertTrue(Path(summary["artifacts"][name]).exists(), name)
            handoff = (qa_out / "CODER_TO_QA.md").read_text(encoding="utf-8")
            self.assertIn("qa-demo", handoff)
            self.assertIn("project-room.json", handoff)
            self.assertIn("all-states-contact.png", handoff)
            self.assertIn("widget-render.png", handoff)

    def test_qa_pack_fails_clearly_for_unknown_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(registry, {"schemaVersion": 1, "projects": []})

            result = subprocess.run(
                [
                    sys.executable,
                    str(QA_PACK_SCRIPT),
                    "--project-id",
                    "missing-demo",
                    "--registry",
                    str(registry),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unknown project id", result.stderr + result.stdout)

    def test_qa_pack_fails_clearly_for_disabled_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "projects.json"
            write_json(
                registry,
                {
                    "schemaVersion": 1,
                    "projects": [
                        {
                            "projectId": "disabled-demo",
                            "displayName": "Disabled Demo",
                            "kitPath": str((ROOT / "runs" / "gakju-imagegen-room-v1" / "kit").resolve()),
                            "petPackagePath": None,
                            "workspacePaths": [],
                            "defaultState": "idle",
                            "theme": "",
                            "enabled": False,
                        }
                    ],
                },
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(QA_PACK_SCRIPT),
                    "--project-id",
                    "disabled-demo",
                    "--registry",
                    str(registry),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("disabled", result.stderr + result.stdout)

    def test_helper_pet_is_mapped_for_all_widget_states(self) -> None:
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
            self.assertNotIn("visibleWhen", helper_layer)
            for state in STATE_FRAMES:
                with self.subTest(state=state):
                    self.assertIn("reviewer", manifest["states"][state]["visibleLayers"])
                    self.assertEqual(manifest["states"][state]["helperPetRow"], "review")

    def test_guardrails_reject_duplicate_prop_ids(self) -> None:
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
                f"desk={plant}",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate prop id `desk`", result.stderr + result.stdout)

    def test_guardrails_reject_prop_and_helper_id_collision(self) -> None:
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
                f"reviewer={desk}",
                "--helper-package",
                f"reviewer={helper}",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("used by both a prop and helper", result.stderr + result.stdout)

    def test_guardrails_reject_asset_ids_that_can_escape_generated_paths(self) -> None:
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
                f"..\\escape={desk}",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not safe for generated file paths", result.stderr + result.stdout)
        self.assertFalse((work / "escape.png").exists())

    def test_guided_create_room_rejects_project_ids_that_escape_runs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room)

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "..\\escape",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not safe for generated file paths", result.stderr + result.stdout)

    def test_guided_create_room_korean_lang_reports_unsafe_project_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room)
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "..\\escape",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--dry-run",
                    "--lang",
                    "ko",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("프로젝트 id", result.stderr + result.stdout)
        self.assertIn("안전하지 않습니다", result.stderr + result.stdout)

    def test_generator_rejects_unsafe_registered_project_id(self) -> None:
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
                "--register-project",
                "--project-id",
                "../escape",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not safe for generated file paths", result.stderr + result.stdout)

    def test_validator_rejects_manifest_layer_paths_that_escape_kit_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_path = self.create_basic_kit(work)
            manifest = json.loads(kit_path.read_text(encoding="utf-8"))
            manifest["layers"][0]["path"] = "../outside.png"
            write_json(kit_path, manifest)

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--kit", str(kit_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escapes the kit directory", result.stdout + result.stderr)

    def test_validator_rejects_style_lock_path_that_escapes_kit_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_path = self.create_basic_kit(work)
            manifest = json.loads(kit_path.read_text(encoding="utf-8"))
            manifest["styleLock"] = "../style-lock.json"
            write_json(kit_path, manifest)

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--kit", str(kit_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("styleLock", result.stdout + result.stderr)
        self.assertIn("escapes the kit directory", result.stdout + result.stderr)

    def test_preview_and_bake_reject_manifest_layer_paths_that_escape_kit_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_path = self.create_basic_kit(work)
            manifest = json.loads(kit_path.read_text(encoding="utf-8"))
            manifest["layers"][1]["path"] = "../outside.png"
            write_json(kit_path, manifest)
            preview = subprocess.run(
                [sys.executable, str(RENDER_SCRIPT), "--kit", str(kit_path), "--state", "idle", "--out", str(work / "preview.png")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            bake = subprocess.run(
                [sys.executable, str(BAKE_SCRIPT), "--kit", str(kit_path), "--out-dir", str(work / "baked")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(preview.returncode, 0)
        self.assertIn("escapes the kit directory", preview.stdout + preview.stderr)
        self.assertNotEqual(bake.returncode, 0)
        self.assertIn("escapes the kit directory", bake.stdout + bake.stderr)

    def test_preview_rejects_manifest_prop_larger_than_room_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_path = self.create_basic_kit(work)
            oversized = Image.new("RGBA", (512, 16), (180, 120, 80, 255))
            oversized.save(kit_path.parent / "props" / "desk.png")

            result = subprocess.run(
                [sys.executable, str(RENDER_SCRIPT), "--kit", str(kit_path), "--state", "idle", "--out", str(work / "preview.png")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("maximum for role `prop`", result.stdout + result.stderr)

    def test_guardrails_reject_empty_and_oversized_props(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            empty = work / "empty.png"
            oversized = work / "oversized.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_empty_prop(empty)
            make_oversized_prop(oversized)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"empty={empty}",
                "--prop",
                f"oversized={oversized}",
            )

        output = result.stderr + result.stdout
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has no visible opaque pixels", output)
        self.assertIn("must fit inside the 384x240 room canvas", output)

    def test_guardrails_reject_malformed_prop_image_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            malformed = work / "malformed.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            malformed.write_text("not an image", encoding="utf-8")

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--prop",
                f"malformed={malformed}",
            )

        output = result.stderr + result.stdout
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be read as an image", output)
        self.assertFalse((out / "kit" / "props" / "malformed.png").exists())

    def test_validator_preview_and_bake_reject_malformed_manifest_prop_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kit_path = self.create_basic_kit(work)
            (kit_path.parent / "props" / "desk.png").write_text("not an image", encoding="utf-8")

            validator = subprocess.run(
                [sys.executable, str(VALIDATOR), "--kit", str(kit_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            preview = subprocess.run(
                [sys.executable, str(RENDER_SCRIPT), "--kit", str(kit_path), "--state", "idle", "--out", str(work / "preview.png")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            bake = subprocess.run(
                [sys.executable, str(BAKE_SCRIPT), "--kit", str(kit_path), "--out-dir", str(work / "baked")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        for result in (validator, preview, bake):
            output = result.stderr + result.stdout
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Image cannot be read", output)

    def test_guardrails_reject_invalid_helper_package_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            helper = work / "helper"
            room = work / "room.png"
            out = work / "out"
            make_pet_package(pet)
            helper.mkdir()
            write_json(helper / "pet.json", {"id": "bad-helper", "spritesheetPath": "missing.webp"})
            make_room(room)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--helper-package",
                f"reviewer={helper}",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has no valid spritesheet path", result.stderr + result.stdout)

    def test_guardrails_report_room_alpha_warnings_and_off_mode_suppresses_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room-with-margin.png"
            out = work / "out"
            make_pet_package(pet)
            make_room_with_edge_margin(room)

            basic = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(out),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            off = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "first-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--out-dir",
                    str(out),
                    "--guardrail-mode",
                    "off",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(basic.returncode, 0, basic.stderr + basic.stdout)
        self.assertEqual(off.returncode, 0, off.stderr + off.stdout)
        basic_data = json.loads(basic.stdout)
        off_data = json.loads(off.stdout)
        self.assertTrue(any(warning["code"] == "room-edge-alpha" for warning in basic_data["guardrails"]["warnings"]))
        self.assertEqual(off_data["guardrails"]["warnings"], [])

    def test_guardrail_mode_off_keeps_structural_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            empty = work / "empty.png"
            out = work / "out"
            make_pet_package(pet)
            make_room(room)
            make_empty_prop(empty)

            result = self.run_cli(
                "--out-dir",
                str(out),
                "--pet-package",
                str(pet),
                "--room-image",
                str(room),
                "--guardrail-mode",
                "off",
                "--prop",
                f"empty={empty}",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has no visible opaque pixels", result.stderr + result.stdout)

    def test_guardrail_failure_format_has_single_sentence_boundary_before_fix(self) -> None:
        scripts_dir = ROOT / "pet-studio-kit" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        module = importlib.import_module("asset_guardrails")

        text = module.format_guardrail_failure(
            {
                "errors": [
                    {
                        "code": "duplicate-prop-id",
                        "message": "Duplicate prop id `desk`.",
                        "repair": "Use unique ids for each prop.",
                    }
                ]
            }
        )

        self.assertIn("Duplicate prop id `desk`. Fix:", text)
        self.assertNotIn(".. Fix:", text)

    def test_guardrail_failure_format_supports_korean_output(self) -> None:
        scripts_dir = ROOT / "pet-studio-kit" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        module = importlib.import_module("asset_guardrails")

        text = module.format_guardrail_failure(
            {
                "errors": [
                    {
                        "code": "duplicate-prop-id",
                        "message": "Duplicate prop id `desk`.",
                        "repair": "Use unique ids for each prop.",
                    }
                ]
            },
            lang="ko",
        )

        self.assertIn("자산 가드레일 검사 실패", text)
        self.assertIn("prop id가 중복", text)
        self.assertIn("해결:", text)
        self.assertNotIn("Fix:", text)

    def test_guided_create_room_korean_lang_reports_guardrail_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room, size=(100, 100))
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "ko-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--dry-run",
                    "--lang",
                    "ko",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("자산 가드레일 검사 실패", result.stderr + result.stdout)
        self.assertIn("방 이미지 크기", result.stderr + result.stdout)
        self.assertIn("해결:", result.stderr + result.stdout)

    def test_guided_create_room_uses_korean_env_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pet = work / "pet"
            room = work / "room.png"
            make_pet_package(pet)
            make_room(room, size=(100, 100))
            env = dict(os.environ)
            env["PET_STUDIO_LANG"] = "ko"
            env["PYTHONIOENCODING"] = "cp1252"

            result = subprocess.run(
                [
                    sys.executable,
                    str(GUIDED_CREATE_SCRIPT),
                    "--project-id",
                    "ko-env-room",
                    "--pet-package",
                    str(pet),
                    "--room-image",
                    str(room),
                    "--dry-run",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("자산 가드레일 검사 실패", result.stderr + result.stdout)

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


if __name__ == "__main__":
    unittest.main()
