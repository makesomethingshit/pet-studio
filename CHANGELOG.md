# Changelog

All notable changes to Pet Studio are documented here.

## 0.4.0 - 2026-06-17

### New Features

- **Auto room switching** — `infer_project_for_workspace()` in `codex_state_adapter.py` and `project_room_widget.py` detects workspace changes and switches rooms automatically.
- **System tray icon** — `tray_icon.py` adds a system tray icon with menu for room switching, state control, and quit (5 tests).
- **Status bar** — canvas overlay showing current project name and state.
- **Project switching** — right-click context menu to switch between registered projects.

### YAGNI/Scope Cleanup

- Removed `tools/workspace_watcher.py` — standalone polling module with no caller.
- Removed `tools/export_room.py` / `tools/import_room.py` — preset export/import deferred to Later.
- Removed `runs/sample-room-cozy-corner/` — sample room pack deferred to Later.
- Removed state transition animation from `project_room_widget.py` — `self.redraw_scene()` immediate settle is sufficient.
- Removed helper pet AI from `project_room_scene.py` — behavior mapping + bubble messages deferred to Later.
- Net: ~1,100 lines removed.

### Test Coverage

- 245 total tests (130 widget + 48 kit + 42 core + 23 tools + 2 smoke)
- QA Gate: 5/5 green (preflight, widget, kit, compile, boundary)

## 0.3.1 - 2026-06-16

### Repository Hygiene

- Moved `tester/` debug artifacts (70+ files) to `archive/tester/`
- Moved 12 experimental `runs/` directories to `archive/runs/` — kept only `gakju-imagegen-room-v1` (public sample) and `gakju-archive-demo` (demo room)
- Moved stale QA RC docs (`docs/qa/020-*, 030-*`) to `docs/qa/archive/`
- Deleted `CODER_TO_QA.md` (auto-generated, reproducible)
- Added `archive/` and `.hermes/` to `.gitignore`

### Documentation

- Synced `README.md` and `README.ko.md` section parity:
  - Added "What Works Today" items to Korean README (one-click install, interactive creator, auto-detect)
  - Added "Korean CLI Output" and "Demo State Cycler" sections to English README
  - Added missing doc links (Architecture, Adapter Boundary, Demo Script) to Korean README
- Updated roadmap links in both READMEs

## 0.3.0 - 2026-06-16

### Architecture

- Added `pet_studio_core/` — shared boundary module for project registry and state bridge.
  - `registry.py`: project assignments, path resolution, workspace-to-project inference, state normalization, kit manifest validation.
  - `state.py`: file-based state bridge with `EXTERNAL_STATES` validation, `resetAfterMs` support.
  - Core has zero runtime imports from Codex, Tkinter, widget host, or adapter modules.

### Fixes

- Removed dangerous `sys.modules` deletion from `prefer_local_room_kit_tools()` in `project_room_widget.py`. The function now only reorders `sys.path` to prefer local tools, without mutating the import cache at runtime. Added regression test.

### Compatibility

- All `project-room-*` v1 file names and shapes preserved.
- Existing `pet-studio-widget/` modules remain as-is; new shared behavior lands in `pet_studio_core` first.

### UX

- Added `install.cmd` — one-click install: clone, install deps, run preflight, launch widget.
- Added `tools/create_room_interactive.py` — interactive room creation with prompts instead of CLI flags.
- Added auto-project-detection to widget `main()`: when `--project-id` is omitted, widget infers the project from the current workspace directory.

### Documentation

- Expanded `ADAPTER_BOUNDARY.md`: clearer core/adapter ownership rules, adapter file map, compatibility rule.
- Strengthened core import-boundary tests with additional forbidden patterns (`install_pet_studio_codex_integration`, `pet_studio_widget`, `image_provider`).
- Updated README Quick Start: one-click install option, interactive room creation, manual steps preserved as Option B.
- Removed "one-click installer" from "Still Experimental" list (now shipped).

## 0.2.0 - 2026-06-15

- Started the first-room creation UX with a guided public wrapper for kit creation, validation, rendering, and registry linking.
- Added a local QA pack generator for validation evidence, renders, and `CODER_TO_QA.md` handoff files.
- Added project-centered preflight checks for generated rooms, including repair hints for registry, kit, hook, dependency, and render issues.
- Added asset guardrails for room size, transparent props, oversized props, duplicate ids, prop/helper collisions, invalid placements, and helper package validation.
- Added registered-project session restore so reopened widgets can restore the last state, bubble visibility, window position, and scale while ignoring stale bridge states.
- Hardened force-replace, hook passthrough, hook command quoting, id validation, manifest path containment, and direct render/bake image bounds.
- Added Korean public documentation and minimal Korean CLI repair hints for first-room creation and preflight failures.
- Fixed the Windows widget launcher path so normal launches focus an existing widget, avoid stacked detached `pythonw.exe` instances, and write detached output to local log files.
- Added a project state demo cycler for README GIF capture and manual QA that reuses the existing state bridge.
- Added `docs/PET_STUDIO_WORKROOM_VISION.md` as a long-term direction document without making workroom features part of the current release.

## 0.1.2 - 2026-06-14

Public stability hardening.

- Added a release preflight command that checks the public demo, local install, Codex hooks, ignored runtime files, and one-frame rendering.
- Documented the first-run demo flow, hook bubble policy, hook log debugging, and known limitations.
- Kept post-tool Codex hook bubbles in `Working` instead of premature review wording.

## 0.1.1 - 2026-06-14

License update.

- Changed the project license from Apache-2.0 to MIT for simpler public reuse.
- Updated package metadata and README badges to report the MIT license.
- Previous `v0.1.0` release remains available under its original Apache-2.0 terms.

## 0.1.0 - 2026-06-13

Initial public release.

- Added the `$pet-studio` Codex skill for generating and maintaining style-matched pet room kits.
- Added layered Pet Studio kit generation, validation, preview rendering, and optional hatch-pet fallback baking.
- Added the frameless Pet Studio widget runtime with draggable room entities, helper pets, speech bubbles, layout persistence, and registered project selection.
- Added Codex event bridge commands plus a local installer for project-scoped `hooks.json` lifecycle integration that updates widget bubble state from Codex task activity.
- Added the public Gakju archive room example and README screenshot.
- Kept `project-room.json` and `project-room-*` runtime files as the v1 compatibility format while exposing Pet Studio naming in public commands.
