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
- Credit-aware role model plan: Scout uses local/free routes, Coordinator uses value routes, Lead follows the active model
- Model profiles for switching between Codex, Hermes, OpenRouter, and local gateway routes from the Workroom or CLI
- Companion desktop pet widget with layered room, props, pets, speech bubbles, status bar, and toast messages
- Shared Tk design tokens for the Workroom in `pet-studio-widget/ui/design_system.py`
- Project registry, saved layout/window/session, workspace auto-detection, and project switching
- File-based state bridge using the existing `project-room-*` compatibility files
- Room creation, validation, preview sheets, QA packs, and preset export/import
- Roost project queues, event logs, L0-L3 security levels, team memory approval, and script/Hermes/gateway/Codex classifiers
- Optional Codex skill and hook bridge, plus Work Packet export/import for tasks, staff assignments, approved memory, model policy, role env, and relative credit estimate
- Korean CLI repair hints via `--lang ko` or `PET_STUDIO_LANG=ko`

Switch the active model profile:

```powershell
.\tools\pet_studio_model.cmd closed
.\tools\pet_studio_model.cmd open-sota
.\tools\pet_studio_model.cmd local
.\tools\pet_studio_model.cmd value
.\tools\pet_studio_model.cmd free
.\tools\pet_studio_model.cmd status
.\tools\pet_studio_model.cmd plan
.\tools\pet_studio_model.cmd team
.\tools\pet_studio_model.cmd env team
.\tools\pet_studio_model.cmd env coordinator
.\tools\pet_studio_model.cmd save-credits
.\tools\pet_studio_model.cmd all-local
.\tools\pet_studio_model.cmd all-value
.\tools\pet_studio_model.cmd lead-sota
.\tools\pet_studio_model.cmd --set-role-model coordinator local
.\tools\pet_studio_model.cmd coordinator local
.\tools\pet_studio_model.cmd reset-role lead
```

Model profiles are shown in this order: closed models such as GPT/Claude,
open-model SOTA, local model routes, value models, then free models. The
default local route uses the script fallback until a local model adapter is
configured. `plan` and `team` both show the role model plan. The team plan
keeps routine Scout and Coordinator work on cheaper routes; the active model is
the Lead route unless you explicitly override role profiles. Task `assignedRole`
values also steer dispatcher model selection, so moving a task to Coordinator
keeps that work on the Coordinator route. Team presets such as `save-credits`,
`all-local`, `all-value`, and `lead-sota` switch all roles at once.
`env team` prints the full team env plan, while `env scout|coordinator|lead`
prints PowerShell env lines for one role. The team env output is a plan: copy
one role section at a time because each role uses the same env variable names.
Those role env lines clear stale provider-specific model variables before
setting the selected route.
`reset-role` returns one role to the default policy. The Workroom's Endpoints tab
shows and edits this plan, including a relative Lead-only savings estimate based
on profile cost hints and copy buttons for selected-role env or the team env
plan.
Work Packet export also includes role-specific env overrides and provider env
cleanup hints for Scout, Coordinator, and Lead handoff. It is not provider
billing data.

Send team work into the Workroom:

```powershell
.\tools\pet_studio_work.cmd goal "Ship a usable workroom" --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd task "Review model workflow" --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd staff scout-1 "Scout One" --staff-role scout --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd assign-role 1 coordinator --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd assign-staff 1 scout-1 --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd start 1 --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd done 1 --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd status --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd clear --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd clear-mission --project-id gakju-archive-demo
.\tools\pet_studio_work.cmd memory add "Prefer cheap Scout routes" --scope team
.\tools\pet_studio_work.cmd memory list
```

`status` includes the current mission, tasks, staff, role model plan, role env,
team preset, and relative Lead-only savings estimate.

Still experimental:

- Team Room is a Workroom tab, not a fully reusable room with its own memory and avatar yet.
- Role dispatch is lightweight; full agent-to-agent delegation is not implemented.
- Hermes classification requires Hermes Agent; script mode is the fallback.
- Visual quality depends on source art and manual QA.
- Windows is the primary tested host.
- Some runtime files intentionally keep `project-room-*` names for compatibility.

Not included: cloud sync, hosted dashboard, macOS/Linux widget host, full game
simulation, trust-score auto-approval.

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
- `GatewayBackend`: optional OpenAI-compatible local gateway, defaulting to `http://127.0.0.1:8787/v1`
- `CodexBackend`: optional Codex CLI subprocess for locally authenticated Codex users

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
