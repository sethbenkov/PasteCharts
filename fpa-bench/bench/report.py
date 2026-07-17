"""Aggregate result JSONL files into a leaderboard / category breakdown."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .runner import RESULTS_DIR


def load_results(results_dir: Path = RESULTS_DIR) -> list[dict]:
    records = []
    for f in sorted(results_dir.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def build_report(results_dir: Path = RESULTS_DIR) -> str:
    records = load_results(results_dir)
    if not records:
        return "No results yet. Run `python -m bench run --model <spec>` first."

    # key: (model, mode) -> aggregate
    runs: dict[tuple, dict] = defaultdict(lambda: {"scores": [], "by_cat": defaultdict(list), "errors": 0})
    for r in records:
        key = (r["model"], r["mode"])
        runs[key]["scores"].append(r["score"])
        runs[key]["by_cat"][r["category"]].append(r["score"])
        if r.get("error"):
            runs[key]["errors"] += 1

    categories = sorted({r["category"] for r in records})
    lines = ["# fpa-bench results", "", "## Leaderboard", ""]
    header = "| Model | Mode | Overall | " + " | ".join(categories) + " | Errors |"
    sep = "|" + "---|" * (len(categories) + 4)
    lines += [header, sep]
    ranked = sorted(runs.items(), key=lambda kv: -(sum(kv[1]["scores"]) / len(kv[1]["scores"])))
    for (model, mode), agg in ranked:
        overall = sum(agg["scores"]) / len(agg["scores"])
        cat_cells = []
        for c in categories:
            s = agg["by_cat"].get(c)
            cat_cells.append(f"{sum(s)/len(s):.2f}" if s else "—")
        lines.append(
            f"| {model} | {mode} | **{overall:.2f}** | " + " | ".join(cat_cells) + f" | {agg['errors']} |"
        )

    # hardest tasks
    by_task: dict[str, list[float]] = defaultdict(list)
    for r in records:
        by_task[r["task_id"]].append(r["score"])
    lines += ["", "## Hardest tasks (mean score across all runs)", ""]
    lines += ["| Task | Mean score | Runs |", "|---|---|---|"]
    for tid, scores in sorted(by_task.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        lines.append(f"| {tid} | {sum(scores)/len(scores):.2f} | {len(scores)} |")

    return "\n".join(lines) + "\n"
