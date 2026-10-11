"""LLM provider layer: Anthropic (live, forced tool use => structured JSON) and an offline Demo client."""
from __future__ import annotations

import copy
from typing import Protocol

from .samples import find_sample
from .schemas import TOOL_NAME, TOOL_SCHEMA


class AnalysisError(Exception):
    """User-presentable failure while producing an analysis."""


class LLMClient(Protocol):
    model: str
    mode: str

    def complete(self, request, system: str, user: str, max_tokens: int) -> dict: ...


class AnthropicClient:
    mode = "live"

    def __init__(self, api_key: str, model: str, timeout: float = 90.0):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise AnalysisError("The 'anthropic' package is not installed. Run: pip install -r requirements.txt") from exc
        self._sdk = anthropic
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)

    def complete(self, request, system: str, user: str, max_tokens: int) -> dict:
        sdk = self._sdk
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[TOOL_SCHEMA],
                tool_choice={"type": "tool", "name": TOOL_NAME},
            )
        except sdk.AuthenticationError as exc:
            raise AnalysisError("The API key was rejected. Check ANTHROPIC_API_KEY.") from exc
        except sdk.RateLimitError as exc:
            raise AnalysisError("Rate limit reached. Wait a moment and try again.") from exc
        except sdk.APIConnectionError as exc:
            raise AnalysisError("Could not reach the Anthropic API. Check your internet connection.") from exc
        except sdk.APIStatusError as exc:
            raise AnalysisError(f"API error ({exc.status_code}): {exc.message}") from exc

        if resp.stop_reason == "max_tokens":
            raise AnalysisError("The response was cut off. Try 'Concise' detail or a shorter snippet.")
        for block in resp.content:
            if getattr(block, "type", "") == "tool_use" and block.name == TOOL_NAME:
                return dict(block.input)
        raise AnalysisError("The model returned no structured analysis. Please try again.")


class DemoClient:
    """Serves pre-written analyses for the built-in samples only (no network, no key)."""

    mode = "demo"
    model = "demo-fixtures"

    def complete(self, request, system: str, user: str, max_tokens: int) -> dict:
        sample = find_sample(request.code, request.language)
        if sample is None:
            raise AnalysisError(
                "Demo mode only analyses the built-in samples (pick one under 'Try a sample'). "
                "Switch to Live mode and add an API key to analyse your own code."
            )
        return copy.deepcopy(sample["demo"])


def get_client(live: bool, api_key: str, model: str, timeout: float = 90.0) -> LLMClient:
    if not live:
        return DemoClient()
    if not api_key:
        raise AnalysisError("No API key found. Add one in the sidebar or switch to Demo mode.")
    return AnthropicClient(api_key=api_key, model=model, timeout=timeout)
