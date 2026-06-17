# Pet Studio 로드맵

## 비전

Pet Studio는 Codex 프로젝트마다 작은 로컬 데스크톱 방을 붙인다. 각 프로젝트는 방, 펫, 소품, 레이아웃, 현재 상태를 가지며, 로그를 읽지 않아도 에이전트가 무엇을 하고 있는지 시각적으로 파악할 수 있다.

장기 방향:
- 모든 Codex workspace가 고유한 방을 가짐
- 방 상태 변화가 실제 에이전트 라이프사이클 이벤트를 반영
- 보조 펫과 소품이 review/blocked/handoff/done 상태를 시각적으로 표현
- 사용자가 JSON 수정 없이 방 프리셋을 만들고 공유 가능
- 로컬 우선, 경량 위젯 유지

---

## 현재 — 0.5.0 팀 오케스트레이션 기반

> 위젯 앱 + 팀 오케스트레이션 레이어 기반 완성.

0.5.0에서 완료:
- `alba/state.py` — `team_state.json`으로 프로젝트 큐, 이벤트 로그, 컨텍스트 축적
- `alba/preset.py` — zip 기반 프리셋 내보내기/가져오기
- `alba/backend/hermes.py` — Hermes Agent 연동 LLM 이벤트 분류 (선택)
- `alba/security.py` — L0~L3 프로젝트별 보안 레벨
- `alba/backend/script.py` — 컨텍스트 기반 우선순위 보정
- 상태바 알바 상태 아이콘 (🟢⚪🔴)
- 보안 레벨 + 컨텍스트 분류 포함 276개 테스트

0.5.0에서 안 할 것:
- 신뢰 점수 자동 승인 (0.6.0)
- 승인 대기 목록 UI (0.6.0)
- 팀 오케스트레이션 UI (0.6.0)

---

## 완료 — 0.4.x 멀티룸 + 트레이

> 방 하나는 된다. 다음: 방 전환 마찰 제거.

0.4.x에서 완료:
- 프로젝트 A 작업 → `cd` → 프로젝트 B → 위젯이 자동으로 방 전환
- 시스템 트레이 아이콘으로 재실행 없이 방 전환
- 상태바에 현재 프로젝트/상태 표시
- 컨텍스트 메뉴에서 프리셋 내보내기/가져오기

0.4.x에서 안 했던 것:
- GUI 방 에디터
- macOS/Linux 호스트
- Team Rooms / Project Hubs
- 클라우드 동기화

---

## 이후 — 0.6.0 팀 UI + 자기 개선
- 트레이: Windows에서 `pystray` 또는 `infi.systray`; 라이브러리 없으면 graceful fallback
- 샘플 방: `runs/` 아래에 미리 빌드된 킷과 함께, README에 문서화
- 내보내기/가져오기: zip = `kit/` + `assets/` + `manifest.json`; 가져오기 시 기존 kit validator로 검증

---

## 이후 — Workroom 개념

> 더 넓은 방향. 특정 버전에 스케줄링되지 않음.

- 작업 진행을 방에 매핑하는 시각화 (대시보드가 아닌 형태)
- macOS/Linux 위젯 호스트
- 방 테마 팩
- 커뮤니티 배포가 가능한 공유 프리셋

장기 Workroom 비전 (Team Rooms, Project Hubs, task cards, delegation traces):
[docs/PET_STUDIO_WORKROOM_VISION.ko.md](PET_STUDIO_WORKROOM_VISION.ko.md) 참고.

---

## 범위 밖

- 탑다운 오피스 시뮬레이션 아님
- 게임 맵, 걷기 경로, 방 내비게이션 아님
- 독립형 대시보드 앱 아님
- 여러 에이전트가 항상 보일 필요 없음
- 클라우드 동기화 또는 호스팅 팀 서비스 아님
