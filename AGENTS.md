# Pet Studio Agent Guide

Use this as the short operating guide for agents working in this repository.

## Current Shape

Pet Studio is a local-first Windows desktop widget for project rooms, plus the
`roost` foundation for lightweight project queues, presets, security levels, and
script/Hermes event classification.

Check `VERSION`, `pyproject.toml`, and `CHANGELOG.md` before making release
claims. Those files have drifted before.

## Read First

| Task | Read |
| --- | --- |
| Roadmap or feature scope | `docs/PET_STUDIO_ROADMAP.md` |
| Orchestration or Roost work | `docs/PET_STUDIO_ORCHESTRATION_PLAN.md` |
| Install, launcher, widget behavior | `docs/INSTALL.md`, `pet-studio-widget/README.md` |
| Codex hook or state bridge work | `docs/CODEX_INTEGRATION.md` |
| Core/adapter boundary work | `docs/ARCHITECTURE.md`, `docs/ADAPTER_BOUNDARY.md` |
| UX priorities and current state | `docs/UX_PRIORITIES.md` |
| Demo / release capture | `docs/DEMO_SCRIPT.md` |
| Long-term workroom vision | `docs/PET_STUDIO_WORKROOM_VISION.md` |
| Room kit or asset work | `pet-studio-kit/SKILL.md` |

Do not edit public docs from memory. Confirm against current files.

## Hard Rules

- Keep Pet Studio local-first and Windows-focused unless a task says otherwise.
- Preserve `project-room-*` file names and CLI compatibility.
- Keep `pet_studio_core` free of Codex, Tkinter, launcher, hook, image-provider,
  and widget imports.
- Do not install Codex hooks unless the user explicitly asks.
- Do not edit `.codex/config.toml` or `.codex/hooks.json` during ordinary work.
- Do not add Project Hub, hosted dashboard, cloud sync, or full simulation
  behavior as current functionality.
- Do not add real model backends (Ollama, llama.cpp, vLLM, remote API) without
  a confirmed call site.
- For orchestration work, Roost must work without an LLM. Script mode is the
  fallback; optional backends are adapters.

## Key Paths

| Path | Role |
| --- | --- |
| `pet-studio-widget/project_room_widget.py` | Tk widget host |
| `pet-studio-widget/project_room_scene.py` | scene/layout/session helpers |
| `pet-studio-widget/codex_pet_hook.py` | Codex hook entry point |
| `pet-studio-widget/codex_state_adapter.py` | event-to-state bridge |
| `pet_studio_core/registry.py` | shared registry primitives |
| `pet_studio_core/state.py` | shared state bridge writer |
| `roost/state.py` | project queue and event state |
| `roost/security.py` | per-project L0-L3 security checks |
| `roost/preset.py` | room preset export/import |
| `roost/backend/__init__.py` | backend interface + registry |
| `roost/backend/script.py` | deterministic script classifier |
| `roost/backend/hermes.py` | optional Hermes subprocess adapter |

## Testing

Minimum checks after code or CLI changes:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
.\tools\pet_studio_python.cmd -m pytest roost/tests/ -q
.\tools\pet_studio_python.cmd -m pytest pet-studio-widget/tests/ -q
.\tools\pet_studio_python.cmd -m pytest pet-studio-kit/tests/ -q
.\tools\pet_studio_python.cmd -m pytest pet_studio_core/tests/ -q
ruff check roost/ pet-studio-widget/ pet-studio-kit/ tools/ pet_studio_core/
ruff format --check roost/ pet-studio-widget/ pet-studio-kit/ tools/ pet_studio_core/
git diff --check
```

For Python entrypoints touched in the change:

```powershell
.\tools\pet_studio_python.cmd -m py_compile <changed-python-files>
```

For Codex hook changes, also run:

```powershell
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\codex_pet_hook.py pet-studio-widget\codex_state_adapter.py
.\tools\pet_studio_python.cmd pet-studio-widget\codex_pet_hook.py --hook user_prompt_submit --project-id gakju-archive-demo
```

## Local-Only Files

Do not commit runtime state, QA packs, or local handoff scratch:

```text
pet-studio-widget/project-room-active.json
pet-studio-widget/project-room-window.json
pet-studio-widget/project-room-session.json
pet-studio-widget/project-room-state.json
pet-studio-widget/project-room-hook-events.jsonl
pet-studio-widget/project-room-widget.lock
runs/*/qa-pack/
tester/
__pycache__/
*.pyc
```

## Handoff

Read `.hermes/handoff.json` at session start. If `nextAgent` is not your role,
report it unless the user explicitly assigns the task to you.

Before a commit that hands work to another agent, update `.hermes/handoff.json`
with:

- `lastAgent`
- `lastAction`
- `nextAgent`
- `nextAction`
- relevant `context`
- a short history entry
