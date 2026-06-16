"""Minimal user-facing localization helpers for Pet Studio CLIs."""

from __future__ import annotations

import os
import sys
from typing import Any

SUPPORTED_LANGS = {"en", "ko"}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def normalize_lang(value: str | None = None) -> str:
    raw = (value or os.environ.get("PET_STUDIO_LANG") or "en").strip().lower()
    if raw.startswith("ko"):
        return "ko"
    if raw.startswith("en"):
        return "en"
    return "en"


def is_korean(value: str | None = None) -> bool:
    return normalize_lang(value) == "ko"


GUARDRAIL_MESSAGES_KO = {
    "room-size": "방 이미지 크기가 올바르지 않습니다",
    "room-missing": "방 이미지 파일을 찾을 수 없습니다",
    "prop-read": "prop 이미지를 읽을 수 없습니다",
    "prop-size": "prop 이미지가 방 캔버스보다 큽니다",
    "prop-empty": "prop 이미지에 보이는 픽셀이 없습니다",
    "duplicate-prop-id": "prop id가 중복되었습니다",
    "duplicate-helper-id": "helper id가 중복되었습니다",
    "asset-id-collision": "prop과 helper가 같은 asset id를 사용합니다",
    "reserved-asset-id": "예약된 asset id입니다",
    "unsafe-asset-id": "asset id가 생성 파일 경로에 안전하지 않습니다",
    "unsafe-placement-id": "prop 배치 id가 생성 파일 경로에 안전하지 않습니다",
    "prop-placement-format": "prop 배치 형식이 올바르지 않습니다",
    "unknown-prop-placement": "prop 배치가 존재하지 않는 prop id를 참조합니다",
    "invalid-prop-placement": "알 수 없는 prop 배치 값입니다",
    "helper-pet-json": "helper 패키지에 pet.json이 없습니다",
    "helper-spritesheet": "helper 패키지의 spritesheet 경로가 올바르지 않습니다",
    "helper-atlas-size": "helper atlas 크기가 올바르지 않습니다",
    "main-pet-json": "main pet 패키지에 pet.json이 없습니다",
    "main-pet-spritesheet": "main pet 패키지의 spritesheet 경로가 올바르지 않습니다",
    "main-pet-atlas-size": "main pet atlas 크기가 올바르지 않습니다",
}


GUARDRAIL_REPAIRS_KO = {
    "room-size": "384x240 PNG 방 이미지를 제공하세요. 생성 후 임의로 자르거나 크기를 바꾸지 마세요.",
    "room-missing": "384x240 방 PNG 파일을 제공하세요.",
    "prop-read": "유효한 투명 PNG prop 파일을 제공하세요.",
    "prop-size": "prop을 줄이거나 여러 개로 나눈 뒤 다시 실행하세요.",
    "prop-empty": "빈 레이어가 아니라 보이는 prop 픽셀이 있는 투명 PNG를 내보내세요.",
    "duplicate-prop-id": "각 prop에 고유한 id를 사용하세요.",
    "duplicate-helper-id": "각 helper pet에 고유한 id를 사용하세요.",
    "asset-id-collision": "prop 또는 helper 중 하나의 asset id를 바꾸세요.",
    "reserved-asset-id": "desk, plant, reviewer 같은 사용자 정의 id를 사용하세요.",
    "unsafe-asset-id": "영문자, 숫자, 밑줄, 하이픈만 사용하고 첫 글자는 영문자나 숫자로 시작하세요.",
    "unsafe-placement-id": "일치하는 --prop 인자와 같은 slug 형식 id를 사용하세요.",
    "prop-placement-format": "desk=behind-pet 또는 desk=foreground 형식으로 입력하세요.",
    "unknown-prop-placement": "일치하는 --prop id=path 인자를 추가하거나 해당 배치 설정을 제거하세요.",
    "invalid-prop-placement": "허용되는 값: background, behind-pet, front-of-pet, foreground.",
    "helper-pet-json": "pet.json과 spritesheet.webp가 있는 hatch-pet 패키지 디렉터리를 전달하세요.",
    "helper-spritesheet": "pet.json의 spritesheetPath를 확인하거나 helper 패키지에 spritesheet.webp를 추가하세요.",
    "helper-atlas-size": "표준 hatch-pet atlas를 다시 생성하거나 올바른 helper 패키지를 제공하세요.",
    "main-pet-json": "기존 hatch-pet 패키지 디렉터리를 전달하세요.",
    "main-pet-spritesheet": "pet.json의 spritesheetPath를 확인하세요.",
    "main-pet-atlas-size": "표준 hatch-pet 패키지를 사용하세요.",
}


def guardrail_issue_message(issue: dict[str, Any], lang: str | None = None) -> str:
    if not is_korean(lang):
        return str(issue.get("message", "")).rstrip().rstrip(".!?")
    code = str(issue.get("code", ""))
    translated = GUARDRAIL_MESSAGES_KO.get(code)
    if translated:
        return translated
    return str(issue.get("message", "")).rstrip().rstrip(".!?")


def guardrail_issue_repair(issue: dict[str, Any], lang: str | None = None) -> str | None:
    if not issue.get("repair"):
        return None
    if not is_korean(lang):
        return str(issue["repair"])
    return GUARDRAIL_REPAIRS_KO.get(str(issue.get("code", "")), str(issue["repair"]))


def guardrail_header(lang: str | None = None) -> str:
    return "자산 가드레일 검사 실패:" if is_korean(lang) else "Asset guardrails failed:"


def repair_label(lang: str | None = None) -> str:
    return "해결:" if is_korean(lang) else "Fix:"


def unsafe_project_id_message(project_id: str, lang: str | None = None) -> str:
    if is_korean(lang):
        return (
            f"프로젝트 id `{project_id}`는 생성 파일 경로에 안전하지 않습니다. "
            "영문자, 숫자, 밑줄, 하이픈만 사용하고 첫 글자는 영문자나 숫자로 시작하세요."
        )
    return (
        f"Project id `{project_id}` is not safe for generated file paths. "
        "Use letters, numbers, underscore, and hyphen only; start with a letter or number."
    )


def preflight_message(name: str, message: str, lang: str | None = None) -> str:
    if not is_korean(lang):
        return message
    if name == "registry":
        if "must contain a projects list" in message or "must contain a JSON object" in message:
            return f"registry 구조가 올바르지 않습니다. 해결: {message}"
        if "is not registered" in message:
            return f"프로젝트가 registry에 등록되어 있지 않습니다. 해결: {message}"
        if "Missing registry" in message:
            return f"registry 파일을 찾을 수 없습니다. 해결: {message}"
        if "disabled" in message:
            return f"프로젝트가 비활성화되어 있습니다. 해결: {message}"
    if name == "project-kit":
        if "has no kitPath" in message:
            return f"프로젝트에 kitPath가 없습니다. 해결: {message}"
        if "Missing project manifest" in message:
            return f"project-room.json을 찾을 수 없습니다. 해결: {message}"
    if name == "python" and "Pillow is missing" in message:
        return f"Pillow가 설치되어 있지 않습니다. 해결: {message}"
    if name == "hooks" and "Missing" in message:
        return f"Codex hook 설정이 없습니다. 해결: {message}"
    return message


def preflight_heading(key: str, lang: str | None = None) -> str:
    if not is_korean(lang):
        return {
            "launch": "Project launch command:",
            "render": "Render output:",
            "hook": "Hook trust hint:",
            "log": "Recent hook log:",
        }[key]
    return {
        "launch": "프로젝트 실행 명령:",
        "render": "렌더 출력:",
        "hook": "Hook 신뢰 확인 안내:",
        "log": "최근 hook 로그:",
    }[key]
