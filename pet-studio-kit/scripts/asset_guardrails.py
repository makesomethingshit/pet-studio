"""Pre-generation asset guardrails for Pet Studio room creation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from project_room_assets import room_edge_margin_pixel_count


ROOM_SIZE = (384, 240)
ATLAS_SIZE = (1536, 1872)
PROP_PLACEMENTS = {"background", "behind-pet", "behindPet", "front-of-pet", "frontOfPet", "foreground"}
GUARDRAIL_MODES = {"basic", "strict", "off"}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class AssetInput:
    id: str
    path: Path


@dataclass(frozen=True)
class GuardrailIssue:
    code: str
    severity: str
    message: str
    path: str | None = None
    repair: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {"code": self.code, "severity": self.severity, "message": self.message}
        if self.path:
            data["path"] = self.path
        if self.repair:
            data["repair"] = self.repair
        return data


def load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as image:
            return image.size
    except (OSError, ValueError):
        return None


def image_has_opaque_pixels(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            alpha = image.convert("RGBA").getchannel("A")
            return alpha.getbbox() is not None
    except (OSError, ValueError):
        return False


def sidecar_path_for(asset_path: Path) -> Path:
    suffix = "".join(asset_path.suffixes)
    if suffix:
        return asset_path.with_name(asset_path.name[: -len(suffix)] + ".asset.json")
    return asset_path.with_suffix(".asset.json")


def helper_spritesheet_path(package_dir: Path) -> Path | None:
    pet_json = load_json_object(package_dir / "pet.json")
    if pet_json is None:
        return None
    sprite = pet_json.get("spritesheetPath", "spritesheet.webp")
    return package_dir / sprite if isinstance(sprite, str) and sprite.strip() else None


def placement_id(value: str) -> str | None:
    if "=" not in value:
        return None
    item_id, _raw_value = value.split("=", 1)
    item_id = item_id.strip()
    return item_id or None


def duplicate_ids(items: list[AssetInput]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item.id in seen:
            duplicates.add(item.id)
        seen.add(item.id)
    return duplicates


def is_safe_id(value: str) -> bool:
    return bool(SAFE_ID_RE.fullmatch(value))


def add_error(issues: list[GuardrailIssue], code: str, message: str, path: Path | None = None, repair: str | None = None) -> None:
    issues.append(GuardrailIssue(code=code, severity="error", message=message, path=str(path) if path else None, repair=repair))


def add_warning(issues: list[GuardrailIssue], mode: str, code: str, message: str, path: Path | None = None, repair: str | None = None) -> None:
    if mode == "off":
        return
    issues.append(GuardrailIssue(code=code, severity="warning", message=message, path=str(path) if path else None, repair=repair))


def check_room_image(path: Path, mode: str, issues: list[GuardrailIssue], room_alpha_mode: str) -> None:
    size = image_size(path)
    if size != ROOM_SIZE:
        add_error(
            issues,
            "room-size",
            f"Room image is {size[0]}x{size[1]} but must be {ROOM_SIZE[0]}x{ROOM_SIZE[1]}." if size else "Room image cannot be read.",
            path,
            "Provide a 384x240 PNG room source. Do not crop or resize after generation.",
        )
        return
    margin_pixels = room_edge_margin_pixel_count(path, room_alpha_mode)
    if margin_pixels:
        add_warning(
            issues,
            mode,
            "room-edge-alpha",
            f"Room image has {margin_pixels} edge-connected margin pixels that alpha cleanup may remove.",
            path,
            "If real wall/floor edges disappear, re-run with --room-alpha-mode safe or revise the source image edge.",
        )


def check_props(props: list[AssetInput], mode: str, issues: list[GuardrailIssue]) -> None:
    for prop in props:
        size = image_size(prop.path)
        if size is None:
            add_error(issues, "prop-read", f"Prop `{prop.id}` cannot be read as an image.", prop.path, "Provide a valid transparent PNG prop.")
            continue
        if size[0] > ROOM_SIZE[0] or size[1] > ROOM_SIZE[1]:
            add_error(
                issues,
                "prop-size",
                f"Prop `{prop.id}` is {size[0]}x{size[1]} and must fit inside the {ROOM_SIZE[0]}x{ROOM_SIZE[1]} room canvas.",
                prop.path,
                "Resize or split the prop before creating the room.",
            )
        if not image_has_opaque_pixels(prop.path):
            add_error(
                issues,
                "prop-empty",
                f"Prop `{prop.id}` has no visible opaque pixels.",
                prop.path,
                "Export a transparent PNG with visible prop pixels, not a blank layer.",
            )
        if size[0] >= 300 or size[1] >= 180:
            add_warning(
                issues,
                mode,
                "prop-large",
                f"Prop `{prop.id}` is large enough to read like room/background art.",
                prop.path,
                "Confirm this should be a draggable prop; otherwise merge it into the room image.",
            )


def check_helpers(helpers: list[AssetInput], mode: str, issues: list[GuardrailIssue]) -> None:
    for helper in helpers:
        pet_json = helper.path / "pet.json"
        if not pet_json.exists():
            add_error(
                issues,
                "helper-pet-json",
                f"Helper `{helper.id}` is missing pet.json.",
                pet_json,
                "Pass a hatch-pet package directory with pet.json and spritesheet.webp.",
            )
            continue
        spritesheet = helper_spritesheet_path(helper.path)
        if spritesheet is None or not spritesheet.exists():
            add_error(
                issues,
                "helper-spritesheet",
                f"Helper `{helper.id}` has no valid spritesheet path.",
                helper.path,
                "Check pet.json spritesheetPath or add spritesheet.webp to the helper package.",
            )
            continue
        size = image_size(spritesheet)
        if size != ATLAS_SIZE:
            add_error(
                issues,
                "helper-atlas-size",
                f"Helper `{helper.id}` atlas is {size[0]}x{size[1]} but must be {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]}." if size else f"Helper `{helper.id}` atlas cannot be read.",
                spritesheet,
                "Regenerate or provide a standard hatch-pet atlas.",
            )
        if not sidecar_path_for(spritesheet).exists():
            add_warning(
                issues,
                mode,
                "helper-style-metadata",
                f"Helper `{helper.id}` has no optional style sidecar next to its spritesheet.",
                spritesheet,
                "Visual QA should confirm the helper matches the main pet style before release.",
            )


def check_ids(props: list[AssetInput], helpers: list[AssetInput], placements: list[str], issues: list[GuardrailIssue]) -> None:
    for item in [*props, *helpers]:
        if not is_safe_id(item.id):
            add_error(
                issues,
                "unsafe-asset-id",
                f"Asset id `{item.id}` is not safe for generated file paths.",
                repair="Use letters, numbers, underscore, and hyphen only; start with a letter or number.",
            )
    for prop_id in sorted(duplicate_ids(props)):
        add_error(issues, "duplicate-prop-id", f"Duplicate prop id `{prop_id}`.", repair="Use unique ids for each prop.")
    for helper_id in sorted(duplicate_ids(helpers)):
        add_error(issues, "duplicate-helper-id", f"Duplicate helper id `{helper_id}`.", repair="Use unique ids for each helper pet.")
    prop_ids = {prop.id for prop in props}
    helper_ids = {helper.id for helper in helpers}
    for item_id in sorted(prop_ids & helper_ids):
        add_error(issues, "asset-id-collision", f"Asset id `{item_id}` is used by both a prop and helper.", repair="Rename one asset id.")
    for reserved in sorted((prop_ids | helper_ids) & {"room", "main-owner"}):
        add_error(issues, "reserved-asset-id", f"Asset id `{reserved}` is reserved by the runtime.", repair="Choose a custom id such as desk, plant, or reviewer.")
    for value in placements:
        if "=" not in value:
            add_error(issues, "prop-placement-format", f"Prop placement must use id=value format: {value}", repair="Use desk=behind-pet or desk=foreground.")
            continue
        prop_id, raw_placement = value.split("=", 1)
        prop_id = prop_id.strip()
        raw_placement = raw_placement.strip()
        if prop_id not in prop_ids:
            add_error(
                issues,
                "unknown-prop-placement",
                f"Prop placement references unknown prop id `{prop_id}`.",
                repair="Add a matching --prop id=path argument or remove the placement.",
            )
        if prop_id and not is_safe_id(prop_id):
            add_error(
                issues,
                "unsafe-placement-id",
                f"Prop placement id `{prop_id}` is not safe for generated file paths.",
                repair="Use the same slug-like id as the matching --prop argument.",
            )
        if raw_placement not in PROP_PLACEMENTS:
            add_error(
                issues,
                "invalid-prop-placement",
                f"Unknown prop placement `{raw_placement}` for `{prop_id}`.",
                repair="Allowed placements: background, behind-pet, front-of-pet, foreground.",
            )


def run_asset_guardrails(
    *,
    pet_package: Path,
    room_image: Path,
    props: list[AssetInput],
    helpers: list[AssetInput],
    prop_placements: list[str],
    mode: str = "basic",
    room_alpha_mode: str = "balanced",
) -> dict[str, Any]:
    if mode not in GUARDRAIL_MODES:
        raise ValueError(f"Unknown guardrail mode: {mode}")
    issues: list[GuardrailIssue] = []

    pet_json = pet_package / "pet.json"
    if not pet_json.exists():
        add_error(issues, "main-pet-json", f"Main pet package is missing pet.json.", pet_json, "Pass an existing hatch-pet package directory.")
    else:
        spritesheet = helper_spritesheet_path(pet_package)
        if spritesheet is None or not spritesheet.exists():
            add_error(issues, "main-pet-spritesheet", "Main pet package has no valid spritesheet path.", pet_package, "Check pet.json spritesheetPath.")
        else:
            size = image_size(spritesheet)
            if size != ATLAS_SIZE:
                add_error(
                    issues,
                    "main-pet-atlas-size",
                    f"Main pet atlas is {size[0]}x{size[1]} but must be {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]}." if size else "Main pet atlas cannot be read.",
                    spritesheet,
                    "Use a standard hatch-pet package.",
                )
    if not room_image.exists():
        add_error(issues, "room-missing", "Room image is missing.", room_image, "Provide a 384x240 room PNG.")
    else:
        check_room_image(room_image, mode, issues, room_alpha_mode)

    check_ids(props, helpers, prop_placements, issues)
    check_props(props, mode, issues)
    check_helpers(helpers, mode, issues)

    if mode == "strict":
        issues = [
            GuardrailIssue(
                code=issue.code,
                severity="error" if issue.severity == "warning" else issue.severity,
                message=issue.message,
                path=issue.path,
                repair=issue.repair,
            )
            for issue in issues
        ]

    errors = [issue.to_dict() for issue in issues if issue.severity == "error"]
    warnings = [issue.to_dict() for issue in issues if issue.severity == "warning"]
    return {"ok": not errors, "mode": mode, "errors": errors, "warnings": warnings}


def format_guardrail_failure(result: dict[str, Any]) -> str:
    lines = ["Asset guardrails failed:"]
    for issue in result.get("errors", []):
        location = f" ({issue['path']})" if issue.get("path") else ""
        message = str(issue["message"]).rstrip().rstrip(".!?")
        repair = f" Fix: {issue['repair']}" if issue.get("repair") else ""
        lines.append(f"- {message}{location}.{repair}")
    return "\n".join(lines)
