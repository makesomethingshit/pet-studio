"""Bake a modular Pet Studio kit into a normal hatch-pet package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from image_guardrails import safe_image_size, safe_rgba_image
from PIL import Image, ImageOps

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


def resolve_kit_subpath(kit_dir: Path, raw_path: str, label: str = "Kit asset path") -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{label} must be a non-empty relative path.")
    path = Path(raw_path)
    if path.is_absolute():
        raise ValueError(f"{label} `{raw_path}` must be relative to the kit directory.")
    base = kit_dir.resolve()
    resolved = (kit_dir / path).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"{label} `{raw_path}` escapes the kit directory.") from exc
    return resolved


def layer_max_size(kit: dict, layer: dict) -> tuple[int, int] | None:
    role = layer.get("role")
    if role == "room":
        return int(kit["roomModule"]["width"]), int(kit["roomModule"]["height"])
    if role in {"mainPet", "helperPet"}:
        return int(kit["atlas"]["width"]), int(kit["atlas"]["height"])
    if role == "prop":
        source = kit.get("sourceCanvas", kit["roomModule"])
        return int(source["width"]), int(source["height"])
    return None


def image_size(path: Path) -> tuple[int, int]:
    return safe_image_size(path)


def validate_layer_image_bounds(kit: dict, layer: dict, path: Path) -> None:
    max_size = layer_max_size(kit, layer)
    if max_size is None:
        return
    width, height = image_size(path)
    max_width, max_height = max_size
    if width > max_width or height > max_height:
        raise ValueError(
            f"Layer `{layer.get('id', '<unknown>')}` image is {width}x{height}; "
            f"maximum for role `{layer.get('role', '<unknown>')}` is {max_width}x{max_height}."
        )


def load_image(path: Path) -> Image.Image:
    return safe_rgba_image(path)


def visible_bbox(layer: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = layer.getchannel("A")
    return alpha.getbbox()


def trim_visible(layer: Image.Image) -> Image.Image:
    bbox = visible_bbox(layer)
    if bbox is None:
        return layer
    return layer.crop(bbox)


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for index in range(0, len(data), 4):
        if data[index + 3] == 0:
            data[index] = 0
            data[index + 1] = 0
            data[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(data))


def paste_with_bottom_anchor(base: Image.Image, layer: Image.Image, anchor: dict[str, int]) -> None:
    visible = trim_visible(layer)
    x = int(anchor["x"] - visible.width / 2)
    y = int(anchor["y"] - visible.height)
    base.alpha_composite(visible, (x, y))


def scale_visible_layer(layer: Image.Image, scale: float, flip_x: bool = False) -> Image.Image:
    visible = trim_visible(layer)
    if flip_x:
        visible = ImageOps.mirror(visible)
    if scale == 1:
        return visible
    width = max(1, int(round(visible.width * scale)))
    height = max(1, int(round(visible.height * scale)))
    return visible.resize((width, height), Image.Resampling.LANCZOS)


def paste_scaled_with_bottom_anchor(
    base: Image.Image,
    layer: Image.Image,
    anchor: dict[str, int],
    scale: float,
    flip_x: bool = False,
) -> None:
    visible = scale_visible_layer(layer, scale, flip_x)
    x = int(anchor["x"] - visible.width / 2)
    y = int(anchor["y"] - visible.height)
    base.alpha_composite(visible, (x, y))


def render_preview_cell(kit: dict, canvas: Image.Image) -> Image.Image:
    cell_width = int(kit["cell"]["width"])
    cell_height = int(kit["cell"]["height"])
    preview = kit.get("previewBake", {})

    if preview.get("mode") == "contain":
        scale = min(cell_width / canvas.width, cell_height / canvas.height)
        scaled_size = (
            max(1, int(round(canvas.width * scale))),
            max(1, int(round(canvas.height * scale))),
        )
        scaled = canvas.resize(scaled_size, Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
        x = int((cell_width - scaled.width) / 2)
        y = cell_height - scaled.height
        cell.alpha_composite(scaled, (x, y))
        return cell

    if preview.get("mode") != "viewport":
        if canvas.size == (cell_width, cell_height):
            return canvas
        left = max(0, int((canvas.width - cell_width) / 2))
        top = max(0, int(canvas.height - cell_height))
        viewport = {"x": left, "y": top, "width": cell_width, "height": cell_height}
    else:
        viewport = preview["viewport"]

    x = int(viewport["x"])
    y = int(viewport["y"])
    width = int(viewport["width"])
    height = int(viewport["height"])
    if (width, height) != (cell_width, cell_height):
        raise ValueError("previewBake viewport must match hatch-pet cell size.")

    cell = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
    crop_left = max(0, x)
    crop_top = max(0, y)
    crop_right = min(canvas.width, x + width)
    crop_bottom = min(canvas.height, y + height)
    if crop_left >= crop_right or crop_top >= crop_bottom:
        return cell

    cropped = canvas.crop((crop_left, crop_top, crop_right, crop_bottom))
    cell.alpha_composite(cropped, (crop_left - x, crop_top - y))
    return cell


def crop_atlas_frame(
    atlas: Image.Image, state: str, frame_index: int, cell_width: int, cell_height: int
) -> Image.Image:
    row = STATE_ROWS[state]["row"]
    left = frame_index * cell_width
    top = row * cell_height
    return atlas.crop((left, top, left + cell_width, top + cell_height))


def visible_layer_ids(state_config: dict, layers: list[dict]) -> set[str]:
    configured = set(state_config.get("visibleLayers", []))
    if configured:
        return configured
    return {layer["id"] for layer in layers}


def layer_visible_for_state(layer: dict, state: str, visible_ids: set[str]) -> bool:
    if layer["id"] not in visible_ids:
        return False
    visible_when = layer.get("visibleWhen")
    return not visible_when or state in visible_when


def resolve_asset(kit_dir: Path, layer: dict) -> Path:
    return resolve_kit_subpath(kit_dir, layer["path"], f"Layer `{layer.get('id', '<unknown>')}` path")


def build_source_frame(
    kit_dir: Path,
    kit: dict,
    state: str,
    frame_index: int,
    layer_assets: dict[str, Image.Image],
    warnings: list[str],
) -> Image.Image:
    cell_width = int(kit["cell"]["width"])
    cell_height = int(kit["cell"]["height"])
    canvas_width = int(kit.get("sourceCanvas", kit["cell"])["width"])
    canvas_height = int(kit.get("sourceCanvas", kit["cell"])["height"])
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    state_config = kit["states"][state]
    visible_ids = visible_layer_ids(state_config, kit["layers"])

    for layer in sorted(kit["layers"], key=lambda item: int(item.get("z", 0))):
        if not layer_visible_for_state(layer, state, visible_ids):
            continue

        layer_id = layer["id"]
        role = layer["role"]
        source = layer_assets.get(layer_id)

        if source is None:
            if role in {"mainPet"}:
                raise FileNotFoundError(f"Required main pet layer is missing: {layer_id}")
            warnings.append(f"Skipped missing optional layer `{layer_id}` in state `{state}`.")
            continue

        anchor_name = layer.get("anchor", "cell-bottom-center")
        anchor = kit["anchors"][anchor_name]
        scale = float(layer.get("scale", 1.0))
        flip_x = bool(layer.get("flipX", False))

        if role == "mainPet":
            row_state = state_config.get("mainPetRow", state)
            frame = crop_atlas_frame(source, row_state, frame_index, cell_width, cell_height)
            paste_scaled_with_bottom_anchor(canvas, frame, anchor, scale, flip_x)
        elif role == "helperPet":
            row_state = state_config.get("helperPetRow", state)
            frame = crop_atlas_frame(source, row_state, frame_index, cell_width, cell_height)
            paste_scaled_with_bottom_anchor(canvas, frame, anchor, scale, flip_x)
        else:
            paste_scaled_with_bottom_anchor(canvas, source, anchor, scale, flip_x)

    return canvas


def build_cell(
    kit_dir: Path,
    kit: dict,
    state: str,
    frame_index: int,
    layer_assets: dict[str, Image.Image],
    warnings: list[str],
) -> Image.Image:
    canvas = build_source_frame(kit_dir, kit, state, frame_index, layer_assets, warnings)
    return render_preview_cell(kit, canvas)


def load_layer_assets(kit_dir: Path, kit_or_layers: dict | list[dict], warnings: list[str]) -> dict[str, Image.Image]:
    kit = kit_or_layers if isinstance(kit_or_layers, dict) else None
    layers = kit_or_layers.get("layers", []) if isinstance(kit_or_layers, dict) else kit_or_layers
    assets: dict[str, Image.Image] = {}
    for layer in layers:
        path = resolve_asset(kit_dir, layer)
        if not path.exists():
            if layer["role"] == "mainPet":
                raise FileNotFoundError(f"Required main pet asset not found: {path}")
            warnings.append(f"Optional asset not found: {path}")
            continue
        if kit is not None:
            validate_layer_image_bounds(kit, layer, path)
        assets[layer["id"]] = load_image(path)
    return assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", required=True, help="Path to project-room.json")
    parser.add_argument("--out-dir", required=True, help="Output pet package directory")
    parser.add_argument("--pet-id", default=None, help="Override package pet id")
    parser.add_argument("--display-name", default=None, help="Override display name")
    args = parser.parse_args()

    kit_path = Path(args.kit)
    out_dir = Path(args.out_dir)
    kit = json.loads(kit_path.read_text(encoding="utf-8"))
    kit_dir = kit_path.parent
    warnings: list[str] = []

    cell_width = int(kit["cell"]["width"])
    cell_height = int(kit["cell"]["height"])
    atlas_width = int(kit["atlas"]["width"])
    atlas_height = int(kit["atlas"]["height"])
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    layer_assets = load_layer_assets(kit_dir, kit, warnings)

    for state, info in STATE_ROWS.items():
        if state not in kit["states"]:
            raise KeyError(f"Kit manifest missing state: {state}")
        for frame_index in range(info["frames"]):
            cell = build_cell(kit_dir, kit, state, frame_index, layer_assets, warnings)
            atlas.alpha_composite(cell, (frame_index * cell_width, info["row"] * cell_height))

    out_dir.mkdir(parents=True, exist_ok=True)
    spritesheet_path = out_dir / "spritesheet.webp"
    atlas = clear_transparent_rgb(atlas)
    atlas.save(
        spritesheet_path,
        "WEBP",
        lossless=True,
        quality=100,
        method=6,
        exact=True,
    )

    pet_id = args.pet_id or kit["id"]
    display_name = args.display_name or kit["displayName"]
    pet_json = {
        "id": pet_id,
        "displayName": display_name,
        "description": kit["description"],
        "spritesheetPath": "spritesheet.webp",
        "sourceKit": str(kit_path),
    }
    (out_dir / "pet.json").write_text(json.dumps(pet_json, indent=2), encoding="utf-8")

    summary = {
        "ok": True,
        "kit": kit["id"],
        "package": str(out_dir),
        "spritesheet": str(spritesheet_path),
        "pet_json": str(out_dir / "pet.json"),
        "bakeMode": "preview/fallback",
        "warnings": sorted(set(warnings)),
    }
    (out_dir / "bake-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
