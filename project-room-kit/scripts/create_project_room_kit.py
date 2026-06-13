"""Create a production Pet Studio kit from a hatch-pet and generated assets."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_room_assets import cleanup_room_image


CELL_WIDTH = 192
CELL_HEIGHT = 208
ROOM_WIDTH = 384
ROOM_HEIGHT = 240
ATLAS_WIDTH = 1536
ATLAS_HEIGHT = 1872
STYLE_ID = "project-room-soft-sticker-v1"
PERSPECTIVE = "eye-level-side-view"
PROMPT_CONSTRAINTS = [
    "SD/chibi dollhouse room",
    "eye-level side view",
    "384x240 room source",
    "no readable text",
    "no letters",
    "no numbers",
    "no watermark",
    "no UI frame",
    "no character in the room background",
]
STATE_ROWS = [
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
]
PROP_PLACEMENTS = {
    "background": "background",
    "behind-pet": "behindPet",
    "behindPet": "behindPet",
    "front-of-pet": "frontOfPet",
    "frontOfPet": "frontOfPet",
    "foreground": "foreground",
}
PROP_PLACEMENT_Z_BASE = {
    "background": 5,
    "behindPet": 12,
    "frontOfPet": 24,
    "foreground": 30,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def validate_image_size(path: Path, expected: tuple[int, int], label: str) -> None:
    actual = image_size(path)
    if actual != expected:
        raise SystemExit(f"{label} is {actual[0]}x{actual[1]}; expected {expected[0]}x{expected[1]}")


def parse_id_path(value: str, label: str) -> tuple[str, Path]:
    if "=" not in value:
        raise SystemExit(f"{label} must use id=path format: {value}")
    item_id, path_value = value.split("=", 1)
    item_id = item_id.strip()
    if not item_id:
        raise SystemExit(f"{label} id cannot be empty: {value}")
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"{label} asset not found: {path}")
    return item_id, path


def parse_id_value(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        raise SystemExit(f"{label} must use id=value format: {value}")
    item_id, raw_value = value.split("=", 1)
    item_id = item_id.strip()
    raw_value = raw_value.strip()
    if not item_id:
        raise SystemExit(f"{label} id cannot be empty: {value}")
    if not raw_value:
        raise SystemExit(f"{label} value cannot be empty: {value}")
    return item_id, raw_value


def parse_prop_placements(values: list[str], prop_ids: list[str]) -> dict[str, str]:
    known_prop_ids = set(prop_ids)
    placements: dict[str, str] = {}
    for value in values:
        prop_id, raw_placement = parse_id_value(value, "Prop placement")
        if prop_id not in known_prop_ids:
            raise SystemExit(f"Prop placement references unknown prop id `{prop_id}`")
        placement = PROP_PLACEMENTS.get(raw_placement)
        if not placement:
            allowed = ", ".join(sorted({key for key in PROP_PLACEMENTS if "-" in key or key in {"background", "foreground"}}))
            raise SystemExit(f"Unknown prop placement `{raw_placement}` for `{prop_id}`. Allowed: {allowed}")
        placements[prop_id] = placement
    return placements


def copy_image(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_pet_package(package_dir: Path, kit_dir: Path, layer_id: str, style: dict, features: list[str]) -> dict:
    pet_json = load_json(package_dir / "pet.json")
    spritesheet = package_dir / pet_json.get("spritesheetPath", "spritesheet.webp")
    if not spritesheet.exists():
        raise SystemExit(f"Spritesheet not found: {spritesheet}")
    validate_image_size(spritesheet, (ATLAS_WIDTH, ATLAS_HEIGHT), "Spritesheet")

    target_dir = kit_dir / "pets" / layer_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "spritesheet.webp"
    shutil.copy2(spritesheet, target)
    metadata = {
        "schemaVersion": 1,
        "styleId": style["styleId"],
        "perspective": style["perspective"],
        "role": "pet",
        "assetType": "pet",
        "sourcePetId": pet_json.get("id"),
        "sourceDisplayName": pet_json.get("displayName"),
        "features": ["hatch-pet-atlas", layer_id, *features],
        "notes": "Registered from a hatch-pet package for Pet Studio composition.",
    }
    write_json(target_dir / "spritesheet.asset.json", metadata)
    return pet_json


def build_style_lock(pet_json: dict, pet_package: Path) -> dict:
    return {
        "schemaVersion": 1,
        "styleId": STYLE_ID,
        "name": "Pet Studio Soft Sticker",
        "sourcePolicy": {
            "requiredAtRuntime": True,
            "preferredSource": "hatch-pet package",
            "acceptedSources": [
                "existing hatch-pet pet package",
                "new hatch-pet pet generated before room assets",
                "explicit style-lock.json supplied by user",
            ],
            "rule": "Do not generate room, prop, or helper assets until the style source is selected.",
            "selectedSource": {
                "type": "existing hatch-pet pet package",
                "petId": pet_json.get("id"),
                "displayName": pet_json.get("displayName"),
                "packageDir": str(pet_package),
                "role": "main-owner",
            },
        },
        "perspective": PERSPECTIVE,
        "rendering": {
            "medium": "2d-sticker",
            "outline": {"color": "#24313a", "width": 3, "joins": "round"},
            "shading": "flat-with-minimal-highlight",
            "texture": "clean-vector-like",
        },
        "geometry": {
            "cellWidth": CELL_WIDTH,
            "cellHeight": CELL_HEIGHT,
            "roomWidth": ROOM_WIDTH,
            "roomHeight": ROOM_HEIGHT,
            "doorLeftX": 28,
            "doorRightX": 356,
            "floorY": 182,
        },
        "palette": {
            "ink": "#24313a",
            "mint": "#38b7a4",
            "coral": "#ff8a65",
            "cream": "#fff2d1",
            "wall": "#f8fcf7",
            "floor": "#e8f2ee",
            "trim": "#bed8d0",
            "wood": "#d3ac86",
            "yellow": "#fff8d6",
        },
        "rules": [
            "All assets must use the same eye-level side-view perspective.",
            "All source room modules must be exactly 384x240 with left and right doors in the same positions.",
            "The 192x208 hatch-pet cell is only for preview/fallback baking; keep layered room sources separate.",
            "Pets, helpers, props, and rooms must share the same outline color and approximate outline width.",
            "Props should be simple, rounded, and readable at pet-widget size.",
            "Do not mix pixel art, painterly rendering, photorealism, heavy gradients, or mismatched outline systems.",
            "Do not add readable text, logos, large UI panels, or unrelated scenery inside baked sprite assets.",
        ],
    }


def write_asset_metadata(path: Path, style: dict, role: str, features: list[str], source: str) -> None:
    write_json(
        path.with_name(path.stem + ".asset.json"),
        {
            "schemaVersion": 1,
            "styleId": style["styleId"],
            "perspective": style["perspective"],
            "role": role,
            "assetType": role,
            "features": features,
            "source": source,
            "notes": "Registered by create_project_room_kit.py.",
        },
    )


def make_manifest(display_name: str, prop_ids: list[str], helper_ids: list[str], prop_placements: dict[str, str] | None = None) -> dict:
    prop_placements = prop_placements or {}
    layers = [
        {
            "id": "room",
            "role": "room",
            "path": "rooms/default-room.png",
            "z": 0,
            "anchor": "room",
            "scale": 1.0,
            "draggable": False,
            "locked": True,
        },
    ]
    anchors = {
        "cell-bottom-center": {"x": 96, "y": 190},
        "room": {"x": 192, "y": 240},
        "owner": {"x": 96, "y": 206},
        "helper": {"x": 285, "y": 204},
    }

    for index, prop_id in enumerate(prop_ids):
        anchor_name = prop_id
        placement = prop_placements.get(prop_id, "behindPet")
        if placement == "foreground":
            x = min(344, 325 + index * 18)
            y = 218
        else:
            x = min(330, 215 + index * 42)
            y = max(196, 216 - (index % 2) * 10)
        anchors[anchor_name] = {"x": x, "y": y}
        layers.append(
            {
                "id": prop_id,
                "role": "prop",
                "path": f"props/{prop_id}.png",
                "placement": placement,
                "z": PROP_PLACEMENT_Z_BASE[placement] + index,
                "anchor": anchor_name,
                "scale": 1.0,
                "draggable": True,
                "locked": False,
            }
        )

    for index, helper_id in enumerate(helper_ids):
        anchor_name = f"{helper_id}-anchor"
        anchors[anchor_name] = {"x": 285 + index * 28, "y": 204}
        layers.append(
            {
                "id": helper_id,
                "role": "helperPet",
                "path": f"pets/{helper_id}/spritesheet.webp",
                "z": 18 + index,
                "anchor": anchor_name,
                "scale": 0.56,
                "visibleWhen": ["review", "failed"],
                "draggable": True,
                "locked": False,
            }
        )

    layers.append(
        {
            "id": "main-owner",
            "role": "mainPet",
            "path": "pets/main-owner/spritesheet.webp",
            "z": 20,
            "anchor": "owner",
            "scale": 0.68,
            "draggable": True,
            "locked": False,
        }
    )
    base_visible = ["room", *prop_ids, "main-owner"]
    helper_visible = ["room", *prop_ids, *helper_ids, "main-owner"]
    states = {}
    for state in STATE_ROWS:
        helper_state = state in {"review", "failed"}
        states[state] = {"mainPetRow": state, "visibleLayers": helper_visible if helper_state else base_visible}
        if helper_state and helper_ids:
            states[state]["helperPetRow"] = "review"

    return {
        "schemaVersion": 1,
        "id": "project-room",
        "displayName": display_name,
        "description": "A side-view room-decorating kit for a Codex pet widget.",
        "styleLock": "style-lock.json",
        "cell": {"width": CELL_WIDTH, "height": CELL_HEIGHT, "purpose": "hatch-pet preview/fallback atlas cell, not the source room size"},
        "sourceCanvas": {"width": ROOM_WIDTH, "height": ROOM_HEIGHT, "purpose": "layered Pet Studio widget canvas"},
        "roomModule": {
            "width": ROOM_WIDTH,
            "height": ROOM_HEIGHT,
            "perspective": PERSPECTIVE,
            "requiredFeatures": ["left-door", "right-door", "floor-line", "back-wall"],
            "safeArea": {"left": 18, "top": 12, "right": 366, "bottom": 228},
            "doorAnchors": {"left": {"x": 28, "y": 182}, "right": {"x": 356, "y": 182}},
        },
        "previewBake": {"mode": "contain", "purpose": "compatibility preview only; real room output should keep source layers separate", "align": "bottom-center"},
        "atlas": {"columns": 8, "rows": 9, "width": ATLAS_WIDTH, "height": ATLAS_HEIGHT},
        "layers": layers,
        "anchors": anchors,
        "states": states,
    }


def make_generation_brief(theme: str, pet_json: dict, prop_ids: list[str]) -> dict:
    return {
        "schemaVersion": 1,
        "theme": theme,
        "styleSource": {
            "petId": pet_json.get("id"),
            "displayName": pet_json.get("displayName"),
            "description": pet_json.get("description"),
        },
        "geometry": {"roomWidth": ROOM_WIDTH, "roomHeight": ROOM_HEIGHT, "cellWidth": CELL_WIDTH, "cellHeight": CELL_HEIGHT},
        "desiredProps": prop_ids,
        "promptConstraints": PROMPT_CONSTRAINTS,
    }


def write_prompts(out_dir: Path, theme: str, prop_ids: list[str]) -> None:
    prompt_dir = out_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    constraints = ", ".join(PROMPT_CONSTRAINTS)
    (prompt_dir / "room-prompt.txt").write_text(
        f"Create a {theme} as an SD/chibi dollhouse room for a Codex pet widget. "
        f"Use eye-level side view, warm soft sticker rendering, thick rounded outlines, and a quiet open floor area. "
        f"Constraints: {constraints}.",
        encoding="utf-8",
    )
    for prop_id in prop_ids:
        (prompt_dir / f"prop-{prop_id}-prompt.txt").write_text(
            f"Create a transparent PNG prop named {prop_id} for a {theme} Pet Studio kit. "
            "Use the same SD/chibi soft sticker style, eye-level side-view perspective, rounded furniture proportions, "
            "simple readable shapes, and no readable text, letters, numbers, logos, watermark, UI frame, or character.",
            encoding="utf-8",
        )


def relative_path_from(path: Path, base_dir: Path) -> str:
    try:
        return os.path.relpath(path.resolve(), base_dir.resolve())
    except ValueError:
        return str(path.resolve())


def upsert_project_registry(
    registry_path: Path,
    project_id: str,
    display_name: str,
    kit_dir: Path,
    pet_package: Path,
    default_state: str,
    theme: str,
    workspace_paths: list[Path] | None = None,
) -> dict:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if registry_path.exists():
        registry = load_json(registry_path)
    else:
        registry = {"schemaVersion": 1, "projects": []}
    projects = registry.setdefault("projects", [])
    if not isinstance(projects, list):
        raise SystemExit("Project registry `projects` must be a list.")

    entry = {
        "projectId": project_id,
        "displayName": display_name,
        "kitPath": relative_path_from(kit_dir, registry_path.parent),
        "petPackagePath": relative_path_from(pet_package, registry_path.parent),
        "defaultState": default_state,
        "theme": theme,
        "enabled": True,
    }
    if workspace_paths:
        entry["workspacePaths"] = [str(path.expanduser().resolve()) for path in workspace_paths]
    registry["projects"] = [project for project in projects if project.get("projectId") != project_id]
    registry["projects"].append(entry)
    write_json(registry_path, registry)
    return entry


def run_step(name: str, command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "name": name,
        "command": command,
        "exitCode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--pet-package", required=True)
    parser.add_argument("--room-image", required=True)
    parser.add_argument("--room-alpha-mode", choices=("safe", "balanced", "aggressive"), default="balanced")
    parser.add_argument("--prop", action="append", default=[], help="Prop asset in id=path format; may be repeated")
    parser.add_argument(
        "--prop-placement",
        action="append",
        default=[],
        help="Prop layer placement in id=background|behind-pet|front-of-pet|foreground format; may be repeated",
    )
    parser.add_argument("--helper-package", action="append", default=[], help="Helper pet in id=path format; may be repeated")
    parser.add_argument("--theme", default="pet studio room")
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--render-preview", action="store_true")
    parser.add_argument("--render-contact", action="store_true")
    parser.add_argument("--bake-fallback", action="store_true")
    parser.add_argument("--register-project", action="store_true", help="Register the created kit in a Pet Studio registry")
    parser.add_argument("--project-id", default=None, help="Project id to use with --register-project")
    parser.add_argument("--registry", default=None, help="Project registry path to update")
    parser.add_argument("--workspace-path", action="append", default=[], help="Workspace path to associate with the registered project; may be repeated")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--hatch-pet-dir", default=str(Path.home() / ".codex" / "skills" / "hatch-pet"))
    args = parser.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parents[1]
    out_dir = Path(args.out_dir)
    kit_dir = out_dir / "kit"
    pet_package = Path(args.pet_package).expanduser()
    room_image = Path(args.room_image).expanduser()

    if not (pet_package / "pet.json").exists():
        raise SystemExit(f"pet.json not found in pet package: {pet_package}")
    if not room_image.exists():
        raise SystemExit(f"Room image not found: {room_image}")

    pet_json = load_json(pet_package / "pet.json")
    pet_spritesheet = pet_package / pet_json.get("spritesheetPath", "spritesheet.webp")
    validate_image_size(pet_spritesheet, (ATLAS_WIDTH, ATLAS_HEIGHT), "Spritesheet")
    validate_image_size(room_image, (ROOM_WIDTH, ROOM_HEIGHT), "Room image")

    prop_inputs = [parse_id_path(value, "Prop") for value in args.prop]
    helper_inputs = [parse_id_path(value, "Helper package") for value in args.helper_package]

    kit_dir.mkdir(parents=True, exist_ok=True)
    style = build_style_lock(pet_json, pet_package)
    display_name = args.display_name or f"{pet_json.get('displayName', 'Project')} Room"

    write_json(kit_dir / "style-lock.json", style)
    copy_pet_package(pet_package, kit_dir, "main-owner", style, ["main-owner"])

    helper_ids: list[str] = []
    for helper_id, helper_package in helper_inputs:
        copy_pet_package(helper_package, kit_dir, helper_id, style, ["helper", helper_id])
        helper_ids.append(helper_id)

    cleanup_room_image(room_image, kit_dir / "rooms" / "default-room.png", args.room_alpha_mode)
    write_asset_metadata(
        kit_dir / "rooms" / "default-room.png",
        style,
        "room",
        ["left-door", "right-door", "floor-line", "back-wall", f"alpha-{args.room_alpha_mode}"],
        "generated-or-authored",
    )

    prop_ids: list[str] = []
    for prop_id, source in prop_inputs:
        target = kit_dir / "props" / f"{prop_id}.png"
        copy_image(source, target)
        write_asset_metadata(target, style, "prop", [prop_id], "generated-or-authored")
        prop_ids.append(prop_id)

    prop_placements = parse_prop_placements(args.prop_placement, prop_ids)
    manifest = make_manifest(display_name, prop_ids, helper_ids, prop_placements)
    write_json(kit_dir / "project-room.json", manifest)
    write_json(out_dir / "generation-brief.json", make_generation_brief(args.theme, pet_json, prop_ids))
    write_prompts(out_dir, args.theme, prop_ids)

    registered_project = None
    project_link = None
    if args.register_project:
        if not args.project_id:
            raise SystemExit("--project-id is required with --register-project")
        registry_path = Path(args.registry) if args.registry else repo_root / "project-room-widget" / "project-room-projects.json"
        workspace_paths = [Path(value) for value in args.workspace_path]
        registered_project = upsert_project_registry(
            registry_path,
            args.project_id,
            display_name,
            kit_dir,
            pet_package,
            "idle",
            args.theme,
            workspace_paths,
        )
        project_link = {
            "projectId": args.project_id,
            "registryPath": str(registry_path.expanduser().resolve()),
            "kitPath": str(kit_dir.resolve()),
            "workspacePaths": [str(path.expanduser().resolve()) for path in workspace_paths],
        }

    steps: list[dict] = []
    validation_path = out_dir / "kit-validation.json"
    steps.append(
        run_step(
            "validate kit",
            [args.python, str(scripts_dir / "validate_project_room_kit.py"), "--kit", str(kit_dir / "project-room.json"), "--json-out", str(validation_path)],
            repo_root,
        )
    )

    if args.render_preview:
        steps.append(
            run_step(
                "render idle preview",
                [args.python, str(scripts_dir / "render_project_room_preview.py"), "--kit", str(kit_dir / "project-room.json"), "--state", "idle", "--out", str(out_dir / "room-preview.png")],
                repo_root,
            )
        )
    if args.render_contact:
        steps.append(
            run_step(
                "render contact sheet",
                [args.python, str(scripts_dir / "render_project_room_preview.py"), "--kit", str(kit_dir / "project-room.json"), "--state", "all", "--out", str(out_dir / "room-contact.png")],
                repo_root,
            )
        )
    if args.bake_fallback:
        package_dir = out_dir / "package"
        steps.append(
            run_step(
                "bake fallback package",
                [args.python, str(scripts_dir / "bake_project_room_pet.py"), "--kit", str(kit_dir / "project-room.json"), "--out-dir", str(package_dir), "--pet-id", manifest["id"], "--display-name", display_name],
                repo_root,
            )
        )
        hatch_pet_dir = Path(args.hatch_pet_dir)
        validate_atlas = hatch_pet_dir / "scripts" / "validate_atlas.py"
        make_contact = hatch_pet_dir / "scripts" / "make_contact_sheet.py"
        if validate_atlas.exists():
            steps.append(
                run_step(
                    "validate fallback atlas",
                    [args.python, str(validate_atlas), str(package_dir / "spritesheet.webp"), "--json-out", str(out_dir / "atlas-validation.json")],
                    repo_root,
                )
            )
        if make_contact.exists():
            steps.append(
                run_step(
                    "render fallback contact sheet",
                    [args.python, str(make_contact), str(package_dir / "spritesheet.webp"), "--output", str(out_dir / "fallback-contact-sheet.png")],
                    repo_root,
                )
            )

    validation = load_json(validation_path) if validation_path.exists() else {"ok": False}
    report = {
        "ok": all(step["ok"] for step in steps),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "kitDir": str(kit_dir),
        "generationBrief": str(out_dir / "generation-brief.json"),
        "promptsDir": str(out_dir / "prompts"),
        "registeredProject": registered_project,
        "projectLink": project_link,
        "roomAlphaMode": args.room_alpha_mode,
        "validation": validation,
        "steps": steps,
    }
    write_json(out_dir / "production-report.json", report)
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
