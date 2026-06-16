# Pet Studio Roadmap

## Vision

Pet Studio turns each project into a small local desktop room. Each project owns a scene with room, pet, prop, layout, and current state, so the desktop host can show where work is happening without becoming a hosted dashboard or full game.

The long-term direction is a local visual workroom for AI projects. The shipped product should stay smaller until each layer earns its place: one workspace, one tiny room, and enough visible state to understand what is happening without reading logs.

The final vision is broader than the current implementation:

- every workspace can have its own recognizable room
- room state changes reflect real project lifecycle events
- helper pets and props make review, blocked, handoff, and done states visible without reading logs
- users can create, tune, and share room presets without editing JSON by hand
- the widget stays local-first and lightweight rather than becoming a hosted dashboard

## Current Reality

Current 0.4.x is a widget-app line, not a team orchestrator.

What exists today:

- local Windows desktop widget
- one-click install path
- layered room rendering
- state bridge and speech bubbles
- workspace/project auto-detection
- system tray controls
- Codex skill and hook bridge as optional adapters
- `pet_studio_core/` boundary for shared registry and state behavior
- QA gate and CI checks

What does not exist today:

- Team Room UI
- Project Hub
- Task Cards
- endpoint registry
- LLM worker orchestration
- preset export/import
- macOS/Linux widget hosts

## Completed - 0.3.x Foundation

### 0.3.0 - Core Boundary

- `pet_studio_core/` shared registry and state bridge with zero Codex/Tkinter/widget imports
- `init_core()` for external path/state injection
- `write_project_state(metadata=...)` for extensible state payloads
- removed dangerous `sys.modules` deletion from widget import preference logic
- documented Core / Adapter / Widget Host boundaries
- preserved `project-room-*` v1 compatibility

### 0.3.1 - UX + Repo Hygiene

- one-click installer via `install.cmd`
- interactive room creator via `tools/create_room_interactive.py`
- auto-project detection in widget startup
- archived debug artifacts and stale QA docs
- synced English/Korean docs
- added QA gate pipeline and CI lint

## Current - 0.4.x Widget App Line

The 0.4.x line makes the room widget usable as a small app.

- room switching without manual `--project-id`
- system tray room list, state override, and quit
- status bar with current project/state
- optional Codex skill install and hook bridge
- release metadata should stay aligned across `VERSION`, `pyproject.toml`, README, and CHANGELOG

## Next - 0.5.x Presets + Script State Manager

Do the useful low-tech version first.

- room preset export/import as local zip files
- a script-only state manager before any LLM backend
- a tiny tray/status panel only if it helps inspect that loop
- a short local event log
- no popups by default
- alba (알바생) state manager: `team_state.json` schema, project queues, event logs
- backend adapters: script / Hermes / OpenClaw

Backend rule: start with script mode. Add Ollama, llama.cpp, vLLM, or remote model adapters only after there is a real call site.

## Later - 0.6 Team UI + Self-Improvement

- Team Room registration and removal
- compact team panel opened on demand
- staff cards with avatar, name, and status
- task queue counts such as `waiting 3 / running 1`
- manual/script routing first; LLM classification later if it earns its keep

### Team Self-Improvement (영감: Hermes memory/skill 시스템)

팀 단위로 학습하고 개선하는 루프. Hermes의 자기 개선(memory, skill, session search)을 팀 오케스트레이션으로 확장한다.

**① 작업 패턴 → 자동 스킬 생성**
- 같은 작업 3회 반복 → "이 작업은 이렇게 한다" 스킬 자동 생성
- 예: "lint → test → commit" 반복 → `auto-dev-cycle` 스킬
- 실패 패턴 → 회전 목록(rotation list) 업데이트

**② 팀 메모리 (`team_state.json` 확장)**
- 프로젝트별 인사이트 축적 (공통 에러, 베스트 프랙티스)
- 직원별 성과 기록 (성공률, 평균 소요 시간)
- 작업 큐 패턴 분석 (어떤 작업이 어떤 직원에게 잘 맞는지)

**③ 자동 최적화**
- 작업 배분 알고리즘 개선: "이 타입 작업은 codex가 2배 빠름" → 자동 가중치
- 프리셋 자동 추천: "이 프로젝트 타입은 이 프리셋이 가장 많이 쓰임"
- 상태 전환 자동화: 스테일 감지 → idle 전환 (clawd-on-desk 참고)

**④ 상태 → 펫 표정 매핑 (clawd-on-desk 참고)**
- idle / thinking / typing / building / error / happy / sleeping 등
- 에이전트 상태 → 펫 애니메이션 자동 전환
- 스테일 감지: 30초 이상 업데이트 없으면 → idle

## Later - 0.7 Project Hub

- Project Hub window
- Mission input
- Task Cards with waiting/running/done states
- Meeting Table summary area
- Codex packet draft/export

## Later - 0.8+ Workroom Expansion

- lightweight room editor
- room theme packs
- macOS/Linux widget hosts
- richer endpoint aliases for local/cheap/SOTA/Codex roles
- permission/trust review for imported skills
- optional image provider integration

## Non-Goals for 0.4.x / 0.5.x

- GUI room editor
- macOS/Linux widget hosts
- Team Rooms / Project Hubs
- cloud sync
- schema-breaking room format changes
- hosted dashboard behavior

## Longer-Term Workroom Concepts

Broader workroom concepts are attractive directions, not current features.

- project progress visualization that maps task progress into the room without becoming a heavy dashboard
- room theme packs and community distribution
- shareable room presets
- Team Rooms, Project Hubs, task cards, and delegation traces

See [Pet Studio Workroom Vision](PET_STUDIO_WORKROOM_VISION.md).

## Out Of Scope

- No top-down office simulation.
- No full game map, walking paths, or room navigation.
- No standalone hosted dashboard app.
- No requirement that many agents are visible at all times.
- No cloud sync or hosted team service.
- No claim of full private Codex pet runtime parity until each behavior is confirmed and reproduced.