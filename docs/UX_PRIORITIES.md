# Pet Studio UX Priorities

## Priority Framework

판단 기준: **"유저가 말 안해도 체감하는가?"**

| Priority | Time | Criteria | Examples |
|---|---|---|---|
| **P0** | < 1h | 즉시 체감. 상태를 바로 알 수 있어야 함. | Status bar, state labels, bubble text. |
| **P1** | 1-2h | 워크플로우 단축. | Context menu, auto-switch, shortcuts. |
| **P2** | 2-4h | 시각 폴리쉬. | Animation, transitions, color polish. |
| **P3** | 백로그 | 니스-투-해브. | Theme packs, room editor, macOS support. |

## Current Implementation (v0.6.1)

### P0 — Shipped

| Feature | File | Status |
|---|---|---|
| Pet avatar + room rendering | `pet-studio-widget/` | ✅ |
| Speech bubble state display | `pet-studio-widget/` | ✅ |
| Project state bridge (JSON) | `pet_studio_core/` | ✅ |
| Workspace/project auto-detection | `pet_studio_core/` | ✅ |
| Team status (idle/running/blocked/review/done) | `roost/state.py` | ✅ |
| Toast notifications (error/warn/info) | `pet-studio-widget/ui/toast.py` | ✅ |

### P1 — Shipped

| Feature | File | Status |
|---|---|---|
| Widget context menu (right-click) | `pet-studio-widget/` | ✅ |
| Team Room Panel (slide-in) | `pet-studio-widget/ui/team_room_popup.py` | ✅ |
| Approval queue for dangerous actions | `roost/state.py` | ✅ |
| Room preset export/import | `roost/preset.py` | ✅ |
| State cycle (idle→running→waiting→blocked→review→done) | `roost/state.py` | ✅ |
| Status bar with employee icons | `pet-studio-widget/ui/status_bar.py` | ✅ |

### P2 — Partial

| Feature | File | Status |
|---|---|---|
| State transition animation | `pet-studio-widget/` | 🟡 Basic (color change only) |
| Helper pet appearance | `pet-studio-widget/` | 🟡 Blocked/review states only |
| Layout persistence | JSON files | ✅ |

### P3 — Planned (v0.7)

| Feature | Target | Status |
|---|---|---|
| Project Hub window | 0.7 | ❌ Planned |
| Mission input | 0.7 | ❌ Planned |
| Task Card board | 0.7 | ❌ Planned |
| Codex packet export | 0.7 | ❌ Planned |

### P3 — Planned (v0.8)

| Feature | Target | Status |
|---|---|---|
| Endpoint Registry UI | 0.8 | ❌ Planned |
| Scout role integration | 0.8 | ❌ Planned |
| Coordinator role integration | 0.8 | ❌ Planned |

### P3 — Planned (v0.9)

| Feature | Target | Status |
|---|---|---|
| Integration testing | 0.9 | ❌ Planned |
| Token savings measurement | 0.9 | ❌ Planned |
| Documentation update | 0.9 | ❌ Planned |

### P3 — Backlog (Post-1.0.0)

| Feature | Status |
|---|---|
| Room editor | ❌ Backlog |
| Theme packs | ❌ Backlog |
| macOS/Linux widget host | ❌ Backlog |

## UX Rules

### State Bubble Text

- Bubble text ≤ 4 words when possible.
- State labels in Korean (로컬 앱) or English (Codex bridge).
- Bubble update = immediate, no fade-in delay.

### Context Menu Order

1. Most frequent action first (`Cycle state`)
2. Middle: navigation (`Open Project Hub` — v1.0.0)
3. Last: meta (`Settings`, `About`)

### Team Panel

- Slide-in from right side of widget.
- Max 3 staff cards visible at once.
- Overflow → scroll, not collapse.

### Permission UX

- Scout actions = silent (read-only).
- Coordinator actions = bubble notification.
- L3/Deny actions = pause + bubble prompt.
- L2/Ask = modal before action.

## v0.7 UX Work

### P0 (Must Have)

- Project Hub window: clean, minimal, shows connected Team Rooms
- Mission input: single text field, submit → auto-route
- Task Cards: waiting/running/done columns, drag or auto-sort

### P1 (Should Have)

- Codex packet export button in Task Card context menu

## v0.8 UX Work

### P0 (Must Have)

- Endpoint Registry UI: add/remove/edit aliases
- Role selector per Team Room (Scout/Coordinator/Lead)

### P1 (Should Have)

- Auto-switch project based on active Codex session
- Team Room preset selector (visual, not CLI)

### P2 (Nice to Have)

- Smooth state transition animation (fade/crossfade)
- Pet expression variants per state
