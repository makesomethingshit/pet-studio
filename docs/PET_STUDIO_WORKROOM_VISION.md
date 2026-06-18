# Pet Studio Vision

## One-Line Vision

> The user gives a goal. Pet teams organize the work, call each other when needed, use the right endpoints and skills, and prepare a compact packet for Codex.

Pet Studio is a **local-first visual AI workroom** — not another coding agent, not a hosted dashboard. It is the visual operating layer around AI work.

## Why Pet Studio Exists

Too many AI tools, too many windows, too much context switching.

- Model fatigue: GPT, Claude, Gemini, Codex, Hermes, OpenClaw, OpenCode...
- Agent fatigue: terminal logs, chat diffs, code editors — all coder-centric
- Token waste: running expensive models for simple tasks

Pet Studio solves this by giving AI work a **visual room** — one window, one pet per team, status at a glance, no log reading required.

## Core Entities

| Entity | Description |
|---|---|
| **Pet** | Visible team identity. One pet = one Team Room. |
| **Team Room** | Reusable unit with its own avatar, memory, skills, endpoint prefs. |
| **Project Hub** | Shared meeting space where Team Rooms connect and work. |
| **Mission** | User-given goal, auto-assigned to relevant rooms. |
| **Task Card** | Decomposed unit of work, visible as a card, not hidden in chat. |
| **Endpoint Registry** | Aliases (`local/fast`, `remote/sota`, `mock/scout`) hiding model details. |

## Internal Roles (Token Optimization)

To avoid wasting tokens on expensive models for simple work:

| Role | Cost | Responsibility |
|---|---|---|
| **Scout** | Low (local/cheap model) | Read-only exploration, file scan, log summary. |
| **Coordinator** | Mid-level | Compress Scout results, draft packets, safe edits, synthesize. |
| **Codex / Lead** | High (SOTA/Codex) | Final judgment, multi-file changes, implementation. |

Delegation flow: `Scout → Coordinator → Codex`, with reverse delegation allowed.

This hierarchy exists to **save tokens**, not for architectural purity.

## Architecture Boundary

```
pet_studio_core/       — shared primitives (registry, state, validation)
pet-studio-widget/     — desktop widget host (Tkinter, canvas, rendering)
roost/                 — team orchestration (state, security, presets, backends)
pet-studio-kit/        — asset pipeline (room creation, validation, QA)
tools/                 — CLI entry points (install, create, QA)
```

Key rule: **Core must not depend on Codex.** Codex is an adapter.

## Security Model

Per-project security levels:

| Level | Behavior |
|---|---|
| L0 Allow | Allow risky actions |
| L1 Warn | Log risky actions, then allow (default) |
| L2 Ask | Require user approval for risky actions |
| L3 Deny | Block risky actions |

## What Pet Studio Is NOT

- Not a ChatGPT/Codex/Hermes replacement
- Not a hosted dashboard or cloud service
- Not a game or office simulation
- Not a generic workflow graph
- Not an image generator

## What Pet Studio IS

> A local-first visual AI workroom where reusable Team Rooms, each represented by a hatch-pet-derived pet and equipped with memory, skills, asset packs, endpoint preferences, and tool permissions, connect to Project Hubs, receive Missions, coordinate work through Scout / Coordinator / Codex roles, and produce compact Codex-ready work packets.
