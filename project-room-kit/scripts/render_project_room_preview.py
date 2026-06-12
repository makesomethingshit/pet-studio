"""Render full-size previews from a layered Project Room Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from bake_project_room_pet import (  # noqa: E402
    STATE_ROWS,
    build_source_frame,
    clear_transparent_rgb,
    load_layer_assets,
)


def render_contact_sheet(
    kit_dir: Path,
    kit: dict,
    layer_assets: dict[str, Image.Image],
    warnings: list[str],
) -> Image.Image:
    canvas_width = int(kit.get("sourceCanvas", kit["cell"])["width"])
    canvas_height = int(kit.get("sourceCanvas", kit["cell"])["height"])
    label_height = 28
    label_gutter = 92
    gap = 10
    columns = 3
    rows = 3
    sheet = Image.new(
        "RGBA",
        (
            columns * (label_gutter + canvas_width) + (columns - 1) * gap,
            rows * (canvas_height + label_height) + (rows - 1) * gap,
        ),
        (255, 255, 255, 0),
    )
    draw = ImageDraw.Draw(sheet)

    for index, state in enumerate(STATE_ROWS):
        column = index % columns
        row = index // columns
        cell_x = column * (label_gutter + canvas_width + gap)
        x = cell_x + label_gutter
        y = row * (canvas_height + label_height + gap)
        frame = build_source_frame(kit_dir, kit, state, 0, layer_assets, warnings)
        sheet.alpha_composite(frame, (x, y + label_height))
        draw.text((cell_x + 12, y + 8), state, fill=(36, 49, 58, 255))

    return sheet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", required=True, help="Path to project-room.json")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--state", default="idle", choices=sorted(STATE_ROWS) + ["all"])
    parser.add_argument("--frame", type=int, default=0)
    args = parser.parse_args()

    kit_path = Path(args.kit)
    kit_dir = kit_path.parent
    kit = json.loads(kit_path.read_text(encoding="utf-8"))
    warnings: list[str] = []
    layer_assets = load_layer_assets(kit_dir, kit["layers"], warnings)

    if args.state == "all":
        image = render_contact_sheet(kit_dir, kit, layer_assets, warnings)
    else:
        frame_count = STATE_ROWS[args.state]["frames"]
        frame_index = max(0, min(args.frame, frame_count - 1))
        image = build_source_frame(kit_dir, kit, args.state, frame_index, layer_assets, warnings)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    clear_transparent_rgb(image).save(output)
    print(json.dumps({"ok": True, "output": str(output), "warnings": sorted(set(warnings))}, indent=2))


if __name__ == "__main__":
    main()
