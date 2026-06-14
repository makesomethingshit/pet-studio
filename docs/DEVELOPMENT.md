# Development

Use these checks before publishing or cutting a release.

## Skill Validation

If Codex's system skill validator is installed:

```powershell
.\tools\pet_studio_python.cmd "%USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "%USERPROFILE%\.codex\skills\pet-studio"
```

Expected result:

```text
Skill is valid!
```

## Development Checks

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\project_room_registry.py pet-studio-kit\scripts\create_project_room_kit.py tools\pet_studio_preflight.py tools\pet_studio_create_room.py
```

## Release Preflight

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --show-hook-log
```

## Known Limitations

- Windows is the primary tested desktop widget host.
- Codex hook commands may need manual trust approval in `/hooks` before they run.
- The file bridge is local and project-scoped; it is not a network service.
- `project-room.json` and `project-room-*` runtime files remain as the v1 compatibility format even though user-facing commands use Pet Studio naming.
- The public demo is a checked-in sample. New generated rooms can vary in quality and should still be visually QA'd.
