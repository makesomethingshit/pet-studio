# Codex Pet Room Skill

Project Room Kit turns a Codex hatch-pet into a modular project room: a `384x240` side-view room, separate props, one main pet, optional helper pets, project assignments, and a frameless desktop widget runtime.

The repo includes:

- `project-room-kit/`: installable Codex skill plus kit creation/validation/rendering scripts
- `project-room-widget/`: local desktop widget runtime and project assignment registry
- `runs/`: preserved demo outputs and validation artifacts
- `docs/PROJECT_ROOM_ROADMAP.md`: milestone roadmap for project-specific pets and state integration

## Install As A Codex Skill

Clone the repository, then run the installer from the repo root:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-room-skill.git
cd codex-pet-room-skill
```

```powershell
python tools\install_project_room_skill.py
```

If you already have an installed copy:

```powershell
python tools\install_project_room_skill.py --force
```

The installer copies the clean skill payload to:

```text
%USERPROFILE%\.codex\skills\project-room-kit
```

You can also copy `project-room-kit/` manually into your Codex skills directory. The folder contains the required `SKILL.md`, bundled scripts, metadata, and template kit.

## Validate The Skill

If you have Codex's system skill validator available:

```powershell
python C:\Users\USER\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\USER\.codex\skills\project-room-kit
```

Expected output:

```text
Skill is valid!
```

## Create A Project Room Kit

```powershell
python project-room-kit\scripts\create_project_room_kit.py `
  --out-dir runs\my-project-room `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --theme "quiet archive nook" `
  --display-name "Archive Nook" `
  --render-preview `
  --render-contact `
  --bake-fallback `
  --register-project `
  --project-id archive-nook `
  --registry project-room-widget\project-room-projects.json
```

This creates a layered room kit, prompt pack, validation report, full-size previews, and optional hatch-pet fallback package.

## Run The Widget

Launch the included demo project:

```powershell
python project-room-widget\project_room_widget.py --project-id gakju-archive-demo --scale 1.25
```

List registered projects:

```powershell
python project-room-widget\project_room_widget.py --list-projects
```

Render one frame without opening a window:

```powershell
python project-room-widget\project_room_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

Update the active project state bridge:

```powershell
python project-room-widget\set_project_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

The widget maps `done` to `jumping`, `handoff` to `review`, and `blocked` to `failed`. Helper pets appear in review/handoff and blocked scenes when the kit includes a helper layer.

## Development Checks

```powershell
python -m unittest project-room-widget.tests.test_project_room_registry project-room-kit.tests.test_project_room_pipeline
python -m py_compile project-room-widget\set_project_state.py project-room-widget\project_room_widget.py project-room-widget\project_room_registry.py project-room-kit\scripts\create_project_room_kit.py
```
