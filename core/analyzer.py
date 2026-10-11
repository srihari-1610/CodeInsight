"""Orchestration: validate -> (cache) -> prompt -> model -> parse -> sanitise -> static cross-check."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from .history import HistoryStore
from .llm import AnalysisError, LLMClient
from .prompts import MAX_TOKENS, SYSTEM_PROMPT, build_user_prompt
from .schemas import Analysis, parse_analysis
from .static_analysis import StaticReport, analyze_static


@dataclass
class AnalysisRequest:
    code: str
    language: str
    problem: str = ""
    n_max: int = 100_000
    m_max: int = 100_000
    k_max: int = 1
    time_limit: float = 1.0
    audience: str = "Intermediate"
    detail: str = "Standard"


@dataclass
class AnalysisResult:
    request: AnalysisRequest
    analysis: Analysis
    static: StaticReport
    model: str
    mode: str
    elapsed: float = 0.0
    from_cache: bool = False
    id: int | None = None
    created_at: str = ""


def normalise_request(req: AnalysisRequest) -> AnalysisRequest:
    return replace(req, code=req.code.replace("\r\n", "\n").rstrip())


def request_hash(req: AnalysisRequest, model: str, mode: str) -> str:
    blob = json.dumps({**asdict(req), "model": model, "mode": mode}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sanitise(analysis: Analysis, total_lines: int) -> Analysis:
    """Clamp line references to the real code and drop empty blocks."""
    blocks = []
    for b in analysis.line_blocks:
        if not b.explanation:
            continue
        s = max(1, min(b.start_line, total_lines))
        e = max(1, min(b.end_line, total_lines))
        if s > e:
            s, e = e, s
        blocks.append(replace(b, start_line=s, end_line=e))
    analysis.line_blocks = sorted(blocks, key=lambda b: (b.start_line, b.end_line))
    for p in analysis.pitfalls:
        if p.line is not None and not (1 <= p.line <= total_lines):
            p.line = None
    return analysis


def result_from_payload(row: dict[str, Any], from_cache: bool = False) -> AnalysisResult:
    payload = row["payload"]
    req = AnalysisRequest(**payload["request"])
    return AnalysisResult(
        request=req,
        analysis=parse_analysis(payload["analysis"]),
        static=analyze_static(req.code, req.language),
        model=row["model"],
        mode=row["mode"],
        elapsed=float(payload.get("elapsed", 0.0)),
        from_cache=from_cache,
        id=row["id"],
        created_at=row["created_at"],
    )


def analyze(
    request: AnalysisRequest,
    client: LLMClient,
    store: HistoryStore | None = None,
    use_cache: bool = True,
) -> AnalysisResult:
    request = normalise_request(request)
    key = request_hash(request, client.model, client.mode)

    if store is not None and use_cache:
        cached = store.find_by_hash(key)
        if cached:
            return result_from_payload(cached, from_cache=True)

    started = time.perf_counter()
    raw = client.complete(request, SYSTEM_PROMPT, build_user_prompt(request), MAX_TOKENS[request.detail])
    try:
        analysis = parse_analysis(raw)
    except ValueError as exc:
        raise AnalysisError("The model returned an unexpected format. Please try again.") from exc
    analysis = _sanitise(analysis, request.code.count("\n") + 1)
    if not analysis.line_blocks and not analysis.summary:
        raise AnalysisError("The model returned an empty analysis. Please try again.")
    elapsed = time.perf_counter() - started

    result = AnalysisResult(
        request=request,
        analysis=analysis,
        static=analyze_static(request.code, request.language),
        model=client.model,
        mode=client.mode,
        elapsed=elapsed,
    )
    if store is not None:
        payload = {"request": asdict(request), "analysis": asdict(analysis), "elapsed": elapsed}
        result.id = store.save(
            request_hash=key,
            language=request.language,
            title=analysis.algorithm,
            model=client.model,
            mode=client.mode,
            payload=payload,
        )
    return result
