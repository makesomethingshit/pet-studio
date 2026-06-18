# Pet Studio Roadmap

## Current State: v0.6.1

Shipped and working:

- Windows desktop widget with layered room rendering
- Project registry, saved layout/window/session, state bridge
- Workspace auto-detection, tray controls, status bar, project switching
- Codex skill and optional Codex hook bridge
- `pet_studio_core` — registry and state primitives (Codex-independent)
- Room creation, validation, previews, and QA packs
- Room preset export/import (`roost.preset`)
- Roost state manager — queues, event history, L0-L3 security
- Script and Hermes event classifiers
- Team Room slide-in panel with approvals, staff status, queue
- Approval queue with L2 ASK auto-enrollment
- Employee status tracking
- QA gate and CI checks (ruff)

Not yet built:

- Project Hub UI
- Mission input
- Task Cards
- Endpoint registry UI
- Trust-score auto-approval
- Scout / Coordinator roles (only Lead exists)
- macOS/Linux widget hosts

---

## v0.7 — Project Hub + Team Room UI Redesign

**Theme**: Shared meeting space for Team Rooms. Fix all current Team Room UX issues.

### Scope

| Feature | Description | Priority |
|---|---|---|
| **Project Hub** | Shared window where Team Rooms connect. Shows connected rooms, mission board, task cards. | P0 |
| **Mission Input** | User types a goal. Hub auto-assigns to relevant Team Rooms based on their skills/roles. | P0 |
| **Task Cards** | Visible work items (waiting/running/done). Not hidden in chat history. | P0 |
| **Team Room UI Redesign** | Replace current Toplevel popup with proper panel. Fix all UX issues (see below). | P0 |
| **Codex Packet Export** | Compact work packet prepared by Coordinator, ready for Codex execution. | P1 |

### Team Room UI — Issues to Fix

1. **Popup hidden behind widget** — topmost conflict + bad position calc. Fix: anchor to widget edge, no topmost on popup.
2. **Window doesn't collapse/minimize** — Toplevel default frame. Fix: use custom frame or proper wm_attributes.
3. **No role display** — Staff cards show name/status but not role (Scout/Coordinator/Lead). Fix: add role badge.
4. **No visual design** — Plain tkinter widgets, no background/border/icons. Fix: styled cards, status colors, icons.
5. **No interaction** — Can't click staff for details, can't drag queue items. Fix: clickable staff cards, queue actions.
6. **Queue items lack actions** — Just text labels. Fix: add action buttons (assign, prioritize, remove).

### Definition of Done

- [ ] Project Hub window opens from widget tray
- [ ] Mission input accepts text and routes to Team Rooms
- [ ] Task Cards show waiting/running/done states
- [ ] Team Room panel replaces old popup (no more Toplevel)
- [ ] Team Room panel is properly anchored to widget (not hidden behind)
- [ ] Team Room panel can be collapsed/minimized
- [ ] Staff cards show role badge (Scout/Coordinator/Lead)
- [ ] Staff cards are clickable → detail view
- [ ] Queue items have action buttons
- [ ] Visual design applied (background, borders, status colors, icons)
- [ ] Codex packet export produces a structured work packet
- [ ] All existing tests pass + new features tested
- [ ] CI green (ruff check + format)

---

## v0.8 — Token-Optimized Roles

**Theme**: Scout/Coordinator roles to reduce token costs

### Scope

| Feature | Description | Priority |
|---|---|---|
| **Scout Role** | Low-cost worker for read-only tasks (file scan, log summary). Saves tokens. | P0 |
| **Coordinator Role** | Mid-level worker that compresses Scout results and drafts packets. | P0 |
| **Endpoint Registry UI** | Visual alias management (`local/fast`, `remote/sota`, `mock/scout`). | P1 |
| **Trust Automation** | Auto-approve low-risk actions based on trust score. | P2 |

### Definition of Done

- [ ] Scout role handles read-only classification (replaces some Lead calls)
- [ ] Coordinator role compresses and drafts (replaces some Lead calls)
- [ ] Token usage reduced vs. Lead-only baseline (measurable)
- [ ] Endpoint Registry UI shows aliases, allows add/remove
- [ ] All existing tests pass + new features tested
- [ ] CI green (ruff check + format)

---

## v0.9 — Integration & Polish

**Theme**: Everything works together, docs caught up, performance measured

### Scope

- End-to-end integration testing (Hub → Mission → Task Cards → Roles → Codex Packet)
- Token savings measured and documented (Scout/Coordinator vs. Lead-only baseline)
- README, INSTALL, guides updated for all new features
- Performance baseline established (startup time, memory, UI responsiveness)
- Bug fixes and edge cases from v0.7 + v0.8

### Definition of Done

- [ ] All v0.7 and v0.8 features working together
- [ ] End-to-end tests pass
- [ ] Token savings measured and documented
- [ ] README/INSTALL updated
- [ ] Performance baseline recorded
- [ ] CI green (ruff check + format)
- [ ] No known critical bugs

---

## v1.0.0 — Stable Release

**Theme**: Ship it. Public-ready.

### Scope

- All features from v0.7, v0.8, v0.9 integrated and stable
- Documentation complete (README, INSTALL, VISION, ROADMAP, guides)
- QA gate passed
- Release notes written

### Out of Scope for v1.0.0

- Tool Broker / Permission Lease system
- Room editor
- Theme packs
- macOS/Linux hosts
- Cloud sync
- Auto-execute from Codex by default
- Separate Scout/Coordinator pets in UI (internal roles only)

### Definition of Done

- [ ] All features stable and tested
- [ ] Documentation complete
- [ ] QA gate passed
- [ ] Release notes published
- [ ] CI green (ruff check + format)

---

## Post-v1.0.0 (Concepts, Not Scheduled)

- Tool Broker with Permission Leases
- Room editor
- Theme packs
- macOS/Linux widget hosts
- Community preset sharing
- Trust-score auto-approval
- Richer endpoint adapters (Ollama, llama.cpp, vLLM)

---

## Version History

| Version | Focus |
|---|---|
| 0.3.x | Boundary + Hygiene — Core/Codex split, installers, QA gate |
| 0.4.x | Widget App — room switching, tray, status bar, Codex skill |
| 0.5.x | Roost Foundation — presets, state manager, security, backends |
| 0.6.x | Team UI — Team Room panel, approvals, staff tracking, toast UX |
| **0.7** | **Project Hub — Mission input, Task Cards, Codex packet export** |
| **0.8** | **Token Roles — Scout, Coordinator, Endpoint Registry, trust** |
| **0.9** | **Integration & Polish — e2e tests, token savings, docs** |
| **1.0.0** | **Stable Release — all features integrated and tested** |
