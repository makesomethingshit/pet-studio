# Pet Studio UX Priorities

## Priority Framework

Use this question first: "Will the user feel this immediately?"

| Priority | Time | Criteria | Examples |
|---|---:|---|---|
| P0 | < 1h | Directly affects daily use or correctness. | status text, project switching, clear errors |
| P1 | 1-2h | Removes repetitive work from the main flow. | shortcuts, import/export, saved window state |
| P2 | 2-4h | Makes the app feel calmer or easier to scan. | transitions, color polish, compact summaries |
| P3 | backlog | Useful, but not required for the current Workroom path. | theme packs, room editor, non-Windows host |

## Current Implementation

### Shipped

| Feature | Surface | Notes |
|---|---|---|
| Widget room rendering | `pet-studio-widget/` | Layered room, props, pets, bubbles, status bar. |
| File state bridge | `pet_studio_core/state.py` | Keeps `project-room-*` compatibility files. |
| Project registry | `pet_studio_core/registry.py` | Workspace/project inference and compatibility wrapper. |
| Workroom window | `pet-studio-widget/ui/project_hub.py` | Projects, Tasks, Team Room, Endpoints tabs. |
| Workroom design tokens | `pet-studio-widget/ui/design_system.py` | Shared colors, spacing, fonts, role/status colors, and ttk styling. |
| Mission input | Workroom Projects tab | Saved in `team_state.json`. |
| Task cards | Workroom Tasks tab | Waiting/running/done lanes, role/staff assignment, dispatcher model routing, start/done actions. |
| Team Room tab | Workroom | Staff registration, approvals, staff status, project queue, queue cleanup, queue-to-task routing. |
| Endpoint registry UI | Workroom Endpoints tab | Role routes and model profiles. |
| Credit-aware role model plan | Workroom, CLI, Work Packet | Scout cheap/local, Coordinator value, Lead active model by default. |
| Relative credit estimate | Workroom, CLI | Compares current role model plan against Lead-only routing using cost hints. |
| Team model presets | Workroom, CLI | `save-credits`, `all-local`, `all-value`, `lead-sota`. |
| Work Packet export/import | Workroom, `roost/packet.py` | Preserves mission, tasks, staff assignments, active model, team model policy, role env cleanup hints, and relative credit estimate. |
| Team memory approval | `roost/team_memory.py`, `tools/pet_studio_memory.py` | Pending candidates are approved or rejected before entering Work Packet context. |
| Preflight team-model check | `tools/pet_studio_preflight.py` | Verifies default `save-credits` role plan and relative savings estimate. |

### Still Rough

| Area | Current state | Preferred next move |
|---|---|---|
| State animation | Basic status/color changes. | Small fade/crossfade only if it stays cheap. |
| Task cards | Functional lanes. | Better density and row actions before visual flourish. |
| Team Room | Workroom tab only, with staff registration, approval, queue cleanup, and queue-to-task routing actions. | Keep expanding this surface before adding a second team UI. |
| Model backends | Script fallback plus optional Hermes, gateway, and Codex adapters. | Keep adapters thin and callable from current Workroom/CLI routes. |

## UX Rules

- Keep the Workroom as the main app surface; avoid separate floating panels for the same data.
- Keep Codex as an optional adapter label, not the product center.
- Keep frequent controls visible: active model, team preset, mission, status, security level.
- Prefer team-level model presets over repeated per-role edits.
- Preserve `project-room-*` file names and CLI compatibility.
- Keep status messages short and operational.

## Current Workroom Priorities

### P0

- Keep the Workroom launch path reliable.
- Keep model switching and team presets visible in the header and Endpoints tab.
- Keep the relative credit estimate visible near the role model plan.
- Keep Work Packet export/import round-tripping mission, tasks, staff assignments, active model, team model policy, role env cleanup hints, and relative credit estimate.
- Keep preflight covering local-only files and default team model policy.

### P1

- Improve Task Card density and action controls.
- Improve routing outcome visibility across Tasks and Team Room.
- Add clearer failure messages for missing Hermes/OpenRouter configuration.

### P2

- State transition fade/crossfade.
- State-aware status bar color.
- Toast slide/fade polish.
- Hover tooltips for role/model summaries.

### Backlog

- Room editor.
- Theme packs.
- macOS/Linux widget host.
