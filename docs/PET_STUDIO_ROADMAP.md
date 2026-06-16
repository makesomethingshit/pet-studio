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

## Current — 0.3.x Widget Stability

> Make the shipped widget reliable and the core boundaries solid.

Completed in 0.3.0:

- `pet_studio_core/` — shared boundary module (registry + state bridge) with zero Codex/Tkinter/widget imports
- `init_core()` — external path/state injection instead of hard-coded widget directory layout
- `write_project_state(metadata=...)` — extensible state payload for future adapters
- Removed dangerous `sys.modules` deletion from `prefer_local_room_kit_tools()`
- Boundary doc (`ADAPTER_BOUNDARY.md`) + import-boundary regression test hardened
- `project-room-*`v1 compatibility preserved
- QA Gate pipeline: `scripts/run-qa.py` (preflight, unittest, compile, boundary, smoke) + `Makefile` + CI lint
- One-click installer (`install.cmd`) — deps + preflight + widget launch
- Interactive room creator (`tools/create_room_interactive.py`) — prompts instead of CLI flags
- Auto-project-detection in widget `main()` — infers project from workspace when `--project-id` omitted
- README/CHANGELOG updated: one-click install option, interactive creation, auto-detect documented

Planned for 0.3.x (hotfix level only):

- fix fresh-clone setup failures
- improve install/preflight error messages
- add clearer repair hints for common user mistakes
- polish the Windows widget launcher and state bridge behavior
- improve README/demo/social-preview material

Out of scope for 0.3.x:

- Team Rooms or Project Hubs
- core package extraction (already done)
- macOS/Linux widget hosts
- GUI room editor
- multi-project switcher
- schema-breaking room format changes

---

## Next — 0.4.x Multi-Room and Tray

> One room works. Next: switch between rooms without friction.

### Goals

- Working on project A, then `cd` to project B → widget auto-switches room
- System tray icon for quick room switching without re-launching
- At least 2 sample rooms (not just `gakju-archive-demo`)
- Room preset sharing (export/import a room as a zip)

### Themes

| Theme | Description | Priority |
|-------|-------------|----------|
| **Auto room switching** | Widget detects workspace change and loads the matching room | P0 |
| **System tray** | Tray icon with room list, state override, quit | P0 |
| **Sample room pack** | 2-3 pre-built rooms with different themes/props | P1 |
| **Room preset export** | `export_room.py` → zip with kit + assets + manifest | P1 |
| **Room preset import** | `import_room.py` ← zip, validates and registers | P1 |
| **Widget state animations** | Smooth transitions between states (not instant swap) | P2 |
| **Helper pet behavior** | Helper pets react to state (e.g. appears on blocked/review) | P2 |

### Non-Goals for 0.4.x

- GUI room editor (0.5+)
- macOS/Linux hosts (later)
- Team Rooms / Project Hubs (separate track)
- Cloud sync

### Success Criteria

1. User can `cd` between two registered projects and widget follows
2. Tray icon shows current room + allows manual switch
3. At least 2 sample rooms included in the repo
4. Room can be exported and imported on another machine
5. All existing 177 tests still pass + new features covered

### Technical Notes

- Auto-switching: widget polls workspace directory on a timer (5s) or watches filesystem events
- Tray: `pystray` or `infi.systray` on Windows; keep optional (graceful fallback if lib missing)
- Sample rooms: add under `runs/` with pre-built kits, document in README
- Export/import: zip = `kit/` + `assets/` + `manifest.json`; import validates via existing kit validator

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
