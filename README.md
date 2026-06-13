# Pet Studio

[![Version](https://img.shields.io/badge/version-0.1.2-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Give a Codex pet its own desktop studio room.

![Gakju archive room widget example](docs/images/gakju-widget-bubble-example.png)

Pet Studio is a Codex skill and lightweight widget runtime for turning a hatch-pet into a layered desktop room. It keeps the room, props, main pet, helper pets, and speech bubbles editable instead of flattening them into one image.

Current release: `v0.1.2`

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

## 30-Second Demo

Run the preflight first. It checks Python/Pillow, the installed skill, the public demo registry, the sample kit, local-only ignore rules, and a one-frame render. It also reports whether Codex hook entries are installed:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py
```

Then launch the included Gakju archive room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

The normal widget launcher uses `pythonw`, so the command prompt does not stay attached. If the widget is already running, close it from the right-click menu or press `Escape`.

Useful demo checks:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --list-projects
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

The sample files under `runs/gakju-imagegen-room-v1/` are intended as public examples. Local QA reports, private test runs, preflight renders, and fresh project experiments stay ignored by git.

## Widget Controls

- Drag props or pets to reposition them.
- Drag the room background or empty space to move the widget window.
- Right-click for the context menu.
- Use `Larger`, `Smaller`, or `Reset size` from the context menu.
- Press `Ctrl` + `+`, `Ctrl` + `-`, or `Ctrl` + `0` for size controls.
- Press `Escape` to close.

Registered projects persist moved anchors and window scale locally.

## Codex Bubble Integration

Install the local Codex bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

The installer:

- installs the skill as `$pet-studio` under `%USERPROFILE%\.codex\skills\pet-studio`
- writes project-local `.codex\hooks.json` entries for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`
- writes an active project pin when `--project-id` is provided
- only wraps the user-level Codex `notify` command when `--install-notify` is provided

After installation, restart Codex or open `/hooks` to review and trust the new command hooks when Codex asks. Pet Studio cannot detect that trust approval directly, so the preflight prints a reminder when hooks are installed.

Hook bubble policy:

- `UserPromptSubmit` shows `Working: ...`
- `PreToolUse` shows `Using <tool>`
- `PostToolUse` stays in `Working`, not `Ready for review`
- `PreCompact` shows `Compacting context`
- `Stop` shows `Done` briefly, then the widget falls back to idle
- `blocked` and explicit review/handoff events are the only normal paths to review-style messaging

To inspect recent hook activity:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --skip-render --show-hook-log
```

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

## Create A Room With Codex

After installing the skill, talk to Codex normally. Useful prompts:

```text
Create a Pet Studio room for my current Codex pet.
```

```text
Use my Gakju pet as the style source and make a cozy archive room.
```

```text
Register this room to the current workspace and launch the widget.
```

Codex should ask for missing art inputs, keep the style source locked, run validation, and report generated files. Helper/sub-pet art should be confirmed before generation because mismatched helper style is hard to repair later.

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
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\project_room_registry.py pet-studio-kit\scripts\create_project_room_kit.py tools\pet_studio_preflight.py
```

Release preflight:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --show-hook-log
```

## Known Limitations

- Windows is the primary tested desktop widget host.
- Codex hook commands may need manual trust approval in `/hooks` before they run.
- The file bridge is local and project-scoped; it is not a network service.
- `project-room.json` and `project-room-*` runtime files remain as the v1 compatibility format even though user-facing commands use Pet Studio naming.
- The public demo is a checked-in sample. New generated rooms can vary in quality and should still be visually QA'd.

## Notes

- The real room format is layered. The fallback baked pet package is only for compatibility.
- Helper pets are optional, but when a kit includes one the widget keeps it visible across normal working, waiting, review, blocked, and done states.
- This repository provides a Codex event adapter, optional notify bridge, and lifecycle hook installer. Use `--install-notify` only if you intentionally want a user-level `notify` wrapper.
