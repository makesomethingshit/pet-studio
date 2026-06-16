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
- `project-room-*` v1 compatibility preserved

Planned for 0.3.x:

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

Candidate themes:

- multi-project room switcher or tray icon
- lightweight room editor for users who do not want to hand-author assets or JSON
- more sample room themes and prop packs
- sharable room presets

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
