# Pet Studio Maintainer Notes

This repository is being prepared for the Pet Studio `v0.8` workroom line.

## Public Positioning

Pet Studio is a local-first Windows Workroom and desktop widget for project
rooms. Codex is an optional adapter, not the product center. The public surface
should use Pet Studio naming and stay focused on what works today:

- launch the sample room
- install the local `$pet-studio` skill
- optionally connect Codex hooks to speech bubbles
- create a first custom room from a hatch-pet package and room assets
- validate, preflight, render, and create local QA evidence
- use the Workroom for mission input, task cards, Team Room status, endpoint
  visibility, and team model presets
- export/import Work Packets for tasks, staff assignments, model policy, role
  env, and relative credit estimates

Longer-term workroom concepts live in `docs/PET_STUDIO_WORKROOM_VISION.md`.
Treat them as direction, not current feature promises.

## Compatibility Names

The old `project-room-*` names remain as v1 compatibility filenames and module names where changing them would break existing kits:

- `project-room.json`
- `project-room-projects.json`
- `project-room-layouts.json`
- `project-room-state.json`
- `project-room-active.json`
- `project-room-window.json`
- `project-room-workroom.json`
- `project-room-session.json`
- `project-room-hook-events.jsonl`
- `team_state.json`
- Python implementation modules named `project_room_*`

Prefer the Pet Studio wrappers in docs and examples:

- `tools/pet_studio_create_room.py`
- `tools/pet_studio_create_qa_pack.py`
- `tools/pet_studio_preflight.py`
- `pet-studio-widget/pet_studio_widget.py`
- `pet-studio-widget/pet_studio_event_adapter.py`
- `pet-studio-widget/set_pet_studio_state.py`
- `pet-studio-widget/set_active_pet_studio.py`
- `tools/install_pet_studio_skill.py`

## Release Checklist

- Keep local QA output under `tester/`; it is ignored by git.
- Keep QA pack output under `runs/<project-id>/qa-pack/`; it is ignored by git.
- Keep local generated experiments under ignored run folders unless explicitly promoted as public examples.
- Do not commit local runtime state files:
  - `pet-studio-widget/project-room-active.json`
  - `pet-studio-widget/project-room-hook-events.jsonl`
  - `pet-studio-widget/project-room-layouts.json`
  - `pet-studio-widget/project-room-workroom.json`
  - `pet-studio-widget/project-room-session.json`
  - `pet-studio-widget/project-room-state.json`
  - `pet-studio-widget/project-room-window.json`
  - `pet-studio-widget/team_state.json`
  - `work-packets/`
  - `codex-packets/`

Before pushing, run:

```powershell
python -m pytest roost/tests/ -q
python -m pytest pet-studio-widget/tests/ -q
python -m pytest pet-studio-kit/tests/ -q
python -m pytest pet_studio_core/tests/ -q
ruff check roost/ pet-studio-widget/ pet-studio-kit/ tools/ pet_studio_core/
ruff format --check roost/ pet-studio-widget/ pet-studio-kit/ tools/ pet_studio_core/
git diff --check
```

Preflight writes `runs/pet-studio-preflight-render.png`; QA packs write under `runs/<project-id>/qa-pack/`. Both are ignored by git.

## Current Demo

The public demo project is:

```text
gakju-archive-demo
```

The checked-in demo kit source is:

```text
runs/gakju-imagegen-room-v1/
```

The README media is:

```text
docs/images/pet-studio-demo.gif
docs/images/gakju-widget-bubble-example.png
```

## Completed 0.4.0 — Status Bar, System Tray, Auto-Switch

- `pet_studio_core` owns shared registry and state bridge primitives
- Workspace auto-switch via `infer_project_for_workspace()` in adapter/widget (no separate watcher module)
- System tray icon (`tray_icon.py`) when caller is connected
- Existing `project_room_*` imports and `project-room-*` files remain compatible
- Codex hook payloads, hook logs, and trust behavior stay in adapter modules
- Architecture docs define Core, Widget Host, Codex Adapter, Asset Forge, CLI Tools, and future Workroom boundaries
- Team Room, Project Hub, endpoint registry, dashboard, and orchestration were future work at this milestone

**Explicitly deferred to Later / separate milestone:**
- Sample room pack (runs/sample-room-cozy-corner/)
- State transition animations (reverse-frame trick)
- Helper pet AI (behavior mapping + bubble messages)
- Standalone workspace_watcher.py polling module

## Completed 0.2.0 — First Room Creation UX

All 0.2.0 features are released. Summary of what was shipped:

- Guided first-room creation via `tools/pet_studio_create_room.py`
- QA pack generation via `tools/pet_studio_create_qa_pack.py`
- Project state demo cycler via `tools/pet_studio_demo_states.py`
- Korean localization for onboarding docs and repair hints (`--lang ko` / `PET_STUDIO_LANG=ko`)
- Local security hardening for IDs, replacement paths, hook commands, and kit manifest asset paths
- Asset guardrails with `basic` / `strict` / `off` modes
- Registered widget session restore via `project-room-session.json`
- Windows widget launcher single-instance/focus behavior and detached launcher logging
- Codex hook bridge with `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop` hooks

Out of scope for 0.2.0 at that milestone:
- No GUI editor
- No cloud sync or remote service
- No full room navigation or game simulation
- No automatic helper/sub-pet concept selection without user confirmation
- No Team Room or Project Hub

## Notes

- License is MIT from `v0.1.1`; `v0.1.0` remains available under its original Apache-2.0 terms.
- Current release version is stored in `VERSION`.
- Changelog entries live in `CHANGELOG.md`.
