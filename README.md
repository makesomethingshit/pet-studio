# Pet Studio

[&#54620;&#44397;&#50612; README](README.ko.md)

[![Version](https://img.shields.io/badge/version-0.4.1-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/makesomethingshit/codex-pet-studio-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/makesomethingshit/codex-pet-studio-skill/actions/workflows/ci.yml)

**Pet Studio** — A desktop widget that shows your project status as a tiny pet room.

- **Use as an app** → `install.cmd` once and you're ready
- **Use with an AI agent** → install the skill once and the agent auto-launches your room

![Pet Studio project room reacting with a pet, props, helper creature, and speech bubble](docs/images/pet-studio-demo.gif)

Pet Studio turns your projects into layered desktop rooms with pets, props, helper pets, and live speech bubbles. It is a local-first agent dashboard disguised as a tiny pet room.

Instead of watching logs, watch your project room react as you work — running, waiting, review, blocked, failed, or done.

The README GIF follows the 10-15 second demo flow in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Quick Start

**How do you use AI tools?**

### Option A: As an app (install.cmd)

Clone and install — one command to get started:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\install.cmd
```

Installs dependencies, runs preflight, and launches the widget. Use the tray icon to switch rooms, change state, or quit.

### Option B: With an AI agent (Codex skill)

Install the skill once and your agent auto-launches the room:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

When you open a project in Codex/Cursor, the widget launches automatically and reacts to your task state.

Optional — live speech bubble bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id your-project-id
```

### Create a room yourself (optional)

If no room kit exists yet, create one interactively:

```powershell
.\tools\pet_studio_python.cmd tools\create_room_interactive.py
```

Answer prompts to create a new project room. No need to remember CLI flags.

## What Works Today

* Windows desktop widget for checked-in sample project rooms
* Layered room rendering: background, props, main pet, optional helper pets, speech bubbles
* Local project registry, saved layout, saved scale, and state file bridge
* Manual project states: `running`, `waiting`, `review`, `blocked`, `failed`, `done`
* **Codex skill** — install once, widget auto-launches when Codex opens a project with a room kit
* Optional Codex hooks for live bubble updates from prompt/tool/compact/stop events
* Script-driven room creation, asset guardrails, validation, preview sheets, and local QA packs
* Auto-project-detection: widget infers project from current workspace directory
* Korean CLI output (`--lang ko` / `PET_STUDIO_LANG=ko`)

## Still Experimental

* New room quality depends on the provided or generated art; visual QA is required.
* First-room creation is script-driven, not a GUI editor.
* Codex skill integration is optional — widget works standalone without Codex.
* Windows is the primary tested host.
* Internal storage still uses some `project-room-*` v1 compatibility names.

Not included today: multi-room gallery, cloud sync, team dashboard, macOS/Linux widget host, full simulation/game behavior, room preset export/import, helper pet AI.

## Model

One room maps to one Codex project or repo.

Each room can have its own mood, props, main pet, helper pets, speech bubble style, saved layout, and current state. The room is not only decoration; it is a compact visual project dashboard.

## Create A Room

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py `
  --project-id my-room `
  --pet-package "$env:USERPROFILE\.codex\pets\my-pet" `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

Then generate local QA evidence:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id my-room
.\tools\pet_studio_widget.cmd --project-id my-room --scale 1.25
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

Full workflow: [docs/CREATE_ROOM.md](docs/CREATE_ROOM.md)

The create command checks common asset mistakes before writing a kit: room sources must be `384x240`, props must be visible and fit inside the room canvas, helper packages must contain a valid hatch-pet atlas, and prop placement ids must match supplied props. Subjective style questions remain visual QA instead of automatic rejection.

## Korean CLI Output

Default CLI output is English. For Korean failure/recovery messages, use `--lang ko` or `PET_STUDIO_LANG=ko`:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --lang ko
```

JSON keys, error codes, command flags, paths, and IDs are not translated. Machine-readable output stays English.

## Demo State Cycler

For README GIF capture or manual QA, use the demo state cycler:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

Use `--dry-run` to inspect state bridge payloads without writing `project-room-state.json`.

## Roadmap

The long-term vision is a local visual workroom for your projects. The current project stays intentionally smaller: one workspace, one tiny desktop room, and enough state to understand what's happening without staring at logs.

Near-term follow-ups after `v0.4.0`:

* add more sample room themes and props
* decompose `project_room_widget.py` into smaller modules (state/session/render/bubble/window)

Completed in `v0.4.0`:

* workspace auto-switch: widget reacts to project changes without manual `--project-id`
* system tray icon: room list, state control, quit from tray
* YAGNI cleanup: removed unimplemented export/import, animation, helper pet AI

Completed in `v0.3.1`:

* repo hygiene: moved debug artifacts to `archive/`, cleaned up `runs/` and `docs/qa/`
* documentation sync: README.md / README.ko.md section parity
* one-click installer (`install.cmd`)
* interactive room creator (`tools/create_room_interactive.py`)
* auto-project-detection in widget `main()`
* QA Gate pipeline: `scripts/run-qa.py` + `Makefile` + CI lint

Completed in `v0.3.0`:

* boundary work: split shared registry/state logic into Pet Studio Core

Larger ideas remain roadmap, not current features:

* shareable room presets / export-import
* state transition animations
* helper pet AI behavior
* multi-project room gallery
* lightweight room editor
* macOS/Linux widget hosts
* broader workroom concepts such as Team Rooms, Project Hubs, and task cards

Detailed roadmap: [docs/PET_STUDIO_ROADMAP.md](docs/PET_STUDIO_ROADMAP.md)

## Docs

* [Install](docs/INSTALL.md)
* [Create a room](docs/CREATE_ROOM.md)
* [Codex integration](docs/CODEX_INTEGRATION.md)
* [Architecture](docs/ARCHITECTURE.md)
* [Core / adapter boundary](docs/ADAPTER_BOUNDARY.md)
* [Development checks](docs/DEVELOPMENT.md)
* [Long-term workroom vision](docs/PET_STUDIO_WORKROOM_VISION.md)
* [Demo script](docs/DEMO_SCRIPT.md)
* [GitHub About metadata](docs/ABOUT.md)
* [Social preview](docs/SOCIAL_PREVIEW.md)
* [Contributing ideas](docs/CONTRIBUTING_IDEAS.md)
* [Contributing](CONTRIBUTING.md)
* [Security](SECURITY.md)

## License

MIT. See [LICENSE](LICENSE).
