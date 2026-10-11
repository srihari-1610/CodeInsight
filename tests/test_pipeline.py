import pytest

from core.analyzer import AnalysisRequest, analyze
from core.history import HistoryStore
from core.llm import AnalysisError, DemoClient
from core.report import to_json, to_markdown
from core.samples import SAMPLES
from core.schemas import parse_analysis
from core.validators import detect_language, validate_submission


def _request(sample):
    return AnalysisRequest(code=sample["code"], language=sample["language"], problem=sample["problem"],
                           n_max=sample["n_max"], m_max=sample["m_max"], k_max=sample["k_max"],
                           time_limit=sample["time_limit"])


def test_parse_analysis_is_tolerant():
    a = parse_analysis({"algorithm": "X", "line_blocks": [{"start_line": "2", "explanation": "hi"}, "junk"],
                        "quality": {"clarity_score": 99}, "pitfalls": [{"kind": "weird", "description": "d", "line": "0"}]})
    assert a.line_blocks[0].end_line == 2
    assert a.quality.clarity_score == 10
    assert a.pitfalls[0].kind == "other" and a.pitfalls[0].line is None
    with pytest.raises(ValueError):
        parse_analysis("not a dict")


def test_every_demo_sample_analyses_and_caches(tmp_path):
    store = HistoryStore(tmp_path / "h.db")
    for sample in SAMPLES:
        first = analyze(_request(sample), DemoClient(), store)
        assert not first.from_cache and first.id
        assert first.analysis.line_blocks
        total = sample["code"].count("\n") + 1
        assert all(1 <= b.start_line <= b.end_line <= total for b in first.analysis.line_blocks)
        again = analyze(_request(sample), DemoClient(), store)
        assert again.from_cache and again.analysis == first.analysis
        assert "# CodeInsight report" in to_markdown(first)
        assert to_json(first).startswith("{")
    assert len(store.list_recent()) == len(SAMPLES)


def test_demo_mode_rejects_custom_code():
    with pytest.raises(AnalysisError):
        analyze(AnalysisRequest(code="print(1)", language="Python"), DemoClient())


def test_history_crud(tmp_path):
    store = HistoryStore(tmp_path / "h.db")
    rid = store.save(request_hash="h", language="Python", title="T", model="m", mode="demo", payload={"a": 1})
    assert store.get(rid)["payload"] == {"a": 1}
    assert store.find_by_hash("h")["id"] == rid
    store.delete(rid)
    assert store.get(rid) is None


def test_validation_and_detection():
    assert detect_language("#include <bits/stdc++.h>\nint main(){}") == "C++"
    assert detect_language("def f(x):\n    return x\n") == "Python"
    assert detect_language("public class A { public static void main(String[] a){} }") == "Java"
    assert not validate_submission("", "Python", 100, 10).ok
    assert not validate_submission("x" * 200, "Python", 100, 10).ok
    assert any("syntax error" in w for w in validate_submission("def (:", "Python", 100, 10).warnings)
    assert any("looks like" in w for w in validate_submission("#include <x>\nint main(){}", "Python", 1000, 10).warnings)
