# LLM Benchmarks for Finance, FP&A, and Strategic Finance — Landscape Report (July 2026)

> Compiled by a research agent on 2026-07-17 via web search. Direct fetches of arxiv.org,
> vals.ai, and several blogs were blocked by the session's egress proxy, so paper details come
> from search summaries cross-checked across multiple queries. Verification caveats at the end.

**Purpose.** Survey of existing benchmarks relevant to a planned FP&A / strategic-finance
benchmark that tests (a) different models and (b) different harnesses (raw chat API vs. agentic
harnesses like Claude Code with code execution).

---

## 1. Existing benchmark inventory

### 1a. Classic financial QA (largely legacy / saturating)

| Benchmark (year) | Tasks | Format | Grading | Size | Saturation | License / availability |
|---|---|---|---|---|---|---|
| **FinQA** (2021) | Multi-step numerical QA over earnings-report excerpts | Single-turn QA with annotated reasoning programs | Program **execution accuracy** (exact numeric match) | 8,281 QA pairs / 2,789 reports | Fine-tuned baseline 68.9%, human expert 89.4%; GPT-4-era models ~76%; recent agentic RAG ~77%. Near-saturated as a discriminator among frontier models | Public (GitHub/HF) |
| **ConvFinQA** (2022) | Conversational chain-of-numeric-reasoning follow-ups on FinQA-style data | Multi-turn QA | Execution accuracy | ~3,890 conversations (~14k turns) | GPT-4 ~76% vs human expert 89.4%; still a measurable gap but heavily used in training pipelines → contamination risk | Public |
| **TAT-QA** (2021) | QA over hybrid table+text from financial reports (add/subtract/count/compare) | Single-turn QA | Exact match + numeric-aware F1 | 16,552 questions / 2,757 contexts | Early baselines 58 F1 vs human 90.8 F1; frontier models far higher now; widely trained-on | **CC BY 4.0**, GitHub |
| **DocFinQA** (Kensho, ACL 2024) | FinQA questions with **full-document** context (avg 123k words) | Long-context QA | Execution accuracy | 7,437 Q (922 test) | Still challenging for long-context pipelines; less saturated than FinQA | Public on HF |
| **FinanceBench** (Patronus, 2023) | Ecologically valid QA on 10-K/10-Q/8-K/earnings calls (lookup, numeric reasoning, inference) | QA over documents (open-book / RAG) | Human/manual grading against gold answers + evidence strings | 10,231 Q total; **150-question open subset** | GPT-4-Turbo+retrieval failed/refused 81% at launch (2023); modern retrieval stacks score far higher; open subset likely contaminated | 150 Q open on HF/GitHub; full set licensed commercially from Patronus. (License of open subset unverified — check the HF dataset card, possibly CC BY-NC 4.0) |
| **BizBench** (Kensho, ACL 2024) | 8 quantitative-reasoning tasks incl. program synthesis for financial QA, SEC-Num span extraction | QA + code generation | Execution accuracy / span match; held-out leaderboard | 8 sub-tasks (thousands of items) | Kensho leaderboard (benchmarks.kensho.com) still accepts submissions; partially saturated | Public on HF (kensho/bizbench); held-out test private |
| **FinEval** (2023, zh) / **PIXIU-FLARE** (2023) / **FinBen** (NeurIPS 2024) | Broad multi-task suites: knowledge MCQ, sentiment, NER, stock movement, etc.; FinEval is Chinese-domain (8,351 Q incl. "Financial Agent" section) | Mostly classification/MCQ/short QA | Exact match / F1 / accuracy | Thousands each | Designed for pre-frontier models; largely saturated for top-tier; FinBen adds zh/es | Public (GitHub/HF); Open FinLLM Leaderboard runs on FinBen |

### 1b. Exam-style / knowledge

| Benchmark | Tasks | Format | Grading | Size | Saturation | Availability |
|---|---|---|---|---|---|---|
| **CFA Level III evals** (arXiv 2507.02954, 2025; also 2509.04468 and "Reasoning Models Ace the CFA Exams," arXiv 2512.08270) | CFA L3 mock exams: MCQ + constructed-response essays (portfolio mgmt, strategy) | Closed-book QA / essay | MCQ exact match; essays via LLM-judge/human rubric | 23 models evaluated on full mock exams | **Effectively saturated**: o4-mini 79.1%, Gemini 2.5 Pro, DeepSeek-R1 all clear the ~63% pass threshold; essay sections remain the only weak spot | Mock-exam content is copyrighted (CFA Institute) — papers publish scores, not full item banks |
| **Vals.ai CFA-style + TaxEval v2, CorpFin v2** | Tax QA (TaxEval); corporate-finance QA over credit agreements etc. (CorpFin) | QA | Correctness + reasoning, expert-built rubrics | TaxEval v2: 20 public / 300 purchasable / **1,223 private test**; CorpFin v2: 20 / 340 / 858 | Not saturated (top TaxEval v2 ~79.7%) | Private held-out; public leaderboard at vals.ai |

### 1c. Agentic financial-research benchmarks (2025–2026, the fastest-moving area)

| Benchmark | Tasks | Format | Grading | Size | State | Availability |
|---|---|---|---|---|---|---|
| **Vals AI Finance Agent** (arXiv 2508.00828, Aug 2025) + **Finance Agent v2** (early 2026) | Entry-level sell-side analyst work over SEC filings: 9 expert-derived categories (earnings analysis, adjustments, comparables, **financial modeling**, precedents, etc.) | **Agentic**: harness gives models Google Search + EDGAR tools | LLM-as-judge against expert rubrics with conjunction rules (all criteria must pass) | 537 expert-authored questions (v1); v2 refreshed | Far from saturated: v2 public snapshot top scores ~52–58%; **"Financial Modeling" and "Precedents" categories collapse to low-20s%** | Open sample on HF (vals-ai/finance_agent_benchmark) + GitHub harness (vals-ai/finance-agent, finance-agent-v2); full test set private |
| **BigFinanceBench** (RogoAI, arXiv 2606.03829, Jun 2026) | Open-ended, multi-source analyst research tasks; grades the **full derivation** (source choice, period, accounting definition, assumptions, adjustments, calculation) | Agentic | Point-weighted rubrics (36,241 rubric points total) → partial credit; LLM judge | 928 expert-authored items | Best agent 58.8% rubric score; finding: final-answer accuracy is a "lossy proxy" for derivation quality | Public: bigfinancebench.com, HF (RogoAI/big-finance-benchmark) |
| **SECQUE** (arXiv 2504.04596, GEM@ACL 2025) | 10-K/10-Q analysis: comparison/trend, ratio calc, risk assessment, analyst insight | Open-book QA | **SECQUE-Judge**: ensemble of LLM judges validated against humans | 565 expert-written questions | Mid-difficulty; open-weights models struggle | Public |
| **GDPval** (OpenAI, arXiv 2510.04374, Sep 2025) | Real work-product tasks across 44 occupations / 9 sectors; Finance & Insurance sector includes financial-analyst-style deliverables (documents, **spreadsheets**, decks); ~25 finance-sector tasks in gold subset | Deliverable production from a brief + reference files (agentic-friendly) | **Blinded pairwise human expert comparison** vs human-made deliverable; Artificial Analysis runs an automated-grader variant (GDPval-AA) | 1,320 tasks total; **220-task open "gold" subset** | Top models "as good as or better than" human experts in just under half of gold tasks | Gold subset open; grading is expensive (human pairwise) |
| **FutureBench** (Together AI + Hugging Face, Jul 2025) | Live forecasting of real future events — *not* FP&A, but pioneered contamination-free live events + explicit **framework/tool/model three-level comparison** | Agentic (web research) | Resolution against real outcomes | Rolling/live | Live benchmark, can't saturate by memorization | Public blog + HF |
| **Others (newer, lightly verified)** | **Fin-RATE** (arXiv 2602.07294); **FinVerBench** (2605.29586); **Herculean** (2605.14355); **BizFinBench** (2505.19457); wealth-management workflow benchmark (2512.02230); **StockBench**/AI-Trader; **IndiaFinBench**, **CFinBench**, **Golden Touchstone** | mixed | mixed | — | — | arXiv; full texts not fetched — treat as pointers |

### 1d. Spreadsheet / financial-modeling benchmarks (closest neighbors)

| Benchmark | Tasks | Format | Grading | Size | State | Availability |
|---|---|---|---|---|---|---|
| **SpreadsheetBench** (NeurIPS 2024) | Real spreadsheet-manipulation asks from Excel forums | File-in/file-out; single- and multi-round | **Online-judge style**: multiple test-case workbooks per instruction, deterministic cell checks | 912 instructions / 2,729 test cases | Large model–human gap at release; not finance-specific | Public (GitHub, RUCKBReasoning) |
| **SpreadsheetBench 2** (arXiv 2606.29955, Jun 2026) | End-to-end business workflows: generation, **debugging**, visualization over multi-sheet workbooks (avg 11.8 sheets, ~594 cell edits per task) | Agentic, multi-turn scaffold | Deterministic + expert-validated checks | 321 tasks | Best model 34.9% overall; debugging 12% — very unsaturated | HF (KAKA22/SpreadsheetBench-v2) |
| **SheetCopilot bench** (NeurIPS 2023) | NL → atomic spreadsheet operations | Agent executes generated code on workbook | Deterministic final-state check | 221 tasks | Older; largely superseded | Public |
| **Alpha Excel Benchmark** (arXiv 2505.04110, 2025) | Financial Modeling World Cup challenges converted to text/JSON | QA-style (no live workbook) | Programmatic/deterministic | 113 challenges | Models good at pattern tasks, weak at complex numeric reasoning | Public paper |
| **MBABench** (a.k.a. WorkstreamBench in v1; arXiv 2605.22664, May 2026) | **End-to-end finance spreadsheet tasks** from FMWC, ModelOff, and Wall Street Prep curriculum (modeling, forecasting, scenario analysis), difficulty 1–5 | **Agentic, explicitly harness-comparative**: Claude web GUI vs ChatGPT Pro vs Claude-for-Excel vs ChatGPT-for-Excel | 3-dimension rubric (Accuracy / Formula / Format) via LLM judge **validated against 408 expert annotations**, plus synthetic perturbation suite | Task count unconfirmed | Claude GUI agent best; **Excel plug-ins hardcode values instead of formulas**; all agents below professional standards | arXiv; data/harness availability unverified |
| **BlueFin** (arXiv 2605.30907, May 2026) | Professional-finance workbook tasks: build models from scratch, modify existing models, examine artifacts | Agentic; ships an **open-source harness** | 3,225 granular rubric criteria across 131 tasks | 131 tasks | Frontier models far from reliable | Open source (per abstract) |
| **Finch / FinWorkBench** (arXiv 2512.13168, Dec 2025) | 172 enterprise finance & accounting **workflows** (budgeting, trading, asset mgmt) over 1,710 real spreadsheets + PDFs/images (Enron corpus etc., 2000–2025) | Agentic, multi-file, multimodal | Human evaluation of workflow completion | 172 workflows | GPT-5.1 Pro passes 38.4% (48h compute), Claude Sonnet 4.5 25% | Public: HF (FinWorkBench/Finch) + GitHub |
| **FinSheet-Bench** (arXiv 2603.07316, Mar 2026) | QA over **synthetic PE fund-portfolio spreadsheets** — a **synthetic-generator precedent** | QA over serialized sheets (non-agentic) | Deterministic numeric | 24 evaluation files | Best 82.4% overall but **48.6% on the largest workbook** | arXiv; dataset availability unverified |
| **FinBalance** (arXiv 2606.15949, Jun 2026) | Multi-document **accounting reconciliation**: source docs → cited journal entries → balance sheet → contradiction detection; 8 industries, 5 difficulty levels | Document-bundle in, structured artifacts out | Deterministic (exact balance sheet; 23 inconsistency codes); **scenarios composed by a deterministic generator** | 710-record eval split | Best model ≤46% exact accuracy | arXiv; closest methodological precedent to a seeded-generator finance benchmark |

**Named players:** OpenAI → GDPval (its hosted Evals *product* is reportedly being sunset — see §3).
Anthropic → no public finance benchmark of its own; markets Claude for Financial Services / Claude
for Excel, cites third-party results. Vals.ai → Finance Agent v1/v2, CorpFin v2, TaxEval v2
(private-test-set model). Scale AI → SEAL leaderboards (no dedicated finance track found).
Vellum → aggregator leaderboard, no finance-specific eval found.

---

## 2. Gap analysis: what FP&A work is NOT covered

Existing work clusters into three families — (i) QA over public SEC filings, (ii) sell-side/analyst
research agents, (iii) generic-or-finance spreadsheet manipulation. **Corporate FP&A — the
buy-side-of-your-own-company planning loop — is essentially unbenchmarked.** One practitioner
survey (Prigent, "Financial AI Benchmarks: What They Test and What They Miss") makes the same
point: "No benchmark tests the kind of forward-looking analysis that defines FP&A: driver-based
modeling, rolling forecasts with changing assumptions, or scenario planning under genuine
uncertainty. LLMs are tested on what happened, not on what might happen."

| FP&A task | Coverage today | Gap |
|---|---|---|
| **Three-statement modeling** (integrated IS/BS/CF, balance checks) | Partial/indirect: MBABench, BlueFin "build a model" tasks; Vals Finance Agent Financial Modeling category (~20% scores) is valuation/sell-side flavored | No benchmark grades statement articulation with deterministic checks |
| **Driver-based forecasting / rolling forecasts** | None found | Open |
| **Budget variance analysis, price-volume-mix decomposition** | None found (FinBalance is close-process, not plan-vs-actual) | Open — PVM has canonical algebra, ideal for deterministic grading |
| **13-week cash flow / liquidity forecasting** | None found | Open |
| **SaaS metrics & cohorts** (ARR waterfall, NRR/GRR, CAC payback, cohort retention) | None found; existing corpora are public-company GAAP filings, not operational SaaS data | Open |
| **Scenario / sensitivity analysis under stated assumptions** | Named in MBABench's scope; not graded as a first-class task anywhere | Mostly open |
| **Board memo / narrative synthesis** | GDPval finance tasks include memo-like deliverables (human pairwise-graded, ~25 tasks); BigFinanceBench grades derivations, not memos | Open for rubric-gradeable memo writing at scale |
| **Private/internal company data** | Only Finch (Enron archives) and FinSheet-Bench (synthetic PE data) escape the SEC-filings monoculture | Open — synthetic generators avoid confidentiality and contamination |
| **Harness as an experimental variable** (chat API vs code-execution agent vs Excel plug-in) | Only MBABench (GUI vs plug-ins) and FutureBench treat harness explicitly | Largely open — no published raw-API-vs-Claude-Code comparisons on finance tasks |
| **Cost/latency reporting** | Finch anecdotal; Vals reports cost; most academic benchmarks don't | Mostly open |

**Positioning implication:** a benchmark of *synthetic, seeded, private-company FP&A scenarios*
(3-statement + drivers + variance/PVM + 13-week cash + SaaS cohorts + scenario memos), graded by
deterministic numeric checks plus validated rubric judges, with harness (raw API vs code-execution
agent) as a first-class axis, would not duplicate anything above. Differentiate explicitly against:
**MBABench** (harness-comparative but competition/course-sourced and judge-only), **FinBalance**
(deterministic generator, but accounting close not planning), **BlueFin/Finch/SpreadsheetBench 2**
(workbook manipulation, backward-looking), **Vals Finance Agent / BigFinanceBench** (public-filings
research, not corporate planning).

---

## 3. Harness / eval-framework recommendation

Two distinct layers — don't conflate them: the **eval framework** (runs the benchmark, calls
graders, logs results) and the **harness-under-test** (raw chat API, Claude Code, Excel agent),
which the framework must treat as a pluggable "solver."

| Framework | Fit | Tradeoffs |
|---|---|---|
| **Inspect AI** (UK AISI, MIT license) — **recommended core** | Purpose-built for the mix: multi-provider model APIs; composable solvers/agents with native tool use; **Docker/K8s sandboxing** for code-execution variants; deterministic scorers + `model_graded_qa()` judges; eval logs + viewer; 200+ reference evals | Python-first; agentic runs can be costly; custom scorers needed for workbook diffing |
| **lm-eval-harness** (EleutherAI) | Fine for static QA baselines | No real agentic/tool-use or sandboxed code execution |
| **OpenAI Evals** | **Avoid.** Reportedly (third-party, unverified): hosted product goes read-only Oct 31, 2026, shuts down Nov 30, 2026; migration pointed at Promptfoo; OSS repo low-maintenance | — |
| **promptfoo** | Good YAML-driven multi-provider CI regression tests | Reportedly acquired by OpenAI in March 2026 (unverified) — vendor-neutrality question; agentic support weaker than Inspect; no first-class sandbox |
| **Braintrust** (commercial) | Best-in-class result tracking, datasets, human review queues | Commercial/SaaS; a platform, not a benchmark runner for external agent harnesses |
| **LangSmith** | Strong if built on LangChain/LangGraph | Ecosystem lock-in; the Claude Code harness axis lives outside it |

**Recommended architecture:**
1. **Inspect AI as the execution engine.** Each FP&A scenario an Inspect task; datasets emitted by
   the seeded generator; scorers = (a) deterministic numeric checks with tolerance, (b)
   `model_graded_qa` rubric judges for memos.
2. **Harness-under-test as solver variants:** (i) raw chat — plain `generate()`; (ii) tools —
   Inspect agent with sandboxed Python tool; (iii) external agent harness — shell out to
   `claude -p` / Claude Agent SDK (or Codex CLI, Gemini CLI) inside the sandbox, score the
   produced artifacts. A thin custom runner is the fallback (that is what fpa-bench v0 ships).
3. **Multi-provider access** via native provider keys for the big three + **OpenRouter** for the
   long tail.
4. Optionally sync run logs into **Braintrust or LangSmith** for dashboards; don't build the
   benchmark inside them.

---

## 4. Benchmark design best practices (2025–2026 consensus)

1. **Contamination avoidance.**
   - *Seeded synthetic generation* is a proven pattern in finance: FinBalance and FinSheet-Bench.
     Parameterize every scenario by seed to mint fresh, never-published instances per run
     (dynamic-sampling literature: LLMEval-3, AntiLeak-Bench, NPHardEval).
   - *Tiered release* (the Vals model): tiny public sample, purchasable validation set,
     never-released test set. Scale SEAL uses fully-private sets.
   - *If publishing data*: canary strings / no-derivatives licensing (Jacovi et al.), and version
     the benchmark so refreshes are expected (LiveBench/FutureBench-style temporal refresh).
2. **Grading.**
   - *Deterministic first.* Relative tolerance (±0.5–1%) + unit/scale/sign normalization. For
     workbook outputs, SpreadsheetBench's online-judge pattern: multiple test-case inputs per
     task, programmatic final-state checks — also catches hardcoding (re-run with perturbed
     inputs; MBABench found Excel agents hardcode values, exposed only by input perturbation).
   - *Rubric LLM judge only where necessary*, following HealthBench/BigFinanceBench practice:
     fine-grained binary, point-weighted criteria; **validate the judge against expert labels**
     (MBABench: 408 expert annotations + synthetic perturbation suite; SECQUE: multi-judge
     ensemble). Grade the *derivation*, not just the final number.
   - *Structural invariant checks* are free accuracy signals unique to FP&A: balance sheet
     balances, cash ties, NRR components sum, PVM bridge reconciles to total variance.
3. **Statistics.** Multiple runs per (model × harness × task); report pass@1 and pass@k, and for
   reliability claims pass^k; confidence intervals over seeds; difficulty tiers and per-category
   breakdowns.
4. **Cost & latency as first-class metrics.** "AI Agents That Matter" (TMLR 2025) documents 50x
   cost variation at similar accuracy; the follow-on **Holistic Agent Leaderboard** (ICLR 2026)
   treats standardized harness + cost logging as missing infrastructure. For the
   harness-comparison thesis this is the headline chart: accuracy vs $ per task per harness.
5. **Harness discipline.** Pin harness versions (Claude Code version, tool configs), publish the
   scaffold, isolate the three variables FutureBench separates: framework, tools, model. Report
   the grader model version; re-validate judges when swapping them.

---

## 5. Sources

Benchmarks — QA/document: [FinanceBench (Patronus docs)](https://docs.patronus.ai/docs/research_and_differentiators/financebench) · [PatronusAI/financebench on HF](https://huggingface.co/datasets/PatronusAI/financebench) · [FinQA paper](https://arxiv.org/pdf/2109.00122) · [ConvFinQA paper](https://arxiv.org/pdf/2210.03849) · [TAT-QA GitHub (CC BY 4.0)](https://github.com/NExTplusplus/TAT-QA) · [DocFinQA (ACL 2024)](https://aclanthology.org/2024.acl-short.42/) · [BizBench (ACL 2024)](https://aclanthology.org/2024.acl-long.452/) · [S&P/Kensho leaderboard](https://benchmarks.kensho.com/) · [SECQUE](https://arxiv.org/abs/2504.04596) · [FinEval](https://arxiv.org/abs/2308.09975) · [PIXIU/FLARE](https://github.com/the-finai/pixiu) · [FinBen (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/adb1d9fa8be4576d28703b396b82ba1b-Paper-Datasets_and_Benchmarks_Track.pdf)

Agentic finance: [Vals Finance Agent paper](https://arxiv.org/abs/2508.00828) · [Finance Agent v2 leaderboard](https://www.vals.ai/benchmarks/fabv2) · [vals-ai/finance-agent-v2 harness](https://github.com/vals-ai/finance-agent-v2) · [HF dataset](https://huggingface.co/datasets/vals-ai/finance_agent_benchmark) · [CorpFin v2](https://www.vals.ai/benchmarks/corp_fin_v2) · [TaxEval v2](https://www.vals.ai/benchmarks/tax_eval_v2) · [BigFinanceBench](https://arxiv.org/abs/2606.03829) / [site](https://bigfinancebench.com/) · [GDPval (OpenAI)](https://openai.com/index/gdpval/) · [GDPval paper](https://arxiv.org/pdf/2510.04374) · [GDPval-AA (Artificial Analysis)](https://artificialanalysis.ai/evaluations/gdpval-aa) · [Epoch AI on GDPval](https://epoch.ai/benchmarks/gdpval) · [FutureBench (Together AI)](https://www.together.ai/blog/futurebench) · [Fin-RATE](https://arxiv.org/html/2602.07294v1) · [FinVerBench](https://arxiv.org/html/2605.29586) · [BizFinBench](https://arxiv.org/pdf/2505.19457)

Spreadsheet/modeling: [SpreadsheetBench](https://spreadsheetbench.github.io/) · [SpreadsheetBench 2](https://arxiv.org/pdf/2606.29955) · [MBABench/WorkstreamBench](https://arxiv.org/abs/2605.22664) · [BlueFin](https://arxiv.org/abs/2605.30907) · [Finch](https://arxiv.org/abs/2512.13168) / [HF org](https://huggingface.co/FinWorkBench) · [FinSheet-Bench](https://arxiv.org/abs/2603.07316) · [FinBalance](https://arxiv.org/abs/2606.15949) · [Alpha Excel Benchmark](https://arxiv.org/abs/2505.04110) · [SheetCopilot context via SODBench](https://arxiv.org/pdf/2510.19864)

Exams: [CFA Level III eval (23 models)](https://arxiv.org/abs/2507.02954) · [Reasoning Models Ace the CFA Exams](https://arxiv.org/pdf/2512.08270) · [WealthManagement.com coverage](https://www.wealthmanagement.com/artificial-intelligence/study-ai-models-now-master-highest-level-of-cfa-exam)

Vendors/leaderboards: [Anthropic — Claude for Financial Services](https://www.anthropic.com/news/claude-for-financial-services) · [Advancing Claude for FS](https://www.anthropic.com/news/advancing-claude-for-financial-services) · [Scale SEAL](https://scale.com/blog/leaderboard) · [Vellum leaderboard](https://www.vellum.ai/llm-leaderboard) · [FP&A gap essay (Prigent)](https://www.bprigent.com/article/fpna-ai-benchmarks)

Frameworks: [Inspect AI docs](https://inspect.aisi.org.uk/) · [inspect_ai GitHub](https://github.com/UKGovernmentBEIS/inspect_ai) · [inspect_evals catalog](https://ukgovernmentbeis.github.io/inspect_evals/) · [AISI sandboxing toolkit](https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations) · [Hamel on Inspect](https://hamel.dev/notes/llm/evals/inspect.html) · [OpenAI Evals deprecation (third-party report)](https://therouter.ai/news/openai-evals-agent-builder-prompts-deprecation-november-2026/) · [2026 framework comparisons](https://www.digitalapplied.com/blog/ai-agent-eval-frameworks-testing-guide-2026), [inference.net guide](https://inference.net/content/llm-evaluation-tools-comparison/), [aiml.qa benchmark](https://aiml.qa/llm-evaluation-framework-benchmark-2026/)

Design practice: [AI Agents That Matter](https://arxiv.org/abs/2407.01502) · [contamination survey (static→dynamic)](https://arxiv.org/html/2502.17521v2) · [data-contamination survey](https://arxiv.org/html/2502.14425v2) · [AntiLeak-Bench (ACL 2025)](https://aclanthology.org/2025.acl-long.901/) · [contamination-resistant datasets position paper](https://arxiv.org/html/2605.19999v1) · [Rubrics across the LLM landscape](https://arxiv.org/pdf/2606.08625) · [RubricEval](https://arxiv.org/pdf/2603.25133) · [CORE-Bench saturation case study](https://arxiv.org/pdf/2606.26158)

**Verification caveats:** (1) arxiv.org, vals.ai, and bprigent.com were egress-blocked for direct
fetch — paper details come from search summaries corroborated across 2+ queries; exact task counts
for MBABench, BlueFin data availability, and FinSheet-Bench dataset release are unconfirmed.
(2) OpenAI Evals shutdown dates and the promptfoo–OpenAI acquisition are third-party reports only.
(3) Leaderboard numbers moved between snapshots — treat scores as of early-to-mid 2026 and
re-check before quoting. (4) FinanceBench open-subset license: verify the HF dataset card before
redistribution.
