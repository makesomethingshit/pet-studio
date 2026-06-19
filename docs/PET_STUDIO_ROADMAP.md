# Pet Studio Roadmap

## Current State: v0.6.1

Shipped and working:

- Windows desktop widget with layered room rendering
- Project registry, saved layout/window/session, state bridge
- Workspace auto-detection, tray controls, status bar, project switching
- Optional Codex skill and hook adapter
- `pet_studio_core` — registry and state primitives (adapter-independent)
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

### Phase 1a: Team Room Quick Fixes (Toplevel 유지)

1. **위치 계산 수정** — 팝업이 위젯 뒤에 가려짐 해결. topmost 제거, 위젯 우측 엣지에 앵커
2. **접기/펴기 버튼** — 최소화 가능한 커스텀 프레임으로 변경
3. **역할 뱃지 추가** — Staff 카드에 Scout/Coordinator/Lead 아이콘
4. **큐 액션 버튼** — 각 큐 아이템에 할당/제거 버튼

**예상 시간**: 2-3h

### Phase 1b: Team Room Canvas Panel (Phase 1a 완료 후)

1. **Toplevel → Canvas 내장 패널** — slide-in 패널로 교체
2. **시각 디자인** — 어두운 배경, 카드 구분선, 상태 색상
3. **Staff 카드 인터랙션** — 클릭 → 상세 보기
4. **큐 드래그** — 순서 변경

**예상 시간**: 3-4h
**리스크**: Canvas 패널 구현 난이도 높음 → Phase 1a 완료 후 필요성 재평가

### Phase 2: Project Hub

1. **Hub 창** — 일반 Toplevel (topmost 없음), 위젯과 별도 생명주기
2. **트레이 메뉴** — "Open Project Hub" 추가
3. **Mission Input** — 텍스트 입력 → 수동 할당 (자동 라우팅은 v0.8)
4. **Task Cards** — Canvas 기반 카드, waiting/running/done 칼럼

**예상 시간**: 5-7h

### Phase 3: Work Packet Export

1. **Packet 구조** — mission, tasks, context, assigned_rooms, target_agent
2. **Export API** — `export_packet(team_state, project_id) → dict`
3. **Save as JSON**

**예상 시간**: 1-2h

### Out of Scope for v0.7

- 자동 라우팅 (v0.8로 이관)
- Canvas 패널 고급 애니메이션
- 다중 프로젝트 동시 Hub

### Definition of Done

- [ ] 팝업 위치 계정 수정 (위젯 뒤에 가려짐 해결)
- [ ] 팝업 접기/펴기 가능
- [ ] Staff 카드에 역할 뱃지 (Scout/Coordinator/Lead)
- [ ] 큐 아이템에 액션 버튼
- [ ] (Phase 1b 진행 시) Canvas 패널로 교체
- [ ] Project Hub 창 열기 (일반 창, topmost 없음)
- [ ] Mission 입력 → 수동 할당
- [ ] Task Cards 렌더링 (waiting/running/done)
- [ ] Work Packet Export (JSON)
- [ ] 로직 단위 테스트 추가 (state, packet)
- [ ] UI 수동 QA 완료
- [ ] CI green (ruff check + format)

### 예상 일정

| Phase | 시간 |
|---|---|
| Phase 1a | 2-3h |
| Phase 1b | 3-4h (조건부) |
| Phase 2 | 5-7h |
| Phase 3 | 1-2h |
| 테스트 + QA | 2-3h |
| **합계** | **13-19h (버퍼 20% 포함)** |

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

- End-to-end integration testing (Hub → Mission → Task Cards → Roles → Work Packet)
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
- Auto-execute from any adapter by default
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
| 0.3.x | Boundary + Hygiene — Core/adapter split, installers, QA gate |
| 0.4.x | Widget App — room switching, tray, status bar, optional Codex adapter |
| 0.5.x | Roost Foundation — presets, state manager, security, backends |
| 0.6.x | Team UI — Team Room panel, approvals, staff tracking, toast UX |
| **0.7** | **Project Hub — Mission input, Task Cards, Work Packet export** |
| **0.8** | **Token Roles — Scout, Coordinator, Endpoint Registry, trust** |
| **0.9** | **Integration & Polish — e2e tests, token savings, docs** |
| **1.0.0** | **Stable Release — all features integrated and tested** |
