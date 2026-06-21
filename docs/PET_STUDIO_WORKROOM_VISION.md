# Pet Studio Vision

## One-Line Vision

> AI를 모르는 사람도 AI팀을 부릴 수 있다.

Pet Studio는 **비전공자를 위한 로컬 AI 작업방**입니다. 사용자는 프로젝트를 고르고 미션을 입력합니다. Pet Studio는 연결된 Codex, Hermes, OpenRouter, gateway, script fallback 같은 실행자를 역할에 맞게 호출하고, 진행 상태를 Workroom과 pet widget에서 보여줍니다.

**Pet은 장식용 캐릭터가 아니라 AI팀의 상태 companion입니다.** 작은 방 안에서 지금 팀이 쉬는지, 일하는지, 막혔는지, 끝냈는지를 바로 보여줍니다. Widget은 보기만 하는 장식이 아니라 빠른 mission 입력入口도 됩니다.

**포지셔닝:** 기능은 남들 뒤에서 따라가도 된다. 사용자가 첫 미션을 던지고 현재 흐름을 이해하는 속도는 앞서야 한다.

## 첫 사용 기준

비전공자는 설치 후 30초 안에 다음 흐름을 끝낼 수 있어야 합니다.

1. Pet Studio를 연다.
2. 프로젝트를 선택하거나 기본 프로젝트를 쓴다.
3. 미션을 입력한다.
4. AI가 연결되어 있으면 실행하고, 없으면 script fallback으로 흐름을 체험한다.
5. 현재 상태와 다음 행동을 한 화면에서 확인한다.

## 핵심 가치

### 1. 체험은 즉시, 연결은 한 단계

- 처음부터 모델, 엔드포인트, 토큰을 이해할 필요가 없어야 합니다.
- 실제 AI 연결은 OpenRouter/Codex/Hermes/gateway 중 하나를 고르는 짧은 setup으로 끝나야 합니다.
- 연결 전에는 로컬 fallback으로 UI와 작업 흐름을 먼저 볼 수 있어야 합니다.

### 2. 미션 중심

- 기본 화면의 주인공은 프로젝트, 미션, task board입니다.
- Team Room, Endpoints, Model Profiles, role routing은 고급 설정입니다.
- 사용자는 "어떤 모델을 고를까"보다 "무슨 일을 시킬까"를 먼저 보아야 합니다.

### 3. 역할은 자동, 비용은 통제

- 미션은 Scout, Coordinator, Lead 같은 역할로 나뉠 수 있습니다.
- 가벼운 일은 저렴한 route, 중요한 일은 강한 route로 보내는 것이 기본값입니다.
- "무료"를 약속하지 않습니다. 사용자가 자기 키와 route로 비용을 통제하게 합니다.

### 4. 한눈에 보이는 상태

- Workroom은 mission, task, result, failure reason을 한 화면에서 보여줍니다.
- Widget은 작게 떠서 현재 흐름을 계속 보여줍니다.
- 로그를 뒤지지 않아도 "지금 무엇이 진행 중이고 왜 멈췄는지" 알 수 있어야 합니다.

### 5. 안전한 실행

- 읽기, 쓰기, 삭제, 배포 같은 위험도를 사용자 말로 보여줍니다.
- 위험한 작업은 확인 없이 실행하지 않습니다.
- 프로젝트별 보안 레벨은 고급 사용자를 위한 설정으로 남깁니다.

## 타겟 유저

- AI 도구를 쓰고 싶지만 어떤 모델을 골라야 할지 모르는 개인 제작자
- 여러 AI를 오가며 쓰는 것이 귀찮은 사용자
- 코드를 직접 읽지는 못해도 AI에게 작업을 맡기고 싶은 사용자
- 비용을 통제하면서 자기 API 키로 AI를 쓰고 싶은 사용자

## Pet Studio가 아닌 것

- AI 모델 자체가 아닙니다. GPT, Claude, local model을 대체하지 않습니다.
- 코드를 직접 수행하는 모델이 아닙니다. 실행자는 Codex/Hermes/OpenRouter/gateway 같은 adapter입니다.
- 호스팅 서비스가 아닙니다. 기본은 로컬 앱입니다.
- 게임이나 자율 시뮬레이션이 아닙니다.

## 제품 원칙

- Daily 화면은 mission/status/tasks만 둡니다.
- Advanced 안에 Team Room, Endpoints, Model Profiles를 둡니다.
- `project-room-*` runtime 파일명과 CLI 호환은 유지합니다.
- Roost는 특정 실행자에 묶이지 않습니다. Adapter는 교체 가능해야 합니다.
