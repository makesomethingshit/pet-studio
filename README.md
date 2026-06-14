# Pet Studio

[![Version](https://img.shields.io/badge/version-0.1.2-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Every Codex project gets its own tiny desktop room.**

![Gakju archive room widget example](docs/images/gakju-widget-bubble-example.png)

Pet Studio turns local Codex workspaces into layered desktop rooms with pets, props, helper pets, and live speech bubbles.

Instead of watching logs, you can watch your project room react as Codex starts working, uses tools, gets blocked, enters review, or finishes.

It is a local-first agent dashboard disguised as a tiny pet room.

- Current release: `v0.1.2`
- Primary host: Windows desktop widget
- Status: experimental, local-first, usable from a fresh clone with the included demo

## Honest Status

Pet Studio is an early open-source prototype with a working local demo, not a polished app store product.

What works today:

- Launch a checked-in Windows desktop room widget for a registered sample project.
- Render a layered room with background, props, main pet, optional helper pets, and speech bubbles.
- Move props/pets, resize the widget, and persist registered project layout/scale locally.
- Send manual project states such as `running`, `waiting`, `review`, `blocked`, `failed`, and `done`.
- Install local Codex hooks that update the room bubble on prompt/tool/compact/stop events after hook trust approval.
- Create and validate project-room kits from a hatch-pet style source plus room/prop assets.

Still experimental:

- New room quality depends on the provided or generated art. Visual QA is still required.
- The first-room creation flow is script-driven, not a GUI editor.
- Codex integration is a local file/hook bridge, not an official Codex dashboard API.
- Windows is the primary tested host. macOS/Linux widget hosts are roadmap items.
- Some internal files still use the older `project-room-*` naming as the v1 compatibility format.

Not yet:

- No multi-room gallery UI.
- No marketplace or one-click installer.
- No cloud sync, remote service, or team dashboard.
- No full simulation/game layer with walking paths or autonomous room behavior.

## Quick Start

Clone the repo and run the public preflight:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py
```

Launch the included project room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Install the Codex skill locally:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

Install the optional Codex hook bridge for live bubbles:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

After installing hooks, restart Codex or open `/hooks` to review and trust the new commands when Codex asks.

No GIF yet? Use the checked-in screenshot above, then see [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the 10-15 second demo shot this repo is designed around.

## Why?

AI coding agents are usually shown through logs, spinners, terminal output, and abstract status labels. Those views are useful, but they do not make a project feel alive.

Pet Studio explores a softer interface: each project becomes a small room that reflects what the agent is doing. The room is still a local developer tool, but it gives status, context, and personality a place to live.

## Project Rooms

One room maps to one Codex project or repo.

Each room can have its own mood, props, main pet, helper pets, speech bubble style, saved layout, and current state. Switching projects can feel like moving between small workspaces instead of staring at another log stream.

The room is not only decoration. It acts as a compact visual project dashboard:

- the main pet shows the current state row
- helper pets can appear during review, handoff, or blocked states
- speech bubbles show local Codex hook messages
- props and pets stay as editable layers
- registered projects persist their room layout and widget scale locally

## Features

- Builds a layered `384x240` Pet Studio room from a hatch-pet package.
- Keeps room, props, pets, and helper pets as separate editable layers.
- Project-bound room registry for local workspaces.
- Editable pets, props, helper pets, anchors, layer order, and widget size.
- Codex hook integration for `SessionStart`, prompt submit, tool use, compact, and stop events.
- Live speech bubbles that follow the project state.
- Visual QA renders, preview sheets, and kit validation.
- Local-first file bridge; no network service required.
- Windows-focused frameless widget host.
- Compatibility path for hatch-pet style sources and fallback pet packages.

## Roadmap

Pet Studio's final vision is a small local dashboard where every Codex workspace has a recognizable room, state, mood, and companion behavior. The current repo is the first working slice of that idea.

Near-term roadmap:

- smoother first-room creation and QA pack generation
- clearer setup checks for hooks, Pillow, registries, and missing assets
- more room themes and prop packs
- more state-specific room animations
- helper pet behavior beyond simple state visibility
- richer Codex event mapping

Longer-term roadmap:

- multi-project room switcher
- macOS/Linux widget host
- shareable room presets
- project progress visualization
- a lightweight room editor for non-script users

See [docs/PET_STUDIO_ROADMAP.md](docs/PET_STUDIO_ROADMAP.md) for the detailed implementation roadmap and current state.

## Requirements

- Windows is the primary tested widget host.
- Python 3.11+ with Pillow.
- Codex Desktop or a local Codex skill folder for `$pet-studio`.
- A hatch-pet package to use as the style source when creating new rooms.

## Full Install

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

## 30-Second Local Demo

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

## Create Your First Room

For a direct command-line first room, use the guided wrapper. It keeps the low-level kit creation defaults aligned with the public demo flow:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py `
  --project-id my-room `
  --pet-package "$env:USERPROFILE\.codex\pets\my-pet" `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

The wrapper validates the pet and room inputs, creates `runs\my-room\kit`, renders preview/contact images, registers the project, links the current workspace, and prints preflight/launch/render commands.

Useful options:

- `--dry-run` prints the planned low-level command without writing files.
- `--force` replaces an existing output directory. Use this only when the old `runs\<project-id>` output can be discarded.
- `--verbose` prints the underlying generator output; the default output is a concise JSON summary with created artifacts and next commands.

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
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\project_room_registry.py pet-studio-kit\scripts\create_project_room_kit.py tools\pet_studio_preflight.py tools\pet_studio_create_room.py
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
- Helper pets are optional. Kits can show them in collaboration/problem-solving states such as review, handoff, blocked, or failed without turning them into a second main pet.
- This repository provides a Codex event adapter, optional notify bridge, and lifecycle hook installer. Use `--install-notify` only if you intentionally want a user-level `notify` wrapper.
