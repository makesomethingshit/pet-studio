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

- Inspect the workspace first and infer project id from the Pet Studio registry when possible. The current v1 compatibility file is `pet-studio-widget/project-room-projects.json`.
- Ask only for missing creative inputs: style source, room image, prop images, theme, display name, or whether fallback baking is wanted.
- Run creation, validation, preview, registry, and state-bridge scripts yourself when the local workspace allows it.
- Report outcomes as artifacts and next choices: created kit path, validation result, preview path, registered project id, layout file path, and any remaining missing asset.
- Treat asset guardrails as part of first-room creation: fix structural input errors before generating, and route subjective style concerns to QA instead of claiming automatic visual judgment.
- If an image generation step is needed, produce prompts and intake instructions, then wait for generated PNGs or use existing assets; do not claim automatic image generation unless an image generation tool is explicitly available and used.
- Before generating helper/sub-pet base art, show the user 2-3 compact concept directions that explicitly reference the selected style source, then wait for the user's choice. Do not silently choose a helper creature, mascot, or coworker form, because helper style mismatch is hard to repair after atlas generation.
- Keep manual shell commands as fallback/debug details, not the main user experience.
- For widget debugging, use `tools\\pet_studio_widget.cmd ... --foreground` or direct `pet-studio-widget/pet_studio_widget.py ... --foreground`; normal detached launches should be single-instance and focus the existing `Pet Studio Widget` window instead of creating stacked `pythonw.exe` copies.
- Preserve pet UX expectations in the scene host: speech bubble messages, right-click context menu, project window position persistence, and registered-project session restore. Full parity with the private Codex pet runtime is incremental; implement and document confirmed behaviors first.
- When working on Codex hook integration, use `tools/pet_studio_hook_status.py` to verify the bridge health (hooks installed, reachable, events flowing, state freshness). Run `tools/pet_studio_hook_status.py --json` for machine-parseable output.
- **Output encoding rule:** When writing docs, terminal output, or markdown that Codex will read, use ONLY ASCII characters for diagrams, arrows, and separators. Replace Unicode box-drawing characters with ASCII equivalents:
  - `│` (U+2502) --> `|`
  - `─` (U+2500) --> `-`
  - `├` (U+251C) --> `+--`
  - `└` (U+2514) --> `+--`
  - `▼` (U+25BC) --> `v` or `-->`
  - `▲` (U+25B2) --> `^` or `<--`
  - `●` (U+25CF) --> `*`
  - `○` (U+25CB) --> `o`
  - `→` (U+2192) --> `->` or `-->`
  - `←` (U+2190) --> `<-` or `<--`
  - `✓` (U+2713) --> `[OK]`
  - `✗` (U+2717) --> `[FAIL]`
  - `⚠` (U+26A0) --> `[WARN]`
  Rationale: Codex may not render non-ASCII box-drawing characters correctly, causing garbled output and failed patch matching.

## First Choice

Before generating or registering room/prop/helper assets, choose the style source:

1. Existing hatch-pet package
2. New main pet generated with hatch-pet first
3. Existing `style-lock.json`

The selected source controls perspective, palette, outline weight, room size, pet scale, and prop rendering.

## Core Workflow

1. Choose a hatch-pet package or style lock.
2. Generate or provide a `384x240` room image and optional transparent prop PNGs.
3. Prefer the repository wrapper `tools/pet_studio_create_room.py` when working inside the Pet Studio repo folder, such as the cloned `D:\pet-studio` checkout on this machine. It creates the kit, validates it, renders preview/contact images, registers the project, links a workspace, and prints preflight/launch/render/QA pack commands.
4. Use `pet-studio-kit/scripts/create_project_room_kit.py` only as a manual/debug fallback when the wrapper is unavailable or the workflow needs low-level control.
5. Run `scripts/validate_project_room_kit.py` before trusting any kit that was produced outside the guided wrapper.
6. Run `tools/pet_studio_preflight.py --project-id <id>` after registration to verify Python/Pillow, registry, kit validation, render-once, hook config, and ignored local state.
7. Create local QA evidence with `tools/pet_studio_create_qa_pack.py --project-id <id>` when a registered project should be reviewed.
8. Use `tools/pet_studio_demo_states.py --project-id <id> --once --delay-seconds 2` when README GIF capture or manual QA needs a deterministic state sequence.
9. Register the kit into a project registry when it should be selectable by project id.
10. Use `pet-studio-widget/pet_studio_widget.py` from the repository scene-host runtime. When operating from the installed `$pet-studio` skill outside the repo folder, use `scripts/launch_pet_studio_widget.py`; it resolves the cloned repo location recorded by `tools/install_pet_studio_skill.py` and must not create a fallback/minimal widget.

## Guided First-Room Command

Use this when the user wants to test or create a first custom room from an existing pet package and a room PNG:

```powershell
python tools/pet_studio_create_room.py `
  --project-id archive-nook `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

The wrapper refuses to overwrite an existing output directory unless `--force` is passed. Use `--dry-run` to inspect the low-level command without writing files. When a custom registry is supplied, the printed preflight/launch/render commands include the matching `--registry` or `--config` argument.

The wrapper runs asset guardrails before creating a kit. Default `--guardrail-mode basic` fails clear structural problems, such as wrong room size, invisible props, oversized props, duplicate ids, unknown prop placements, or invalid helper packages. Subjective style consistency remains a warning and QA responsibility. Use `--guardrail-mode strict` to turn warnings into failures, or `--guardrail-mode off` to suppress subjective warnings while keeping required structural validation.
Project ids, prop ids, and helper ids must be slug-like: letters, numbers, underscore, and hyphen only, starting with a letter or number. They become local file paths and registry keys, so reject path separators, dots, spaces, and shell-like fragments.
For Korean users, pass `--lang ko` or set `PET_STUDIO_LANG=ko` to show user-facing repair hints in Korean while preserving command flags, paths, JSON keys, and error codes in English.

Run setup check and create the local QA pack after registration:

```powershell
python tools/pet_studio_preflight.py --project-id archive-nook
python tools/pet_studio_create_qa_pack.py --project-id archive-nook
```

Preflight validates the selected registry project and kit before launch or QA handoff. The QA pack writes validation JSON, idle render, all-state contact sheet, widget render, `CODER_TO_QA.md`, and `qa-pack-summary.json`. Treat it as local evidence; do not edit `QA_REPORT.md` from this handoff.

When launching from the installed skill directory instead of the repo:

```powershell
python C:\Users\USER\.codex\skills\pet-studio\scripts\launch_pet_studio_widget.py --project-id archive-nook --scale 1.25
```

## Manual/Debug Command

```powershell
python pet-studio-kit/scripts/create_project_room_kit.py `
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
  --registry pet-studio-widget/project-room-projects.json `
  --workspace-path .
```

## Module Contract

- Source room modules are exactly `384x240`.
- Hatch-pet atlas cells remain `192x208`, only for pet frames and fallback baking.
- Pet atlases are `1536x1872`.
- Every generated asset has a sidecar `.asset.json`.
- Rooms include `left-door`, `right-door`, `floor-line`, and `back-wall` feature metadata.
- Room intake clears edge-connected near-white margin pixels to transparency while preserving the `384x240` canvas; do not crop the room source.
- Kit manifest asset paths must be relative paths that stay inside the kit directory; reject absolute paths and `..` escapes before opening images or sidecar metadata.
- Static layers must not contain transparent RGB residue.
- Prop layers should declare placement relative to the pet: `background`, `behind-pet`, `front-of-pet`, or `foreground`. Default generated props are `behindPet` so the main pet renders in front of furniture.
- Props must have visible opaque pixels and fit inside the `384x240` source canvas. If a prop is large enough to read as room/background art, confirm whether it should be a prop or merged into the room source.
- Helper packages must be standard hatch-pet packages with `pet.json` and a `1536x1872` atlas. Missing optional style sidecars are not an automatic failure, but require visual QA against the selected style source.
- Layers may set `flipX: true` for a runtime/preview/fallback horizontal mirror. Use it for simple orientation fixes only; do not use it to paper over asymmetric text, logos, lighting direction, or identity drift.
- Live runtime keeps room, prop, main pet, and helper pet as independent Canvas entities. Props and pets are draggable; room/background layers are locked by default.

## Pet Studio Registry

Use the Pet Studio registry to map project ids to room kits. The v1 compatibility file is `pet-studio-widget/project-room-projects.json`. Each entry has:

- `projectId`
- `displayName`
- `kitPath`
- `petPackagePath`
- `workspacePaths`
- `defaultState`
- `theme`
- `enabled`

Project linking lives in this registry. Created kit reports also include a `projectLink` block so the assigned project id, registry path, kit path, and workspace paths can be inspected without opening the registry by hand.

Project-specific entity position overrides live in `pet-studio-widget/project-room-layouts.json`. That filename remains the v1 compatibility storage contract. The host writes this file only for registered `--project-id` runs; direct `--kit` runs are temporary and do not persist layout, window, or session overrides.

Project-specific host window position and scale live in `pet-studio-widget/project-room-window.json`. That filename remains the v1 compatibility storage contract. The host writes this file only for registered `--project-id` runs; direct `--kit` runs do not persist window placement.

Registered project session snapshots live in `pet-studio-widget/project-room-session.json`. The session file stores the last visible state, message, bubble visibility, window position/scale, update time, and state source. Registered `--project-id` launches restore this by default; direct `--kit` launches do not. For deterministic QA or render/debug launches, pass `--no-restore-session`. Startup priority is explicit CLI values, fresh state bridge, session snapshot, then registry/window defaults. Stale working bridge states older than five minutes should not pin the widget in `running`, `waiting`, `review`, `failed`, `blocked`, or `handoff` after reopening.

Use `pet-studio-widget/project-room-state.json` as the v1 file-based bridge from external task state to widget state. Supported external states include `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`.

Write the state bridge with:

```powershell
python pet-studio-widget/set_pet_studio_state.py --project-id archive-nook --state running --message "building room kit"
python pet-studio-widget/pet_studio_event_adapter.py --event start --message "working"
```

`done` maps briefly to the hatch-pet `jumping` row and can include `resetAfterMs`/`resetToState` metadata so the widget returns to idle after completion. `handoff` maps to `review`, and `blocked` maps to `failed`. When `codex_state_adapter.py` omits `--project-id`, infer it from the current workspace and registry `workspacePaths`. State `message` text should appear as a runtime-only speech bubble near the main pet; it must not be baked into previews or kit assets. Helper pets should stay visible across normal working, waiting, review, blocked, and done states; kits without helper assets must still render clearly with the main pet only.

## Visual QA

Reject or regenerate assets when:

- room, prop, or helper perspective differs from the main pet
- outline weight, palette, shading, or texture visibly differs
- doors do not align to the fixed `384x240` room module
- props look imported from a different game asset pack
- helper pets read as a different franchise or rendering style
- the room buries the main pet or makes helper states feel crowded

## Handoff Protocol

Every agent session must read and update `.hermes/handoff.json`.

**On session start:**
1. Read `.hermes/handoff.json` — understand what the last agent did and what you should do next
2. If `nextAgent` is not your role (`codex`), stop and report the mismatch to the user

**On session end (before committing):**
1. Update `.hermes/handoff.json`:
   - Set `lastAgent` to `codex`
   - Summarize what you did in `lastAction`
   - Set `nextAgent` to `hermes`
   - Describe what Hermes should do next in `nextAction`
   - Add a `context` field pointing to relevant docs/code paths
   - Append to `history` array (keep last 10 entries)
2. Include the handoff update in your commit

**File location:** `.hermes/handoff.json` (committed to git, shared between agents)

**Do not** put runtime state or local paths in handoff.json — only task-level coordination.
