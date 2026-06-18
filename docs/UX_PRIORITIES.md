# Pet Studio UX Priorities

## Priority Framework

판단 기준: **"유저가 말 안해도 체감하는가?"**

| Priority | Time | Criteria | Examples |
|---|---|---|---|
| **P0** | < 1h | 즉시 체감. 상태 바로 알 수 있어야 함. | Status bar, state labels, bubble text. |
| **P1** | 1-2h | 워크플로우 단축. | Context menu, auto-switch, shortcuts. |
| **P2** | 2-4h | 시각 폴리쉬. | Animation, transitions, color polish. |
| **P3** | 백로그 | 니스-투-해브. | Theme packs, room editor, macOS support. |

## Current Implementation (v0.6)

### P0 — Shipped

| Feature | File | Status |
|---|---|---|
| Pet avatar + room rendering | `pet-studio-widget/` | ✅ |
| Speech bubble state display | `pet-studio-widget/` | ✅ |
| Project state bridge (JSON) | `pet_studio_core/` | ✅ |
| Workspace/project auto-detection | `pet_studio_core/` | ✅ |
| Team status (idle/running/blocked/review/done) | `roost/state.py` | ✅ |

### P1 — Shipped

| Feature | File | Status |
|---|---|---|
| Widget context menu (right-click) | `pet-studio-widget/` | ✅ |
| Team Room Panel (slide-in) | `pet-studio-widget/` | ✅ |
| Approval queue for dangerous actions | `roost/state.py` | ✅ |
| Room preset export/import | `roost/preset.py` | ✅ |
| State cycle (idle→running→waiting→blocked→review→done) | `roost/state.py` | ✅ |

### P2 — Partial

| Feature | File | Status |
|---|---|---|
| State transition animation | `pet-studio-widget/` | 🟡 Basic (color change only) |
| Helper pet appearance | `pet-studio-widget/` | 🟡 Blocked/review states only |
| Layout persistence | JSON files | ✅ |

### P3 — Not Yet

| Feature | Target Version | Status |
|---|---|---|
| Project Hub window | 0.7 | ❌ Planned |
| Mission input | 0.7 | ❌ Planned |
| Task Card board | 0.7 | ❌ Planned |
| Room editor | 0.8+ | ❌ Backlog |
| Theme packs | 0.8+ | ❌ Backlog |
| macOS/Linux widget host | 0.8+ | ❌ Backlog |

## UX Rules

### State Bubble Text

- Bubble text ≤ 4 words when possible.
- State labels in Korean (로컬 앱) or English (Codex bridge).
- Bubble update = immediate, no fade-in delay.

### Context Menu Order

1. Most frequent action first (`Cycle state`)
2. Middle: navigation (`Open project hub` — future)
3. Last: meta (`Settings`, `About`)

### Team Panel

- Slide-in from right side of widget.
- Max 3 staff cards visible at once.
- Overflow → scroll, not collapse.

### Permission UX

- Scout actions = silent (read-only).
- Coordinator actions = bubble notification.
- L3/Deny actions = pause + bubble prompt.
- Ask (L2) = modal before action.

## Future UX Work (Post-0.6)

### P0 Candidates

- Staff card status indicator color consistency
- Bubble i18n (English/Korean toggle)

### P1 Candidates

- Auto-switch project based on active Codex session
- Team Room preset selector (visual, not CLI)

### P2 Candidates

- Smooth state transition animation (fade/crossfade)
- Pet expression variants per state
