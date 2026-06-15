# Pet Studio Workroom Vision

[English version](PET_STUDIO_WORKROOM_VISION.md)

> 이 문서는 현재 기능 설명서가 아니라 장기 제품 방향 문서입니다.  
> 현재 0.2.x의 Pet Studio는 로컬 방/위젯, 첫 방 생성, preflight, QA pack, Codex hook bubble bridge에 집중합니다.  
> Team Room, Project Hub, Endpoint Registry, Orchestrator는 아직 현재 기능이 아닙니다.

## Purpose

Pet Studio는 현재 Codex 중심의 hatch-pet 데스크톱 방/위젯으로 동작합니다. 이 기반은 버리지 않고 유지합니다.

장기적으로는 Pet Studio를 더 넓은 **local-first visual AI workroom**으로 확장합니다. Pet Studio는 Codex, Hermes, ChatGPT 같은 실행 agent를 대체하지 않습니다. 대신 AI 작업을 눈에 보이게 운영하는 시각 레이어가 됩니다.

Pet Studio가 다루는 장기 영역:

- 방과 team identity
- mission과 task card
- endpoint alias
- skill pack과 tool permission
- delegation trace
- Codex-ready work packet

## One-Line Vision

Pet Studio는 재사용 가능한 AI Team Room이 Project Hub에 연결되고, 사용자의 mission을 받아 역할과 팀 사이에 작업을 위임하며, local/cheap/SOTA/Codex endpoint를 alias로 사용하고, skill과 permission을 관리하며, 압축된 Codex-ready work packet을 만드는 local-first visual AI workroom입니다.

짧게 말하면:

> 사용자는 목표를 말합니다. Pet team은 작업을 정리하고, 필요한 팀을 부르고, 알맞은 endpoint와 skill을 사용해 Codex에 넘길 수 있는 compact packet을 준비합니다.

## Current State

현재 Pet Studio는 다음에 가깝습니다.

```text
Codex Project
  - hatch-pet room
  - desktop widget
  - speech bubble / state bridge
  - optional Codex hook updates
```

현재 강점:

- 귀여운 hatch-pet room metaphor
- 시각적인 project state
- local-first file-based workflow
- script-driven room creation
- layered room rendering
- asset validation과 QA pack
- Codex hook bubble bridge

현재 한계:

> 아직은 범용 visual AI workroom이라기보다 Codex skill/widget에 가깝습니다.

## Architecture Direction

장기적으로 Pet Studio는 다음 layer로 나누어야 합니다.

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
  - hatch-pet based asset creation pipeline
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

핵심 규칙:

```text
Core must not depend on Codex.
```

Codex는 core가 아니라 adapter입니다.

## Core Concepts

### Team Room

Team Room은 Pet Studio의 장기 재사용 단위입니다.

Team Room은 project가 아닙니다. 자체 identity, pet avatar, memory, skill, endpoint preference를 가진 시각적인 AI team입니다.

예시:

- **Paper Dev Room**: 구현 계획, risk review, Codex packet 생성
- **Docs Librarian Room**: README, onboarding, changelog, 설명 작성
- **Design Critique Room**: hierarchy, spacing, visual flow, structure critique
- **Security Booth**: API key, endpoint risk, permission, config risk 검토

### Pet as Team Avatar

하나의 pet은 하나의 team을 대표합니다.

```text
Visible unit = Pet
Operational unit = Team Room
Internal execution unit = Role
```

사용자는 compact한 pet identity를 봅니다.

```text
Paper Dev Pet:
"Preparing a Codex packet..."
```

내부적으로는 Scout, Coordinator, Codex/Lead flow가 있을 수 있지만, 기본 UI에서 모두 별도 pet으로 보여줄 필요는 없습니다.

### Project Hub

Project Hub는 여러 Team Room이 한 project에서 만나는 공유 공간입니다.

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

중요한 원칙:

```text
Concept owner = Team Room
Context owner = Project Hub
Work unit = Task Card
Visible team identity = Pet
```

이렇게 하면 작은 project마다 새 visual concept을 만들 필요가 없습니다.

### Mission and Task Card

사용자가 매번 team을 직접 고르는 UX는 기본값이 아니어야 합니다.

사용자는 mission을 말합니다. Project Hub는 어떤 Team Room이 architecture를 보고, 어떤 Team Room이 security를 보고, 어떤 Team Room이 docs를 준비할지 결정합니다.

Mission은 Task Card로 나뉩니다. Task Card는 chat history 안에 사라지지 않고 visible work item으로 남아야 합니다.

## Tool Broker and Permission Lease

장기적으로 worker는 tool을 직접 실행하지 않아야 합니다.

```text
Worker
  -> Tool Request
  -> Tool Broker
  -> Permission Check
  -> Tool Execution
  -> Tool Result
  -> Worker / TaskCard / MeetingTable
```

Permission Lease는 임시 권한 상승입니다.

- temporary
- scoped
- purpose-specific
- revocable
- visible in the trace

영구적인 role upgrade가 아닙니다.

## Asset Forge

Asset Forge는 hatch-pet 기반 visual asset creation pipeline입니다.

역할:

- Hatch Pet Base 관리
- Team Room Concept 읽기
- image prompt 생성
- pet, room, prop, bubble, state variant prompt 생성
- generated image import
- Asset Pack 생성
- preview sheet와 QA sheet 생성

Asset Forge는 특정 image provider에 종속되지 않아야 합니다.

초기 MVP는 manual ChatGPT mode가 적합합니다. Pet Studio가 prompt를 만들고, 사용자가 ChatGPT에서 이미지를 만든 뒤, Pet Studio가 결과를 import하고 validate합니다.

## Roadmap

### v0.2: Stable Hatch Room

현재 hatch-pet room/widget 기반을 안정화합니다.

- first room creation UX
- create room -> validate -> QA pack -> launch flow
- registry, asset, project-id validation
- repair hint
- Codex hook bubble bridge stability

Team Room이나 Project Hub는 아직 만들지 않습니다.

### v0.3: Core / Codex Adapter Boundary

Pet Studio Core를 Codex-specific logic에서 분리합니다.

목표:

> Codex is an adapter, not the core.

### v0.4: Asset Pack / Hatch Pet Base

현재 hatch-pet/Codex-themed asset을 generic Asset Pack으로 정리합니다.

### v0.5: Team Room Reframe

Team Room 개념을 도입합니다.

### v0.6 이후

Asset Forge prompt mode, Project Hub shell, Mission Board, Endpoint Registry, mock orchestrator, real Scout/Coordinator, Codex Packet Compiler를 단계적으로 도입합니다.

## Out of Scope for Early Versions

초기 버전에서는 하지 않습니다.

- Hermes 같은 full execution agent 만들기
- 처음부터 Codex 자동 실행 만들기
- 모든 project에 새 visual world를 강제하기
- Scout / Coordinator / Codex를 기본적으로 별도 pet으로 보여주기
- generic node graph UI가 되기
- 사용자가 모든 결정을 승인하게 만들기
- trust review 없이 external skill 실행하기
- Tool Broker를 우회하는 worker 만들기
- image generation API를 필수로 만들기
- OAuth를 image generation mechanism처럼 다루기

## First Implementation Instruction

향후 Workroom 기능을 만들기 전에 먼저 boundary를 세웁니다.

```text
Do not build Team Rooms yet.
Do not build Project Hub yet.
Do not integrate real endpoints yet.
Do not add image generation API yet.

Start by separating architecture boundaries.
```

## Final Product Identity

Pet Studio는 다음이 아닙니다.

- ChatGPT replacement
- Codex replacement
- Hermes replacement
- image generator
- generic workflow graph

Pet Studio는 다음입니다.

> AI workroom을 위한 visual operating layer.

최종 정의:

> Pet Studio is a local-first visual AI workroom where reusable Team Rooms, each represented by a hatch-pet-derived pet and equipped with memory, skills, asset packs, endpoint preferences, and tool permissions, connect to Project Hubs, receive Missions, coordinate work through Scout / Coordinator / Codex roles, perform visible delegation and parallel mid-level judgment, safely manage tool access through a Tool Broker and Permission Leases, and produce compact Codex-ready work packets.
