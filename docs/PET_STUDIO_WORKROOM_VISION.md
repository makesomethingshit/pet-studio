# Pet Studio Vision

## One-Line Vision

> AI work, visible at a glance. Pet Studio is the visual operating layer around AI work — one window, role-aware model routing, compact packets for the lead agent. No log reading required.

Pet Studio is a **local-first visual AI workroom** - not another coding agent, not a hosted dashboard. It is the visual operating layer around AI work.

## Why Pet Studio Exists

Too many AI tools, too many windows — and you still can't see what any of them are actually doing.

- **Model sprawl**: GPT, Claude, Gemini, Codex, Hermes, OpenCode... each in its own tab, its own log, its own mental model. You switch contexts just to check status.
- **Agent opacity**: terminal logs, chat diffs, code editors — all coder-centric. You read output to understand what happened. There's no visual room where the work is visible at a glance.
- **Token waste**: expensive models doing simple scans, cheap models sitting idle while the SOTA burns credits on formatting. No role-aware routing by default.

Pet Studio solves this by giving AI work a **visual room** — one window, one pet per team, status visible without log reading, role-aware model routing that saves tokens by default.

## Core Entities

| Entity | Description |
|---|---|
| **Pet** | Visible team identity. One pet = one Team Room. Currently rendered as the widget canvas avatar; future: independent scene entity. |
| **Team Room** | Reusable unit with its own avatar, memory, skills, endpoint prefs. |
| **Project Hub** | Shared meeting space where Team Rooms connect and work. |
| **Mission** | User-given goal, auto-assigned to relevant rooms. |
| **Task Card** | Decomposed unit of work, visible as a card, not hidden in chat. |
| **Endpoint Registry** | Aliases (`local/fast`, `remote/sota`, `mock/scout`) hiding model details. |
| **Model Profile** | User-facing model choice ordered as closed models, open-model SOTA, local model routes, value models, then free models. |

## Internal Roles (Token Optimization)

To avoid wasting tokens on expensive models for simple work:

Model choices should be shown in this user-facing order:

1. **Closed models**: GPT, Claude, and similar hosted frontier models.
2. **Open-model SOTA**: strongest available open model route.
3. **Local model routes**: local-first adapters or script fallback when no local LLM adapter is configured.
4. **Value models**: good enough for routine work at lower cost.
5. **Free models**: fallback or no-cost routes.

| Role | Cost | Responsibility |
|---|---|---|
| **Scout** | Low (local/cheap model) | Read-only exploration, file scan, log summary. |
| **Coordinator** | Mid-level | Compress Scout results, draft packets, safe edits, synthesize. |
| **Lead** | High (SOTA or user-selected agent) | Final judgment, multi-file changes, implementation. |

Delegation flow: `Scout -> Coordinator -> Lead`, with reverse delegation allowed (future: agents call each other when blocked).

This hierarchy exists to **save tokens**, not for architectural purity.

The default role model plan should be credit-aware:

- **Scout** starts on `local/default` or another free/local route.
- **Coordinator** starts on a value route such as `openrouter/fast`.
- **Lead** follows the active model profile, because this is where user-selected
  GPT, Claude, OpenRouter SOTA, or Codex-level judgment belongs.

The Workroom should let the user switch that whole plan at once. Presets such
as `save-credits`, `all-local`, `all-value`, and `lead-sota` exist so model
changes are team-level operations instead of repeated per-role edits.

## Security Model

Per-project security levels:

| Level | Behavior |
|---|---|
| L0 Allow | Allow risky actions |
| L1 Warn | Log risky actions, then allow (default) |
| L2 Ask | Require user approval for risky actions |
| L3 Deny | Block risky actions |

## Architecture Boundary

```
roost/                 -> team orchestration (state, security, presets, backends)
pet-studio-widget/     -> desktop widget host (Tkinter, canvas, rendering)
pet-studio-kit/        -> asset pipeline (room creation, validation, QA)
tools/                 -> CLI entry points (install, create, QA)
```

Key rule: **Roost must not depend on any single adapter.** Codex, Hermes, OpenCode — all are adapters, not the product center.

## What Pet Studio Is NOT

- Not a ChatGPT/Codex/Hermes replacement
- Not a hosted dashboard or cloud service
- Not a game or office simulation
- Not a generic workflow graph
- Not an image generator

## What Pet Studio IS

> A local-first visual AI workroom. You see who's working, what role they have, and which model they use — then hand off a compact packet to the lead agent. No log reading required.
