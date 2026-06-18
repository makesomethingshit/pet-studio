# Pet Studio Architecture

Pet Studio is currently a local-first room kit generator plus a desktop widget host. The 0.3.0 architecture boundary keeps that behavior intact while making future Workroom features easier to add without turning Codex integration into the core product.

## Layers

### Pet Studio Core

`pet_studio_core` owns shared, host-neutral primitives:

- project registry parsing and selection
- workspace-to-project inference
- widget state normalization
- file-based state bridge payload writing

Core must not import Codex hook code, Tkinter widget code, launcher scripts, image generation providers, or future Workroom orchestration.

### Widget Host

`pet-studio-widget` owns desktop runtime behavior:

- Tkinter window lifecycle
- canvas rendering and animation
- saved layout, window, and session files
- context menu and bubble presentation

Compatibility modules such as `project_room_registry.py` remain in this folder, but they should delegate shared behavior to `pet_studio_core`.

### Codex Adapter

The Codex adapter owns Codex-specific event translation:

- Codex hook payload fields
- hook event to Pet Studio state mapping
- hook logs
- hook install and trust guidance

Codex is an adapter, not the core. Core should be usable by another adapter later without importing Codex-specific files.

### Asset Forge

The current asset forge is the kit generator and guardrail toolchain in `pet-studio-kit/scripts`. In 0.3.0 this remains script-based. Future asset packs and prompt workflows should build on this boundary instead of moving image generation concerns into Core.

### CLI Tools

`tools/` contains user-facing CLI commands for installation, room creation, QA, and Codex integration:

- `tools/pet_studio_preflight.py` — preflight checks for a project room
- `tools/pet_studio_create_room.py` — scripted room creation
- `tools/create_room_interactive.py` — interactive room creation
- `tools/pet_studio_codex_integration.py` — install Codex hooks
- `tools/pet_studio_skill.py` — install Pet Studio skill

**Boundary rule:** `tools/` scripts are thin wrappers. They must not contain core business logic — shared behavior belongs in `pet_studio_core/`. `tools/` may import from `pet_studio_core/` and `pet-studio-kit/scripts/` but not from `pet-studio-widget/` directly.

**Distinction from Asset Forge:** `pet-studio-kit/scripts/` generates and validates room art assets (PNGs, kits). `tools/` orchestrates user workflows (install, create, QA). Do not merge these concerns.

### Future Workroom

Team Room, Project Hub, endpoint registry, mission board, and orchestration concepts remain future layers. Team Room Panel (v0.6) is the first orchestration UI, implemented as a slide-in tkinter frame on the widget host. They should depend on Core contracts, not on Codex hook internals or the Tkinter widget host.

## Compatibility

The v1 compatibility storage names stay unchanged:

- `project-room.json`
- `project-room-projects.json`
- `project-room-state.json`
- `project-room-active.json`
- `project-room-layouts.json`
- `project-room-window.json`
- `project-room-session.json`

Public commands also stay compatible. 0.3.0 is an internal boundary release, not a schema-breaking rename.
