# Pet Studio

[![Version](https://img.shields.io/badge/version-0.1.1-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Give a Codex pet its own desktop studio room.

![Gakju archive room widget example](docs/images/gakju-widget-bubble-example.png)

Pet Studio is a Codex skill and lightweight widget runtime for turning a hatch-pet into a layered desktop room. It keeps the room, props, main pet, helper pets, and speech bubbles editable instead of flattening them into one image.

Current release: `v0.1.1`

## What It Does

- Builds a layered `384x240` Pet Studio room from a hatch-pet package.
- Keeps room, props, pets, and helper pets as separate editable layers.
- Validates room kits so mismatched assets are caught early.
- Renders preview and contact-sheet images for visual QA.
- Registers rooms to local project ids.
- Runs a frameless desktop widget that can show project state such as working, waiting, review, blocked, and done.
- Accepts Codex-style event payloads through a small local adapter.

## Requirements

- Windows is the primary tested widget host.
- Python 3.11+ with Pillow.
- Codex Desktop or a local Codex skill folder for `$pet-studio`.
- A hatch-pet package to use as the style source when creating new rooms.

## Install

Clone the repo and install the skill:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

To replace an older installed copy:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py --force
```

The installer copies the skill to:

```text
%USERPROFILE%\.codex\skills\pet-studio
```

The repository also keeps the older `project-room-*` file names as the v1 compatibility format. New public commands use Pet Studio names.

The Windows examples use repository wrappers instead of calling `python` directly. `tools\pet_studio_widget.cmd` launches the desktop widget through `pythonw` so the terminal does not stay attached. `tools\pet_studio_python.cmd` is the console/debug wrapper used for commands that print output, render files, or run tests.

## Use It With Codex

After installing, talk to Codex normally. Useful prompts:

```text
Create a Pet Studio room for my current Codex pet.
```

```text
Use my Gakju pet as the style source and make a cozy archive room.
```

```text
Register this room to the current workspace and launch the widget.
```

```text
Set the Pet Studio state to blocked with the message "waiting on approval".
```

Codex should guide the workflow, ask for missing art inputs, run validation, and report the generated files.

## Example Room

This repository includes a public Gakju archive room sample built from separated room, prop, main pet, helper pet, and runtime speech-bubble layers.

You can render or inspect the checked-in sample without generating new art:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --kit runs\gakju-imagegen-room-v1\kit --render-once runs\gakju-imagegen-room-v1\widget-render-test.png
```

The sample files under `runs/gakju-imagegen-room-v1/` are intended as public examples. Local QA reports, private test runs, and fresh project experiments stay ignored by git.

## Try The Demo

List registered room projects:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --list-projects
```

Launch the included demo room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Render one frame without opening the widget:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
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
.\tools\pet_studio_python.cmd pet-studio-widget\set_pet_studio_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

Publish a Codex-style event:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event start --message "working"
```

Or send a structured JSON payload, which is the command target used by the lifecycle hook bridge:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | .\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --event-json -
```

When no project id is provided, the adapter resolves project identity in this order:

1. Explicit `projectId`
2. Active project pin
3. Workspace path matching

Pin an active project when several rooms share one workspace:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

State messages appear as runtime speech bubbles. Long messages are whitespace-normalized and capped at 80 characters so hook output stays compact.

For local Codex bubble integration, install the Pet Studio Codex bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py
```

The installer:

- installs the skill as `$pet-studio` under `%USERPROFILE%\.codex\skills\pet-studio`
- writes project-local `.codex\hooks.json` entries for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`
- can write an active project pin when `--project-id` is provided
- only wraps the user-level Codex `notify` command when `--install-notify` is provided

After installation, restart Codex or open `/hooks` to review and trust the new non-managed command hooks when Codex asks.

## What Gets Created

Typical generated output includes:

```text
runs/my-pet-studio-room/
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

- `pet-studio-kit/` - source folder for the installable `$pet-studio` skill and kit creation scripts.
- `pet-studio-widget/` - desktop scene-host runtime and project registry.
- `runs/` - checked-in demo outputs plus ignored local experiments.
- `docs/PET_STUDIO_ROADMAP.md` - roadmap and data model notes.
- `tools/install_pet_studio_skill.py` - local installer.
- `CHANGELOG.md` - release notes.
- `VERSION` - current release version.

## Validate

If Codex's system skill validator is installed:

```powershell
.\tools\pet_studio_python.cmd "%USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "%USERPROFILE%\.codex\skills\pet-studio"
```

Expected result:

```text
Skill is valid!
```

Development checks:

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\project_room_registry.py pet-studio-kit\scripts\create_project_room_kit.py
```

## Notes

- The real room format is layered. The fallback baked pet package is only for compatibility.
- Helper pets are optional, but when a kit includes one the widget keeps it visible across normal working, waiting, review, blocked, and done states.
- `project-room.json` and `project-room-*` runtime files remain supported as the v1 compatibility format while the user-facing skill and commands use Pet Studio naming.
- This repository provides a Codex event adapter, optional notify bridge, and lifecycle hook installer. `tools\install_pet_studio_codex_integration.py` installs project-local hooks into `.codex\hooks.json`; Codex may still require reviewing/trusting those hooks before they run. Use `--install-notify` only if you intentionally want a user-level `notify` wrapper.
