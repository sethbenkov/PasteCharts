"""Benchmark runner: run tasks against an adapter, grade, and persist results."""

from __future__ import annotations

import dataclasses
import json
import shutil
import tempfile
import time
from pathlib import Path

from .adapters import Adapter, make_adapter
from .graders import grade_numeric, grade_with_judge
from .schema import Task, discover_tasks

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

ANSWER_FORMAT_REMINDER = (
    "\n\nReturn your final answers as a single JSON object in a ```json fenced code block, "
    "using exactly the field names specified above. Numbers must be plain JSON numbers "
    "(no currency symbols, commas, or percent signs)."
)


def run_task(task: Task, adapter: Adapter, mode: str, judge: Adapter | None) -> dict:
    prompt = task.render_prompt(mode)
    if task.grading == "numeric":
        prompt += ANSWER_FORMAT_REMINDER

    workdir = None
    tmpdir = None
    if mode == "agent":
        tmpdir = tempfile.mkdtemp(prefix=f"fpabench-{task.task_id}-")
        dest = Path(tmpdir) / "data"
        if task.data_dir.exists():
            shutil.copytree(task.data_dir, dest)
        workdir = tmpdir

    try:
        text, meta = adapter.generate(prompt, workdir=workdir)
        error = None
    except Exception as e:  # capture and score 0 rather than abort the run
        text, meta, error = "", None, f"{type(e).__name__}: {e}"
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

    if error:
        grade = None
    elif task.grading == "judge":
        if judge is None:
            raise RuntimeError(f"Task {task.task_id} needs a judge model (--judge)")
        grade = grade_with_judge(task, text, lambda p: judge.generate(p)[0])
    else:
        grade = grade_numeric(task, text)

    return {
        "task_id": task.task_id,
        "category": task.category,
        "difficulty": task.difficulty,
        "model": adapter.name,
        "mode": mode,
        "score": grade.score if grade else 0.0,
        "parsed": grade.parsed if grade else False,
        "error": error,
        "fields": [dataclasses.asdict(f) for f in grade.fields] if grade else [],
        "judge_notes": grade.judge_notes if grade else "",
        "latency_s": round(meta.latency_s, 2) if meta else None,
        "input_tokens": meta.input_tokens if meta else None,
        "output_tokens": meta.output_tokens if meta else None,
        "response_text": text,
    }


def run_benchmark(
    model_spec: str,
    mode: str = "chat",
    task_ids: list[str] | None = None,
    judge_spec: str | None = None,
    config: dict | None = None,
    trials: int = 1,
    out_dir: Path = RESULTS_DIR,
) -> Path:
    adapter = make_adapter(model_spec, config)
    judge = make_adapter(judge_spec, config) if judge_spec else None
    tasks = discover_tasks(ids=task_ids)
    if not tasks:
        raise SystemExit("No tasks found. Run `python -m bench generate` first.")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_model = model_spec.replace("/", "_")
    out_path = out_dir / f"{stamp}_{safe_model}_{mode}.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as fh:
        for task in tasks:
            for trial in range(trials):
                print(f"[{adapter.name} | {mode}] {task.task_id} (trial {trial + 1}/{trials}) ...", flush=True)
                rec = run_task(task, adapter, mode, judge)
                rec["trial"] = trial
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                status = f"score={rec['score']:.2f}" if not rec["error"] else f"ERROR {rec['error']}"
                print(f"    -> {status}", flush=True)
    print(f"\nResults written to {out_path}")
    return out_path
