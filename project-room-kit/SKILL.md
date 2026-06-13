---
name: pet-studio
description: Create modular room-decorating Codex pet kits and Pet Studio widgets that match a selected hatch-pet style, preserve layered room sources, generate or register props and helper pets, validate style consistency, render previews, register project-specific pet rooms, and connect Codex task state to runtime speech bubbles. Use when working on Pet Studio rooms, room-decorating pet widgets, project-to-pet assignments, style-matched props, helper pets, or Codex pet bubble integration workflows.
---

# Pet Studio

## Overview

Use this skill to create and run modular Pet Studio rooms. The real source is a layered `384x240` room kit with separate room, prop, main pet, and optional helper pet entities. A standard hatch-pet package is only a compatibility preview or fallback.

Keep assets style-locked. Do not mix downloaded asset packs or generated images unless their sidecar metadata and visual QA match the selected style source.

## Agent Behavior

Guide the user through the workflow instead of handing them command lists. Treat commands in this skill as tools for Codex to run, not instructions for the user to type.

- Inspect the workspace first and infer project id from the Pet Studio registry when possible. The current v1 compatibility file is `project-room-widget/project-room-projects.json`.
- Ask only for missing creative inputs: style source, room image, prop images, theme, display name, or whether fallback baking is wanted.
- Run creation, validation, preview, registry, and state-bridge scripts yourself when the local workspace allows it.
- Report outcomes as artifacts and next choices: created kit path, validation result, preview path, registered project id, layout file path, and any remaining missing asset.
- If an image generation step is needed, produce prompts and intake instructions, then wait for generated PNGs or use existing assets; do not claim automatic image generation unless an image generation tool is explicitly available and used.
- Before generating helper/sub-pet base art, show the user 2-3 compact concept directions that explicitly reference the selected style source, then wait for the user's choice. Do not silently choose a helper creature, mascot, or coworker form, because helper style mismatch is hard to repair after atlas generation.
- Keep manual shell commands as fallback/debug details, not the main user experience.
- Preserve pet UX expectations in the scene host: speech bubble messages, right-click context menu, and project window position persistence. Full parity with the private Codex pet runtime is incremental; implement and document confirmed behaviors first.

## First Choice

Before generating or registering room/prop/helper assets, choose the style source:

1. Existing hatch-pet package
2. New main pet generated with hatch-pet first
3. Existing `style-lock.json`

The selected source controls perspective, palette, outline weight, room size, pet scale, and prop rendering.

## Core Workflow

1. Choose a hatch-pet package or style lock.
2. Generate or provide a `384x240` room image and optional transparent prop PNGs.
3. Run `scripts/create_project_room_kit.py` to create a kit, prompt pack, validation report, previews, and optional fallback package.
4. Run `scripts/validate_project_room_kit.py` before trusting the kit.
5. Render visual QA with `scripts/render_project_room_preview.py --state idle` and `--state all`.
6. Register the kit into a project registry when it should be selectable by project id.
7. Use `project-room-widget/pet_studio_widget.py` from the repository scene-host runtime, or copy the generated kit into another host. `project_room_widget.py` remains as a legacy alias.

## Manual/Debug Command

```powershell
python project-room-kit/scripts/create_project_room_kit.py `
  --out-dir runs/my-pet-studio-room `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image runs/my-assets/room.png `
  --prop desk=runs/my-assets/desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook" `
  --display-name "Archive Nook" `
  --render-preview `
  --render-contact `
  --bake-fallback `
  --register-project `
  --project-id archive-nook `
  --registry project-room-widget/project-room-projects.json `
  --workspace-path .
```

## Module Contract

- Source room modules are exactly `384x240`.
- Hatch-pet atlas cells remain `192x208`, only for pet frames and fallback baking.
- Pet atlases are `1536x1872`.
- Every generated asset has a sidecar `.asset.json`.
- Rooms include `left-door`, `right-door`, `floor-line`, and `back-wall` feature metadata.
- Room intake clears edge-connected near-white margin pixels to transparency while preserving the `384x240` canvas; do not crop the room source.
- Static layers must not contain transparent RGB residue.
- Prop layers should declare placement relative to the pet: `background`, `behind-pet`, `front-of-pet`, or `foreground`. Default generated props are `behindPet` so the main pet renders in front of furniture.
- Layers may set `flipX: true` for a runtime/preview/fallback horizontal mirror. Use it for simple orientation fixes only; do not use it to paper over asymmetric text, logos, lighting direction, or identity drift.
- Live runtime keeps room, prop, main pet, and helper pet as independent Canvas entities. Props and pets are draggable; room/background layers are locked by default.

## Pet Studio Registry

Use the Pet Studio registry to map project ids to room kits. The v1 compatibility file is `project-room-widget/project-room-projects.json`. Each entry has:

- `projectId`
- `displayName`
- `kitPath`
- `petPackagePath`
- `workspacePaths`
- `defaultState`
- `theme`
- `enabled`

Project linking lives in this registry. Created kit reports also include a `projectLink` block so the assigned project id, registry path, kit path, and workspace paths can be inspected without opening the registry by hand.

Project-specific entity position overrides live in `project-room-widget/project-room-layouts.json`. That filename remains the v1 compatibility storage contract. The host writes this file only for registered `--project-id` runs; direct `--kit` runs are session-only.

Project-specific host window position and scale live in `project-room-widget/project-room-window.json`. That filename remains the v1 compatibility storage contract. The host writes this file only for registered `--project-id` runs; direct `--kit` runs do not persist window placement.

Use `project-room-widget/project-room-state.json` as the v1 file-based bridge from external task state to widget state. Supported external states include `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`.

Write the state bridge with:

```powershell
python project-room-widget/set_pet_studio_state.py --project-id archive-nook --state running --message "building room kit"
python project-room-widget/pet_studio_event_adapter.py --event start --message "working"
```

`done` maps to the hatch-pet `jumping` row, `handoff` maps to `review`, and `blocked` maps to `failed`. When `codex_state_adapter.py` omits `--project-id`, infer it from the current workspace and registry `workspacePaths`. State `message` text should appear as a runtime-only speech bubble near the main pet; it must not be baked into previews or kit assets. Helper pets should appear only in collaboration/problem-solving scenes: `review`, `handoff`, and `blocked`; kits without helper assets must still render clearly with the main pet only.

## Visual QA

Reject or regenerate assets when:

- room, prop, or helper perspective differs from the main pet
- outline weight, palette, shading, or texture visibly differs
- doors do not align to the fixed `384x240` room module
- props look imported from a different game asset pack
- helper pets read as a different franchise or rendering style
- the room buries the main pet or makes helper states feel crowded
