"""Provider-agnostic LLM client abstractions for annotation analyzers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request

from maana_ingest.config import Settings


class AnnotationClientError(RuntimeError):
    """Raised when the configured annotation client cannot complete a request."""


@dataclass(frozen=True)
class AnnotationRequest:
    analyzer_name: str
    prompt_version: str
    system_prompt: str
    user_prompt: str


class AnnotationLLMClient(Protocol):
    """Protocol shared by live and mock annotation clients."""

    provider_name: str
    model_name: str

    def annotate_json(self, request: AnnotationRequest) -> dict[str, Any]:
        """Return a JSON-serializable payload for a specialized analyzer."""


class MockAnnotationLLMClient:
    """Deterministic mock client used for tests and offline architecture checks."""

    provider_name = "mock"

    def __init__(self, *, model_name: str = "mock-annotation-model") -> None:
        self.model_name = model_name

    def annotate_json(self, request: AnnotationRequest) -> dict[str, Any]:
        if request.analyzer_name == "couplet_detector":
            return {"couplets": []}
        if request.analyzer_name == "quran_detector":
            return {"verses": []}
        if request.analyzer_name == "hadith_detector":
            return {"hadiths": []}
        if request.analyzer_name == "poet_detector":
            return {"poets": []}
        if request.analyzer_name == "persian_detector":
            return {"passages": []}
        if request.analyzer_name == "citation_resolver":
            return {"citations": []}
        raise AnnotationClientError(f"Unsupported analyzer for mock client: {request.analyzer_name}")


class OpenAICompatibleAnnotationLLMClient:
    """Minimal OpenAI-compatible JSON client for annotation analyzers."""

    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def annotate_json(self, request_data: AnnotationRequest) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": request_data.system_prompt},
                {"role": "user", "content": request_data.user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            request_headers["Authorization"] = f"Bearer {self._api_key}"

        http_request = request.Request(
            url=f"{self._base_url}/chat/completions",
            data=body,
            headers=request_headers,
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AnnotationClientError(
                f"Annotation request failed for provider {self.provider_name}"
            ) from exc

        try:
            content = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AnnotationClientError(
                f"Annotation response was not in the expected OpenAI-compatible format for {self.provider_name}"
            ) from exc

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AnnotationClientError(
                f"Annotation response did not contain valid JSON for provider {self.provider_name}"
            ) from exc


class AnnotationClientFactory:
    """Construct configured annotation clients from runtime settings."""

    _DEFAULT_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": "http://localhost:11434/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    }

    @classmethod
    def from_settings(cls, settings: Settings) -> AnnotationLLMClient:
        provider = settings.annotation_provider.strip().lower()
        if provider == "mock":
            return MockAnnotationLLMClient(model_name=settings.annotation_model)

        base_url = settings.annotation_base_url or cls._DEFAULT_BASE_URLS.get(provider)
        if not base_url:
            raise AnnotationClientError(f"Unsupported annotation provider: {settings.annotation_provider}")

        return OpenAICompatibleAnnotationLLMClient(
            provider_name=provider,
            model_name=settings.annotation_model,
            base_url=base_url,
            api_key=settings.annotation_api_key or settings.openai_api_key,
            timeout_seconds=settings.annotation_timeout_seconds,
        )
