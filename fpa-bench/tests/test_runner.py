"""Runner smoke test with a stub adapter (no network)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.adapters import Adapter, GenMeta
from bench.runner import run_task
from bench.schema import discover_tasks


class StubAdapter(Adapter):
    """Answers every task with its own answer key (perfect score)."""

    name = "stub:oracle"

    def generate(self, prompt, workdir=None):
        self.last_workdir = workdir
        # identify the task by matching data mentioned in the prompt is overkill;
        # the test passes the key in via closure instead.
        return self.canned, GenMeta(latency_s=0.01)


def test_run_task_chat_and_agent_modes():
    for task in discover_tasks():
        if task.grading != "numeric":
            continue
        stub = StubAdapter()
        stub.canned = "```json\n" + json.dumps(task.answer_key) + "\n```"
        for mode in ("chat", "agent"):
            rec = run_task(task, stub, mode, judge=None)
            assert rec["score"] == 1.0, f"{task.task_id} [{mode}] scored {rec['score']}"
            assert rec["error"] is None
        # agent mode must have staged files in a temp workdir
        if task.data_files():
            assert stub.last_workdir is not None


def test_run_task_captures_adapter_errors():
    class Boom(Adapter):
        name = "stub:boom"

        def generate(self, prompt, workdir=None):
            raise RuntimeError("no api key")

    task = next(t for t in discover_tasks() if t.grading == "numeric")
    rec = run_task(task, Boom(), "chat", judge=None)
    assert rec["score"] == 0.0
    assert "no api key" in rec["error"]


def test_chat_prompt_inlines_data_agent_prompt_lists_files():
    task = next(t for t in discover_tasks() if t.data_files())
    chat = task.render_prompt("chat")
    agent = task.render_prompt("agent")
    first_file = task.data_files()[0].name
    assert "```csv" in chat and first_file in chat
    assert "```csv" not in agent and f"data/{first_file}" in agent
