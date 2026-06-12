# Codex Pet Room Skill

Project Room Kit turns a Codex hatch-pet into a modular project room: a `384x240` side-view scene host with separate room, prop, main pet, and optional helper pet entities, project assignments, and a frameless desktop runtime.

The repo includes:

- `project-room-kit/`: installable Codex skill plus kit creation/validation/rendering scripts
- `project-room-widget/`: local desktop scene-host runtime and project assignment registry
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

When used as a Codex skill, Codex should guide this flow and run the scripts directly. The commands below are for manual debugging or for users who want to run the pipeline themselves.

```powershell
python project-room-kit\scripts\create_project_room_kit.py `
  --out-dir runs\my-project-room `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook" `
  --display-name "Archive Nook" `
  --render-preview `
  --render-contact `
  --bake-fallback `
  --register-project `
  --project-id archive-nook `
  --registry project-room-widget\project-room-projects.json `
  --workspace-path .
```

This creates a layered room kit, prompt pack, validation report, full-size previews, and optional hatch-pet fallback package.

Room intake preserves the `384x240` source size but clears edge-connected near-white margin pixels to transparency. This removes visible white top/bottom fringe without deleting bright wall or furniture pixels that are separated from the image edge.

Prop placement is explicit. Use `behind-pet` for furniture the pet should stand in front of, `front-of-pet` for props that can overlap the pet, `background` for wall/floor decorations, and `foreground` for near-camera accents.

## Run The Widget

Codex can launch the scene host, render compatibility previews, or update project state for the user. These examples show the underlying commands.

The live runtime uses separate Canvas entities for room, props, main pet, and helper pets. Props and pets are draggable. Room/background layers are locked by default. Registered projects persist moved entity anchors in `project-room-widget\project-room-layouts.json`; direct `--kit` runs are session-only.

Pet UX parity v1 keeps the basics visible in the scene host: state messages render as a runtime-only speech bubble near the pet, right-click opens a context menu instead of closing immediately, and registered projects persist window position/scale in `project-room-widget\project-room-window.json`. Escape still closes the host. Full Codex pet runtime parity is tracked incrementally because the internal runtime implementation is not bundled in this repo.

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

Publish a Codex-style task event through the adapter:

```powershell
python project-room-widget\codex_state_adapter.py --event start --message "working"
python project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event start --message "implementing adapter"
python project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event review --message "ready for review"
python project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event block --message "needs input"
python project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event done --message "finished"
```

When `--project-id` is omitted, the adapter resolves project identity in this order: explicit project id, active project pin, then registry `workspacePaths`. Pin a project when several rooms share one workspace:

```powershell
python project-room-widget\set_active_project.py --project-id gakju-archive-demo --cwd .
```

Codex host hooks can publish structured JSON to the same local command target. This repo provides the adapter contract, but does not install host hooks automatically:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | python project-room-widget\codex_state_adapter.py --event-json -
```

## Development Checks

```powershell
python -m unittest project-room-widget.tests.test_project_room_registry project-room-kit.tests.test_project_room_pipeline
python -m py_compile project-room-widget\codex_state_adapter.py project-room-widget\set_project_state.py project-room-widget\set_active_project.py project-room-widget\project_room_widget.py project-room-widget\project_room_registry.py project-room-kit\scripts\create_project_room_kit.py
```
