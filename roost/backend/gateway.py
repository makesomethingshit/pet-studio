"""OpenAI-compatible gateway backend for local proxy adapters."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from roost.auth_config import apply_auth_config_env
from roost.model_profile import build_model_profile_env

logger = logging.getLogger(__name__)


class GatewayBackend:
    """Call a local OpenAI-compatible gateway directly.

    This is intentionally small: it targets local proxies such as the user's
    Fusion proxy and avoids depending on a Hermes CLI launcher.
    """

    name = "gateway"

    def __init__(self, timeout: int = 30) -> None:
        env = apply_auth_config_env()
        self.gateway_url = (
            env.get("HERMES_GATEWAY_URL")
            or env.get("HERMES_BASE_URL")
            or "http://127.0.0.1:8787/v1"
        ).rstrip("/")
        self.gateway_token = env.get("HERMES_GATEWAY_TOKEN", "")
        self.timeout = timeout
        self.model_profile: dict[str, Any] | None = None

    def set_model_profile(self, profile: dict[str, Any]) -> None:
        self.model_profile = dict(profile)

    def _env(self) -> dict[str, str]:
        return build_model_profile_env(self.model_profile)

    def _model(self) -> str:
        env = self._env()
        profile_model = str((self.model_profile or {}).get("model", "")).strip()
        return profile_model or env.get("PET_STUDIO_MODEL") or "fusion"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = self._env().get("HERMES_GATEWAY_TOKEN") or self.gateway_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _post_chat(self, prompt: str) -> str | None:
        payload = {
            "model": self._model(),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.gateway_url}/chat/completions",
            data=body,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            logger.warning("Gateway request failed: %s", error)
            return None
        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            return None
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        return str(content).strip() if content is not None else None

    def classify_event(
        self,
        event: dict[str, Any],
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prompt = (
            "Classify this event by priority (high/normal/low). Reply with ONE word only.\n"
            f"Event: {json.dumps(event, ensure_ascii=False)}"
        )
        output = self._post_chat(prompt)
        priority = self._parse_priority(output)
        if priority:
            event["classification"] = {"priority": priority, "source": "gateway"}
        else:
            event["classification"] = {"priority": "normal", "source": "gateway (no response)"}
        return event

    def health_check(self) -> bool:
        request = urllib.request.Request(f"{self.gateway_url}/models", headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return 200 <= int(getattr(response, "status", 200)) < 500
        except (OSError, urllib.error.URLError):
            return False

    @staticmethod
    def _parse_priority(output: str | None) -> str | None:
        text = (output or "").strip().lower()
        for word in ("high", "normal", "low"):
            if word in text:
                return word
        return None

    def deliver_packet(self, packet: dict[str, Any]) -> dict[str, Any]:
        output = self._post_chat(
            "Execute this Pet Studio Work Packet:\n"
            f"{json.dumps(packet, ensure_ascii=False, indent=2)}"
        )
        return {
            "agent": "gateway",
            "status": "delivered" if output else "failed",
            "output": output or "(no output)",
        }

    def __repr__(self) -> str:
        return f"<GatewayBackend name={self.name}>"
