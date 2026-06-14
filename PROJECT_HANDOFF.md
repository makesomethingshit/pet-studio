# Pet Studio Maintainer Notes

This repository is prepared for the Pet Studio `v0.1.2` public release.

## Public Positioning

Pet Studio is a Codex skill plus desktop widget runtime for building layered pet rooms from hatch-pet packages. The public commands and documentation should use Pet Studio naming.

The old `project-room-*` names remain as v1 compatibility filenames and module names where changing them would break existing kits:

- `project-room.json`
- `project-room-projects.json`
- `project-room-layouts.json`
- `project-room-state.json`
- `project-room-window.json`
- Python implementation modules named `project_room_*`

Prefer the new wrappers in docs and examples:

- `tools/pet_studio_create_room.py`
- `tools/pet_studio_create_qa_pack.py`
- `pet-studio-widget/pet_studio_widget.py`
- `pet-studio-widget/pet_studio_event_adapter.py`
- `pet-studio-widget/set_pet_studio_state.py`
- `pet-studio-widget/set_active_pet_studio.py`
- `tools/install_pet_studio_skill.py`

## Release Checklist

- Keep local QA output under `tester/`; it is ignored by git.
- Keep local generated experiments under ignored run folders unless they are explicitly promoted as public examples.
- Do not commit local runtime state files:
  - `pet-studio-widget/project-room-active.json`
  - `pet-studio-widget/project-room-layouts.json`
  - `pet-studio-widget/project-room-state.json`
  - `pet-studio-widget/project-room-window.json`
- Before pushing, run:

```powershell
python tools\pet_studio_preflight.py --show-hook-log
python -m unittest discover -s pet-studio-widget\tests
python -m unittest discover -s pet-studio-kit\tests
python -m py_compile pet-studio-widget\pet_studio_widget.py pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\codex_pet_hook.py tools\install_pet_studio_skill.py tools\install_pet_studio_codex_integration.py tools\pet_studio_preflight.py tools\pet_studio_create_room.py tools\pet_studio_create_qa_pack.py
```

Preflight writes `runs/pet-studio-preflight-render.png`, and QA packs write under `runs/<project-id>/qa-pack/`; both are ignored by git.

## Current Demo

The public demo is:

```text
runs/gakju-imagegen-room-v1/
```

The README screenshot is:

```text
docs/images/gakju-widget-bubble-example.png
```

## Notes

- License is MIT from `v0.1.1`; `v0.1.0` remains available under its original Apache-2.0 terms.
- Current release version is stored in `VERSION`.
- Changelog entries live in `CHANGELOG.md`.
