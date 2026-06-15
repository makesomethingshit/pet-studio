"""Validate Pet Studio kit structure and style-lock metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from bake_project_room_pet import resolve_asset, resolve_kit_subpath
from project_room_assets import room_edge_margin_pixel_count


PET_ROLES = {"mainPet", "helperPet"}
STATIC_ROLES = {"room", "prop"}
PROP_PLACEMENTS = {"background", "behindPet", "frontOfPet", "foreground"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def metadata_path_for(asset_path: Path) -> Path:
    suffix = "".join(asset_path.suffixes)
    if suffix:
        return asset_path.with_name(asset_path.name[: -len(suffix)] + ".asset.json")
    return asset_path.with_suffix(".asset.json")


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def transparent_rgb_residue_count(path: Path) -> int:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        data = rgba.tobytes()
    residue = 0
    for index in range(0, len(data), 4):
        if data[index + 3] == 0 and data[index : index + 3] != b"\x00\x00\x00":
            residue += 1
    return residue


def expected_asset_type(role: str) -> str:
    if role in PET_ROLES:
        return "pet"
    return role


def validate_layer(kit_dir: Path, kit: dict, style: dict, layer: dict, errors: list[str], warnings: list[str]) -> None:
    layer_id = layer["id"]
    role = layer["role"]
    try:
        asset_path = resolve_asset(kit_dir, layer)
    except ValueError as exc:
        errors.append(str(exc))
        return
    scale = layer.get("scale", 1.0)
    if not isinstance(scale, (int, float)) or scale <= 0:
        errors.append(f"Layer `{layer_id}` has invalid scale: {scale}")
    for field in ("draggable", "locked", "flipX"):
        if field in layer and not isinstance(layer[field], bool):
            errors.append(f"Layer `{layer_id}` has invalid {field}: {layer[field]}")

    if not asset_path.exists():
        if role == "mainPet":
            errors.append(f"Required main pet asset missing: {asset_path}")
        else:
            warnings.append(f"Optional layer asset missing: {asset_path}")
        return

    meta_path = metadata_path_for(asset_path)
    if not meta_path.exists():
        errors.append(f"Missing style metadata for `{layer_id}`: {meta_path}")
        return

    metadata = load_json(meta_path)
    if metadata.get("styleId") != style["styleId"]:
        errors.append(
            f"Style mismatch for `{layer_id}`: {metadata.get('styleId')} != {style['styleId']}"
        )
    if metadata.get("perspective") != style["perspective"]:
        errors.append(
            f"Perspective mismatch for `{layer_id}`: {metadata.get('perspective')} != {style['perspective']}"
        )
    actual_asset_type = metadata.get("assetType", metadata.get("role"))
    expected_type = expected_asset_type(role)
    if actual_asset_type != expected_type:
        errors.append(f"Asset type mismatch for `{layer_id}`: {actual_asset_type} != {expected_type}")

    width, height = image_size(asset_path)
    if role == "room":
        expected = (kit["roomModule"]["width"], kit["roomModule"]["height"])
        if (width, height) != expected:
            errors.append(f"Room `{layer_id}` is {width}x{height}; expected {expected[0]}x{expected[1]}")
        margin_pixels = room_edge_margin_pixel_count(asset_path)
        if margin_pixels:
            warnings.append(f"Room `{layer_id}` has {margin_pixels} opaque edge-connected near-white margin pixels.")
        for required in kit["roomModule"].get("requiredFeatures", []):
            if required not in metadata.get("features", []):
                errors.append(f"Room `{layer_id}` missing required feature metadata: {required}")
    elif role in PET_ROLES:
        expected = (kit["atlas"]["width"], kit["atlas"]["height"])
        if (width, height) != expected:
            errors.append(f"Pet atlas `{layer_id}` is {width}x{height}; expected {expected[0]}x{expected[1]}")
    elif role in STATIC_ROLES:
        if role == "prop":
            placement = layer.get("placement")
            if placement is None:
                warnings.append(f"Prop layer `{layer_id}` has no placement; default runtime behavior is behindPet")
            elif placement not in PROP_PLACEMENTS:
                errors.append(f"Prop layer `{layer_id}` has invalid placement: {placement}")
        max_w = kit["roomModule"]["width"]
        max_h = kit["roomModule"]["height"]
        if width > max_w or height > max_h:
            errors.append(f"Prop `{layer_id}` is {width}x{height}; must fit inside source room {max_w}x{max_h}")
        residue = transparent_rgb_residue_count(asset_path)
        if residue:
            errors.append(f"Static layer `{layer_id}` has transparent RGB residue in {residue} pixels.")
    else:
        warnings.append(f"Unknown layer role for `{layer_id}`: {role}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", required=True, help="Path to project-room.json")
    parser.add_argument("--json-out", default=None, help="Optional validation report path")
    args = parser.parse_args()

    kit_path = Path(args.kit)
    kit_dir = kit_path.parent
    kit = load_json(kit_path)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        style_path = resolve_kit_subpath(kit_dir, kit["styleLock"], "styleLock")
    except (KeyError, ValueError) as exc:
        style_path = None
        errors.append(str(exc))
    if style_path and not style_path.exists():
        errors.append(f"styleLock not found: {style_path}")

    style = load_json(style_path) if style_path and style_path.exists() else {"styleId": "", "geometry": {}, "perspective": ""}
    style_geometry = style.get("geometry", {})

    if kit["cell"]["width"] != style_geometry.get("cellWidth") or kit["cell"]["height"] != style_geometry.get("cellHeight"):
        errors.append("Cell size does not match style-lock geometry.")
    if kit.get("sourceCanvas", {}).get("width") != kit["roomModule"]["width"] or kit.get("sourceCanvas", {}).get("height") != kit["roomModule"]["height"]:
        errors.append("Source canvas size must match room module size.")
    if kit["roomModule"]["width"] != style_geometry.get("roomWidth") or kit["roomModule"]["height"] != style_geometry.get("roomHeight"):
        errors.append("Room module size does not match style-lock geometry.")
    if kit["roomModule"]["perspective"] != style["perspective"]:
        errors.append("Room module perspective does not match style-lock perspective.")

    for layer in kit["layers"]:
        validate_layer(kit_dir, kit, style, layer, errors, warnings)

    report = {
        "ok": not errors,
        "styleId": style["styleId"],
        "kit": kit["id"],
        "errors": errors,
        "warnings": sorted(set(warnings)),
    }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
