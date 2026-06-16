# Pet Studio Workroom Vision

## Purpose

This document captures the long-term direction for Pet Studio.

Pet Studio currently works as a Codex-oriented hatch-pet desktop room and widget. That foundation should stay intact. The next direction is to gradually reframe it into a broader **local-first visual AI workroom**.

Pet Studio should not become another coding agent like Codex, Hermes, or ChatGPT. Its role is to become the **visual operating layer** around AI work:

- rooms and team identities
- missions and task cards
- endpoint aliases
- skill packs and tool permissions
- delegation traces
- Codex-ready work packets

The product should keep the user out of the bottleneck while keeping them inside the visible loop.

## One-Line Vision

Pet Studio is a local-first visual AI workroom where reusable AI Team Rooms, each represented by a hatch-pet-derived team avatar, connect to Project Hubs, receive user missions, delegate work across roles and teams, use local/cheap/SOTA/Codex endpoints through aliases, manage skills and permissions, and produce compact Codex-ready work packets.

Short version:

> The user gives a goal. Pet teams organize the work, call each other when needed, use the right endpoints and skills, and prepare a compact packet for Codex.

## Current State

Pet Studio currently behaves like this:

```text
Codex Project
  - hatch-pet room
  - desktop widget
  - speech bubble / state bridge
  - optional Codex hook updates
```

Current strengths:

- cute hatch-pet room metaphor
- visual project state
- local-first file-based workflow
- script-driven room creation
- layered room rendering
- asset validation and QA packs
- Codex hook bubble bridge

Current limitation:

> Pet Studio still feels like a Codex skill/widget, not yet a general visual AI workroom.

The goal is to keep the working foundation while separating the core product model from Codex-specific assumptions.

## Architecture Direction

Pet Studio should be split into clear layers.

```text
pet-studio-core
  - room schema
  - asset pack schema
  - hatch-pet base schema
  - registry
  - state bridge contract
  - validation
  - QA pack contracts

pet-studio-widget
  - desktop widget host
  - room rendering
  - speech bubble display
  - window state
  - state file watching

pet-studio-adapters/codex
  - Codex skill install
  - Codex hooks
  - Codex event mapping
  - Codex bubble bridge
  - Codex handoff/export integration

pet-studio-asset-forge
  - hatch-pet-based asset creation pipeline
  - prompt generation
  - generated image import
  - asset pack creation
  - preview and QA sheet generation

pet-studio-workroom
  - Team Rooms
  - Project Hubs
  - Missions
  - Task Cards
  - Endpoint Registry
  - Skill Packs
  - Tool Broker
  - Orchestrator
  - Delegation Trace
```

Dependency rule:

```text
Core must not depend on Codex.

Allowed:
  codex-adapter -> core
  widget-host -> core
  asset-forge -> core
  workroom -> core

Forbidden:
  core -> codex-adapter
  core -> specific image provider
  core -> specific LLM endpoint
```

## Core Concepts

### Team Room

A Team Room is the main reusable unit of Pet Studio.

It is not a project. It is a visual AI team with its own identity, pet avatar, memory, skills, and endpoint preferences.

Examples:

- **Paper Dev Room**: implementation planning, risk review, Codex packet generation
- **Docs Librarian Room**: README, onboarding, changelog, explanation writing
- **Design Critique Room**: hierarchy, spacing, visual flow, structure critique
- **Security Booth**: API keys, endpoint risk, permission review, config risk

### Pet as Team Avatar

One pet represents one team.

```text
Visible unit = Pet
Operational unit = Team Room
Internal execution unit = Role
```

The user sees a compact pet identity:

```text
Paper Dev Pet:
"Preparing a Codex packet..."
```

Internally, that pet may represent a Scout, Coordinator, and Codex/Lead flow. Those roles do not need to appear as separate pets by default.

### Project Hub

A Project Hub is the shared meeting space where Team Rooms connect and work on a project.

```text
Project Hub
  - project name
  - project path
  - connected Team Rooms
  - Mission Board
  - Task Cards
  - Meeting Table
  - Decision Log
  - Delegation Trace
  - Codex Packets
  - Handoff Notes
```

Important principle:

```text
Concept owner = Team Room
Context owner = Project Hub
Work unit = Task Card
Visible team identity = Pet
```

This avoids requiring a new visual concept for every small project.

### Mission

The user should not need to manually choose a team every time.

Poor default UX:

```text
@DevRoom do this
@SecurityRoom review this
@DocsRoom document this
```

Preferred UX:

```text
User gives a goal:
"Plan the first implementation steps for turning Pet Studio into a Team Room / Project Hub workroom."
```

Then the Project Hub decides which rooms should inspect architecture, review design, check security, write docs, and prepare the final Codex-ready packet.

Manual team dispatch can exist, but it should not be the primary workflow.

### Task Card

A Mission is decomposed into Task Cards.

```text
Task Card
  - title
  - mission id
  - target Team Room
  - status
  - user goal
  - scout notes
  - coordinator summary
  - skills used
  - tool requests
  - Codex packet
  - result summary
  - handoff note
```

Tasks should not disappear into chat history. They should remain visible as cards.

### Meeting Table

The Meeting Table collects results from multiple Team Rooms.

```text
Meeting Table
  - Dev Room result
  - Docs Room result
  - Security Booth result
  - Design Room critique
  - conflicts
  - agreements
  - decisions
  - final Codex Packet
```

The user should be able to watch work happen without becoming the bottleneck.

## Team Internal Roles

A Team Room normally has three internal roles.

```text
Scout = low-cost researcher
Coordinator = working manager and compression layer
Codex / Lead = high-value judgment and implementation layer
```

### Scout

Scout is the low-cost exploration role.

Usually powered by:

- local model
- cheap API model
- mock provider during early versions

Responsibilities:

- list files
- inspect repository structure
- search files
- summarize logs
- find relevant files
- extract risks
- draft rough notes

Scout should mostly use read-only tools.

### Coordinator

Coordinator is the mid-level intelligence layer.

It is not just a prompt compiler. It is the team's working manager.

Responsibilities:

- organize Scout results
- remove unnecessary context
- create compact Codex packets
- perform small safe edits
- update docs or labels
- delegate subtasks back to Scout
- synthesize multiple reviews
- resolve simple decisions without Codex
- escalate risky decisions to Codex / Lead

Coordinator is the main token-saving layer.

### Codex / Lead

Codex / Lead is the upper intelligence layer.

It should handle high-value judgment and implementation, not broad low-value scanning.

Responsibilities:

- final architecture judgment
- dangerous or multi-file code changes
- deep test failure analysis
- actual implementation or Codex handoff
- reverse delegation to Coordinator
- deciding whether more Scout work is needed

## Delegation Model

### Upward Compression

Poor flow:

```text
Codex, inspect the whole repo and figure it out.
```

Preferred flow:

```text
User Mission
  -> Scout gathers broad context
  -> Coordinator compresses and structures it
  -> Codex receives a compact packet
```

A good Codex Packet should include:

- objective
- context
- relevant files
- risks
- options
- recommended path
- constraints
- forbidden changes
- implementation steps
- acceptance criteria
- test plan
- requested Codex judgment

### Downward Delegation

Codex / Lead can delegate lower-value work back down.

```text
Codex:
"The test log is too long. Coordinator, extract only the core failure."

Coordinator:
"Scout, scan the log for type errors, missing props, and path issues."

Scout:
"Core failures summarized."

Coordinator:
"Repackaged into a 500-token Codex-ready summary."

Codex:
"Proceeding with patch plan."
```

Target structure:

```text
Scout -> Coordinator -> Codex
Codex -> Coordinator -> Scout -> Coordinator -> Codex
```

## Coordinator Parallel Review

Coordinator may perform internal parallel judgment.

This should not create new permanent pets or visible team members. It is an internal Coordinator capability.

Purpose:

- compare implementation options
- review risks
- check prompt quality before Codex
- decide whether to escalate to Codex
- reduce unnecessary SOTA/Codex calls

Example:

```text
Scout
  -> Coordinator
       - Implementation Reviewer
       - Risk Reviewer
       - Prompt Reviewer
  -> Coordinator Synthesis
  -> Codex
```

UI should show this as a temporary review trace, not as separate permanent agents.

## Permission Lease

During Coordinator Parallel Review, temporary permission elevation may be useful. This should be implemented as a Permission Lease.

A Permission Lease is:

- temporary
- scoped
- purpose-specific
- revocable
- visible in the trace

It is not a permanent role upgrade.

Permission levels:

```text
Level 0: Observe
Level 1: Read scoped files
Level 2: Analyze logs, diffs, and configs
Level 3: Draft docs, summaries, or packet edits
Level 4: Propose patch plans or diff drafts
Level 5: Execute, only with explicit approval
```

## Skill Packs

A Skill Pack is a reusable capability package that a Team Room can use.

Examples:

- code review skill
- release checklist skill
- UI critique skill
- security review skill
- README writing skill
- GitHub issue triage skill

Skill Packs should have a trust gate before use.

The trust gate should show:

- what the skill can do
- what tools it requests
- whether it can read files
- whether it can write files
- whether it can run shell commands
- whether it can use external APIs
- what risk level it has

External skills should not run silently.

## Tool Broker

Workers should not execute tools directly.

Correct flow:

```text
Worker
  -> Tool Request
  -> Tool Broker
  -> Permission Check
  -> Tool Execution
  -> Tool Result
  -> Worker / TaskCard / MeetingTable
```

The Tool Broker checks:

- is this role allowed to use this tool?
- are arguments valid?
- is the request inside project scope?
- is this write/delete/shell?
- does this require elevated permission?
- is there a fallback?

Role defaults:

```text
Scout:
  - read-only exploration
  - no writes
  - no shell
  - no API key access

Coordinator:
  - read files
  - draft packets
  - update docs
  - small safe patches only

Codex / Lead:
  - multi-file patches
  - tests and lint
  - refactors
  - git diff review
  - dangerous actions only with explicit approval
```

## Team Memory

Team Memory is long-lived memory attached to a Team Room.

It should store compressed decisions, rules, preferences, and lessons. It should not store raw chat logs.

Memory layers:

- Team Identity Memory: personality, visual tone, work style
- Team Working Memory: recurring rules, output formats, constraints
- Project Memory: project-specific decisions and handoff notes
- Task Scratchpad: temporary notes for the current task
- Handoff Notes: compressed notes created when a task or session ends

Principle:

```text
Raw chat storage: no
Compressed decisions / rules / risks / next actions: yes
```

## Endpoint Registry

Endpoint Registry hides serving engines and APIs behind aliases.

Examples:

- `mock/scout`
- `mock/coordinator`
- `local/main`
- `local/fast`
- `remote/cheap`
- `remote/sota`
- `codex/lead`

Potential engines:

- mock
- local OpenAI-compatible endpoint
- vLLM
- SGLang
- Ollama
- OpenRouter
- OpenAI API
- SOTA API
- Codex bridge

Team Rooms should not depend on exact model names.

## Asset Forge

Asset Forge is the hatch-pet-based visual asset creation pipeline.

Responsibilities:

- manage Hatch Pet Base
- read Team Room Concept
- generate image prompts
- create pet, room, prop, bubble, and state-variant prompts
- import generated images
- create Asset Packs
- generate preview sheets and QA sheets

Asset Forge should be generation-provider agnostic.

Supported modes:

```text
Manual ChatGPT Mode:
  Pet Studio generates prompts.
  User creates images manually in ChatGPT.
  User imports generated images into Pet Studio.

API Mode:
  Pet Studio optionally calls image generation APIs.
  API keys stay in local config or environment variables.

ChatGPT App / OAuth Connector Mode:
  ChatGPT connects to the Pet Studio workflow.
  OAuth is connection/authentication, not the image mechanism itself.

Manual Design Mode:
  User creates assets in Photoshop, Illustrator, ComfyUI, or other tools.
  Pet Studio imports and validates them.
```

Important principle:

> Asset Forge is prompt-first, import-friendly, and provider-agnostic.

## Orchestration Rules

### User Should Not Be the Bottleneck

If a team is uncertain, it should not immediately ask the user.

Preferred escalation order:

```text
uncertainty
  -> ask another Team Room
  -> ask a Specialist Room
  -> run Coordinator Parallel Review
  -> escalate to remote/sota or Codex / Lead
  -> ask user only if needed
```

Ask the user only when:

- cost limits would be exceeded
- destructive change is required
- major product/design intent is ambiguous
- goals conflict
- user preference is genuinely required

### Visibility Without Micromanagement

The user should see:

- what is being worked on
- which Team Room is responsible
- when a decision is being made
- what tools were requested
- when Codex / Lead is being invoked
- what final packet or result was produced

The user should not need to approve every internal step.

## Roadmap

This roadmap is intentionally staged. Pet Studio should not jump from a room widget to a full agent orchestrator in one release.

### Current: 0.4.x Widget App Foundation

The current product is still a local desktop room widget.

- one-click install
- project room rendering
- project/state bridge
- system tray controls
- workspace/project auto-detection
- Codex skill and hook bridge as optional adapters
- Core boundary split so future adapters do not depend on Codex or Tkinter

There is no Team Room UI, Project Hub, Task Card board, endpoint registry, or orchestrator yet.

### Next: 0.5.x Presets + Script State Manager

Build the smallest useful bridge toward workroom behavior without adding LLM complexity.

- local room preset export/import
- script-only state manager
- local `team_state` or equivalent state file only if the script loop needs it
- tray/status-panel visibility for active/idle/error state
- short local event log

Backend rule: start with script mode. Add Ollama, llama.cpp, vLLM, or remote model adapters only after there is a real call site.

### Later: 0.6 Team UI

Introduce the first visible team surface.

- Team Room registration/removal
- compact team panel opened on demand
- staff cards with avatar, name, and status
- task queue counts
- manual routing first; automatic classification later

### Later: 0.7 Project Hub + Task Cards

Introduce the work surface only after team state is boring.

- Project Hub window
- Mission input
- Task Cards with waiting/running/done states
- Meeting Table summary area
- Codex packet draft/export

### Later: 0.8+ Workroom Expansion

These remain broad future directions.

- room editor
- theme packs
- macOS/Linux widget hosts
- richer endpoint aliases
- permission/trust review for imported skills
- optional image provider integration

## Out of Scope for Early Versions

Do not do these early:

- build a full Hermes-like execution agent
- make Codex auto-execute from the beginning
- force every project to have a new visual world
- show Scout / Coordinator / Codex as separate pets by default
- become a generic node graph UI
- ask user to approve every decision
- run external skills without trust review
- let workers bypass Tool Broker
- require image generation API
- treat OAuth as the image generation mechanism

## First Implementation Instruction

Before building future workroom features, keep the next step boring.

Immediate task:

```text
Do not build Team Rooms yet.
Do not build Project Hub yet.
Do not integrate real endpoints yet.
Do not add image generation API yet.

Start with local room presets and a script-only state manager.
```

Suggested first PR:

1. Add local preset export/import.
2. Add the smallest script-only state manager.
3. Show state only through tray/status UI if it helps debugging.
4. Keep current widget behavior working.
5. Add real model backends only after the script path proves useful.

Definition of done:

- existing Codex skill/widget still works
- architecture docs clearly say Codex is an adapter
- Core does not depend on Codex-specific assumptions
- future roadmap is documented but not prematurely implemented

## Final Product Identity

Pet Studio is not:

- a ChatGPT replacement
- a Codex replacement
- a Hermes replacement
- an image generator
- a generic workflow graph

Pet Studio is:

> A visual operating layer for AI workrooms.

It manages:

- visual team identity
- hatch-pet-based team assets
- asset packs
- team memory
- skill packs
- endpoint aliases
- tool permissions
- mission decomposition
- task cards
- delegation traces
- parallel mid-level judgment
- permission leases
- Codex-ready work packets
- handoff notes

Final definition:

> Pet Studio is a local-first visual AI workroom where reusable Team Rooms, each represented by a hatch-pet-derived pet and equipped with memory, skills, asset packs, endpoint preferences, and tool permissions, connect to Project Hubs, receive Missions, coordinate work through Scout / Coordinator / Codex roles, perform visible delegation and parallel mid-level judgment, safely manage tool access through a Tool Broker and Permission Leases, and produce compact Codex-ready work packets.

