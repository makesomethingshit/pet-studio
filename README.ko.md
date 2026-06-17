# Pet Studio

[English README](README.md)

[![Version](https://img.shields.io/badge/version-0.5.0-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Codex 프로젝트마다 작은 데스크톱 방을 붙입니다.**

Pet Studio는 Codex 작업 상태를 작은 방, 펫, 소품, 말풍선으로 보여주는 로컬 우선 데스크톱 위젯입니다.

![Pet Studio project room reacting with a pet, props, helper creature, and speech bubble](docs/images/pet-studio-demo.gif)

로그를 계속 보는 대신, 프로젝트 방이 작업 시작, 도구 사용, 차단, 리뷰, 완료 상태에 맞춰 반응하는 모습을 볼 수 있습니다.

## 빠른 시작

### 방법 A: 원클릭 설치 (권장)

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\install.cmd
```

의존성 설치, preflight 체크, 샘플 방 위젯 실행까지 한 번에 끝납니다.

### 방법 B: 수동 설치

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Codex skill 설치:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

선택 사항: Codex hook을 연결해 live bubble bridge 사용:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

hook 설치 후 Codex를 다시 시작하거나 `/hooks`를 열어 새 명령을 확인하고 신뢰 승인하세요.

### 대화형 방 만들기

```powershell
.\tools\pet_studio_python.cmd tools\create_room_interactive.py
```

질문에 답하면 새 프로젝트 방이 만들어집니다. CLI 플래그를 외울 필요 없음.

### 내 프로젝트 자동 감지

프로젝트 폴더에서 위젯을 실행하면 자동으로 프로젝트를 감지합니다.

```powershell
.\tools\pet_studio_widget.cmd --scale 1.25
```

`--project-id`를 생략하면 현재 작업 디렉토리에서 프로젝트를 추론합니다.

## 현재 가능한 것

- Windows 데스크톱 위젯으로 샘플 프로젝트 방 실행
- 배경, 소품, 메인 펫, 보조 펫, 말풍선의 레이어 렌더링
- 로컬 프로젝트 registry, layout 저장, scale 저장, state file bridge
- 수동 상태: `running`, `waiting`, `review`, `blocked`, `failed`, `done`
- 선택적 Codex hook으로 prompt/tool/compact/stop 이벤트를 말풍선에 반영
- 스크립트 기반 방 생성, asset guardrails, validation, preview sheet, local QA pack
- 원클릭 설치 (`install.cmd`)
- 대화형 방 만들기 (`create_room_interactive.py`)
- 프로젝트 자동 감지 (workspace 기반 추론)
- **룸 프리셋 내보내기/가져오기** — zip 파일로 방 저장 및 공유
- **알바 상태 관리자** — `team_state.json`으로 프로젝트 큐, 이벤트 로그 관리
- **Hermes 백엔드** — Hermes Agent 연동 시 LLM 기반 이벤트 분류 (선택)
- 상태바 알바 상태 아이콘 (🟢 활성 / ⚪ 비활성 / 🔴 오류)

## 아직 실험적인 부분

- 새 방 품질은 제공하거나 생성한 이미지 품질에 따라 달라지며 시각 QA가 필요합니다.
- 첫 방 만들기는 아직 GUI editor가 아니라 스크립트 기반입니다.
- Codex 연동은 로컬 file/hook bridge이며 공식 Codex dashboard API가 아닙니다.
- Windows가 주 테스트 환경입니다.
- 내부 저장소에는 호환성을 위해 일부 `project-room-*` 파일명이 남아 있습니다.
- Hermes 백엔드는 Hermes Agent 별도 설치 필요 (없으면 규칙 기반으로 폴백).

현재 포함되지 않은 것: multi-room gallery, cloud sync, team dashboard, macOS/Linux widget host, full simulation/game behavior, 팀 자기 개선 루프.

## 방 만들기

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py `
  --project-id my-room `
  --pet-package "$env:USERPROFILE\.codex\pets\my-pet" `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

생성 후 setup check와 local QA evidence를 만듭니다.

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id my-room
.\tools\pet_studio_widget.cmd --project-id my-room --scale 1.25
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

전체 흐름: [docs/CREATE_ROOM.md](docs/CREATE_ROOM.md)

## 룸 프리셋

zip 파일로 방을 내보내고 가져올 수 있습니다:

```
위젯 우클릭 → Preset → Export preset
위젯 우클릭 → Preset → Import preset
```

Python으로도 가능:

```python
from alba.preset import export_preset, import_preset
from pathlib import Path

export_preset(Path("runs/my-room"), Path("presets/my-room.zip"), "내 방")
import_preset(Path("presets/my-room.zip"), Path("runs/my-room-imported"))
```

## 알바 상태 관리자

Pet Studio에는 `alba`라는 팀 오케스트레이션 레이어가 포함되어 있습니다:

```python
from alba.state import TeamState

ts = TeamState()
ts.alba_status = "active"
ts.register_project("my-project", "내 프로젝트")
ts.enqueue_project("my-project", {"task": "lint"})
ts.log_event("my-project", {"type": "build", "status": "pass"})
```

백엔드:
- **ScriptBackend** — 규칙 기반, LLM 없음 (기본)
- **HermesBackend** — Hermes Agent 연동 LLM (선택)

## 한국어 CLI 출력

기본 CLI 출력은 영어입니다. 사람이 읽는 실패/복구 안내만 한국어로 보고 싶으면 `--lang ko` 또는 `PET_STUDIO_LANG=ko`를 사용하세요.

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --lang ko
```

JSON key, error code, command flag, path, id는 번역하지 않습니다.

## 데모 상태 순환

README GIF나 수동 QA를 찍을 때:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

상태 파일을 쓰지 않고 payload만 확인하려면 `--dry-run`을 붙이세요.

## 로드맵

장기 방향은 모든 Codex workspace가 알아보기 쉬운 방, 상태, 분위기를 갖는 것입니다.

v0.5.0에서 완료:
- 룸 프리셋 내보내기/가져오기 (zip)
- 스크립트 전용 상태 관리자 (`alba/state.py`)
- Hermes 백엔드 (`alba/backend/hermes.py`)
- 상태바 알바 상태 아이콘
- 컨텍스트 메뉴 프리셋 서브메뉴

v0.6.0 목표:
- 팀 오케스트레이션 UI
- 팀 자기 개선 (Hermes memory/skill 참고)

자세한 로드맵: [docs/PET_STUDIO_ROADMAP.md](docs/PET_STUDIO_ROADMAP.md)
장기 Workroom 비전: [docs/PET_STUDIO_WORKROOM_VISION.ko.md](docs/PET_STUDIO_WORKROOM_VISION.ko.md)

## 문서

- [Install](docs/INSTALL.md)
- [Create a room](docs/CREATE_ROOM.md)
- [Codex integration](docs/CODEX_INTEGRATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Core / adapter boundary](docs/ADAPTER_BOUNDARY.md)
- [Development checks](docs/DEVELOPMENT.md)
- [Long-term workroom vision](docs/PET_STUDIO_WORKROOM_VISION.ko.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [English README](README.md)

## License

MIT. See [LICENSE](LICENSE).
