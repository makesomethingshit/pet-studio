# Pet Studio UX Priorities

## Priority Framework

Use this question first: "Can a non-expert send a mission and understand the current flow?"

| Priority | Time | Criteria | Examples |
|---|---:|---|---|
| P0 | < 1h | Blocks first mission or status understanding. | launch, mission input, AI/fallback result, clear errors |
| P1 | 1-2h | Removes friction from daily use. | widget quick mission, saved window state, task actions |
| P2 | 2-4h | Makes the app calmer and easier to scan. | card density, status color, small transitions |
| P3 | backlog | Useful, but not required for the current Workroom path. | theme packs, room editor, non-Windows host |

## Current Implementation

### Shipped

| Feature | Surface | Notes |
|---|---|---|
| Workroom Daily view | `pet-studio-widget/ui/project_hub.py` | Project rail, Mission Console, Task Board. |
| Advanced Workroom settings | Workroom | Team Room, Endpoints, role routes, model profiles. |
| Widget companion | `pet-studio-widget/` | Room rendering, flow rail, bubble/status display, quick mission entry. |
| File state bridge | `pet_studio_core/state.py` | Keeps `project-room-*` compatibility files. |
| Project registry | `pet_studio_core/registry.py` | Workspace/project inference and compatibility wrapper. |
| Workroom design tokens | `pet-studio-widget/ui/design_system.py` | Shared colors, spacing, fonts, role/status colors, and ttk styling. |
| Task cards | Workroom Daily | Waiting/running/done lanes, role assignment, start/done actions. |
| Endpoint registry UI | Advanced | Role routes and model profiles. |
| Credit-aware role model plan | Advanced, CLI, Work Packet | Scout/Coordinator can use cheaper routes, Lead can use the active model. |
| Work Packet export/import | Workroom, `roost/packet.py` | Preserves mission, tasks, staff assignments, model policy, role env, and credit estimate. |
| Team memory approval | `roost/team_memory.py`, `tools/pet_studio_memory.py` | Pending candidates are approved or rejected before entering Work Packet context. |

### Still Rough

| Area | Current state | Preferred next move |
|---|---|---|
| First AI connection | Optional adapters exist. | Add one-step setup for Codex/OpenRouter/Hermes/gateway. |
| Failure messages | Some friendly errors exist. | Translate connection/auth/fallback failures into user actions. |
| Task cards | Functional lanes. | Improve density and selected-task actions before adding visual effects. |
| Team Room | Advanced tab only. | Keep it secondary; do not add another team UI. |

## UX Rules

- Daily shows only project, mission, status, and task board.
- Advanced contains Team Room, Endpoints, Model Profiles, and role routing.
- Widget is a companion: status at a glance plus quick mission entry.
- Keep Codex/Hermes/OpenRouter/gateway as adapter labels, not the product center.
- Prefer team-level presets over repeated per-role edits.
- Preserve `project-room-*` file names and CLI compatibility.
- Keep status messages short and actionable.

## Current Workroom Priorities

### P0

- Keep Workroom and widget launch reliable.
- Keep mission input available from Daily and widget.
- Show whether mission dispatch used AI or fallback.
- Show friendly failures for missing API key, gateway URL, Hermes, or network.

### P1

- Add first-run AI connection setup.
- Improve routing outcome visibility across Tasks and Team Room.
- Keep Work Packet export/import round-tripping mission, tasks, staff assignments, model policy, role env hints, and credit estimate.

### P2

- Improve Task Card density and selected-task actions.
- State-aware status bar color.
- Small fade/crossfade only if it stays cheap.

### Backlog

- Room editor.
- Theme packs.
- macOS/Linux widget host.
