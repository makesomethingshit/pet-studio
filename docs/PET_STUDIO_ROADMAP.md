# Pet Studio Roadmap

## Vision

Pet Studio turns each project or chat room into a small pet room. Each project owns a scene with room, pet, prop, layout, and current state, so the desktop host can show where work is happening and how it is going without becoming a full dashboard or game.

The long-term experience should feel like a living Codex pet scene: a compact side-view room near the edge of the desktop, one main owner pet as the emotional focus, optional helper pets for review or handoff moments, draggable props, and project-specific layout details that make each workspace recognizable.

The final vision is broader than the current implementation:

- every Codex workspace can have its own recognizable room
- room state changes reflect real agent lifecycle events
- helper pets and props make review, blocked, handoff, and done states visible without reading logs
- users can create, tune, and share room presets without editing JSON by hand
- the widget stays local-first and lightweight rather than becoming a hosted dashboard

## Current State

This is what the repository can do today.

- `pet-studio-kit` can create, validate, preview, and optionally bake layered `384x240` room kits.
- `create_project_room_kit.py` accepts an arbitrary hatch-pet package plus generated or authored room/prop assets.
- `pet-studio-widget` can render a layered kit as independent Canvas entities in a frameless desktop scene host.
- `codex_state_adapter.py` can publish manual Codex-like task events into the state bridge and infer project ids from registered workspace paths.
- `project-room-layouts.json` stores project-specific moved entity anchors without changing kit files.
- `project-room-window.json` stores registered project host window position and scale.
- `project-room-active.json` can pin an active project for Codex event adapters when workspace matching is ambiguous.
- Room asset intake clears edge-connected near-white margins to transparent alpha without cropping the `384x240` source.
- The scene host has pet UX parity v1: state speech bubbles, a right-click context menu, explicit close, and Escape close.
- The current best demo is `runs/gakju-imagegen-room-v1`, a Gakju SD/chibi archive room.

## Current Limitations

- Windows is the primary tested desktop widget host.
- First-room creation is script-driven. There is no GUI editor yet.
- Codex integration uses local hooks and a file bridge. It depends on Codex hook trust approval.
- Generated room/helper quality depends on the supplied art and should be visually QA'd.
- Some filenames still use `project-room-*` because they are the v1 compatibility storage contract.
- There is no cloud service, marketplace packaging, room gallery, or team dashboard.

## Milestones

### 0.2.0 Target. First Room Creation UX

Pet Studio 0.2.0 should make the first custom room feel achievable from a fresh clone. The release theme is: choose an existing hatch-pet package, provide a room image and optional props/helpers, generate the kit, validate it, register it, and launch or preflight it without memorizing the lower-level script flags.

#### M1. Guided Create Command

Status: implemented in development.

Done when:

- `tools/pet_studio_create_room.py` wraps the lower-level kit generator with first-room defaults.
- The command validates input paths before running the generator.
- Generated rooms are validated, preview-rendered, contact-sheet-rendered, registered, and linked to the current workspace by default.
- Default output is a concise JSON summary with created artifacts and next commands.
- `--dry-run` previews the generated command without writing files.
- Existing output directories are refused unless `--force` is passed.

#### M2. First Room QA Pack

Status: next.

Done when:

- A generated room can produce validation JSON, idle render, all-state contact sheet, widget render, and `CODER_TO_QA.md`.
- The QA pack stays local by default and remains ignored by git.

#### M3. First Room Setup Check

Status: next.

Done when:

- Preflight can validate any generated project id, not only the bundled demo.
- The guided output clearly points to preflight, launch, and render commands.
- Missing hook trust, missing Pillow, invalid registry entries, and missing kit assets produce direct repair hints.

#### M4. Asset Guardrails

Status: next.

Done when:

- User-facing docs explain helper/sub-pet style confirmation, alpha cleanup limits, room bounds, and prop placement choices.
- The generator or wrapper fails clearly for common room/pet/prop mismatch cases before producing misleading output.

Out of scope for 0.2.0:

- No GUI editor.
- No cloud sync or remote service.
- No full room navigation or game simulation.
- No automatic helper/sub-pet concept selection without user confirmation.

### Completed Foundation. Project Assignment Registry

Create a local registry that maps project ids to pet packages and room kits.

Done when:

- `pet-studio-widget/project-room-projects.json` exists.
- Each project entry has `projectId`, `displayName`, `kitPath`, `petPackagePath`, `defaultState`, `theme`, and `enabled`.
- Disabled, unknown, or missing-kit projects produce clear errors.

Status: implemented.

### Completed Foundation. Active Project Launcher

Let the widget choose a room by project id instead of only by direct kit path.

Done when:

- `project_room_widget.py --config <path> --project-id <id>` launches or renders that project.
- `--kit <path>` still works for direct compatibility.
- `--list-projects` prints the registry contents.
- `--render-project-once` writes a project-selected PNG without opening a window.

Status: implemented.

### Completed Foundation. Project State Bridge

Use a small state file as the first external event bridge.

Done when:

- `pet-studio-widget/project-room-state.json` documents the active project state shape.
- `--state-file <path>` can switch a project between `idle`, `running`, `waiting`, `review`, `failed`, and `done`.
- State aliases are deterministic: `done` maps to `jumping`, `blocked` maps to `failed`, and `handoff` maps to `review`.

Status: implemented.

### Completed Foundation. Multi-Project Kit Production

Register newly generated kits directly into the project registry.

Done when:

- `create_project_room_kit.py --register-project --project-id <id> --registry <path>` creates or updates a registry entry.
- New kits can immediately be selected by the widget through `--project-id`.

Status: implemented.

### Completed Foundation. Helper/Sub-Agent Presentation

Make helper pets appear intentionally during collaboration states.

Done when:

- `review`, `handoff`, and `blocked` states have clear visual mappings.
- Missing helper pet assets degrade to a readable main-pet-only room.
- Helper placement does not crowd the main pet.

Status: implemented at the manifest/runtime level; art quality remains a visual QA responsibility.

### Current Integration. Codex Event Layer

Connect real Codex project or task state to the state bridge.

Done when:

- A thin adapter can write `project-room-state.json` from a local command or hook.
- The adapter accepts structured JSON payloads from a host hook command.
- Active project pinning can resolve ambiguous workspace matches.
- The widget reacts without needing manual double-click state cycling.
- Automatic workspace/project discovery is documented and isolated from the core widget.

Status: partially implemented. Manual event publishing, workspace matching, active project pinning, and hook installation exist. The bridge still depends on local hook files and trust approval.

## Longer-Term Ideas

These are attractive directions, not current features.

- Multi-project room switcher or tray.
- More state-specific room animation, not only pet row changes and bubbles.
- macOS/Linux widget hosts.
- Room theme packs and reusable prop packs.
- Shareable room presets.
- Lightweight room editor for users who do not want to hand-author assets or JSON.
- Project progress visualization that maps task progress into the room without becoming a heavy dashboard.
- Richer helper pet behavior for review, blocked, and handoff moments.

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
- No cloud sync or hosted team service.
- No claim of full private Codex pet runtime parity until each behavior is confirmed and reproduced.
