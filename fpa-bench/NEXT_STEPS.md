# Next steps (written overnight, 2026-07-17)

## What exists now

- **A working benchmark** (`fpa-bench/`): 12 FP&A tasks, seeded synthetic data + code-computed
  answer keys, chat vs agent run modes, deterministic tolerance grading + one LLM-judged memo
  task, adapters for Anthropic / OpenAI-compatible / OpenRouter APIs and CLI agent harnesses,
  results JSONL + leaderboard reporting. 26 tests; every answer key is re-derived by independent
  solvers (`python -m bench validate`).
- **Landscape research** (`docs/RESEARCH.md`): what exists, gaps, framework recommendations.
  Headline: corporate FP&A is essentially unbenchmarked; harness-as-a-variable is nearly
  untouched; nearest neighbors are MBABench, FinBalance, BlueFin.
- **A first baseline** (`results/`): all 12 tasks run through Claude (Fable 5) subagents in two
  conditions — "chat" (reasoning only, no code) and "agent" (Python allowed). Scores: **0.97
  chat / 1.00 agent**. The only chat failure was NPV precision on capital-allocation-001
  (~1.4% off from hand-rounded discount factors — exactly the failure mode the chat/agent axis
  is meant to expose).
  - *Caveats*: this baseline used session subagents (with extended reasoning), not the raw API
    adapters — treat it as a harness smoke-test + a saturation warning, not a leaderboard entry.

## The saturation warning (most important design takeaway)

A frontier model with reasoning nearly saturates v0. That's expected — v0 prompts fully specify
every convention, and data sizes are small. The benchmark will differentiate on weaker/faster
models and on precision, but to keep headroom for frontier models you'll want the hardening
levers in §3 below. Decide early whether the target is "differentiate frontier models" (harden)
or "measure the chat→agent harness gap across the model spectrum" (current design already does
this well).

## 1. Tomorrow morning: real runs (30–60 min)

1. `cd fpa-bench && pip install -r requirements.txt && python -m bench validate`
2. Export keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and/or `OPENROUTER_API_KEY`
   (OpenRouter alone covers Gemini/Llama/DeepSeek/etc.).
3. Run the matrix (see `models.json` → `suggested_matrix`):
   ```bash
   python -m bench run --model anthropic/claude-haiku-4-5-20251001 --mode chat --judge anthropic/claude-opus-4-8
   python -m bench run --model anthropic/claude-sonnet-5 --mode chat --judge anthropic/claude-opus-4-8
   python -m bench run --model openai/gpt-5.2 --mode chat --judge anthropic/claude-opus-4-8
   python -m bench run --model openrouter/google/gemini-3-pro --mode chat --judge anthropic/claude-opus-4-8
   python -m bench run --model cli/claude-code --mode agent --judge anthropic/claude-opus-4-8
   python -m bench report
   ```
   Start with Haiku — a small model's scores will show whether the tasks discriminate.
4. `--trials 3` on anything you care about (results keep every trial for pass@k later).

## 2. Decisions for you (I made provisional calls — review them)

- **Tolerances**: default ±0.5% relative. The NPV miss suggests this is a *feature* (punishes
  sloppy arithmetic) but you may want a looser "directionally right" tier reported alongside.
- **Conventions fully specified in prompts** (PVM formulas, NDR basis, payback interpolation).
  Alternative: a harder "ambiguous" variant where choosing a defensible convention and stating
  it is part of the task (judge-graded). Real FP&A skill, but noisier grading.
- **Scoring**: per-field partial credit, equal task weighting. Alternatives: all-or-nothing per
  task (harsher, more discriminating), difficulty weighting.
- **Judge model**: pick and pin one (suggest opus-4-8) and note it in every report.

## 3. Hardening levers (to keep frontier headroom)

- **Scale the data**: 10× the invoice/transaction row counts — chat-mode arithmetic degrades
  with volume (FinSheet-Bench saw 82%→49% as workbooks grew).
- **Multi-instance**: run each template at 5+ seeds and report mean±CI
  (`python -m bench generate --seed N` already works; runner needs a small loop).
- **Harder task variants**: multi-year three-statement with a revolver (circularity), PVM with
  new/discontinued SKUs, 13-week cash with collections uncertainty bands, cohort data with
  messy/duplicate records (data-hygiene-first), scenario trees ("rerun the forecast under these
  3 assumption changes").
- **Multi-turn rolling forecast**: assumptions change mid-conversation; completely unbenchmarked
  per the research, and the most FP&A-authentic format.
- **Spreadsheet-artifact grading** for agent mode: require an .xlsx with formulas; grade final
  state AND re-run with perturbed inputs to catch hardcoded values (MBABench found Excel agents
  hardcode; only perturbation exposes it).

## 4. Infrastructure roadmap

- **Migrate the runner to Inspect AI** (UK AISI, MIT) once task count grows — sandboxed code
  execution, multi-provider, judge scorers built in. Keep the generators/tolerances; they port
  directly. (Rationale in docs/RESEARCH.md §3. Avoid OpenAI Evals — reportedly sunsetting.)
- **Cost + latency reporting**: adapters already capture tokens/latency; add $/task using a
  price table — accuracy-vs-cost per harness is the headline chart per "AI Agents That Matter".
- **Judge validation**: before trusting judged tasks at scale, hand-score ~20 memos yourself and
  measure agreement (MBABench used 408 expert annotations).
- **Contamination policy if you publish**: keep a private seed for the "official" test set,
  publish a different seed as the dev set; add a canary string to published data.

## 5. Open questions

- Name? ("fpa-bench" is a placeholder.)
- Publish as its own repo? It's self-contained in `fpa-bench/` — `git filter-repo` or a fresh
  repo copy would take minutes. This repo (PasteCharts) is otherwise an unrelated tool.
- Do you want an Excel-native track (xlsx in/out via openpyxl) to test Claude-for-Excel-style
  harnesses? Natural fit with this repo's existing openpyxl usage.
- Baseline the human side: time yourself on 2–3 tasks to anchor difficulty claims.
