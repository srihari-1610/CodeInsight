"""Live-client logic tested against a stubbed SDK response (no network, no key)."""
from types import SimpleNamespace

import pytest

from core.analyzer import AnalysisRequest, analyze
from core.llm import AnalysisError, AnthropicClient
from core.samples import SAMPLES
from core.schemas import TOOL_NAME


class _Messages:
    def __init__(self, response):
        self.response, self.kwargs = response, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def _client(response):
    c = AnthropicClient(api_key="test-key", model="test-model")
    c._client = SimpleNamespace(messages=_Messages(response))
    return c


def _req():
    s = SAMPLES[0]
    return AnalysisRequest(code=s["code"], language=s["language"])


def test_forced_tool_use_is_parsed_and_request_shape_is_correct():
    resp = SimpleNamespace(stop_reason="tool_use", content=[
        SimpleNamespace(type="text", text="ignored"),
        SimpleNamespace(type="tool_use", name=TOOL_NAME, input=SAMPLES[0]["demo"]),
    ])
    client = _client(resp)
    result = analyze(_req(), client)
    sent = client._client.messages.kwargs
    assert sent["tool_choice"] == {"type": "tool", "name": TOOL_NAME}
    assert "<code" in sent["messages"][0]["content"] and "  1: import sys" in sent["messages"][0]["content"]
    assert result.mode == "live" and result.analysis.algorithm.startswith("One-pass")


def test_truncated_response_gives_friendly_error():
    with pytest.raises(AnalysisError, match="cut off"):
        analyze(_req(), _client(SimpleNamespace(stop_reason="max_tokens", content=[])))


def test_missing_tool_block_gives_friendly_error():
    resp = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="hi")])
    with pytest.raises(AnalysisError, match="no structured analysis"):
        analyze(_req(), _client(resp))
