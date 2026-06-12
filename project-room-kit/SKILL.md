---
name: project-room-kit
description: Create modular room-decorating Codex pet kits that match a selected hatch-pet style, preserve a large layered room source, generate or register props and helper pets, validate style consistency, render full-size previews, register project-specific pet rooms, and run a frameless project-room widget. Use when working on project-room pets, room-decorating pet widgets, project-to-pet assignments, style-matched props, helper pets, or hatch-pet composition workflows.
---

# Project Room Kit

## Overview

Use this skill to create and run modular project-room pets. The real source is a layered `384x240` room kit with separate room, prop, main pet, and optional helper pet layers. A standard hatch-pet package is only a compatibility preview or fallback.

Keep assets style-locked. Do not mix downloaded asset packs or generated images unless their sidecar metadata and visual QA match the selected style source.

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
7. Use `project-room-widget/project_room_widget.py` from the repository runtime, or copy the generated kit into another widget host.

## Production Command

```powershell
python project-room-kit/scripts/create_project_room_kit.py `
  --out-dir runs/my-project-room `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image runs/my-assets/room.png `
  --prop desk=runs/my-assets/desk.png `
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
- Static layers must not contain transparent RGB residue.

## Project Registry

Use `project-room-widget/project-room-projects.json` to map project ids to room kits. Each entry has:

- `projectId`
- `displayName`
- `kitPath`
- `petPackagePath`
- `workspacePaths`
- `defaultState`
- `theme`
- `enabled`

Use `project-room-widget/project-room-state.json` as the first file-based bridge from external task state to widget state. Supported external states include `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`.

Write the state bridge with:

```powershell
python project-room-widget/set_project_state.py --project-id archive-nook --state running --message "building room kit"
python project-room-widget/codex_state_adapter.py --event start --message "working"
```

`done` maps to the hatch-pet `jumping` row, `handoff` maps to `review`, and `blocked` maps to `failed`. When `codex_state_adapter.py` omits `--project-id`, infer it from the current workspace and registry `workspacePaths`. Helper pets should appear only in collaboration/problem-solving scenes: `review`, `handoff`, and `blocked`; kits without helper assets must still render clearly with the main pet only.

## Visual QA

Reject or regenerate assets when:

- room, prop, or helper perspective differs from the main pet
- outline weight, palette, shading, or texture visibly differs
- doors do not align to the fixed `384x240` room module
- props look imported from a different game asset pack
- helper pets read as a different franchise or rendering style
- the room buries the main pet or makes helper states feel crowded
