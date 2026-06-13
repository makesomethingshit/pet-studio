# Codex Pet Studio

Give a Codex pet its own project room.

This skill helps Codex turn a hatch-pet into a small desktop room with a background, props, a main pet, optional helper pets, project state, and a lightweight widget runtime. It is meant to be used through Codex: ask Codex to make or run a room, and Codex uses the scripts in this repository for you.

## What It Does

- Builds a layered `384x240` project room from a hatch-pet package.
- Keeps room, props, pets, and helper pets as separate editable layers.
- Validates room kits so mismatched assets are caught early.
- Renders preview and contact-sheet images for visual QA.
- Registers rooms to local project ids.
- Runs a frameless desktop widget that can show project state such as working, waiting, review, blocked, and done.
- Accepts Codex-style event payloads through a small local adapter.

## Install

Clone the repo and install the skill:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
python tools\install_project_room_skill.py
```

To replace an older installed copy:

```powershell
python tools\install_project_room_skill.py --force
```

The installer copies the skill to:

```text
%USERPROFILE%\.codex\skills\pet-studio
```

## Use It With Codex

After installing, talk to Codex normally. Useful prompts:

```text
Create a project room for my current Codex pet.
```

```text
Use my Gakju pet as the style source and make a cozy archive room.
```

```text
Register this room to the current workspace and launch the widget.
```

```text
Set the project room state to blocked with the message "waiting on approval".
```

Codex should guide the workflow, ask for missing art inputs, run validation, and report the generated files.

## Example Room

This repository includes a public Gakju archive room sample built from separated room, prop, main pet, helper pet, and runtime speech-bubble layers.

![Gakju archive room widget example](docs/images/gakju-widget-bubble-example.png)

You can render or inspect the checked-in sample without generating new art:

```powershell
python project-room-widget\project_room_widget.py --kit runs\gakju-imagegen-room-v1\kit --render-once runs\gakju-imagegen-room-v1\widget-render-test.png
```

The sample files under `runs/gakju-imagegen-room-v1/` are intended as public examples. Local QA reports, private test runs, and fresh project experiments stay ignored by git.

## Try The Demo

List registered room projects:

```powershell
python project-room-widget\project_room_widget.py --list-projects
```

Launch the included demo room:

```powershell
python project-room-widget\project_room_widget.py --project-id gakju-archive-demo --scale 1.25
```

Render one frame without opening the widget:

```powershell
python project-room-widget\project_room_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

## Widget Controls

- Drag props or pets to reposition them.
- Drag the room background or empty space to move the widget window.
- Right-click for the context menu.
- Use `Larger`, `Smaller`, or `Reset size` from the context menu.
- Press `Ctrl` + `+`, `Ctrl` + `-`, or `Ctrl` + `0` for size controls.
- Press `Escape` to close.

Registered projects persist moved anchors and window scale locally.

## Project State

Update the active project state directly:

```powershell
python project-room-widget\set_project_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

Publish a Codex-style event:

```powershell
python project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event start --message "working"
```

Or send a structured JSON payload, which is the command target intended for future Codex host hooks:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | python project-room-widget\codex_state_adapter.py --event-json -
```

When no project id is provided, the adapter resolves project identity in this order:

1. Explicit `projectId`
2. Active project pin
3. Workspace path matching

Pin an active project when several rooms share one workspace:

```powershell
python project-room-widget\set_active_project.py --project-id gakju-archive-demo --cwd .
```

State messages appear as runtime speech bubbles. Long messages are whitespace-normalized and capped at 80 characters so hook output stays compact.

For local Codex bubble integration, install the Pet Studio notify bridge:

```powershell
python tools\install_pet_studio_codex_integration.py
```

The installer:

- installs the skill as `$pet-studio` under `%USERPROFILE%\.codex\skills\pet-studio`
- backs up `%USERPROFILE%\.codex\config.toml`
- wraps the existing Codex `notify` command so Pet Studio updates `project-room-state.json` when turns end
- writes `project-room-active.json` for the current project room

For fuller lifecycle integration, this repo also ships `.codex-plugin/plugin.json` and `hooks/hooks.codex.json`. Those hooks call `project-room-widget\codex_pet_hook.py` for session start, prompt submit, tool use, compaction, and stop events.

## What Gets Created

Typical generated output includes:

```text
runs/my-project-room/
  kit/
    project-room.json
    style-lock.json
    rooms/
    props/
    pets/
  generation-brief.json
  kit-validation.json
  production-report.json
  room-preview.png
  room-contact.png
```

Local QA evidence and experimental run folders are intentionally ignored by git unless you choose to preserve them.

## Repository Layout

- `project-room-kit/` - source folder for the installable `$pet-studio` skill and kit creation scripts.
- `project-room-widget/` - desktop scene-host runtime and project registry.
- `runs/` - checked-in demo outputs plus ignored local experiments.
- `docs/PROJECT_ROOM_ROADMAP.md` - roadmap and data model notes.
- `tools/install_project_room_skill.py` - local installer.

## Validate

If Codex's system skill validator is installed:

```powershell
python C:\Users\USER\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\USER\.codex\skills\pet-studio
```

Expected result:

```text
Skill is valid!
```

Development checks:

```powershell
python -m unittest project-room-widget.tests.test_project_room_registry project-room-kit.tests.test_project_room_pipeline
python -m py_compile project-room-widget\codex_state_adapter.py project-room-widget\set_project_state.py project-room-widget\set_active_project.py project-room-widget\project_room_widget.py project-room-widget\project_room_registry.py project-room-kit\scripts\create_project_room_kit.py
```

## Notes

- The real room format is layered. The fallback baked pet package is only for compatibility.
- Helper pets are optional, but make review, handoff, and blocked scenes more expressive.
- This repository provides a Codex event adapter, notify bridge, and optional hook manifest. `tools\install_pet_studio_codex_integration.py` installs the local notify bridge; host lifecycle hooks still depend on the Codex plugin/hook surface accepting the bundled `.codex-plugin/plugin.json`.
