# Changelog

All notable changes to Pet Studio are documented here.

## 0.6.0 - 2026-06-18

### Added

- Approval queue in `roost/state.py`: `add_approval_request()`, `resolve_approval()`, `get_pending_approvals()`.
- Employee status tracking: `get_employees()`, `set_employee_status()`.
- L2 ASK actions auto-enqueue approval requests via `_try_enqueue_approval()` in `roost/security.py`.
- Team Room slide-in panel (`pet-studio-widget/team_room_panel.py`) with approvals, staff status, and queue.
- `Ctrl+Shortcut+T` toggle for Team Room panel.
- Default employee pool (Codex, Claude) in `team_state.json`.
- Full UUID (36 chars) for approval IDs instead of truncated 8-char.
- Zip Slip prevention in `import_preset()` — `is_relative_to()` check on all extracted paths.

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
