# 🧠 CodeInsight - AI Code Explainer for Competitive Programmers

Paste a Python / C++ / Java solution and get a line-by-line explanation, time & space complexity with
derivation, a **TLE-risk estimate for your constraints**, optimization ideas and pitfalls.
Built with **Python + Streamlit + Anthropic Claude API** (no Flask, no separate backend).

## What makes it different
| Feature | How it works |
|---|---|
| **Constraint-aware TLE check** | The model returns an operation-count formula (e.g. `(n + m) * log2(m + 2)`); a *sandboxed AST evaluator* plugs in your n, m, k and time limit and compares against a per-language ops/sec budget. Change constraints live, no new API call. |
| **Local static cross-check (no AI)** | `ast` (Python) and a brace scanner (C++/Java) compute loop-nesting depth, recursion and sort usage, and warn when they contradict the AI's complexity claim. |
| **Structured output** | Forced tool use with a JSON schema, so there is no fragile text parsing. |
| **Demo mode** | 3 built-in samples with pre-written analyses; works with no API key or internet. |
| **History + cache** | SQLite stores every analysis; an identical request is served from cache (zero API cost). |
| **Export** | Download the report as Markdown or JSON. |

The submitted code is only ever read as text; it is **never executed**.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY (optional: Demo mode needs none)
streamlit run app.py
```
Run the tests: `python -m pytest -q`

Deploy free on **Streamlit Community Cloud**: push to GitHub, create the app, and add
`ANTHROPIC_API_KEY = "..."` under *Secrets*.

## Architecture
```
Streamlit UI (app.py)
  │  code + language + constraints
  ▼
validators.py ──► analyzer.py ──► history.py (SQLite cache) ─ hit ─► result
                     │ miss
                     ▼
         prompts.py (untrusted-data wrapped, line-numbered)
                     ▼
         llm.py: Anthropic API (forced tool call → JSON)   |   DemoClient (offline)
                     ▼
         schemas.py (tolerant parse) → sanitise line refs
                     ▼
   static_analysis.py + complexity.py (safe eval, TLE verdict, cross-check)
                     ▼
         Tabs: Overview · Line by line · Complexity & TLE · Optimizations · Pitfalls · Export
```

## Project layout
```
app.py                 Streamlit UI
core/config.py         env / Streamlit-secrets settings
core/validators.py     input checks, language detection
core/prompts.py        system + user prompt builders
core/llm.py            Anthropic client + offline Demo client
core/schemas.py        tool JSON schema, dataclasses, tolerant parser
core/analyzer.py       orchestration, caching, sanitising
core/static_analysis.py  AST / brace-scanner heuristics
core/complexity.py     safe expression evaluator, TLE verdict
core/history.py        SQLite store
core/report.py         Markdown / JSON export
core/samples.py        built-in samples + demo analyses
tests/                 39 tests (logic, pipeline, stubbed live client, headless UI)
```

## Configuration
| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | - | Live mode (or paste it in the sidebar) |
| `CODEINSIGHT_MODEL` | `claude-sonnet-5-5` | Any Claude model id |
| `CODEINSIGHT_DB` | `data/history.db` | History / cache file |

## Limitations
- Complexity and optimizations come from an LLM and can be wrong; the static cross-check and TLE estimate are heuristics, not proofs.
- TLE budget assumes ~1e7 (Python), 5e7 (Java), 1e8 (C++) simple ops/sec.
- Single-file solutions, up to 400 lines / 12,000 characters; Python, C++ and Java only.
- Demo mode only works for the 3 bundled samples.

## Future scope
Codeforces/AtCoder problem-URL import · run the code against sample tests in a sandbox · more languages ·
complexity-vs-runtime benchmarking · fine-tuned model on accepted solutions · multi-user auth.

## Mapping to the LB1 report template
| Template section | Where in this project |
|---|---|
| 1-2 Introduction / Problem | This README ("What makes it different") |
| 5 Methodology | `core/analyzer.py` flow + Architecture above |
| 6 Architecture diagram | Architecture block above |
| 7 Implementation | `core/prompts.py` (prompt template), `core/llm.py` (API call), `core/schemas.py` |
| 8 Screenshots | Run the app; capture each tab after loading a sample |
| 9 Challenges | Malformed model output → schema + tolerant parser; wrong line refs → sanitiser; unsafe formula → AST whitelist |
