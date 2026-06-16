"""Create simple sample assets for Pet Studio bake verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

STATE_ROWS = {
    "idle": {"row": 0, "frames": 6},
    "running-right": {"row": 1, "frames": 8},
    "running-left": {"row": 2, "frames": 8},
    "waving": {"row": 3, "frames": 4},
    "jumping": {"row": 4, "frames": 5},
    "failed": {"row": 5, "frames": 8},
    "waiting": {"row": 6, "frames": 6},
    "running": {"row": 7, "frames": 6},
    "review": {"row": 8, "frames": 6},
}


STYLE_ID = "project-room-soft-sticker-v1"
PERSPECTIVE = "eye-level-side-view"


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for index in range(0, len(data), 4):
        if data[index + 3] == 0:
            data[index] = 0
            data[index + 1] = 0
            data[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(data))


def write_asset_metadata(
    asset_path: Path,
    role: str,
    features: list[str] | None = None,
) -> None:
    metadata = {
        "schemaVersion": 1,
        "styleId": STYLE_ID,
        "perspective": PERSPECTIVE,
        "role": role,
        "features": features or [],
        "notes": "Sample asset generated for Pet Studio pipeline validation.",
    }
    asset_path.with_name(asset_path.stem + ".asset.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def save_room(path: Path) -> None:
    img = Image.new("RGBA", (384, 240), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    wall = (248, 252, 247, 220)
    trim = (190, 216, 208, 255)
    floor = (232, 242, 238, 235)
    door = (222, 238, 232, 255)
    knob = (255, 138, 101, 255)

    draw.rounded_rectangle((8, 14, 376, 228), radius=14, fill=wall, outline=trim, width=2)
    draw.rectangle((10, 182, 374, 226), fill=floor)
    draw.line((18, 182, 366, 182), fill=trim, width=2)

    # Fixed left and right doors make every room module connect like a side-view dollhouse.
    draw.rounded_rectangle((12, 84, 54, 184), radius=7, fill=door, outline=trim, width=2)
    draw.rounded_rectangle((330, 84, 372, 184), radius=7, fill=door, outline=trim, width=2)
    draw.ellipse((40, 133, 46, 139), fill=knob)
    draw.ellipse((338, 133, 344, 139), fill=knob)

    draw.rounded_rectangle((122, 36, 262, 86), radius=8, fill=(255, 248, 214, 210), outline=trim, width=2)
    draw.line((140, 58, 244, 58), fill=(56, 183, 164, 190), width=3)
    draw.line((158, 74, 226, 74), fill=(255, 138, 101, 170), width=3)
    draw.rounded_rectangle((80, 112, 138, 154), radius=6, fill=(255, 248, 214, 180), outline=trim, width=2)
    draw.rounded_rectangle((268, 108, 314, 154), radius=6, fill=(255, 248, 214, 160), outline=trim, width=2)
    img.save(path)
    write_asset_metadata(path, "room", ["left-door", "right-door", "floor-line", "back-wall"])


def save_desk(path: Path) -> None:
    img = Image.new("RGBA", (110, 70), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((8, 28, 102, 50), radius=4, fill=(211, 172, 134, 255), outline=(121, 88, 62, 255), width=2)
    draw.rectangle((18, 50, 25, 68), fill=(121, 88, 62, 255))
    draw.rectangle((84, 50, 91, 68), fill=(121, 88, 62, 255))
    draw.rounded_rectangle((42, 6, 72, 30), radius=4, fill=(48, 61, 68, 255), outline=(35, 45, 50, 255), width=2)
    draw.line((48, 18, 66, 18), fill=(56, 183, 164, 255), width=3)
    draw.rounded_rectangle((78, 20, 96, 34), radius=3, fill=(255, 138, 101, 255))
    img.save(path)
    write_asset_metadata(path, "prop", ["desk", "monitor", "mug"])


def draw_pet(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int], bob: int, mood: str) -> None:
    ink = (36, 49, 58, 255)
    cream = (255, 242, 209, 255)
    draw.ellipse((x + 17, y + bob + 12, x + 53, y + bob + 48), fill=cream, outline=ink, width=3)
    draw.polygon([(x + 20, y + bob + 16), (x + 14, y + bob + 4), (x + 31, y + bob + 10)], fill=color, outline=ink)
    draw.polygon([(x + 50, y + bob + 16), (x + 56, y + bob + 4), (x + 39, y + bob + 10)], fill=color, outline=ink)
    draw.rounded_rectangle((x + 20, y + bob + 46, x + 50, y + bob + 82), radius=12, fill=color, outline=ink, width=3)
    draw.ellipse((x + 27, y + bob + 28, x + 32, y + bob + 34), fill=ink)
    draw.ellipse((x + 40, y + bob + 28, x + 45, y + bob + 34), fill=ink)
    if mood == "failed":
        draw.arc((x + 31, y + bob + 39, x + 43, y + bob + 49), 200, 340, fill=ink, width=2)
    else:
        draw.arc((x + 31, y + bob + 35, x + 43, y + bob + 45), 20, 160, fill=ink, width=2)
    draw.rounded_rectangle((x + 9, y + bob + 56, x + 27, y + bob + 64), radius=4, fill=cream, outline=ink, width=2)
    draw.rounded_rectangle((x + 44, y + bob + 56, x + 62, y + bob + 64), radius=4, fill=cream, outline=ink, width=2)
    draw.rounded_rectangle((x + 20, y + bob + 80, x + 35, y + bob + 88), radius=4, fill=cream, outline=ink, width=2)
    draw.rounded_rectangle((x + 37, y + bob + 80, x + 52, y + bob + 88), radius=4, fill=cream, outline=ink, width=2)


def create_pet_atlas(path: Path, color: tuple[int, int, int, int], x: int, scale_hint: str) -> None:
    atlas = Image.new("RGBA", (1536, 1872), (0, 0, 0, 0))
    for state, info in STATE_ROWS.items():
        for frame in range(info["frames"]):
            cell = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
            draw = ImageDraw.Draw(cell)
            bob = -2 if frame % 2 else 0
            if state == "jumping":
                bob = -8 - frame
            if state == "done":
                bob = -5
            draw_pet(draw, x, 76, color, bob, "failed" if state == "failed" else state)
            atlas.alpha_composite(cell, (frame * 192, info["row"] * 208))
    atlas = clear_transparent_rgb(atlas)
    atlas.save(path, "WEBP", lossless=True, quality=100, method=6, exact=True)
    write_asset_metadata(path, "pet", ["hatch-pet-atlas", scale_hint])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit-dir", required=True)
    args = parser.parse_args()

    kit_dir = Path(args.kit_dir)
    (kit_dir / "rooms").mkdir(parents=True, exist_ok=True)
    (kit_dir / "props").mkdir(parents=True, exist_ok=True)
    (kit_dir / "pets" / "main-owner").mkdir(parents=True, exist_ok=True)
    (kit_dir / "pets" / "helper-reviewer").mkdir(parents=True, exist_ok=True)

    save_room(kit_dir / "rooms" / "default-room.png")
    save_desk(kit_dir / "props" / "desk.png")
    create_pet_atlas(kit_dir / "pets" / "main-owner" / "spritesheet.webp", (56, 183, 164, 255), 22, "main")
    create_pet_atlas(kit_dir / "pets" / "helper-reviewer" / "spritesheet.webp", (255, 179, 156, 255), 15, "helper")

    print(f"sample assets written to {kit_dir}")


if __name__ == "__main__":
    main()
