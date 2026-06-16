# Pet Studio Roadmap

## Vision

Pet Studio turns each Codex project into a small local desktop room. Each project owns a scene with room, pet, prop, layout, and current state, so the desktop host can show where work is happening and how it is going without becoming a hosted dashboard or full game.

The long-term experience should feel like a compact side-view room near the edge of the desktop: one main owner pet as the emotional focus, optional helper pets for review or handoff moments, draggable props, and project-specific layout details that make each workspace recognizable.

The final vision is broader than the current implementation:

- every Codex workspace can have its own recognizable room
- room state changes reflect real agent lifecycle events
- helper pets and props make review, blocked, handoff, and done states visible without reading logs
- users can create, tune, and share room presets without editing JSON by hand
- the widget stays local-first and lightweight rather than becoming a hosted dashboard

---

## Completed — 0.3.x Widget Stability

> Make the shipped widget reliable and the core boundaries solid.

### 0.3.0 — Architecture Boundary

- `pet_studio_core/` — shared boundary module (registry + state bridge) with zero Codex/Tkinter/widget imports
- `init_core()` — external path/state injection instead of hard-coded widget directory layout
- `write_project_state(metadata=...)` — extensible state payload for future adapters
- Removed dangerous `sys.modules` deletion from `prefer_local_room_kit_tools()`
- Boundary doc (`ADAPTER_BOUNDARY.md`) + import-boundary regression test hardened
- `project-room-*` v1 compatibility preserved
- QA Gate pipeline: `scripts/run-qa.py` (preflight, unittest, compile, boundary, smoke) + `Makefile` + CI lint

### 0.3.1 — UX + Repo Hygiene

- One-click installer (`install.cmd`) — deps + preflight + widget launch
- Interactive room creator (`tools/create_room_interactive.py`) — prompts instead of CLI flags
- Auto-project-detection in widget `main()` — infers project from workspace when `--project-id` omitted
- Repo hygiene: moved `tester/` debug artifacts to `archive/tester/`, cleaned up 12 experimental `runs/` dirs, archived stale `docs/qa/` RC files
- README/CHANGELOG synced: version badges, roadmap sections, Korean/English parity
- Ruff lint + format CI passing

---

## Active — 0.4.0 Auto-Switch + Tray

> One room works. Next: switch between rooms without friction.

- `workspace_watcher.py` — polls workspace, auto-switches room on project change
- `tray_icon.py` — system tray icon with room list, state override, quit
- **Not in 0.4.0**: room preset export/import, state animations, helper pet behavior (Later)

## Later — Presets + Animations

- Room preset export/import (zip)
- State transition animations
- Helper pet reactive behavior
- Sample room pack

## Non-Goals for 0.4.0

- GUI room editor (0.5+)
- macOS/Linux widget hosts (later)
- Team Rooms / Project Hubs (separate track)
- Cloud sync
- Schema-breaking room format changes

---

## Later — Workroom Concepts

> Broader directions. Not currently scheduled for a specific version.

These are attractive directions, not current features:

- project progress visualization that maps task progress into the room without becoming a heavy dashboard
- macOS/Linux widget hosts
- room theme packs
- shareable room presets with community distribution

Long-term workroom vision (Team Rooms, Project Hubs, task cards, delegation traces):
see [docs/PET_STUDIO_WORKROOM_VISION.md](docs/PET_STUDIO_WORKROOM_VISION.md).

---

## Out Of Scope

- No top-down office simulation.
- No full game map, walking paths, or room navigation.
- No standalone dashboard app.
- No requirement that many agents are visible at all times.
- No cloud sync or hosted team service.
- No claim of full private Codex pet runtime parity until each behavior is confirmed and reproduced.
