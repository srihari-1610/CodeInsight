"""Gemini client tests using mocked responses."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.llm import AnalysisError, GeminiClient


def _valid_analysis():
    return {
        "algorithm": "One-pass Algorithm",
        "category": "Searching",
        "tags": ["test"],
        "summary": "Mock analysis result",
        "line_blocks": [],
        "complexity": {
            "time": "O(n)",
            "space": "O(1)",
            "explanation": "Test explanation",
        },
        "optimizations": [],
        "pitfalls": [],
        "quality": {
            "score": 90,
            "label": "Good",
            "explanation": "Test quality",
        },
    }


def test_gemini_response_is_parsed():
    expected = _valid_analysis()

    with patch("core.llm.genai.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(expected)
        )

        client = GeminiClient(api_key="test-key")
        result = client.complete("Analyze sample code")

        assert result == expected
        mock_instance.models.generate_content.assert_called_once()


def test_empty_gemini_response_raises_friendly_error():
    with patch("core.llm.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = (
            SimpleNamespace(text=None)
        )

        client = GeminiClient(api_key="test-key")

        with pytest.raises(AnalysisError, match="empty response"):
            client.complete("Analyze sample code")


def test_invalid_json_raises_analysis_error():
    with patch("core.llm.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = (
            SimpleNamespace(text="not valid JSON")
        )

        client = GeminiClient(api_key="test-key")

        with pytest.raises(AnalysisError, match="Gemini analysis failed"):
            client.complete("Analyze sample code")


def test_missing_api_key_raises_error():
    with patch("core.llm.settings") as mock_settings:
        mock_settings.gemini_api_key = ""

        with pytest.raises(AnalysisError, match="API key is missing"):
            GeminiClient()