from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "project-room-kit" / "scripts" / "create_project_room_kit.py"
VALIDATOR = ROOT / "project-room-kit" / "scripts" / "validate_project_room_kit.py"


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
            self.assertEqual(manifest["sourceCanvas"], {"width": 384, "height": 240, "purpose": "layered project-room widget canvas"})
            self.assertEqual(style["sourcePolicy"]["selectedSource"]["type"], "existing hatch-pet pet package")
            self.assertEqual(style["sourcePolicy"]["selectedSource"]["petId"], "sample-pet")
            self.assertEqual(prop_meta["role"], "prop")
            self.assertEqual(prop_meta["assetType"], "prop")
            self.assertIn("desk", manifest["anchors"])
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


if __name__ == "__main__":
    unittest.main()
