"""Headless smoke test of the Streamlit UI (Demo mode, no network)."""
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")

os.environ.pop("ANTHROPIC_API_KEY", None)


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEINSIGHT_DB", str(tmp_path / "ui.db"))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return AppTest.from_file(APP, default_timeout=60).run()

def test_app_loads_without_errors(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch)
    assert not at.exception
    assert at.title[0].value.endswith("CodeInsight")


def test_sample_flow_renders_all_tabs(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch)
    at.selectbox(key="sample_choice").select("Longest Increasing Subsequence O(n^2) - C++").run()
    assert "scanf" in at.text_area(key="code").value
    at.button(key="analyze").click().run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 6
    # The quadratic LIS at n = 1e5 must be flagged, and nothing else may be an error.
    errors = [e.value for e in at.error]
    assert errors and all("Likely Time Limit Exceeded" in v for v in errors), errors


def test_custom_code_in_demo_mode_shows_friendly_error(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch)
    at.text_area(key="code").set_value("print(1)").run()
    at.button(key="analyze").click().run()
    assert not at.exception
    assert any("Demo mode only analyses" in e.value for e in at.error)
