# Pet Studio Architecture

Pet Studio is a local-first visual AI workroom: a desktop widget that shows AI team state at a glance, plus an orchestration layer that manages projects, tasks, and security.

## Layers

### pet_studio_core

Shared, host-neutral primitives:

- Project registry parsing and selection
- Workspace-to-project inference
- Widget state normalization
- File-based state bridge payload writing

**Boundary**: Core must not import Codex hook code, Tkinter widget code, launcher scripts, image generation providers, or Workroom orchestration.

### pet-studio-widget

Desktop widget host:

- Tkinter window lifecycle
- Canvas rendering (room, pet, props, speech bubble)
- Saved layout, window, and session files
- Context menu and bubble presentation
- Workroom window with Projects, Tasks, Team Room, and Endpoints tabs
- Shared Tk design tokens in `ui/design_system.py`
- Toast notifications
- Status bar

### roost - Team Orchestration

`roost/` is the orchestration layer:

- `state.py` - TeamState: projects, queues, employees, approvals, event logs
- `team_memory.py` - approved team memory and project culture context
- `model_profile.py` - model tiers, env overrides, cleanup hints, and relative credit estimates
- `packet.py` - Work Packet export/import, with legacy marker compatibility
- `preset.py` - Room preset export/import (zip-based)
- `security.py` - L0-L3 security levels per project
- `auth_config.py` - local auth/env config loading
- `backend/script.py` - Rule-based event classification (no LLM)
- `backend/hermes.py` - Hermes subprocess adapter (optional LLM)
- `backend/gateway.py` - OpenAI-compatible local gateway adapter
- `backend/codex.py` - Codex CLI subprocess adapter

**Boundary**: roost works without any LLM. Hermes, gateway, and Codex backends are optional adapters.

### Codex Adapter

Codex-specific event translation:

- Codex hook payload fields
- Hook event to Pet Studio state mapping
- Hook install and trust guidance

**Boundary**: Codex is an adapter, not the core. Core must be usable by another adapter without importing Codex-specific files.

### pet-studio-kit

Asset pipeline:

- Room creation scripts
- Asset validation and guardrails
- Preview and QA sheet generation

### tools/

User-facing CLI commands:

- `pet_studio_preflight.py` - preflight checks
- `pet_studio_model.cmd` - model profile and team preset shortcuts
- `pet_studio_work.cmd` - mission, task, staff, and status shortcuts
- `pet_studio_memory.py` - team memory candidate approval CLI
- `pet_studio_create_room.py` - scripted room creation
- `create_room_interactive.py` - interactive room creation
- `install_pet_studio_codex_integration.py` - install Codex hooks
- `install_pet_studio_skill.py` - install Pet Studio skill

**Boundary**: `tools/` scripts are thin wrappers. Shared behavior belongs in `pet_studio_core/` or `roost/`.

## Data Flow

```
User Mission (text)
    -> Workroom / Project Hub
        -> Task Cards (waiting/running/done)
            -> Team Room roles
                -> Scout (read-only, cheap/local)
                -> Coordinator (compress, draft, value route)
                -> Lead (final, user-selected active model)
                    -> Work Packet Export / Import
                        -> role env overrides + provider cleanup hints
```

## Compatibility

v1 storage names stay unchanged:

- `project-room.json`
- `project-room-projects.json`
- `project-room-state.json`
- `project-room-active.json`
- `project-room-layouts.json`
- `project-room-window.json`
- `project-room-workroom.json`
- `project-room-session.json`
- `team_state.json` (roost)
- `work-packets/` and `codex-packets/` stay local-only export folders
