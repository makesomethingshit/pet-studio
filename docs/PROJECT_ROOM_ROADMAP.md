# Project Room Roadmap

## Vision

Project Room turns each project or chat room into a small pet room. Each project owns a scene with room, pet, prop, layout, and current state, so the desktop host can show where work is happening and how it is going without becoming a full dashboard or game.

The long-term experience should feel like a living Codex pet scene: a compact side-view room near the edge of the desktop, one main owner pet as the emotional focus, optional helper pets for review or handoff moments, draggable props, and project-specific layout details that make each workspace recognizable.

## Current State

- `project-room-kit` can create, validate, preview, and optionally bake layered `384x240` room kits.
- `create_project_room_kit.py` accepts an arbitrary hatch-pet package plus generated or authored room/prop assets.
- `project-room-widget` can render a layered kit as independent Canvas entities in a frameless desktop scene host.
- `codex_state_adapter.py` can publish manual Codex-like task events into the state bridge and infer project ids from registered workspace paths.
- `project-room-layouts.json` stores project-specific moved entity anchors without changing kit files.
- `project-room-window.json` stores registered project host window position and scale.
- `project-room-active.json` can pin an active project for Codex event adapters when workspace matching is ambiguous.
- Room asset intake clears edge-connected near-white margins to transparent alpha without cropping the `384x240` source.
- The scene host has pet UX parity v1: state speech bubbles, a right-click context menu, explicit close, and Escape close.
- The current best demo is `runs/gakju-imagegen-room-v1`, a Gakju SD/chibi archive room.

## Milestones

### M1. Project Assignment Registry

Create a local registry that maps project ids to pet packages and room kits.

Done when:

- `project-room-widget/project-room-projects.json` exists.
- Each project entry has `projectId`, `displayName`, `kitPath`, `petPackagePath`, `defaultState`, `theme`, and `enabled`.
- Disabled, unknown, or missing-kit projects produce clear errors.

### M2. Active Project Launcher

Let the widget choose a room by project id instead of only by direct kit path.

Done when:

- `project_room_widget.py --config <path> --project-id <id>` launches or renders that project.
- `--kit <path>` still works for direct compatibility.
- `--list-projects` prints the registry contents.
- `--render-project-once` writes a project-selected PNG without opening a window.

### M3. Project State Bridge

Use a small state file as the first external event bridge.

Done when:

- `project-room-widget/project-room-state.json` documents the active project state shape.
- `--state-file <path>` can switch a project between `idle`, `running`, `waiting`, `review`, `failed`, and `done`.
- State aliases are deterministic: `done` maps to `jumping`, `blocked` maps to `failed`, and `handoff` maps to `review`.

### M4. Multi-Project Kit Production

Register newly generated kits directly into the project registry.

Done when:

- `create_project_room_kit.py --register-project --project-id <id> --registry <path>` creates or updates a registry entry.
- New kits can immediately be selected by the widget through `--project-id`.

### M5. Helper/Sub-Agent Presentation

Make helper pets appear intentionally during collaboration states.

Done when:

- `review`, `handoff`, and `blocked` states have clear visual mappings.
- Missing helper pet assets degrade to a readable main-pet-only room.
- Helper placement does not crowd the main pet.

### M6. Codex Integration Layer

Connect real Codex project or task state to the state bridge.

Done when:

- A thin adapter can write `project-room-state.json` from a local command or hook.
- The adapter accepts structured JSON payloads from a host hook command.
- Active project pinning can resolve ambiguous workspace matches.
- The widget reacts without needing manual double-click state cycling.
- Automatic workspace/project discovery is documented and isolated from the core widget.

## Data Model

The first project identity model is a local string id. A project assignment entry points to:

- project identity: `projectId`, `displayName`, `theme`
- visual source: `petPackagePath`, `kitPath`
- workspace matching: `workspacePaths`
- active selection: local `project-room-active.json` pin
- runtime defaults: `defaultState`, `enabled`

The state bridge uses:

- `projectId`
- `state`
- `message`
- `updatedAt`

Codex-style event payloads accepted by the adapter use:

- `event`
- `message`
- optional `projectId`
- optional `cwd`
- optional `threadId`
- optional `worktreeId`
- optional `updatedAt`

## Out Of Scope

- No top-down office simulation.
- No full game map, walking paths, or room navigation.
- No standalone dashboard app.
- No requirement that many agents are visible at all times.
- No direct Codex hook integration before the file-based bridge is stable.
- No claim of full private Codex pet runtime parity until each behavior is confirmed and reproduced.
