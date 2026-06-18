# Pet Studio Workroom Vision

## Purpose

Pet Studio started as a Codex-oriented hatch-pet desktop room widget. That foundation stays intact. The next direction is to gradually reframe it into a broader **local-first visual AI workroom**.

Pet Studio should not become another coding agent. Its role is the **visual operating layer** around AI work.

## One-Line Vision

> The user gives a goal. Pet teams organize the work, call each other when needed, use the right endpoints and skills, and prepare a compact packet for Codex.

## Core Entities

| Entity | Description |
|---|---|
| **Pet** | Visible team identity. One pet = one Team Room. |
| **Team Room** | Reusable unit with its own avatar, memory, skills, endpoint prefs. |
| **Project Hub** | Shared meeting space where Team Rooms connect and work. |
| **Mission** | User-given goal, auto-assigned to relevant rooms. |
| **Task Card** | Decomposed unit of work, visible as a card, not hidden in chat. |
| **Endpoint Registry** | Aliases (`local/fast`, `remote/sota`, `mock/scout`) hiding model details. |

## Internal Roles

| Role | Intelligence | Responsibility |
|---|---|---|
| **Scout** | Low-cost (local/cheap model) | Read-only exploration, file scan, log summary. |
| **Coordinator** | Mid-level | Compress Scout results, draft packets, safe edits, synthesize. |
| **Codex / Lead** | High-value (SOTA/Codex) | Final judgment, multi-file changes, implementation. |

Delegation flow: `Scout → Coordinator → Codex`, with reverse delegation allowed.

## Architecture Boundary

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for current layer structure.

Key rule: **Core must not depend on Codex.** Codex is an adapter.

See [`PET_STUDIO_ORCHESTRATION_PLAN.md`](PET_STUDIO_ORCHESTRATION_PLAN.md) for roost package design.

## Roadmap

| Stage | Version | Focus |
|---|---|---|
| Foundation | 0.4.x | Widget app, state bridge, Core/Codex boundary split. |
| Presets | 0.5.x | Local room preset export/import, script-only state manager. |
| Team UI | 0.6 | Team Room panel, staff cards, task queue. *(current)* |
| Workroom | 0.7 | Project Hub, Mission input, Task Cards, Codex packet export. |
| Expansion | 0.8+ | Richer endpoints, room editor, multi-platform widget host. |

## UX Priorities

See [`UX_PRIORITIES.md`](UX_PRIORITIES.md) for P0–P3 framework and current implementation.

## Out of Scope (Early)

- Full Hermes-like execution agent
- Auto-execute from Codex by default
- Separate Scout/Coordinator/Codex pets in UI
- Generic node graph UI
- External skills without trust review
- Required image generation API

## Final Definition

> Pet Studio is a local-first visual AI workroom where reusable Team Rooms, each represented by a hatch-pet-derived pet and equipped with memory, skills, asset packs, endpoint preferences, and tool permissions, connect to Project Hubs, receive Missions, coordinate work through Scout / Coordinator / Codex roles, and produce compact Codex-ready work packets.
