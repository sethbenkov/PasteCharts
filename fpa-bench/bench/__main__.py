"""CLI. Run from the fpa-bench directory:

  python -m bench generate [--seed 42] [--task ID]
  python -m bench validate
  python -m bench list
  python -m bench show --task ID [--mode chat|agent]
  python -m bench run --model anthropic/claude-sonnet-5 [--mode chat|agent]
                      [--tasks id1,id2] [--judge anthropic/claude-opus-4-8] [--trials 1]
  python -m bench report
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(prog="bench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="(re)generate task data + answer keys")
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--task", default=None)

    sub.add_parser("validate", help="re-solve every task from its CSVs and diff vs answer keys")
    sub.add_parser("list", help="list tasks")

    s = sub.add_parser("show", help="print a task's rendered prompt")
    s.add_argument("--task", required=True)
    s.add_argument("--mode", default="chat", choices=["chat", "agent"])

    r = sub.add_parser("run", help="run the benchmark against a model/harness")
    r.add_argument("--model", required=True, help="e.g. anthropic/claude-sonnet-5, openai/gpt-5.2, openrouter/google/gemini-3-pro, cli/claude-code")
    r.add_argument("--mode", default="chat", choices=["chat", "agent"])
    r.add_argument("--tasks", default=None, help="comma-separated task ids (default: all)")
    r.add_argument("--judge", default=None, help="judge model spec for narrative tasks")
    r.add_argument("--trials", type=int, default=1)

    sub.add_parser("report", help="aggregate results/ into a leaderboard")

    args = ap.parse_args()

    if args.cmd == "generate":
        from .generators import generate_all
        generate_all(seed=args.seed, only=args.task)
    elif args.cmd == "validate":
        rc = subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"]).returncode
        sys.exit(rc)
    elif args.cmd == "list":
        from .schema import discover_tasks
        for t in discover_tasks():
            print(f"{t.task_id:28s} {t.category:22s} {t.difficulty:7s} {t.grading:8s} {t.title}")
    elif args.cmd == "show":
        from .schema import discover_tasks
        tasks = discover_tasks(ids=[args.task])
        if not tasks:
            sys.exit(f"no such task: {args.task}")
        print(tasks[0].render_prompt(args.mode))
    elif args.cmd == "run":
        cfg_path = ROOT / "models.json"
        config = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
        from .runner import run_benchmark
        run_benchmark(
            model_spec=args.model,
            mode=args.mode,
            task_ids=args.tasks.split(",") if args.tasks else None,
            judge_spec=args.judge,
            config=config,
            trials=args.trials,
        )
    elif args.cmd == "report":
        from .report import build_report
        text = build_report()
        (ROOT / "results" / "REPORT.md").write_text(text)
        print(text)


if __name__ == "__main__":
    main()
