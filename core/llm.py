"""Gemini Live Mode and built-in Demo Mode clients."""

from __future__ import annotations

import json
from typing import Any, Protocol

from google import genai
from google.genai import types

from core.config import settings
from core.schemas import TOOL_SCHEMA
from core.samples import SAMPLES


class AnalysisError(Exception):
    """Raised when code analysis fails."""


class LLMClient(Protocol):
    model: str
    mode: str

    def complete(
        self,
        request: Any,
        system_prompt: str = "",
        user_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        ...


class GeminiClient:
    """Use Gemini to analyse submitted code."""

    mode = "live"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key

        if not key:
            raise AnalysisError(
                "Gemini API key is missing. Configure GEMINI_API_KEY in .env."
            )

        self.model = model or settings.gemini_model
        self.client = genai.Client(api_key=key)

    def complete(
        self,
        request: Any,
        system_prompt: str = "",
        user_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        if user_prompt is None:
            user_prompt = str(request)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt or None,
                    response_mime_type="application/json",
                    response_json_schema=TOOL_SCHEMA["input_schema"],
                    temperature=0.2,
                    max_output_tokens=max_tokens,
                ),
            )

            if not response.text:
                raise AnalysisError(
                    "Gemini returned an empty response. Please try again."
                )

            result = json.loads(response.text)

            if not isinstance(result, dict):
                raise AnalysisError(
                    "Gemini returned an unexpected response format."
                )

            return result

        except AnalysisError:
            raise
        except Exception as exc:
            raise AnalysisError(
                f"Gemini analysis failed: {exc}"
            ) from exc


class DemoClient:
    """Provide pre-written analysis for built-in samples without an API key."""

    mode = "demo"
    model = "built-in-demo"

    def complete(
        self,
        request: Any,
        system_prompt: str = "",
        user_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        code = (
            request.code
            if hasattr(request, "code")
            else str(request)
        )
        code = code.replace("\r\n", "\n").strip()

        for sample in SAMPLES:
            sample_code = sample["code"].replace("\r\n", "\n").strip()

            if code == sample_code:
                result = sample.get("demo")

                if not isinstance(result, dict):
                    raise AnalysisError(
                        "The built-in sample analysis is unavailable."
                    )

                return json.loads(json.dumps(result))

        raise AnalysisError(
            "Demo mode only analyses built-in sample code. "
            "Select a built-in sample or configure a Gemini API key "
            "to analyse custom code in Live Mode."
        )


def get_client(
    live: bool = True,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
) -> LLMClient:
    """Return the client for the selected application mode."""

    if not live:
        return DemoClient()

    return GeminiClient(
        api_key=api_key,
        model=model,
        timeout=timeout,
    )