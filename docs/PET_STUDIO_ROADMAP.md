# Pet Studio Roadmap

## Vision

Pet Studio turns each project into a small local desktop room. Each project owns a scene with room, pet, prop, layout, and current state, so the desktop host can show where work is happening without becoming a hosted dashboard or full game.

The long-term direction is a local visual workroom for AI projects. The shipped product should stay smaller until each layer earns its place: one workspace, one tiny room, and enough visible state to understand what is happening without reading logs.

The final vision is broader than the current implementation:

- every workspace can have its own recognizable room
- room state changes reflect real project lifecycle events
- helper pets and props make review, blocked, handoff, and done states visible without reading logs
- users can create, tune, and share room presets without editing JSON by hand
- the widget stays local-first and lightweight rather than becoming a hosted dashboard

## Current Reality

Current 0.4.x is a widget-app line, not a team orchestrator.

What exists today:

- local Windows desktop widget
- one-click install path
- layered room rendering
- state bridge and speech bubbles
- workspace/project auto-detection
- system tray controls
- Codex skill and hook bridge as optional adapters
- `pet_studio_core/` boundary for shared registry and state behavior
- QA gate and CI checks

What does not exist today:

- Team Room UI
- Project Hub
- Task Cards
- endpoint registry
- LLM worker orchestration
- preset export/import
- macOS/Linux widget hosts

## Completed - 0.3.x Foundation

### 0.3.0 - Core Boundary

- `pet_studio_core/` shared registry and state bridge with zero Codex/Tkinter/widget imports
- `init_core()` for external path/state injection
- `write_project_state(metadata=...)` for extensible state payloads
- removed dangerous `sys.modules` deletion from widget import preference logic
- documented Core / Adapter / Widget Host boundaries
- preserved `project-room-*` v1 compatibility

### 0.3.1 - UX + Repo Hygiene

- one-click installer via `install.cmd`
- interactive room creator via `tools/create_room_interactive.py`
- auto-project detection in widget startup
- archived debug artifacts and stale QA docs
- synced English/Korean docs
- added QA gate pipeline and CI lint

## Current - 0.4.x Widget App Line

The 0.4.x line makes the room widget usable as a small app.

- room switching without manual `--project-id`
- system tray room list, state override, and quit
- status bar with current project/state
- optional Codex skill install and hook bridge
- release metadata should stay aligned across `VERSION`, `pyproject.toml`, README, and CHANGELOG

## Next - 0.5.x Presets + Script State Manager

Do the useful low-tech version first.

- room preset export/import as local zip files
- a script-only state manager before any LLM backend
- a tiny tray/status panel only if it helps inspect that loop
- a short local event log
- no popups by default

Backend rule: start with script mode. Add Ollama, llama.cpp, vLLM, or remote model adapters only after there is a real call site.

## Later - 0.6 Team UI

- Team Room registration and removal
- compact team panel opened on demand
- staff cards with avatar, name, and status
- task queue counts such as `waiting 3 / running 1`
- manual/script routing first; LLM classification later if it earns its keep

## Later - 0.7 Project Hub

- Project Hub window
- Mission input
- Task Cards with waiting/running/done states
- Meeting Table summary area
- Codex packet draft/export

## Later - 0.8+ Workroom Expansion

- lightweight room editor
- room theme packs
- macOS/Linux widget hosts
- richer endpoint aliases for local/cheap/SOTA/Codex roles
- permission/trust review for imported skills
- optional image provider integration

## Non-Goals for 0.4.x / 0.5.x

- GUI room editor
- macOS/Linux widget hosts
- Team Rooms / Project Hubs
- cloud sync
- schema-breaking room format changes
- hosted dashboard behavior

## Longer-Term Workroom Concepts

Broader workroom concepts are attractive directions, not current features.

- project progress visualization that maps task progress into the room without becoming a heavy dashboard
- room theme packs and community distribution
- shareable room presets
- Team Rooms, Project Hubs, task cards, and delegation traces

See [Pet Studio Workroom Vision](PET_STUDIO_WORKROOM_VISION.md).

## Out Of Scope

- No top-down office simulation.
- No full game map, walking paths, or room navigation.
- No standalone hosted dashboard app.
- No requirement that many agents are visible at all times.
- No cloud sync or hosted team service.
- No claim of full private Codex pet runtime parity until each behavior is confirmed and reproduced.