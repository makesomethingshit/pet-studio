# Pet Studio Maintainer Notes

This repository is being prepared for the Pet Studio `v0.2.0` release candidate.

## Public Positioning

Pet Studio is a local-first Codex skill plus desktop widget runtime for building layered pet rooms from hatch-pet packages. The public surface should use Pet Studio naming and stay focused on what works today:

- launch the sample room
- install the local `$pet-studio` skill
- optionally connect Codex hooks to speech bubbles
- create a first custom room from a hatch-pet package and room assets
- validate, preflight, render, and create local QA evidence

Longer-term workroom concepts live in `docs/PET_STUDIO_WORKROOM_VISION.md`. Treat them as direction, not current feature promises.

## Compatibility Names

The old `project-room-*` names remain as v1 compatibility filenames and module names where changing them would break existing kits:

- `project-room.json`
- `project-room-projects.json`
- `project-room-layouts.json`
- `project-room-state.json`
- `project-room-active.json`
- `project-room-window.json`
- `project-room-session.json`
- `project-room-hook-events.jsonl`
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
  - `pet-studio-widget/project-room-session.json`
  - `pet-studio-widget/project-room-state.json`
  - `pet-studio-widget/project-room-window.json`

Before pushing, run:

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m py_compile tools\pet_studio_create_room.py tools\pet_studio_preflight.py tools\pet_studio_create_qa_pack.py tools\install_pet_studio_skill.py tools\install_pet_studio_codex_integration.py pet-studio-kit\scripts\create_project_room_kit.py pet-studio-kit\scripts\validate_project_room_kit.py pet-studio-kit\scripts\bake_project_room_pet.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\codex_pet_hook.py
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id gakju-archive-demo
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

## Current 0.2.0 Focus

- First-room create wrapper and repair-oriented output.
- QA pack generation.
- Project-centered preflight.
- Asset guardrails and style-confirmation guidance.
- Registered widget session restore.
- Korean README and minimal Korean CLI repair hints for first-room setup errors.
- Local security hardening for IDs, replacement paths, hook commands, and kit manifest asset paths.

## Notes

- License is MIT from `v0.1.1`; `v0.1.0` remains available under its original Apache-2.0 terms.
- Current release version is stored in `VERSION`.
- Changelog entries live in `CHANGELOG.md`.
- Do not add Team Room, Project Hub, Core package extraction, or Codex Adapter architecture docs to the 0.2.0 release scope.
