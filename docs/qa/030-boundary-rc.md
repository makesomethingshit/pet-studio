# CODER_TO_QA: 0.3.0 Boundary RC

## Summary

Implemented the 0.3.0 boundary release candidate. This is not a Team Room or Project Hub feature pass; it separates shared registry/state bridge primitives into `pet_studio_core` while preserving existing widget, CLI, and `project-room-*` compatibility behavior.

## What Changed

- Added `pet_studio_core` with registry and state bridge primitives.
- Converted `pet-studio-widget/project_room_registry.py` into a compatibility re-export wrapper.
- Kept `pet-studio-widget/set_project_state.py` as the same CLI entrypoint while delegating payload writes to core.
- Added architecture docs for Core, Widget Host, Codex Adapter, Asset Forge, and future Workroom boundaries.
- Updated roadmap/README/development checks for the 0.3.0 Boundary RC.

## QA Focus

- Existing commands and imports must continue to work:
  - `pet-studio-widget/project_room_registry.py`
  - `pet-studio-widget/set_project_state.py`
  - `pet-studio-widget/pet_studio_event_adapter.py`
- Confirm `project-room-*` file names and JSON payload shapes are unchanged.
- Confirm Codex hook mapping and hook logs still behave as adapter-owned behavior.
- Confirm no Team Room, Project Hub, endpoint registry, dashboard, or orchestrator behavior was added.
- Confirm `docs/ARCHITECTURE.md` and `docs/ADAPTER_BOUNDARY.md` clearly describe current boundaries without promising future features as current functionality.

## Verification Run

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m py_compile pet_studio_core\__init__.py pet_studio_core\registry.py pet_studio_core\state.py pet-studio-widget\project_room_registry.py pet-studio-widget\set_project_state.py pet-studio-widget\codex_state_adapter.py pet-studio-widget\codex_pet_hook.py
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
git diff --check
```

Observed result: all checks passed locally.
