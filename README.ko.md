# Pet Studio

[English README](README.md)

**Codex 프로젝트마다 작은 데스크톱 방을 붙입니다.**

Pet Studio는 Codex 작업 상태를 작은 방, 펫, 소품, 말풍선으로 보여주는 로컬 우선 데스크톱 위젯입니다.

![Pet Studio project room reacting with a pet, props, helper creature, and speech bubble](docs/images/pet-studio-demo.gif)

로그를 계속 보는 대신, 프로젝트 방이 작업 시작, 도구 사용, 차단, 리뷰, 완료 상태에 맞춰 반응하는 모습을 볼 수 있습니다.

## 빠른 시작

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

## 현재 가능한 것

- Windows 데스크톱 위젯으로 샘플 프로젝트 방 실행
- 배경, 소품, 메인 펫, 보조 펫, 말풍선의 레이어 렌더링
- 로컬 프로젝트 registry, layout 저장, scale 저장, state file bridge
- 수동 상태: `running`, `waiting`, `review`, `blocked`, `failed`, `done`
- 선택적 Codex hook으로 prompt/tool/compact/stop 이벤트를 말풍선에 반영
- 스크립트 기반 방 생성, asset guardrails, validation, preview sheet, local QA pack

## 아직 실험적인 부분

- 새 방 품질은 제공하거나 생성한 이미지 품질에 따라 달라지며 시각 QA가 필요합니다.
- 첫 방 만들기는 아직 GUI editor가 아니라 스크립트 기반입니다.
- Codex 연동은 로컬 file/hook bridge이며 공식 Codex dashboard API가 아닙니다.
- Windows가 주 테스트 환경입니다.
- 내부 저장소에는 호환성을 위해 일부 `project-room-*` 파일명이 남아 있습니다.

현재 포함되지 않은 것: multi-room gallery, one-click installer, cloud sync, team dashboard, macOS/Linux widget host, full simulation/game behavior.

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

## 한국어 CLI 출력

기본 CLI 출력은 영어입니다. 사람이 읽는 실패/복구 안내만 한국어로 보고 싶으면 `--lang ko` 또는 `PET_STUDIO_LANG=ko`를 사용하세요.

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --lang ko
```

JSON key, error code, command flag, path, id는 번역하지 않습니다. 자동화가 깨지지 않도록 machine-readable 출력은 영어 구조를 유지합니다.

## 로드맵

장기 방향은 모든 Codex workspace가 알아보기 쉬운 방, 상태, 분위기, companion behavior를 갖는 것입니다. 이는 현재 기능이 아니라 미래 방향입니다.

자세한 로드맵: [docs/PET_STUDIO_ROADMAP.md](docs/PET_STUDIO_ROADMAP.md)

장기 Workroom 비전: [docs/PET_STUDIO_WORKROOM_VISION.ko.md](docs/PET_STUDIO_WORKROOM_VISION.ko.md)

## 문서

- [Install](docs/INSTALL.md)
- [Create a room](docs/CREATE_ROOM.md)
- [Codex integration](docs/CODEX_INTEGRATION.md)
- [Development checks](docs/DEVELOPMENT.md)
- [Long-term workroom vision](docs/PET_STUDIO_WORKROOM_VISION.ko.md)
- [English README](README.md)

## License

MIT. See [LICENSE](LICENSE).
