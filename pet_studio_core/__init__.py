"""Core Pet Studio primitives shared by widget hosts and adapters."""

from __future__ import annotations

from .registry import (
    DEFAULT_ACTIVE_PROJECT_FILE,
    DEFAULT_REGISTRY,
    DEFAULT_STATE_FILE,
    STATE_ALIASES,
    WIDGET_STATES,
    ProjectAssignment,
    ProjectRegistryError,
    infer_project_for_workspace,
    init_core,
    list_projects,
    normalize_state,
    project_to_summary,
    read_active_project_id,
    read_project_state,
    select_active_project,
    select_project,
)
from .state import EXTERNAL_STATES, utc_now, write_project_state

__all__ = [
    "DEFAULT_ACTIVE_PROJECT_FILE",
    "DEFAULT_REGISTRY",
    "DEFAULT_STATE_FILE",
    "EXTERNAL_STATES",
    "STATE_ALIASES",
    "WIDGET_STATES",
    "ProjectAssignment",
    "ProjectRegistryError",
    "infer_project_for_workspace",
    "init_core",
    "list_projects",
    "normalize_state",
    "project_to_summary",
    "read_active_project_id",
    "read_project_state",
    "select_active_project",
    "select_project",
    "utc_now",
    "write_project_state",
]
