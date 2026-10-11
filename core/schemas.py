"""Typed result objects + the JSON schema the model must fill (via forced tool use)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOOL_NAME = "report_analysis"
IMPACT_LEVELS = ["high", "medium", "low"]
PITFALL_KINDS = ["overflow", "edge_case", "off_by_one", "io", "recursion", "memory", "tle", "other"]


def _obj(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required}


TOOL_SCHEMA: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": "Return the complete structured analysis of the submitted solution.",
    "input_schema": _obj(
        {
            "algorithm": {"type": "string", "description": "Short name, e.g. 'Dijkstra with binary heap'."},
            "category": {
                "type": "string",
                "description": "Graphs, DP, Greedy, Math, Strings, Data Structures, Searching, Sorting, Implementation...",
            },
            "tags": {"type": "array", "items": {"type": "string"}, "description": "2-5 lowercase tags."},
            "summary": {"type": "string", "description": "2-4 sentences: the approach and why it is correct."},
            "line_blocks": {
                "type": "array",
                "description": "Ordered, non-overlapping blocks covering the meaningful lines of the code.",
                "items": _obj(
                    {
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                        "explanation": {"type": "string"},
                        "key_insight": {"type": "string", "description": "Optional one-liner, empty if none."},
                    },
                    ["start_line", "end_line", "explanation"],
                ),
            },
            "complexity": _obj(
                {
                    "time": {"type": "string", "description": "e.g. 'O(n log n)'"},
                    "space": {"type": "string"},
                    "ops_expression": {
                        "type": "string",
                        "description": "Arithmetic expression in n, m, k using + - * / ** ( ) log2() sqrt() only.",
                    },
                    "variables": {
                        "type": "object",
                        "description": "Meaning of n, m, k for this program; use '-' for unused ones.",
                        "properties": {
                            "n": {"type": "string"},
                            "m": {"type": "string"},
                            "k": {"type": "string"},
                        },
                    },
                    "derivation": {"type": "string", "description": "Step-by-step reasoning."},
                    "best_case": {"type": "string"},
                    "worst_case": {"type": "string"},
                },
                ["time", "space", "ops_expression", "derivation"],
            ),
            "optimizations": {
                "type": "array",
                "items": _obj(
                    {
                        "title": {"type": "string"},
                        "bottleneck": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "tradeoff": {"type": "string"},
                        "impact": {"type": "string", "enum": IMPACT_LEVELS},
                        "optimized_code": {"type": "string", "description": "Complete code or empty string."},
                    },
                    ["title", "bottleneck", "suggestion", "tradeoff", "impact"],
                ),
            },
            "pitfalls": {
                "type": "array",
                "items": _obj(
                    {
                        "kind": {"type": "string", "enum": PITFALL_KINDS},
                        "description": {"type": "string"},
                        "line": {"type": "integer", "description": "Relevant line or 0 if general."},
                    },
                    ["kind", "description"],
                ),
            },
            "quality": _obj(
                {
                    "clarity_score": {"type": "integer", "description": "1-10"},
                    "naming_feedback": {"type": "string"},
                    "structure_feedback": {"type": "string"},
                    "tips": {"type": "array", "items": {"type": "string"}},
                },
                ["clarity_score", "naming_feedback", "structure_feedback"],
            ),
        },
        ["algorithm", "category", "tags", "summary", "line_blocks", "complexity", "optimizations", "pitfalls", "quality"],
    ),
}


@dataclass
class LineBlock:
    start_line: int
    end_line: int
    explanation: str
    key_insight: str = ""


@dataclass
class Complexity:
    time: str = ""
    space: str = ""
    ops_expression: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    derivation: str = ""
    best_case: str = ""
    worst_case: str = ""


@dataclass
class Optimization:
    title: str
    bottleneck: str = ""
    suggestion: str = ""
    tradeoff: str = ""
    impact: str = "medium"
    optimized_code: str = ""


@dataclass
class Pitfall:
    kind: str
    description: str
    line: int | None = None


@dataclass
class Quality:
    clarity_score: int = 5
    naming_feedback: str = ""
    structure_feedback: str = ""
    tips: list[str] = field(default_factory=list)


@dataclass
class Analysis:
    algorithm: str
    category: str
    tags: list[str]
    summary: str
    line_blocks: list[LineBlock]
    complexity: Complexity
    optimizations: list[Optimization]
    pitfalls: list[Pitfall]
    quality: Quality


# ---------------------------------------------------------------- parsing
def _s(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _i(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def parse_analysis(raw: dict[str, Any]) -> Analysis:
    """Tolerant conversion of model output (or stored JSON) into typed objects."""
    if not isinstance(raw, dict):
        raise ValueError("Analysis payload must be an object")

    cx = raw.get("complexity") if isinstance(raw.get("complexity"), dict) else {}
    variables = cx.get("variables") if isinstance(cx.get("variables"), dict) else {}
    q = raw.get("quality") if isinstance(raw.get("quality"), dict) else {}

    blocks = [
        LineBlock(
            start_line=_i(b.get("start_line"), 1),
            end_line=_i(b.get("end_line"), _i(b.get("start_line"), 1)),
            explanation=_s(b.get("explanation")),
            key_insight=_s(b.get("key_insight")),
        )
        for b in _list(raw.get("line_blocks"))
        if isinstance(b, dict)
    ]
    opts = [
        Optimization(
            title=_s(o.get("title")) or "Optimization",
            bottleneck=_s(o.get("bottleneck")),
            suggestion=_s(o.get("suggestion")),
            tradeoff=_s(o.get("tradeoff")),
            impact=_s(o.get("impact")).lower() if _s(o.get("impact")).lower() in IMPACT_LEVELS else "medium",
            optimized_code=_s(o.get("optimized_code")),
        )
        for o in _list(raw.get("optimizations"))
        if isinstance(o, dict)
    ]
    pits = [
        Pitfall(
            kind=_s(p.get("kind")) if _s(p.get("kind")) in PITFALL_KINDS else "other",
            description=_s(p.get("description")),
            line=_i(p.get("line")) or None,
        )
        for p in _list(raw.get("pitfalls"))
        if isinstance(p, dict) and _s(p.get("description"))
    ]
    return Analysis(
        algorithm=_s(raw.get("algorithm")) or "Unidentified",
        category=_s(raw.get("category")) or "General",
        tags=[_s(t).lower() for t in _list(raw.get("tags")) if _s(t)][:6],
        summary=_s(raw.get("summary")),
        line_blocks=blocks,
        complexity=Complexity(
            time=_s(cx.get("time")),
            space=_s(cx.get("space")),
            ops_expression=_s(cx.get("ops_expression")),
            variables={str(k): _s(v) for k, v in variables.items()},
            derivation=_s(cx.get("derivation")),
            best_case=_s(cx.get("best_case")),
            worst_case=_s(cx.get("worst_case")),
        ),
        optimizations=opts,
        pitfalls=pits,
        quality=Quality(
            clarity_score=max(1, min(10, _i(q.get("clarity_score"), 5))),
            naming_feedback=_s(q.get("naming_feedback")),
            structure_feedback=_s(q.get("structure_feedback")),
            tips=[_s(t) for t in _list(q.get("tips")) if _s(t)],
        ),
    )
