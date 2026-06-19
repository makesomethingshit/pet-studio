# Pet Studio

[Korean README](README.ko.md)

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/makesomethingshit/pet-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/makesomethingshit/pet-studio/actions/workflows/ci.yml)

**Pet Studio** is a local-first Windows workroom for AI-assisted project work,
with an optional tiny pet widget for at-a-glance status.

![Pet Studio project room reacting with a pet, props, helper creature, and speech bubble](docs/images/pet-studio-demo.gif)

## Quick Start

Install:

```powershell
git clone https://github.com/makesomethingshit/pet-studio.git
cd pet-studio
.\install.cmd
```

Open the Workroom app:

```powershell
.\tools\pet_studio_workroom.cmd --project-id gakju-archive-demo
```

Open the companion pet widget:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Create a room interactively:

```powershell
.\tools\pet_studio_python.cmd tools\create_room_interactive.py
```

Optional Codex adapter:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id your-project-id
```

## What Works

- Workroom app window with Projects, Tasks, Team Room, and Endpoints tabs
- Mission input and Task Cards split into waiting, running, and done columns
- Team Room tab for approvals, staff status, and Roost queue
- Endpoint registry with role mappings for Scout, Coordinator, and Lead
- Companion desktop pet widget with layered room, props, pets, speech bubbles, status bar, and toast messages
- Project registry, saved layout/window/session, workspace auto-detection, and project switching
- File-based state bridge using the existing `project-room-*` compatibility files
- Room creation, validation, preview sheets, QA packs, and preset export/import
- Roost project queues, event logs, L0-L3 security levels, and script/Hermes classifiers
- Optional Codex skill, hook bridge, and packet export/import path
- Korean CLI repair hints via `--lang ko` or `PET_STUDIO_LANG=ko`

Still experimental:

- Team Room is a Workroom tab, not a fully reusable room with its own memory and avatar yet.
- Role dispatch is lightweight; full agent-to-agent delegation is not implemented.
- Hermes classification requires Hermes Agent; script mode is the fallback.
- Visual quality depends on source art and manual QA.
- Windows is the primary tested host.
- Some runtime files intentionally keep `project-room-*` names for compatibility.

Not included: cloud sync, hosted dashboard, macOS/Linux widget host, full game
simulation, model backend management, trust-score auto-approval.

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
.\tools\pet_studio_workroom.cmd --project-id my-room
.\tools\pet_studio_widget.cmd --project-id my-room --scale 1.25
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

Full workflow: [docs/CREATE_ROOM.md](docs/CREATE_ROOM.md)

## Presets

Widget menu: right-click the room, then use preset export/import.

Python API:

```python
from pathlib import Path
from roost.preset import export_preset, import_preset

export_preset(Path("runs/my-room"), Path("presets/my-room.zip"), "My Room")
import_preset(Path("presets/my-room.zip"), Path("runs/my-room-imported"))
```

## Roost

`roost` stores local project orchestration state in `team_state.json`.

```python
from roost.state import TeamState

state = TeamState()
state.register_project("my-project", "My Project")
state.enqueue_project("my-project", {"task": "lint"})
state.log_event("my-project", {"type": "build", "status": "pass"})
```

Backends:

- `ScriptBackend`: rule-based, no LLM
- `HermesBackend`: optional Hermes Agent subprocess

Security levels are per project: L0 allow, L1 warn, L2 ask, L3 deny.

### Team Room

Open the Workroom and select the **Team Room** tab. It shows pending approvals,
staff status, and the Roost queue.

```python
from roost.state import TeamState

state = TeamState()
state.register_project("my-project", "My Project", security_level=2)
approval_id = state.add_approval_request("my-project", "deploy")
state.resolve_approval(approval_id, approved=True)
```

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
