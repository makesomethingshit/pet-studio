"""Register a hatch-pet package as a Pet Studio pet layer."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from image_guardrails import ImageResourceError, safe_image_size


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def validate_spritesheet(path: Path, expected_width: int, expected_height: int) -> None:
    try:
        width, height = safe_image_size(path)
    except ImageResourceError as exc:
        raise SystemExit(str(exc)) from exc
    if (width, height) != (expected_width, expected_height):
        raise SystemExit(
            f"Spritesheet is {width}x{height}; expected {expected_width}x{expected_height}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit-dir", required=True, help="Path to a Pet Studio kit directory")
    parser.add_argument("--package-dir", required=True, help="Path to a hatch-pet package containing pet.json and spritesheet.webp")
    parser.add_argument("--layer-id", required=True, help="Kit pet layer id, for example main-owner or helper-reviewer")
    parser.add_argument("--feature", action="append", default=[], help="Extra metadata feature; may be repeated")
    args = parser.parse_args()

    kit_dir = Path(args.kit_dir)
    package_dir = Path(args.package_dir)
    kit = load_json(kit_dir / "project-room.json")
    style = load_json(kit_dir / kit["styleLock"])
    pet_json = load_json(package_dir / "pet.json")
    source_spritesheet = package_dir / pet_json.get("spritesheetPath", "spritesheet.webp")

    if not source_spritesheet.exists():
        raise SystemExit(f"Spritesheet not found: {source_spritesheet}")

    validate_spritesheet(source_spritesheet, kit["atlas"]["width"], kit["atlas"]["height"])

    target_dir = kit_dir / "pets" / args.layer_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_spritesheet = target_dir / "spritesheet.webp"
    shutil.copy2(source_spritesheet, target_spritesheet)

    metadata = {
        "schemaVersion": 1,
        "styleId": style["styleId"],
        "perspective": style["perspective"],
        "role": "pet",
        "sourcePetId": pet_json.get("id"),
        "sourceDisplayName": pet_json.get("displayName"),
        "features": ["hatch-pet-atlas", args.layer_id, *args.feature],
        "notes": "Registered from a hatch-pet package for Pet Studio composition."
    }
    write_json(target_dir / "spritesheet.asset.json", metadata)

    summary = {
        "ok": True,
        "layerId": args.layer_id,
        "sourcePackage": str(package_dir),
        "targetSpritesheet": str(target_spritesheet),
        "metadata": str(target_dir / "spritesheet.asset.json")
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
