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

## Quick Start

Run the preflight:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py
```

Launch the included project room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Install the Codex skill:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

Install the optional Codex hook bridge for live bubbles:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

After installing hooks, restart Codex or open `/hooks` to review and trust the new commands when Codex asks.

## Honest Status

Pet Studio is an early open-source prototype with a working local demo, not a polished app store product.

What works today:

- A checked-in Windows desktop room widget for a registered sample project.
- Layered room rendering with background, props, main pet, optional helper pets, and speech bubbles.
- Local layout/scale persistence for registered projects.
- Manual project states such as `running`, `waiting`, `review`, `blocked`, `failed`, and `done`.
- Optional local Codex hooks that update bubbles on prompt/tool/compact/stop events.
- Script-driven room creation and validation from hatch-pet style sources plus room/prop assets.

Still experimental:

- New room quality depends on the provided or generated art. Visual QA is still required.
- First-room creation is script-driven, not a GUI editor.
- Codex integration is a local file/hook bridge, not an official Codex dashboard API.
- Windows is the primary tested host. macOS/Linux widget hosts are roadmap items.
- Some internal files still use older `project-room-*` names as the v1 compatibility format.

Not yet:

- No multi-room gallery UI.
- No marketplace or one-click installer.
- No cloud sync, remote service, or team dashboard.
- No full simulation/game layer with walking paths or autonomous room behavior.

## Why?

AI coding agents are usually shown through logs, spinners, terminal output, and abstract status labels. Those views are useful, but they do not make a project feel alive.

Pet Studio explores a softer interface: each project becomes a small room that reflects what the agent is doing. The room is still a local developer tool, but it gives status, context, and personality a place to live.

## Project Rooms

One room maps to one Codex project or repo.

Each room can have its own mood, props, main pet, helper pets, speech bubble style, saved layout, and current state. Switching projects can feel like moving between small workspaces instead of staring at another log stream.

The room acts as a compact visual project dashboard:

- the main pet shows the current state row
- helper pets can appear during review, handoff, or blocked states
- speech bubbles show local Codex hook messages
- props and pets stay as editable layers
- registered projects persist their room layout and widget scale locally

## Features

- Layered `384x240` Pet Studio room kits
- Project-bound room registry for local workspaces
- Editable pets, props, helper pets, anchors, layer order, and widget size
- Codex hook integration for `SessionStart`, prompt submit, tool use, compact, and stop events
- Live speech bubbles that follow project state
- Visual QA renders, preview sheets, and kit validation
- Local-first file bridge; no network service required
- Windows-focused frameless widget host
- Compatibility path for hatch-pet style sources and fallback pet packages

## Create A Room

For a direct command-line first room, use the guided wrapper:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py `
  --project-id my-room `
  --pet-package "$env:USERPROFILE\.codex\pets\my-pet" `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

Or install `$pet-studio` and ask Codex to create a room for the current workspace.

After generation, create a local QA pack:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

See [docs/CREATE_ROOM.md](docs/CREATE_ROOM.md) for the full workflow.

## Roadmap

Pet Studio's final vision is a small local dashboard where every Codex workspace has a recognizable room, state, mood, and companion behavior. The current repo is the first working slice of that idea.

Near-term:

- smoother first-room creation and QA pack generation
- clearer setup checks for hooks, Pillow, registries, and missing assets
- more room themes and prop packs
- more state-specific room animations
- helper pet behavior beyond simple state visibility
- richer Codex event mapping

Longer-term:

- multi-project room switcher
- macOS/Linux widget host
- shareable room presets
- project progress visualization
- a lightweight room editor for non-script users

See [docs/PET_STUDIO_ROADMAP.md](docs/PET_STUDIO_ROADMAP.md) for the detailed roadmap.

## Docs

- [Install](docs/INSTALL.md)
- [Create a room](docs/CREATE_ROOM.md)
- [Codex integration](docs/CODEX_INTEGRATION.md)
- [Development checks](docs/DEVELOPMENT.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [GitHub metadata](docs/GITHUB_METADATA.md)
- [Social preview](docs/SOCIAL_PREVIEW.md)
- [Contributing ideas](docs/CONTRIBUTING_IDEAS.md)

## Repository Layout

- `pet-studio-kit/` - installable `$pet-studio` skill and room creation scripts
- `pet-studio-widget/` - desktop scene-host runtime and project registry
- `tools/` - public wrappers, installers, and preflight checks
- `runs/` - checked-in demo outputs plus ignored local experiments
- `docs/` - roadmap, integration notes, demo scripts, and release packaging docs

## License

MIT. See [LICENSE](LICENSE).
