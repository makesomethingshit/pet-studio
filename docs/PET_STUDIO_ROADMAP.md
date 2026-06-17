# Pet Studio Roadmap

Pet Studio should stay local-first and small: a desktop room that shows project
state without becoming a hosted dashboard or a game.

## Current Product

Shipped or present in the current codebase:

- Windows desktop widget with layered room rendering
- project registry, saved layout/window/session, and state bridge
- workspace auto-detection, tray controls, status bar, project switching
- Codex skill and optional Codex hook bridge
- `pet_studio_core` for registry and state primitives
- room creation, validation, previews, and QA packs
- room preset export/import through `roost.preset`
- Roost state manager with queues, event history, L0-L3 security levels
- script and Hermes event classifiers
- QA gate and CI checks

Not current:

- Team Room UI
- Project Hub UI
- Task Cards
- endpoint registry UI
- trust-score auto-approval
- approval queue UI
- macOS/Linux widget hosts
- hosted/cloud sync

## Completed Line

### 0.3.x - Boundary + Hygiene

- split shared registry/state code into `pet_studio_core`
- kept Core free of Codex, Tkinter, widget, launcher, and image-provider imports
- preserved `project-room-*` compatibility
- added installer, interactive room creator, auto project detection, QA gate, CI
- cleaned stale debug and QA artifacts

### 0.4.x - Widget App

- room switching without manual `--project-id`
- system tray and right-click project controls
- status bar with current project/state
- Codex skill install and optional hook bridge
- removed speculative watcher/export/import/animation/helper-AI code until it had callers

### 0.5.x - Roost Foundation

- room preset export/import
- script-only state manager with `team_state.json`
- project queues and event logs
- security levels L0 allow, L1 warn, L2 ask, L3 deny
- context-aware script classification from event history
- optional Hermes backend using the same `classify_event(event, context=None)` shape

## Next

### 0.6 - Small Team Panel

- compact Team Room panel opened on demand
- project queue counts and current staff status
- approval queue view for security L2 actions
- manual/script routing first; LLM routing only after a real call site needs it

### 0.7 - Project Hub

- Project Hub window
- mission input
- Task Cards with waiting/running/done states
- Meeting Table summary
- Codex packet draft/export

### 0.8+ - Workroom Expansion

- lightweight room editor
- room theme packs
- richer endpoint aliases
- permission/trust review for imported skills
- optional image provider integration
- macOS/Linux widget hosts

## Non-Goals

- no top-down office simulation
- no full game map, walking paths, or room navigation
- no standalone hosted dashboard
- no cloud sync or hosted team service
- no private Codex pet runtime parity claims until behavior is confirmed

Longer-term concepts live in [PET_STUDIO_WORKROOM_VISION.md](PET_STUDIO_WORKROOM_VISION.md).
