# Changelog

All notable changes to Pet Studio are documented here.

## Unreleased

### Added

- Workroom-oriented team model presets for Scout, Coordinator, and Lead.
- Model profile CLI wrapper (`tools/pet_studio_model.cmd`) for active model,
  team preset, role model, and role env plan switching.
- Work CLI wrapper (`tools/pet_studio_work.cmd`) for mission, task, staff, role,
  start/done, and status updates without opening the GUI.
- Work Packet model metadata: active model profile, team model preset, role
  model plan, role env overrides, provider env cleanup hints, and relative
  Lead-only savings estimate.
- Team memory candidate approval flow and Work Packet approved-memory context.
- Local OpenAI-compatible gateway backend and Codex CLI backend.
- Shared Workroom Tk design tokens in `pet-studio-widget/ui/design_system.py`.

### Changed

- Workroom Endpoints tab now exposes model profiles, credit-aware role plan,
  team presets, selected-role env copy, and team env plan copy.
- Dispatcher and packet delivery can route work by assigned team role instead
  of always using the active Lead profile.
- Project Hub ttk styling now routes through shared design tokens.
- `team_state.json` contract version is now `0.8.0-dev`.

### Fixed

- Role env output now clears stale provider-specific model variables before
  setting a different route in the same shell.
- Preflight local-only checks now include Work Packet export directories.

## 0.7.0 - 2026-06-19

### Added

- Project Hub Toplevel window (`ui/project_hub.py`) - project list, switching, mission input, task cards.
- Task Cards tab - waiting/running/done columns with auto-sort from team_state queue.
- Work Packet export (`roost/packet.py`) - team_state to Work Packet v1 JSON with slug validation and legacy marker compatibility.
- Mission input in Project Hub - per-project mission text saved to team_state.
- State-aware status bar colors (green=running/done, red=failed/blocked, yellow=review, blue=waiting).
- Toast/status bar separation - toast hides status bar text, restores on expiry.

### Changed

- Team Room panel - converted from slide-in Toplevel to right-click context menu submenu (`add_team_room_menu`).
- `roost/state.py` - `list_projects()`, `set_project_mission()`, `get_project_mission()` added; `register_project()` now accepts `mission` field.

### Fixed

- Popup close reference leak (`_team_room_panel` not cleaned up) - replaced with menu-based approach.
- Context menu topmost conflict - menu opens with topmost released, restores after close.
- Export path escape vulnerability - `_safe_project_filename()` slug validation on project_id.

### Tests

- 201 total tests: 83 roost, 118 widget (unchanged, all green).

## 0.6.0 - 2026-06-18

### Added

- Approval queue in `roost/state.py`: `add_approval_request()`, `resolve_approval()`, `get_pending_approvals()`.
- Employee status tracking: `get_employees()`, `set_employee_status()`.
- L2 ASK actions auto-enqueue approval requests via `_try_enqueue_approval()` in `roost/security.py`.
- Team Room slide-in panel (`pet-studio-widget/team_room_panel.py`) with approvals, staff status, and queue.
- `Ctrl+Shortcut+T` toggle for Team Room panel.
- Default employee pool (Codex, Claude) in `team_state.json`.
- Full UUID (36 chars) for approval IDs instead of truncated 8-char.
- Zip Slip prevention in `import_preset()` - `is_relative_to()` check on all extracted paths.

### Tests

- 90 total tests: added `test_team_panel.py` (9 cases) + 3 new state tests.
- Zip Slip blocking tests for kit/ paths.
- UUID uniqueness and full-length tests.

### Security

- Zip Slip vulnerability fixed in preset import.
- Approval IDs now use full UUID to prevent collisions.

## 0.5.0 - 2026-06-17

### Added

- Security levels L0-L3 for per-project access control in `roost/security.py`.
- Context-aware event classification in `ScriptBackend`.
- Unified backend signature: `classify_event(event, context=None)`.
- Automatic context accumulation through `TeamState.log_event()`.
- `trust: {}` field in `team_state.json` for future auto-approval.

### Tests

- 276 total tests: 68 roost, 42 core, 118 widget, 48 kit/tools.
- Added `roost/tests/test_security.py` and `roost/tests/test_script_backend.py`.

### Fixed

- Removed external `PYTHONPATH` pollution from local test runs.
- Updated `install.cmd` dependency checks for tkinter and Pillow.

## 0.4.2 - 2026-06-17

### Fixed

- Fixed `ProjectRoomWidget` startup crash caused by `<Double-Button-1>` binding to
  the removed `cycle_state` method. The binding now calls `run_demo_cycle()`.

### Added

- Auto pet generation path in `create_room_interactive.py`.
- Python package dependency declaration for Pillow and Python 3.11+.
- `docs/PET_STUDIO_ORCHESTRATION_PLAN.md`.

## 0.4.1 - 2026-06-17

### Documentation

- Clarified app install vs Codex skill install as two entry points.
- Restored Codex skill install and hook integration scripts/tests in docs.
- Updated roadmap and feature lists.

## 0.4.0 - 2026-06-17

### Added

- Workspace auto-detection through registry workspace paths.
- System tray icon.
- Status bar with current project/state.
- Right-click project switching.
- Codex skill install and optional Codex hook bridge.

### Removed

- Unused standalone `tools/workspace_watcher.py`.
- Uncalled preset import/export tools before the later Alba preset implementation.
- Deferred sample room pack, state transition animation, and helper pet AI.

### Tests

- 245 total tests.
- QA Gate 5/5 green.

## 0.3.1 - 2026-06-16

### Repository Hygiene

- Archived stale debug artifacts and QA docs.
- Kept only public/demo room assets in active `runs/`.
- Added one-click installer, interactive room creator, and auto project detection.
- Added QA gate pipeline and CI lint.
- Synced English/Korean docs.

## 0.3.0 - 2026-06-16

### Architecture

- Added `pet_studio_core` for shared registry and state bridge behavior.
- Kept Core free of Codex, Tkinter, widget, launcher, and image-provider imports.
- Re-exported compatibility APIs from existing widget modules.
- Preserved `project-room-*` v1 file names and payload shapes.

### Fixed

- Removed runtime `sys.modules` deletion from widget import preference logic.
