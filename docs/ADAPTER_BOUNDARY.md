# Core / Adapter Boundary

Pet Studio 0.3.0 defines a simple boundary:

> Core describes Pet Studio projects and state. Adapters translate external systems into that state.

## Core May Know

- project ids, display names, themes, and enabled flags
- registry paths and workspace paths
- kit manifest paths
- supported Pet Studio states and aliases
- state bridge payload fields: `projectId`, `state`, `message`, `updatedAt`, `resetAfterMs`, `resetToState`

## Core Must Not Know

- Codex hook names or payload shapes
- Codex trust approval behavior
- Codex transcript, session, turn, tool, or permission fields
- Tkinter widget lifecycle
- shell launcher behavior
- endpoint/model names
- Team Room, Project Hub, or orchestrator behavior

## Codex Adapter Owns

The Codex adapter lives in `pet-studio-widget/` and consists of three layers:

### 1. Hook Entry Point — `codex_pet_hook.py`

Receives Codex lifecycle events via stdin. Each hook maps to a Pet Studio event and default message (see `HOOK_TO_EVENT` table in the file). Reads stdin payload for prompt text, tool names, and error context to build user-facing bubble messages.

Responsibilities:
- Decode stdin payload (UTF-8 / locale fallback)
- Resolve project ID (explicit → active pin → workspace match)
- Translate hook → event + message
- Write state bridge via `codex_pet_hook.py`
- Append audit entry to `project-room-hook-events.jsonl`
- Optional passthrough to previous notify command

### 2. Event Adapter — `codex_state_adapter.py`

Thin translation layer between external event names and Pet Studio states.

Responsibilities:
- `EVENT_TO_STATE` mapping: `start→running`, `wait→waiting`, `review→review`, `block→blocked`, `fail→failed`, `done→done`, `idle→idle`
- Project ID resolution chain
- State file write delegation to `set_project_state.py`
- JSON payload parsing (file or stdin)

### 3. Installer — `tools/install_pet_studio_codex_integration.py`

One-shot setup for development environments.

Responsibilities:
- Install `$pet-studio` skill to `%USERPROFILE%\.codex\skills\pet-studio`
- Write `.codex/hooks.json` entries for all 6 lifecycle hooks
- Optionally wrap `notify` in `.codex/config.toml`
- Write active project pin
- Backup existing hooks.json and config.toml before modification

## Adapter File Map

| File | Role | Boundary |
| --- | --- | --- |
| `pet-studio-widget/codex_pet_hook.py` | Hook entry point | Adapter |
| `pet-studio-widget/codex_state_adapter.py` | Event→state translation | Adapter |
| `pet-studio-widget/pet_studio_event_adapter.py` | Alias/wrapper | Adapter |
| `tools/install_pet_studio_codex_integration.py` | Installer | Adapter |
| `pet_studio_core/registry.py` | Registry primitives | Core |
| `pet_studio_core/state.py` | State bridge primitives | Core |

## Compatibility Rule

Existing modules under `pet-studio-widget` may remain as wrappers so old imports keep working. New shared behavior should land in `pet_studio_core` first, then be re-exported from compatibility modules when needed.

## Hook Lifecycle Reference

For the full hook event → state mapping table and troubleshooting guide, see `docs/CODEX_INTEGRATION.md`.
