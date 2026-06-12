# Project Room Kit Design

## Summary

Project Room Kit extends the existing eye-level 2D pet idea into a modular room-decorating system. Instead of drawing the pet, desk props, and room into one inseparable image, the kit treats them as separate assets that can be arranged per project or chat room. Each room still has one main owner pet, but the room, props, and optional helper are independent pieces.

## Goals

- Keep the current pet's cute eye-level side-view feeling.
- Use project or chat room identity as the primary room unit.
- Keep the main pet as the emotional focus.
- Support room-decorating composition: pet, props, furniture, wall items, and room layer.
- Show multi-agent work through optional helper assets, not a crowded scene.
- Stay compatible with hatch-pet by baking a composed spritesheet when the runtime cannot render layers directly.

## Non-Goals

- Do not turn the pet into a top-down office simulation.
- Do not create a full game map with walking paths and room navigation.
- Do not require many agents to be visible at all times.
- Do not force every room detail into the pet's body silhouette.
- Do not replace the existing pet style with a new unrelated mascot system.

## Core Metaphor

Each project/chat room is a small side-view room kit.

- Chat room: the selected room.
- Main pet: the project owner assigned to the room.
- Room layer: wall/floor/base environment.
- Props: desk, monitor, chair, board, mug, notebook, plants, lamps, or project-specific decor.
- Helper pet: a temporary coworker asset that appears only during states such as review, handoff, or blocked work.
- Status bubble: runtime overlay or baked label-free visual state, depending on integration mode.

## Visual Direction

The room should feel like a tiny side-view dollhouse or desk nook at pet eye level. It should be built from separable assets: a quiet room base, furniture props, small decorative props, and one or more pet sprites. The composition should still sit near the bottom of the app like a pet widget, not open as a separate window.

The main pet should be readable at the same approximate scale as the current pet. Props must not overpower the character. Room decoration should make the project feel personal, but the pet remains the part the user emotionally tracks.

## State Model

The first version should support these project-room states:

- `idle`: main pet calmly present at the desk.
- `running`: main pet actively working at the monitor or notes.
- `waiting`: main pet turns toward the user, asking for input or approval.
- `review`: a reviewer helper asset appears beside the desk.
- `failed`: main pet reacts to a small project problem without large visual effects.
- `done`: main pet reports completion with a small celebratory pose.

Existing hatch-pet states can map into this model:

- `idle` remains idle.
- `running` becomes focused project work, not literal running.
- `waiting` becomes needs-user-input.
- `review` becomes helper-reviewer visit.
- `failed` becomes blocked or error state.
- `waving` can become greeting or completion acknowledgment.
- `jumping` can be reserved for brief delight when a project completes.
- `running-right` and `running-left` remain drag or movement states if the app needs them.

## Interaction Model

The room reacts to the active project or chat room:

- Switching projects changes the room label, status bubble, and possibly a small prop accent.
- When a task begins, the main pet moves into focused work.
- When review starts, one helper pet appears beside the desk or chair.
- When waiting for the user, the helper leaves and the main pet looks outward.
- When work finishes, the main pet briefly celebrates and then returns to idle.

Speech bubbles should be short and status-like:

- `planning...`
- `working on it`
- `reviewing`
- `needs input`
- `fixed`
- `done`

## Asset Strategy

Version 1 should create a modular asset kit before changing the production pet atlas. The kit should store separate pet, room, and prop assets plus a layout manifest.

Recommended kit structure:

- `pets/main-owner/spritesheet.webp`
- `pets/helper-reviewer/spritesheet.webp`
- `rooms/default-room.png`
- `props/desk.png`
- `props/monitor.png`
- `props/chair.png`
- `props/board.png`
- `props/notebook.png`
- `props/mug.png`
- `layouts/project-room.json`

There are two integration modes:

- **Layered runtime mode:** the pet runtime renders room, props, pet, helper, and overlays as separate layers.
- **Baked hatch-pet mode:** a composer combines the selected room, props, and pet state frames into a standard hatch-pet `spritesheet.webp` and `pet.json`.

Baked mode is the compatibility path for the current pet widget if it only accepts one normal pet package.

## Architecture

Recommended implementation units:

- `RoomKit`: owns available rooms, props, pets, and layout manifests.
- `LayoutManifest`: defines anchors, scale, z-order, visibility rules, and state variants.
- `MainPet`: normal hatch-pet compatible pet atlas.
- `HelperPet`: optional collaborator atlas used by review/handoff states.
- `RoomLayer`: background/floor/wall asset.
- `PropLayer`: furniture and decor sprites.
- `Composer`: bakes layers into a normal hatch-pet atlas when layered runtime support is unavailable.
- `RoomStateMachine`: defines state transitions and timed helper appearances.

The state machine should stay simple and deterministic for the first version. Layer visibility and prop variants should be data-driven through the layout manifest.

## Error Handling

- If project identity is missing, show a neutral room label and idle pet.
- If helper assets are missing, hide the helper and keep the main pet state readable.
- If prop assets are missing, skip only that prop and keep the pet visible.
- If room assets are missing, use a transparent or minimal floor-line room.
- If animation assets fail to load, fall back to a static idle frame.
- If state is unknown, treat it as `running` only when work is active; otherwise treat it as `idle`.

## Testing And QA

Visual QA should check:

- side-view eye-level perspective is preserved
- main pet remains the emotional focus
- helper pet never makes the room feel crowded
- bubbles do not cover the pets or important UI
- all text fits at small desktop and mobile widths
- states are distinct without relying on large effects
- the experience still feels like a pet, not a dashboard widget

Functional checks should cover:

- project switching updates selected room kit and state
- state transitions render or bake the correct pet, helper, and prop changes
- reduced motion mode disables or softens looping animations
- missing assets degrade gracefully

## Current Compatibility Choice

The next build should not be a standalone app. It should be a Project Room Kit generator that can produce modular assets and then optionally bake them into a normal hatch-pet package. This preserves the user's desired no-window pet widget experience while keeping the system flexible enough for room decorating later.
