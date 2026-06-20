# Pet Studio Vision

## One-Line Vision

> Multi-agent orchestration with a visual command center. Pet Studio connects your AI tools into a team — each with a role, a model, and a task — and hands off compact work packets to the lead agent.

## Why Pet Studio Exists

Too many AI tools, too many windows — and you still can't see what any of them are actually doing.

- **Model sprawl**: GPT, Claude, Gemini, Codex, Hermes, OpenCode... each in its own tab, its own log, its own mental model. You switch contexts just to check status.
- **Agent opacity**: terminal logs, chat diffs, code editors — all coder-centric. You read output to understand what happened. There's no single place where the work is visible at a glance.
- **Token waste**: expensive models doing simple scans, cheap models sitting idle while the SOTA burns credits on formatting. No role-aware routing by default.

Pet Studio solves this by giving AI work a **command center** — one window, role-aware model routing, compact packets for the lead agent, and a visual layer that makes the work visible without reading logs.

## What Pet Studio IS

A local-first multi-agent orchestration layer with a visual command center.

You define projects and missions. Pet Studio routes tasks through Scout, Coordinator, and Lead roles — each using the right model for the job. Staff are tracked, approvals are queued, and work packets are compressed and delivered to the lead agent. All visible in one window.

## Core Entities

| Entity | Description |
|---|---|
| **Project** | A unit of work with a mission, task queue, and security level. |
| **Team State** | Shared state: projects, staff, approvals, queue, endpoints, model profiles. Persisted as `team_state.json`. |
| **Staff** | Team members with roles (Scout, Coordinator, Lead) and statuses (idle, busy, etc.). |
| **Task** | A unit of work with a type, status, and optional role/staff assignment. |
| **Work Packet** | Compressed context export: mission, tasks, staff, model profile, role env. Delivered to the lead agent. |
| **Model Profile** | User-facing model choice: closed, open-SOTA, local, value, free. |
| **Endpoint Registry** | Aliases (`local/fast`, `remote/sota`) hiding backend details. |

## Internal Roles (Token Optimization)

To avoid wasting tokens on expensive models for simple work:

| Role | Cost | Responsibility |
|---|---|---|
| **Scout** | Low (local/cheap model) | Read-only exploration, file scan, log summary. |
| **Coordinator** | Mid-level | Compress Scout results, draft packets, safe edits, synthesize. |
| **Lead** | High (SOTA or user-selected agent) | Final judgment, multi-file changes, implementation. |

Delegation flow: `Scout -> Coordinator -> Lead`, with reverse delegation allowed (future: agents call each other when blocked).

This hierarchy exists to **save tokens**, not for architectural purity.

The default role model plan is credit-aware:

- **Scout** starts on `local/default` or another free/local route.
- **Coordinator** starts on a value route such as `openrouter/fast`.
- **Lead** follows the active model profile, because this is where user-selected GPT, Claude, OpenRouter SOTA, or Codex-level judgment belongs.

Presets (`save-credits`, `all-local`, `all-value`, `lead-sota`) let the user switch the whole plan at once instead of editing per-role.

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
- Not a coding agent — it orchestrates agents, it doesn't replace them
