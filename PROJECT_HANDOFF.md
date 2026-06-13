# Pet Studio Maintainer Notes

This repository is prepared for the Pet Studio `v0.1.1` public release.

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

- `project-room-widget/pet_studio_widget.py`
- `project-room-widget/pet_studio_event_adapter.py`
- `project-room-widget/set_pet_studio_state.py`
- `project-room-widget/set_active_pet_studio.py`
- `tools/install_pet_studio_skill.py`

## Release Checklist

- Keep local QA output under `tester/`; it is ignored by git.
- Keep local generated experiments under ignored run folders unless they are explicitly promoted as public examples.
- Do not commit local runtime state files:
  - `project-room-widget/project-room-active.json`
  - `project-room-widget/project-room-layouts.json`
  - `project-room-widget/project-room-state.json`
  - `project-room-widget/project-room-window.json`
- Before pushing, run:

```powershell
python -m unittest discover -s project-room-widget\tests
python -m unittest discover -s project-room-kit\tests
python -m py_compile project-room-widget\pet_studio_widget.py project-room-widget\pet_studio_event_adapter.py project-room-widget\set_pet_studio_state.py project-room-widget\set_active_pet_studio.py project-room-widget\codex_pet_hook.py tools\install_pet_studio_skill.py tools\install_pet_studio_codex_integration.py
```

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
