# fpa-bench design

## What this benchmark measures

How well an LLM (or an agentic harness wrapping one) performs the core quantitative and
communication work of a corporate FP&A / strategic finance team: variance analysis, driver-based
forecasting, three-statement modeling, liquidity forecasting, SaaS/unit economics, capital
allocation, model review, and board-level narrative.

Per the landscape research (docs/RESEARCH.md), this space is essentially unbenchmarked as of
mid-2026: existing finance benchmarks are SEC-filings QA, sell-side research agents, or generic
spreadsheet manipulation. Corporate *planning* work — plan-vs-actual, forward-looking,
private-company-data — is the gap, and "harness as an experimental variable" (raw chat API vs
code-execution agent) is nearly untouched.

## Core design decisions

1. **Synthetic, seeded data. No real-world data anywhere.**
   Every task's inputs AND answer key are produced by `bench/generators.py` from a seed.
   - Contamination-proof: regenerate with `--seed N` to mint a fresh, never-published instance.
   - Ground truth is computed by code from the data exactly as written to disk (post-rounding),
     never hand-authored.
   - Precedent: FinBalance (arXiv 2606.15949) and FinSheet-Bench (2603.07316) validated this
     pattern for finance.

2. **Two run modes on identical tasks — the harness axis.**
   - `chat`: CSVs are inlined into the prompt. Tests raw model reasoning + arithmetic.
   - `agent`: CSVs are staged as files in a temp workdir; an agentic harness (e.g. Claude Code
     via `cli/claude-code`) can inspect them and write/execute code.
   The chat-vs-agent delta on the *same* tasks is the headline result.

3. **Deterministic grading first; judge only where unavoidable.**
   - 11 of 12 tasks: the model must emit a JSON object with specified field names; each field is
     graded with per-field relative/absolute tolerance (default ±0.5% rel), weighted, partial
     credit. Formatted numbers ("$1,234", "(450)", "42.5%") are normalized before comparison.
   - 1 task (board memo): rubric-based LLM judge, fed the ground-truth facts computed by the
     generator so it can check numeric claims. Judge model is pinned per run (`--judge`).
   - Prompts pin down methodology conventions explicitly (PVM formulas, NDR basis, payback
     interpolation) so the benchmark tests *execution*, not convention-guessing. Where real FP&A
     work involves convention ambiguity, that's a deliberate non-goal for v0.

4. **Structural invariants as free correctness signals.**
   The test suite asserts the identities every task's answer key must satisfy: PVM components sum
   to total variance, FX + organic = total variance, balance sheet balances, IRR zeroes the NPV.
   The same invariants are stated in prompts as self-checks for the model.

5. **Every answer key is independently verified.**
   `tests/test_answer_keys.py` re-derives all answers from the CSVs on disk with solvers written
   separately from the generators. `python -m bench validate` runs them. A generator bug can't
   silently ship a wrong key.

## Task inventory (v0 — 12 tasks)

| Task | Category | Difficulty | Grading |
|---|---|---|---|
| variance-pvm-001 | variance_analysis | medium | numeric (6 fields) |
| budget-variance-fx-001 | variance_analysis | medium | numeric (6) |
| three-statement-001 | financial_modeling | hard | numeric (9) |
| thirteen-week-cash-001 | cash_forecasting | hard | numeric (6) |
| forecast-revrec-001 | forecasting | hard | numeric (10) |
| saas-metrics-001 | saas_metrics | medium | numeric (8) |
| cohort-retention-001 | cohort_analysis | medium | numeric (6) |
| capital-allocation-001 | corporate_finance | medium | numeric (7) |
| unit-economics-001 | unit_economics | medium | numeric (5) |
| working-capital-001 | working_capital | easy | numeric (5) |
| error-detection-001 | review_and_controls | medium | numeric (6) |
| board-memo-001 | strategic_narrative | medium | LLM judge (20-pt rubric) |

## Scoring

- Task score = weighted fraction of correct fields (partial credit).
- Overall = unweighted mean of task scores. Report per-category means and hardest-task table.
- `--trials N` reruns each task; results JSONL keeps every trial for pass@k analysis later.
- Latency and token usage are captured per call where the API reports them.

## Architecture

```
fpa-bench/
  bench/
    schema.py       task definition + prompt rendering (chat/agent)
    generators.py   seeded data + answer-key generation (source of truth)
    graders.py      JSON extraction, tolerance grading, LLM judge
    adapters.py     Anthropic API / OpenAI-compatible (incl. OpenRouter) / CLI harness
    runner.py       orchestration, per-trial JSONL results
    report.py       leaderboard + hardest-tasks aggregation
    __main__.py     CLI: generate | validate | list | show | run | report
  tasks/<id>/       task.json, prompt.md, data/*.csv, answer_key.json
  tests/            independent answer-key solvers + grader/runner unit tests
  results/          run outputs (JSONL) + REPORT.md
  docs/RESEARCH.md  benchmark landscape survey (July 2026)
```

The runner is dependency-free stdlib Python. This is deliberate for v0: trivially portable, no
framework lock-in. The research recommends **Inspect AI** (UK AISI) as the long-term execution
engine — migrating means writing an Inspect `Task` per task.json and reusing the same generators
and tolerance scorers (see NEXT_STEPS.md).

## Known limitations of v0 (deliberate scope cuts)

- Single instance per task template. The generator supports arbitrary seeds, but a proper eval
  should sample k instances per template and report variance across seeds.
- No spreadsheet-artifact grading (model returns JSON, not an .xlsx). The SpreadsheetBench-style
  "grade the produced workbook, re-run with perturbed inputs to catch hardcoding" pattern is the
  v1 upgrade path for agent mode.
- Judge is not yet validated against human labels (1 judged task; MBABench used 408 expert
  annotations for calibration).
- No multi-turn / rolling-forecast tasks ("assumptions changed, update your forecast") — the most
  FP&A-authentic format and completely unbenchmarked; needs a stateful harness.
- Conventions are fully specified in prompts; ambiguity-handling (a real FP&A skill) is untested.
