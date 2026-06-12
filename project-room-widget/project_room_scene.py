"""Scene entity helpers for Project Room widget runtime."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LAYOUT_FILE = Path(__file__).with_name("project-room-layouts.json")


@dataclass(frozen=True)
class SceneEntity:
    id: str
    role: str
    path: str
    anchor_name: str
    anchor: dict[str, int]
    scale: float
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


def project_layout_document(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": 1, "projects": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data.setdefault("schemaVersion", 1)
    data.setdefault("projects", {})
    return data


def load_project_layout(path: Path, project_id: str | None) -> dict:
    if not project_id:
        return {"anchors": {}}
    data = project_layout_document(path)
    project = data.get("projects", {}).get(project_id, {})
    anchors = project.get("anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}
    return {"anchors": {entity_id: coerce_anchor(anchor) for entity_id, anchor in anchors.items()}}


def save_project_anchor(path: Path, project_id: str, entity_id: str, anchor: dict[str, int]) -> None:
    data = project_layout_document(path)
    projects = data.setdefault("projects", {})
    project = projects.setdefault(project_id, {})
    anchors = project.setdefault("anchors", {})
    anchors[entity_id] = coerce_anchor(anchor)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def layer_anchor(kit: dict, layer: dict, layout: dict | None) -> dict[str, int]:
    anchor_name = layer.get("anchor", "cell-bottom-center")
    anchors = kit.get("anchors", {})
    anchor = anchors.get(anchor_name, anchors.get("cell-bottom-center", {"x": 0, "y": 0}))
    layout_anchor = (layout or {}).get("anchors", {}).get(layer["id"])
    return coerce_anchor(layout_anchor or anchor)


def scene_entities_from_kit(kit: dict, layout: dict | None = None) -> list[SceneEntity]:
    entities: list[SceneEntity] = []
    for layer in kit["layers"]:
        role = layer["role"]
        visible_when = tuple(layer.get("visibleWhen", []))
        entities.append(
            SceneEntity(
                id=layer["id"],
                role=role,
                path=layer["path"],
                anchor_name=layer.get("anchor", "cell-bottom-center"),
                anchor=layer_anchor(kit, layer, layout),
                scale=float(layer.get("scale", 1.0)),
                z=int(layer.get("z", 0)),
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
