"""Scene entity helpers for Pet Studio widget runtime."""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


DEFAULT_LAYOUT_FILE = Path(__file__).with_name("project-room-layouts.json")
DEFAULT_WINDOW_FILE = Path(__file__).with_name("project-room-window.json")
DEFAULT_SESSION_FILE = Path(__file__).with_name("project-room-session.json")
DEFAULT_BUBBLE_MESSAGES = {
    "running": "Working",
    "waiting": "Waiting",
    "review": "Reviewing",
    "failed": "Need input",
    "blocked": "Need input",
    "handoff": "Reviewing",
    "jumping": "Done",
    "done": "Done",
}
MAX_BUBBLE_TEXT_LENGTH = 80
BUBBLE_STYLE = {
    "fill": "#fffaf1",
    "outline": "#7a6554",
    "shadow": "#d8c0a1",
    "text": "#2d241e",
}


def rounded_rectangle_points(
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float,
    steps: int = 4,
) -> list[float]:
    radius = max(0.0, min(float(radius), (right - left) / 2, (bottom - top) / 2))
    if radius <= 0:
        return [left, top, right, top, right, bottom, left, bottom]
    points: list[float] = []
    corners = (
        (right - radius, top + radius, -90, 0),
        (right - radius, bottom - radius, 0, 90),
        (left + radius, bottom - radius, 90, 180),
        (left + radius, top + radius, 180, 270),
    )
    for cx, cy, start, end in corners:
        for index in range(steps + 1):
            angle = math.radians(start + (end - start) * index / steps)
            points.extend([cx + math.cos(angle) * radius, cy + math.sin(angle) * radius])
    return points


@dataclass(frozen=True)
class SceneEntity:
    id: str
    role: str
    path: str
    anchor_name: str
    anchor: dict[str, int]
    scale: float
    flip_x: bool
    z: int
    placement: str | None
    visible_when: tuple[str, ...]
    draggable: bool
    locked: bool


def default_locked(role: str) -> bool:
    return role == "room"


def default_draggable(role: str) -> bool:
    return role in {"prop", "mainPet", "helperPet"}


def coerce_anchor(anchor: dict[str, Any]) -> dict[str, int]:
    return {"x": int(anchor["x"]), "y": int(anchor["y"])}


def source_canvas_size(kit: dict[str, Any]) -> tuple[int, int]:
    source_canvas = kit.get("sourceCanvas", kit.get("cell", {}))
    return int(source_canvas.get("width", 0)), int(source_canvas.get("height", 0))


def anchor_inside_source_canvas(kit: dict[str, Any], anchor: dict[str, int]) -> bool:
    width, height = source_canvas_size(kit)
    return 0 <= anchor["x"] <= width and 0 <= anchor["y"] <= height


def clamp_anchor_to_source_canvas(kit: dict[str, Any], anchor: dict[str, int]) -> dict[str, int]:
    width, height = source_canvas_size(kit)
    if width <= 0 or height <= 0:
        return coerce_anchor(anchor)
    return {
        "x": max(0, min(width, int(anchor["x"]))),
        "y": max(0, min(height, int(anchor["y"]))),
    }


def project_layout_document(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": 1, "projects": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data.setdefault("schemaVersion", 1)
    data.setdefault("projects", {})
    return data


def load_project_layout(path: Path, project_id: str | None) -> dict:
    if not project_id:
        return {"anchors": {}, "zOrder": {}}
    data = project_layout_document(path)
    project = data.get("projects", {}).get(project_id, {})
    anchors = project.get("anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}
    z_order = project.get("zOrder", {})
    if not isinstance(z_order, dict):
        z_order = {}
    return {
        "anchors": {entity_id: coerce_anchor(anchor) for entity_id, anchor in anchors.items()},
        "zOrder": {entity_id: int(value) for entity_id, value in z_order.items() if isinstance(value, (int, float))},
    }


def save_project_anchor(path: Path, project_id: str, entity_id: str, anchor: dict[str, int]) -> None:
    data = project_layout_document(path)
    projects = data.setdefault("projects", {})
    project = projects.setdefault(project_id, {})
    anchors = project.setdefault("anchors", {})
    anchors[entity_id] = coerce_anchor(anchor)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_project_z_order(path: Path, project_id: str, entity_id: str, z: int) -> None:
    data = project_layout_document(path)
    projects = data.setdefault("projects", {})
    project = projects.setdefault(project_id, {})
    z_order = project.setdefault("zOrder", {})
    z_order[entity_id] = int(z)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reset_project_layout(path: Path, project_id: str) -> None:
    data = project_layout_document(path)
    project = data.setdefault("projects", {}).setdefault(project_id, {})
    project["anchors"] = {}
    project["zOrder"] = {}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def project_window_document(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": 1, "projects": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data.setdefault("schemaVersion", 1)
    data.setdefault("projects", {})
    return data


def load_project_window(path: Path, project_id: str | None) -> dict | None:
    if not project_id:
        return None
    data = project_window_document(path)
    project = data.get("projects", {}).get(project_id)
    if not isinstance(project, dict):
        return None
    window: dict[str, int | float] = {}
    if isinstance(project.get("x"), int):
        window["x"] = project["x"]
    if isinstance(project.get("y"), int):
        window["y"] = project["y"]
    if isinstance(project.get("scale"), (int, float)) and project["scale"] > 0:
        window["scale"] = float(project["scale"])
    return window or None


def save_project_window(path: Path, project_id: str, window: dict[str, int | float]) -> None:
    data = project_window_document(path)
    projects = data.setdefault("projects", {})
    projects[project_id] = {
        "x": int(window["x"]),
        "y": int(window["y"]),
        "scale": float(window["scale"]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def project_session_document(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": 1, "projects": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"schemaVersion": 1, "projects": {}}
    if not isinstance(data, dict):
        return {"schemaVersion": 1, "projects": {}}
    projects = data.get("projects")
    if not isinstance(projects, dict):
        projects = {}
    data["schemaVersion"] = int(data.get("schemaVersion", 1)) if isinstance(data.get("schemaVersion", 1), int) else 1
    data["projects"] = projects
    return data


def coerce_session_window(value: Any) -> dict[str, int | float] | None:
    if not isinstance(value, dict):
        return None
    window: dict[str, int | float] = {}
    if isinstance(value.get("x"), int):
        window["x"] = value["x"]
    if isinstance(value.get("y"), int):
        window["y"] = value["y"]
    if isinstance(value.get("scale"), (int, float)) and value["scale"] > 0:
        window["scale"] = float(value["scale"])
    return window or None


def normalize_project_session(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    session: dict[str, Any] = {}
    if isinstance(value.get("state"), str) and value["state"].strip():
        session["state"] = value["state"].strip()
    if isinstance(value.get("message"), str):
        session["message"] = value["message"]
    if isinstance(value.get("bubbleVisible"), bool):
        session["bubbleVisible"] = value["bubbleVisible"]
    window = coerce_session_window(value.get("window"))
    if window is not None:
        session["window"] = window
    if isinstance(value.get("stateSource"), str) and value["stateSource"].strip():
        session["stateSource"] = value["stateSource"].strip()
    if isinstance(value.get("updatedAt"), str) and value["updatedAt"].strip():
        session["updatedAt"] = value["updatedAt"].strip()
    return session


def load_project_session(path: Path, project_id: str | None) -> dict[str, Any]:
    if not project_id:
        return {}
    data = project_session_document(path)
    return normalize_project_session(data.get("projects", {}).get(project_id))


def save_project_session(path: Path, project_id: str, session: dict[str, Any]) -> None:
    data = project_session_document(path)
    projects = data.setdefault("projects", {})
    normalized = normalize_project_session(session)
    if "updatedAt" not in normalized:
        normalized["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    projects[project_id] = normalized
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_bubble_text(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= MAX_BUBBLE_TEXT_LENGTH:
        return normalized
    return normalized[: MAX_BUBBLE_TEXT_LENGTH - 3].rstrip() + "..."


def is_hex_color(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value[1:])


def normalize_bubble_style(style: dict[str, Any] | None) -> dict[str, str]:
    normalized = dict(BUBBLE_STYLE)
    if not isinstance(style, dict):
        return normalized
    for key in ("fill", "outline", "shadow", "text"):
        value = style.get(key)
        if is_hex_color(value):
            normalized[key] = str(value).lower()
    return normalized


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def main_pet_layer(kit: dict[str, Any]) -> dict[str, Any] | None:
    for layer in kit.get("layers", []):
        if isinstance(layer, dict) and layer.get("role") == "mainPet":
            return layer
    return None


def layer_asset_path(kit_dir: Path, layer: dict[str, Any] | None) -> Path | None:
    if not layer or not isinstance(layer.get("path"), str):
        return None
    return kit_dir / layer["path"]


def layer_sidecar_path(asset_path: Path | None) -> Path | None:
    if asset_path is None:
        return None
    return asset_path.with_name(asset_path.stem + ".asset.json")


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def mix_rgb(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(int(round(a[index] * (1 - amount) + b[index] * amount)) for index in range(3))


def average_opaque_rgb(path: Path) -> tuple[int, int, int] | None:
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
            image.thumbnail((96, 96), Image.Resampling.LANCZOS)
            source_pixels = image.load()
            pixels = [
                source_pixels[x, y][:3]
                for y in range(image.height)
                for x in range(image.width)
                if source_pixels[x, y][3] >= 96
            ]
    except (OSError, ValueError):
        return None
    if not pixels:
        return None
    count = len(pixels)
    return (
        sum(pixel[0] for pixel in pixels) // count,
        sum(pixel[1] for pixel in pixels) // count,
        sum(pixel[2] for pixel in pixels) // count,
    )


def bubble_style_from_pet_image(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    color = average_opaque_rgb(path)
    if color is None:
        return None
    return normalize_bubble_style(
        {
            "fill": rgb_to_hex(mix_rgb(color, (255, 255, 255), 0.78)),
            "outline": rgb_to_hex(mix_rgb(color, (20, 24, 28), 0.45)),
            "shadow": rgb_to_hex(mix_rgb(color, (255, 255, 255), 0.52)),
            "text": BUBBLE_STYLE["text"],
        }
    )


def resolve_bubble_style(kit: dict[str, Any], kit_dir: Path) -> dict[str, str]:
    manifest_style = kit.get("bubbleStyle")
    if isinstance(manifest_style, dict):
        return normalize_bubble_style(manifest_style)

    asset_path = layer_asset_path(kit_dir, main_pet_layer(kit))
    sidecar_path = layer_sidecar_path(asset_path)
    if sidecar_path and sidecar_path.exists():
        sidecar_style = read_json_object(sidecar_path).get("bubbleStyle")
        if isinstance(sidecar_style, dict):
            return normalize_bubble_style(sidecar_style)

    image_style = bubble_style_from_pet_image(asset_path)
    if image_style:
        return image_style
    return normalize_bubble_style(None)


def bubble_text_for_state(state: str, message: str | None, enabled: bool = True) -> str | None:
    if not enabled:
        return None
    if message and message.strip():
        return normalize_bubble_text(message)
    return DEFAULT_BUBBLE_MESSAGES.get(state)


def context_menu_labels(project_id: str | None, bubble_visible: bool = True, entity_selected: bool = False) -> tuple[str, ...]:
    labels = ["Cycle state"]
    if project_id:
        labels.append("Reset layout")
    if project_id and entity_selected:
        labels.extend(["Bring forward", "Send backward", "Bring to front", "Send to back"])
    labels.extend(["Larger", "Smaller", "Reset size"])
    labels.append("Hide bubble" if bubble_visible else "Show bubble")
    labels.append("Close")
    return tuple(labels)


def layer_anchor(kit: dict, layer: dict, layout: dict | None) -> dict[str, int]:
    anchor_name = layer.get("anchor", "cell-bottom-center")
    anchors = kit.get("anchors", {})
    anchor = anchors.get(anchor_name, anchors.get("cell-bottom-center", {"x": 0, "y": 0}))
    layout_anchor = (layout or {}).get("anchors", {}).get(layer["id"])
    if layout_anchor:
        coerced_layout_anchor = coerce_anchor(layout_anchor)
        if anchor_inside_source_canvas(kit, coerced_layout_anchor):
            return coerced_layout_anchor
    return coerce_anchor(anchor)


def scene_entities_from_kit(kit: dict, layout: dict | None = None) -> list[SceneEntity]:
    entities: list[SceneEntity] = []
    z_order = (layout or {}).get("zOrder", {})
    if not isinstance(z_order, dict):
        z_order = {}
    for layer in kit["layers"]:
        role = layer["role"]
        visible_when = tuple(layer.get("visibleWhen", []))
        layer_z = z_order.get(layer["id"], layer.get("z", 0))
        entities.append(
            SceneEntity(
                id=layer["id"],
                role=role,
                path=layer["path"],
                anchor_name=layer.get("anchor", "cell-bottom-center"),
                anchor=layer_anchor(kit, layer, layout),
                scale=float(layer.get("scale", 1.0)),
                flip_x=bool(layer.get("flipX", False)),
                z=int(layer_z),
                placement=layer.get("placement"),
                visible_when=visible_when,
                draggable=bool(layer.get("draggable", default_draggable(role))),
                locked=bool(layer.get("locked", default_locked(role))),
            )
        )
    return sorted(entities, key=lambda entity: entity.z)


def visible_entity_ids(state_config: dict, entities: list[SceneEntity]) -> set[str]:
    configured = set(state_config.get("visibleLayers", []))
    if configured:
        return configured
    return {entity.id for entity in entities}


def entity_visible_for_state(entity: SceneEntity, state: str, visible_ids: set[str]) -> bool:
    if entity.id not in visible_ids:
        return False
    return not entity.visible_when or state in entity.visible_when


def visible_scene_entities(kit: dict, entities: list[SceneEntity], state: str) -> list[SceneEntity]:
    state_config = kit["states"][state]
    visible_ids = visible_entity_ids(state_config, entities)
    return [entity for entity in entities if entity_visible_for_state(entity, state, visible_ids)]


def kit_with_layout(kit: dict, layout: dict | None) -> dict:
    next_kit = copy.deepcopy(kit)
    for entity_id, anchor in (layout or {}).get("anchors", {}).items():
        if entity_id in next_kit.get("anchors", {}):
            next_kit["anchors"][entity_id] = coerce_anchor(anchor)
    return next_kit
