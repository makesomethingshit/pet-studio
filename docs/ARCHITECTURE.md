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
- Team Room slide-in panel (v0.6)
- Toast notifications (v0.6)
- Status bar (v0.6)

### roost — Team Orchestration

`roost/` is the orchestration layer:

- `state.py` — TeamState: projects, queues, employees, approvals, event logs
- `preset.py` — Room preset export/import (zip-based)
- `security.py` — L0-L3 security levels per project
- `backend/script.py` — Rule-based event classification (no LLM)
- `backend/hermes.py` — Hermes subprocess adapter (optional LLM)

**Boundary**: roost works without any LLM. Hermes backend is optional.

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

- `pet_studio_preflight.py` — preflight checks
- `pet_studio_create_room.py` — scripted room creation
- `create_room_interactive.py` — interactive room creation
- `install_pet_studio_codex_integration.py` — install Codex hooks
- `install_pet_studio_skill.py` — install Pet Studio skill

**Boundary**: `tools/` scripts are thin wrappers. Shared behavior belongs in `pet_studio_core/` or `roost/`.

## Data Flow

```
User Mission (text)
    → Project Hub (v1.0.0)
        → Task Cards (waiting/running/done)
            → Team Rooms (assigned by role)
                → Scout (read-only, cheap)
                → Coordinator (compress, draft)
                → Lead (final, expensive, user-selected)
                    → Work Packet Export
```

## Compatibility

v1 storage names stay unchanged:

- `project-room.json`
- `project-room-projects.json`
- `project-room-state.json`
- `project-room-active.json`
- `project-room-layouts.json`
- `project-room-window.json`
- `project-room-session.json`
- `team_state.json` (roost)
