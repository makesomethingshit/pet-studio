# Pet Studio Agent Guide

This file is the operating guide for agents working on Pet Studio.
Use it to avoid re-reading every document while still respecting the project scope and release workflow.

## Current Status

Pet Studio `v0.5.0` is released.

What is shipped in v0.5.0:
- Desktop widget with pet room, props, helper pets, speech bubbles
- System tray icon, auto room switching, status bar, project switching
- Codex skill + hooks integration for live bubble updates
- `pet_studio_core` with shared registry and state bridge primitives
- **Alba state manager** (`alba/state.py`) — `team_state.json` for project queues, event logs, context accumulation
- **Room preset export/import** — zip-based preset sharing
- **Hermes backend** (`alba/backend/hermes.py`) — optional LLM-powered event classification
- **Security levels L0–L3** (`alba/security.py`) — per-project access control (Allow/Warn/Ask/Deny)
- **Context-aware event classification** — ScriptBackend adjusts priority from recent history (3+ high → keep high)
- **Backend signature unification** — `classify_event(event, context=None)` across all backends
- 276 total tests, CI green, QA Gate 5/5

What v0.6.0 targets:
- Team orchestration UI
- Trust score auto-approval
- Approval queue (status bar popup)
- Team self-improvement (Hermes memory/skill reference)

See [docs/PET_STUDIO_ORCHESTRATION_PLAN.md](docs/PET_STUDIO_ORCHESTRATION_PLAN.md) for the full orchestration plan.

## Orchestration Rules (ALL AGENTS MUST FOLLOW)

When working on Pet Studio 0.5.0+ features, agents MUST respect these rules:

1. **Read the orchestration plan first** — `docs/PET_STUDIO_ORCHESTRATION_PLAN.md` is the source of truth for team orchestration design
2. **Alba is shared, not per-project** — route all local LLM work through the single alba backend; do not create separate local LLM instances per project
3. **Employee pool, not per-project employees** — use the shared employee pool with project assignment, not dedicated per-project workers
4. **Lead is user-selectable** — do not hardcode Codex; the lead endpoint is configurable (Codex/Claude Code/Cursor/Continue)
5. **Skill packs over individual skills** — define skills as packs (감시 팩, 코딩 팩, 전체 팩) with per-agent customization
6. **Security levels are per-project** — each project sets its own L0-L3 security level; default is L1 (경고). L2+ actions raise `SecurityError` that must be caught by the caller.
7. **Context accumulation is automatic** — `log_event()` records to history; `ScriptBackend` uses it for priority adjustment. Do not call `add_context_history()` manually.
8. **Progressive intelligence** — 0.5.0 has context accumulation + security levels. Trust scores and auto-approval are v0.6.0.
9. **Backend adapter pattern** — alba supports vllm/Ollama/llama.cpp/script — do not couple to a single backend
10. **LLM-independent fallback** — alba MUST work in pure script mode without any LLM for GPU-less environments
11. **Queue-based project switching** — alba cycles through projects by queue; do not implement real-time multi-project monitoring

## Required Reading

Before feature work, read the relevant guide first:

| Task | Read first |
| --- | --- |
| New feature or CLI command | `docs/PET_STUDIO_ROADMAP.md`, `docs/DEVELOPMENT.md` |
| Install/launcher/widget behavior | `docs/INSTALL.md`, `pet-studio-widget/README.md` |
| Demo or state bridge work | `docs/DEMO_SCRIPT.md`, `docs/CODEX_INTEGRATION.md` |
| Release closure / QA focus | `docs/qa/020-release-closure.md`, `PROJECT_HANDOFF.md` |
| Skill behavior | `pet-studio-kit/SKILL.md` |
| Codex integration / hook work | `docs/CODEX_INTEGRATION.md`, then see **Code Paths** below |
| Architecture / boundary work | `docs/ARCHITECTURE.md`, `docs/ADAPTER_BOUNDARY.md` |

Do not edit public docs based only on memory. Confirm wording against the existing files.

## Code Paths

Key source files for Codex integration and hook work:

| File | Role |
| --- | --- |
| `pet-studio-widget/codex_pet_hook.py` | Hook entry point — receives Codex lifecycle events, translates to state bridge writes |
| `pet-studio-widget/codex_state_adapter.py` | Event-to-state translation layer — `EVENT_TO_STATE` mapping, project id resolution |
| `pet-studio-widget/pet_studio_event_adapter.py` | Alias/wrapper for `codex_state_adapter.py` |
| `tools/install_pet_studio_codex_integration.py` | One-shot installer — skill install + hooks.json + config.toml notify wrap + active project pin |
| `tools/pet_studio_hook_status.py` | Hook bridge health check — verifies hooks installed, events flowing, state freshness |
| `pet-studio-widget/project_room_registry.py` | Project registry — re-exports from `pet_studio_core` (0.3.0+) |
| `pet-studio-widget/set_project_state.py` | Low-level state file writer |
| `pet-studio-widget/set_active_pet_studio.py` | Active project pin writer |
| `pet_studio_core/registry.py` | Core registry primitives (0.3.0+) |
| `pet_studio_core/state.py` | Core state bridge primitives (0.3.0+) |

### Hook Event → State Mapping

Defined in `codex_pet_hook.py` (`HOOK_TO_EVENT`):

| Codex Hook | Event | Default Message |
| --- | --- | --- |
| `session_start` | `idle` | "Pet Studio ready" |
| `user_prompt_submit` | `running` | "Working: <prompt>" |
| `pre_tool_use` | `running` | "Using <tool>" |
| `post_tool_use` | `running` | "Working" |
| `pre_compact` | `waiting` | "Compacting context" |
| `stop` | `done` → `idle` (auto-reset 1.5s) | "Done" |
| `notify` | `done` → `idle` (auto-reset 1.5s) | "Turn ended" |

State aliases: `done` → `jumping` (hatch-pet row), `blocked` → `failed`, `handoff` → `review`.

### Project ID Resolution Order

When `--project-id` is omitted, the adapter resolves in this order:
1. Explicit `projectId` argument or JSON payload field
2. Active project pin (`project-room-active.json`)
3. Workspace path matching against registry `workspacePaths`

## Scope Rules

Stay within Pet Studio `v0.2.0` / `v0.3.0` scope.

Do not add these as current features:
- Team Room
- Project Hub
- cloud sync
- hosted dashboard
- full simulation/game behavior
- automatic helper/sub-pet selection without user confirmation

Long-term concepts may be mentioned in vision docs, but they must not be implemented as current functionality.

## Working Style

- Prefer small, testable changes.
- Reuse existing modules and CLI patterns.
- Keep machine-readable output stable.
- Keep user-facing repair hints short and actionable.
- Do not install Codex hooks unless the command explicitly asks for hook installation.
- Do not modify `.codex/config.toml` or `.codex/hooks.json` during ordinary feature work.

## Testing Before Finishing

Run the relevant checks before reporting completion.

Minimum for code/CLI work:

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
git diff --check
```

For Python entrypoints:

```powershell
.\tools\pet_studio_python.cmd -m py_compile <changed-python-files>
```

For the demo state cycler, also verify:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --dry-run
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 0
```

For Codex hook changes, also verify:

```powershell
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\codex_pet_hook.py pet-studio-widget\codex_state_adapter.py
.\tools\pet_studio_python.cmd pet-studio-widget\codex_pet_hook.py --hook user_prompt_submit --project-id gakju-archive-demo
```

## Local Runtime Files

Do not commit local runtime state or QA output.

Ignored/local-only paths include:

```text
pet-studio-widget/project-room-active.json
pet-studio-widget/project-room-window.json
pet-studio-widget/project-room-session.json
pet-studio-widget/project-room-state.json
pet-studio-widget/project-room-hook-events.jsonl
runs/*/qa-pack/
tester/
```

`PROJECT_HANDOFF.md` says to keep local QA output under `tester/` and generated QA packs under `runs/<project-id>/qa-pack/`.

## Useful Commands

Install or refresh the local Pet Studio skill:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py --force
```

Install Codex hooks and notify bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

Launch the demo widget:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Debug the widget with visible console output:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --foreground
```

Generate QA evidence for the demo project:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id gakju-archive-demo
```

Inspect hook event log:

```powershell
type pet-studio-widget\project-room-hook-events.jsonl
```

Quick hook bridge health check:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py --json
```

## Release Mindset

Pet Studio should remain:
- local-first
- lightweight
- Windows-focused for now
- understandable to first-time users
- safe for local file bridges and hooks
- clear about what is current functionality versus long-term vision

## Handoff Protocol

Every agent session must read and update `.hermes/handoff.json`.

**On session start:**
1. Read `.hermes/handoff.json` — understand what the last agent did and what you should do next
2. If `nextAgent` is not your role, stop and report the mismatch to the user

**On session end (before committing):**
1. Update `.hermes/handoff.json`:
   - Set `lastAgent` to your role (`hermes` or `codex`)
   - Summarize what you did in `lastAction`
   - Set `nextAgent` to the other agent
   - Describe what the next agent should do in `nextAction`
   - Add a `context` field pointing to relevant docs/code paths
   - Append to `history` array (keep last 10 entries)
2. Include the handoff update in your commit

**File location:** `.hermes/handoff.json` (committed to git, shared between agents)

**Do not** put runtime state or local paths in handoff.json — only task-level coordination.
