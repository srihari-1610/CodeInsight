"""CodeInsight - AI code explainer for competitive programmers (Streamlit UI)."""
from __future__ import annotations

import re

import altair as alt
import pandas as pd
import streamlit as st

from core.analyzer import AnalysisRequest, AnalysisResult, analyze, result_from_payload
from core.complexity import (
    ExpressionError,
    cross_check,
    estimate_ops,
    format_number,
    growth_exponent,
    growth_series,
    judge,
)
from core.config import load_settings
from core.history import HistoryStore
from core.llm import AnalysisError, get_client
from core.prompts import AUDIENCE_GUIDE, DETAIL_GUIDE
from core.report import to_json, to_markdown
from core.samples import SAMPLES
from core.validators import SUPPORTED_LANGUAGES, detect_language, validate_submission

LANG_ID = {"Python": "python", "C++": "cpp", "Java": "java"}
AUTO = "Auto-detect"
PLACEHOLDER = "- choose a sample -"
KIND_ICON = {"overflow": "🔢", "edge_case": "🧩", "off_by_one": "↔️", "io": "⌨️", "recursion": "🔁",
             "memory": "💾", "tle": "⏱️", "other": "⚠️"}
IMPACT_ICON = {"high": "🔴", "medium": "🟠", "low": "🟢"}

DEFAULTS = {
    "code": "", "language_choice": AUTO, "problem": "", "n_max": 100_000, "m_max": 100_000, "k_max": 1,
    "time_limit": 1.0, "audience": "Intermediate", "detail": "Standard", "sample_choice": PLACEHOLDER,
    "result": None,
}

CSS = """
<style>
textarea[aria-label="Paste your solution"] {
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
    font-size: 0.88rem !important;
}
.block-container { padding-top: 2rem; }
</style>
"""


# ------------------------------------------------------------------ state helpers
def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def apply_request(req: AnalysisRequest) -> None:
    st.session_state.update(
        code=req.code, language_choice=req.language, problem=req.problem, n_max=req.n_max,
        m_max=req.m_max, k_max=req.k_max, time_limit=req.time_limit,
    )


def set_result(result: AnalysisResult | None) -> None:
    st.session_state.result = result
    if result is not None:
        r = result.request
        st.session_state.update(est_n=r.n_max, est_m=r.m_max, est_k=r.k_max, est_tl=r.time_limit)


def on_sample_change() -> None:
    choice = st.session_state.sample_choice
    sample = next((s for s in SAMPLES if s["title"] == choice), None)
    if sample is None:
        return
    apply_request(AnalysisRequest(
        code=sample["code"], language=sample["language"], problem=sample["problem"], n_max=sample["n_max"],
        m_max=sample["m_max"], k_max=sample["k_max"], time_limit=sample["time_limit"],
    ))
    set_result(None)


def load_history(store: HistoryStore, analysis_id: int) -> None:
    row = store.get(analysis_id)
    if row:
        result = result_from_payload(row)
        apply_request(result.request)
        set_result(result)


def delete_history(store: HistoryStore, analysis_id: int) -> None:
    store.delete(analysis_id)


# ------------------------------------------------------------------ sidebar
def render_sidebar(settings, store: HistoryStore) -> tuple[bool, str, str]:
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        mode = st.radio(
            "Mode", ["Live (Gemini API)", "Demo (built-in samples)"], index=0 if settings.api_key else 1,
            help="Demo mode serves pre-written analyses for the 3 samples - no key or internet needed.",
        )
        live = mode.startswith("Live")
        api_key, model = settings.api_key, settings.model
        if live:
            if not settings.api_key:
                api_key = st.text_input("Gemini API key", type="password", help="Kept in memory for this session only.")
            model = st.text_input("Model", value=settings.model)
        st.selectbox("Explanation level", list(AUDIENCE_GUIDE), key="audience", help="Who the explanation is written for.")
        st.selectbox("Detail", list(DETAIL_GUIDE), key="detail")

        st.divider()
        st.markdown("### 🕘 History")
        rows = store.list_recent(8)
        if not rows:
            st.caption("Nothing analysed yet.")
        for row in rows:
            c1, c2 = st.columns([5, 1])
            c1.button(f"{row['title'][:26]} · {row['language']}", key=f"hist_{row['id']}",
                      on_click=load_history, args=(store, row["id"]))
            c2.button("🗑", key=f"del_{row['id']}", on_click=delete_history, args=(store, row["id"]), help="Delete")
        st.divider()
        st.caption("Your code is analysed as text only. It is never executed.")
    return live, api_key, model


# ------------------------------------------------------------------ input form
def render_inputs() -> bool:
    st.selectbox("Try a sample", [PLACEHOLDER] + [s["title"] for s in SAMPLES], key="sample_choice",
                 on_change=on_sample_change)
    left, right = st.columns([3, 2], gap="large")
    with left:
        upload = st.file_uploader("…or upload a source file", type=["py", "cpp", "cc", "cxx", "java", "txt"],
                                  label_visibility="collapsed")
        if upload is not None and st.session_state.get("_last_upload") != upload.file_id:
            st.session_state["_last_upload"] = upload.file_id
            st.session_state.code = upload.getvalue().decode("utf-8", errors="replace")
            ext = upload.name.rsplit(".", 1)[-1].lower()
            st.session_state.language_choice = {"py": "Python", "java": "Java"}.get(ext, "C++" if ext in {"cpp", "cc", "cxx"} else AUTO)
            set_result(None)
            st.rerun()
        st.text_area("Paste your solution", key="code", height=380, placeholder="Paste a Python / C++ / Java solution here…")
    with right:
        st.selectbox("Language", [AUTO] + SUPPORTED_LANGUAGES, key="language_choice")
        st.text_area("Problem statement (optional, improves accuracy)", key="problem", height=150)
        st.markdown("**Constraints** (used for the TLE estimate)")
        c1, c2, c3 = st.columns(3)
        c1.number_input("n", min_value=1, max_value=10**12, step=1, key="n_max", help="Primary input size")
        c2.number_input("m", min_value=1, max_value=10**12, step=1, key="m_max", help="Second dimension: edges, queries…")
        c3.number_input("k", min_value=1, max_value=10**12, step=1, key="k_max", help="Third dimension, if any")
        st.number_input("Time limit (seconds)", min_value=0.1, max_value=30.0, step=0.5, format="%.1f", key="time_limit")
    return st.button("🔍 Analyze code", type="primary", key="analyze")


def resolve_language() -> str | None:
    choice = st.session_state.language_choice
    return detect_language(st.session_state.code) if choice == AUTO else choice


def run_analysis(settings, store, live, api_key, model) -> None:
    language = resolve_language()
    if language is None:
        st.error("Couldn't detect the language. Pick Python, C++ or Java from the Language box.")
        return
    validation = validate_submission(st.session_state.code, language, settings.max_code_chars, settings.max_code_lines)
    for warning in validation.warnings:
        st.warning(warning)
    if not validation.ok:
        for err in validation.errors:
            st.error(err)
        return

    request = AnalysisRequest(
        code=st.session_state.code, language=language, problem=st.session_state.problem,
        n_max=int(st.session_state.n_max), m_max=int(st.session_state.m_max), k_max=int(st.session_state.k_max),
        time_limit=float(st.session_state.time_limit), audience=st.session_state.audience, detail=st.session_state.detail,
    )
    try:
        client = get_client(live, api_key, model, settings.request_timeout)
        with st.spinner("Analyzing your code…"):
            result = analyze(request, client, store)
    except AnalysisError as exc:
        st.error(str(exc))
        return
    set_result(result)


# ------------------------------------------------------------------ result renderers
def quick_verdict(result: AnalysisResult):
    r = result.request
    try:
        ops = estimate_ops(result.analysis.complexity.ops_expression, r.n_max, r.m_max, r.k_max)
        return judge(ops, r.time_limit, r.language)
    except ExpressionError:
        return None


def render_overview(result: AnalysisResult) -> None:
    a = result.analysis
    verdict = quick_verdict(result)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Algorithm", a.algorithm)
    c2.metric("Time", a.complexity.time or "-")
    c3.metric("Space", a.complexity.space or "-")
    c4.metric("TLE check", verdict.label if verdict else "n/a")
    if result.mode == "demo":
        st.info("Demo result: pre-written analysis for a built-in sample. Use Live mode for your own code.")
    elif result.from_cache:
        st.caption("Loaded from history (no API call was made).")
    st.markdown(f"**Category:** {a.category}  \n**Tags:** " + (" · ".join(f"`{t}`" for t in a.tags) or "-"))
    st.markdown("#### Approach")
    st.write(a.summary)
    st.caption(f"{result.model} · {result.mode} · {result.elapsed:.1f}s")


def render_lines(result: AnalysisResult) -> None:
    code_lines = result.request.code.split("\n")
    lang = LANG_ID.get(result.request.language, None)
    if not result.analysis.line_blocks:
        st.info("No line-by-line blocks were returned.")
    for b in result.analysis.line_blocks:
        with st.container(border=True):
            left, right = st.columns(2, gap="medium")
            span = f"Line {b.start_line}" if b.start_line == b.end_line else f"Lines {b.start_line}–{b.end_line}"
            left.caption(span)
            left.code("\n".join(code_lines[b.start_line - 1 : b.end_line]), language=lang)
            right.markdown(b.explanation)
            if b.key_insight:
                right.info(f"💡 {b.key_insight}")


def render_growth_chart(expr: str, n: int, m: int, k: int, budget: float) -> None:
    series = growth_series(expr, n, m, k)
    if not series:
        return
    frame = pd.DataFrame(series, columns=["input size (n)", "operations"])
    frame["series"] = "Estimated operations"
    limit = frame[["input size (n)"]].copy()
    limit["operations"] = budget
    limit["series"] = "Budget for time limit"
    data = pd.concat([frame, limit], ignore_index=True)
    lines = alt.Chart(data).mark_line().encode(
        x=alt.X("input size (n):Q", scale=alt.Scale(type="log")),
        y=alt.Y("operations:Q", scale=alt.Scale(type="log")),
        color=alt.Color("series:N", legend=alt.Legend(orient="bottom", title=None)),
    )
    marker = alt.Chart(pd.DataFrame({"input size (n)": [n]})).mark_rule(strokeDash=[4, 4], color="#999").encode(
        x="input size (n):Q"
    )
    st.altair_chart((lines + marker).properties(width="container", height=300))


def render_complexity(result: AnalysisResult) -> None:
    cx, req, static = result.analysis.complexity, result.request, result.static
    c1, c2 = st.columns(2)
    c1.metric("Time complexity", cx.time or "-")
    c2.metric("Space complexity", cx.space or "-")
    st.caption(f"Operation model: `{cx.ops_expression or 'n/a'}`")
    legend = ", ".join(f"{k} = {v}" for k, v in cx.variables.items() if v and v != "-")
    if legend:
        st.caption(f"Variables: {legend}")
    st.markdown("#### Derivation")
    st.write(cx.derivation or "-")
    if cx.best_case:
        st.markdown(f"**Best case:** {cx.best_case}")
    if cx.worst_case:
        st.markdown(f"**Worst case:** {cx.worst_case}")

    st.divider()
    st.markdown("#### ⏱️ TLE risk estimator")
    st.caption("Change the constraints to see how the solution scales - no new API call needed.")
    e1, e2, e3, e4 = st.columns(4)
    n = e1.number_input("n", min_value=1, max_value=10**12, step=1, key="est_n")
    m = e2.number_input("m", min_value=1, max_value=10**12, step=1, key="est_m")
    k = e3.number_input("k", min_value=1, max_value=10**12, step=1, key="est_k")
    tl = e4.number_input("Time limit (s)", min_value=0.1, max_value=30.0, step=0.5, format="%.1f", key="est_tl")
    exponent = None
    try:
        ops = estimate_ops(cx.ops_expression, n, m, k)
    except ExpressionError as exc:
        st.warning(f"Couldn't evaluate `{cx.ops_expression}`: {exc}")
    else:
        v = judge(ops, tl, req.language)
        exponent = growth_exponent(cx.ops_expression, n, m, k)
        a1, a2, a3 = st.columns(3)
        a1.metric("Estimated operations", format_number(v.ops))
        a2.metric(f"Budget ({req.language})", format_number(v.budget))
        a3.metric("Load", "∞" if v.ratio == float("inf") else f"{v.ratio * 100:,.0f}%")
        if v.level == "safe":
            st.success("Comfortably within the limit.")
        elif v.level == "borderline":
            st.warning("Borderline: constant factors or a slow judge could push this over the limit.")
        else:
            st.error("Likely Time Limit Exceeded at these constraints. See the Optimizations tab.")
        st.caption(f"Assumes ~{v.ops_per_sec:.0e} simple operations/second for {req.language}. A heuristic, not a guarantee.")
        render_growth_chart(cx.ops_expression, int(n), int(m), int(k), v.budget)

    st.divider()
    st.markdown("#### 🔎 Local static cross-check (no AI)")
    if static.parse_error:
        st.warning(f"Could not parse the code ({static.parse_error}).")
        return
    s1, s2, s3 = st.columns(3)
    s1.metric("Max loop nesting", static.loop_depth if static.loop_depth is not None else "-")
    s2.metric("Recursive functions", ", ".join(static.recursive_functions) or "none")
    s3.metric("Sort calls", static.sort_calls)
    mismatch = cross_check(static.loop_depth, exponent, bool(static.recursive_functions), static.sort_calls)
    if mismatch:
        st.warning(mismatch)
    elif exponent is not None:
        st.success("Loop nesting is consistent with the reported complexity.")
    for note in static.notes:
        st.markdown(f"- {note}")


def render_optimizations(result: AnalysisResult) -> None:
    opts = result.analysis.optimizations
    if not opts:
        st.success("No significant optimizations found - the approach looks appropriate.")
    lang = LANG_ID.get(result.request.language, None)
    for o in opts:
        with st.expander(f"{IMPACT_ICON.get(o.impact, '🟠')} {o.title}  ·  {o.impact} impact", expanded=o.impact == "high"):
            st.markdown(f"**Bottleneck:** {o.bottleneck}")
            st.markdown(f"**Suggestion:** {o.suggestion}")
            st.markdown(f"**Trade-off:** {o.tradeoff}")
            if o.optimized_code:
                st.code(o.optimized_code, language=lang)


def render_quality(result: AnalysisResult) -> None:
    a = result.analysis
    st.markdown("#### Pitfalls")
    if not a.pitfalls:
        st.success("No pitfalls flagged.")
    for p in a.pitfalls:
        where = f" (line {p.line})" if p.line else ""
        st.markdown(f"{KIND_ICON.get(p.kind, '⚠️')} **{p.kind.replace('_', ' ')}**{where}: {p.description}")
    st.markdown("#### Code quality")
    q = a.quality
    st.progress(q.clarity_score / 10, text=f"Clarity score: {q.clarity_score}/10")
    st.markdown(f"**Naming:** {q.naming_feedback}")
    st.markdown(f"**Structure:** {q.structure_feedback}")
    for tip in q.tips:
        st.markdown(f"- {tip}")


def render_export(result: AnalysisResult) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", result.analysis.algorithm.lower()).strip("-") or "analysis"
    md = to_markdown(result)
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Download report (.md)", md, file_name=f"codeinsight-{slug}.md", mime="text/markdown")
    c2.download_button("⬇️ Download data (.json)", to_json(result), file_name=f"codeinsight-{slug}.json", mime="application/json")
    with st.expander("Preview report"):
        st.markdown(md)


def render_result(result: AnalysisResult) -> None:
    tabs = st.tabs(["Overview", "Line by line", "Complexity & TLE", "Optimizations", "Pitfalls & quality", "Export"])
    for tab, fn in zip(tabs, [render_overview, render_lines, render_complexity, render_optimizations, render_quality, render_export]):
        with tab:
            fn(result)


# ------------------------------------------------------------------ main
def main() -> None:
    st.set_page_config(page_title="CodeInsight", page_icon="🧠", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    settings = load_settings()
    store = HistoryStore(settings.db_path)
    live, api_key, model = render_sidebar(settings, store)

    st.title("🧠 CodeInsight")
    st.caption("Paste a competitive-programming solution → line-by-line explanation, complexity, TLE check and optimizations.")
    if render_inputs():
        run_analysis(settings, store, live, api_key, model)

    result = st.session_state.get("result")
    if result is not None:
        st.divider()
        render_result(result)


main()
