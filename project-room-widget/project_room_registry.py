"""Project assignment registry for Project Room Widget."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REGISTRY = Path(__file__).with_name("project-room-projects.json")
DEFAULT_STATE_FILE = Path(__file__).with_name("project-room-state.json")
STATE_ALIASES = {
    "done": "jumping",
    "blocked": "failed",
    "handoff": "review",
}
WIDGET_STATES = {
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
}


class ProjectRegistryError(RuntimeError):
    """Raised when a project assignment registry cannot resolve a project."""


@dataclass(frozen=True)
class ProjectAssignment:
    project_id: str
    display_name: str
    kit_manifest: Path
    kit_dir: Path
    pet_package_path: Path | None
    default_state: str
    theme: str
    enabled: bool
    raw: dict


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_registry_path(value: str | Path | None) -> Path:
    path = Path(value).expanduser() if value else DEFAULT_REGISTRY
    if not path.exists():
        raise ProjectRegistryError(f"Project registry not found: {path}")
    return path


def resolve_path(value: str | None, base_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def resolve_kit_manifest(value: str, base_dir: Path) -> Path:
    path = resolve_path(value, base_dir)
    if path is None:
        raise ProjectRegistryError("Project assignment is missing kitPath")
    if path.is_dir():
        path = path / "project-room.json"
    if not path.exists():
        raise ProjectRegistryError(f"Project Room Kit manifest not found: {path}")
    return path


def normalize_state(state: str | None, fallback: str = "idle") -> str:
    value = (state or fallback or "idle").strip()
    mapped = STATE_ALIASES.get(value, value)
    if mapped not in WIDGET_STATES:
        return normalize_state(fallback, "idle") if mapped != fallback else "idle"
    return mapped


def project_from_entry(entry: dict, registry_dir: Path, *, validate_kit: bool) -> ProjectAssignment:
    project_id = entry.get("projectId")
    if not project_id:
        raise ProjectRegistryError("Project entry is missing projectId")
    kit_path = entry.get("kitPath")
    if validate_kit:
        kit_manifest = resolve_kit_manifest(kit_path, registry_dir)
    else:
        resolved = resolve_path(kit_path, registry_dir)
        kit_manifest = (resolved / "project-room.json") if resolved and resolved.is_dir() else resolved
        if kit_manifest is None:
            kit_manifest = Path("")
    pet_package = resolve_path(entry.get("petPackagePath"), registry_dir)
    return ProjectAssignment(
        project_id=project_id,
        display_name=entry.get("displayName") or project_id,
        kit_manifest=kit_manifest,
        kit_dir=kit_manifest.parent if str(kit_manifest) else Path(""),
        pet_package_path=pet_package,
        default_state=normalize_state(entry.get("defaultState"), "idle"),
        theme=entry.get("theme") or "",
        enabled=bool(entry.get("enabled", True)),
        raw=entry,
    )


def list_projects(registry_path: str | Path | None = None, *, validate_kit: bool = False) -> list[ProjectAssignment]:
    path = resolve_registry_path(registry_path)
    data = load_json(path)
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        raise ProjectRegistryError("Project registry `projects` must be a list")
    return [project_from_entry(entry, path.parent, validate_kit=validate_kit) for entry in projects]


def select_project(registry_path: str | Path | None, project_id: str) -> ProjectAssignment:
    for project in list_projects(registry_path, validate_kit=True):
        if project.project_id != project_id:
            continue
        if not project.enabled:
            raise ProjectRegistryError(f"Project `{project_id}` is disabled")
        return project
    raise ProjectRegistryError(f"Unknown project id: {project_id}")


def read_project_state(state_file: str | Path | None, project_id: str | None, fallback: str) -> str:
    if not state_file:
        return normalize_state(fallback, "idle")
    path = Path(state_file).expanduser()
    if not path.exists():
        return normalize_state(fallback, "idle")
    data = load_json(path)
    state_project = data.get("projectId")
    if project_id and state_project and state_project != project_id:
        return normalize_state(fallback, "idle")
    return normalize_state(data.get("state"), fallback)


def project_to_summary(project: ProjectAssignment) -> dict:
    return {
        "projectId": project.project_id,
        "displayName": project.display_name,
        "kitPath": str(project.kit_manifest),
        "petPackagePath": str(project.pet_package_path) if project.pet_package_path else None,
        "defaultState": project.default_state,
        "theme": project.theme,
        "enabled": project.enabled,
    }
