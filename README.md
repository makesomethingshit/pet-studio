# Pet Studio

[Korean README](README.ko.md)

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/makesomethingshit/codex-pet-studio-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/makesomethingshit/codex-pet-studio-skill/actions/workflows/ci.yml)

**Pet Studio** is a local Windows desktop widget that shows project status as a
small pet room.

![Pet Studio project room reacting with a pet, props, helper creature, and speech bubble](docs/images/pet-studio-demo.gif)

## Quick Start

Install and launch:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\install.cmd
```

Use it with Codex:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

Optional live Codex hook bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id your-project-id
```

Create a room interactively:

```powershell
.\tools\pet_studio_python.cmd tools\create_room_interactive.py
```

## What Works

- Layered desktop room widget: room, props, main pet, helper pets, speech bubbles
- Project registry, saved layout/window/session, state file bridge
- Manual states: `running`, `waiting`, `review`, `blocked`, `failed`, `done`
- Workspace auto-detection and project switching
- Tray icon, status bar, context menu controls
- Codex skill install and optional hook integration
- Room creation, validation, preview sheets, and QA packs
- Room preset export/import through `alba.preset`
- Alba project queues, event logs, security levels, and script/Hermes classifiers
- Korean CLI repair hints via `--lang ko` or `PET_STUDIO_LANG=ko`

Still experimental:

- Visual quality depends on source art and manual QA.
- Windows is the primary tested widget host.
- Some runtime files still use `project-room-*` compatibility names.
- Hermes classification requires Hermes Agent; script mode is the fallback.

Not included: cloud sync, hosted dashboard, macOS/Linux widget host, full game
simulation, Team Room UI, Project Hub UI, trust-score auto-approval.

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

Then verify:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id my-room
.\tools\pet_studio_widget.cmd --project-id my-room --scale 1.25
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

Full workflow: [docs/CREATE_ROOM.md](docs/CREATE_ROOM.md)

## Presets

Widget menu: right-click the room, then use preset export/import.

Python API:

```python
from pathlib import Path
from alba.preset import export_preset, import_preset

export_preset(Path("runs/my-room"), Path("presets/my-room.zip"), "My Room")
import_preset(Path("presets/my-room.zip"), Path("runs/my-room-imported"))
```

## Alba

`alba` stores local project orchestration state in `team_state.json`.

```python
from alba.state import TeamState

state = TeamState()
state.register_project("my-project", "My Project")
state.enqueue_project("my-project", {"task": "lint"})
state.log_event("my-project", {"type": "build", "status": "pass"})
```

Backends:

- `ScriptBackend`: rule-based, no LLM
- `HermesBackend`: optional Hermes Agent subprocess

Security levels are per project: L0 allow, L1 warn, L2 ask, L3 deny.

## Demo State Cycler

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

Use `--dry-run` to inspect payloads without writing `project-room-state.json`.

## Docs

- [Install](docs/INSTALL.md)
- [Create a room](docs/CREATE_ROOM.md)
- [Codex integration](docs/CODEX_INTEGRATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Core / adapter boundary](docs/ADAPTER_BOUNDARY.md)
- [Roadmap](docs/PET_STUDIO_ROADMAP.md)
- [Orchestration plan](docs/PET_STUDIO_ORCHESTRATION_PLAN.md)
- [Long-term workroom vision](docs/PET_STUDIO_WORKROOM_VISION.md)
- [Development checks](docs/DEVELOPMENT.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

MIT. See [LICENSE](LICENSE).
