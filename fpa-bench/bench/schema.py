"""Task schema and loading.

A task lives in tasks/<task_id>/ and consists of:
  task.json        -- metadata (category, difficulty, grading spec)
  prompt.md        -- the prompt shown to the model. May contain {data} which is
                      replaced with inlined CSVs in chat mode, or a file listing
                      in agent mode.
  data/*.csv       -- input data files
  answer_key.json  -- ground-truth answers (computed by the generator, never by hand)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


@dataclass
class FieldSpec:
    """Grading spec for one answer field."""

    name: str
    # "number" (tolerance-graded), "string" (case-insensitive exact), "integer" (exact)
    type: str = "number"
    # relative tolerance (fraction). Field passes if within rel_tol OR abs_tol.
    rel_tol: float = 0.005
    abs_tol: float = 0.01
    weight: float = 1.0


@dataclass
class Task:
    task_id: str
    title: str
    category: str
    difficulty: str  # easy | medium | hard
    grading: str  # "numeric" | "judge"
    fields: list[FieldSpec] = field(default_factory=list)
    rubric: str = ""  # for judge-graded tasks
    path: Path | None = None

    @property
    def data_dir(self) -> Path:
        return self.path / "data"

    @property
    def prompt_template(self) -> str:
        return (self.path / "prompt.md").read_text()

    @property
    def answer_key(self) -> dict:
        p = self.path / "answer_key.json"
        return json.loads(p.read_text()) if p.exists() else {}

    def data_files(self) -> list[Path]:
        if not self.data_dir.exists():
            return []
        return sorted(self.data_dir.glob("*.csv"))

    def render_prompt(self, mode: str) -> str:
        """Render the prompt for `chat` (inline data) or `agent` (file paths) mode."""
        template = self.prompt_template
        if "{data}" not in template:
            return template
        if mode == "chat":
            blocks = []
            for f in self.data_files():
                blocks.append(f"### File: {f.name}\n```csv\n{f.read_text().strip()}\n```")
            return template.replace("{data}", "\n\n".join(blocks))
        else:
            names = "\n".join(f"- data/{f.name}" for f in self.data_files())
            return template.replace(
                "{data}",
                "The input data files are on disk in your working directory:\n" + names,
            )


def load_task(task_dir: Path) -> Task:
    meta = json.loads((task_dir / "task.json").read_text())
    fields = [FieldSpec(**f) for f in meta.get("fields", [])]
    return Task(
        task_id=meta["task_id"],
        title=meta["title"],
        category=meta["category"],
        difficulty=meta["difficulty"],
        grading=meta.get("grading", "numeric"),
        fields=fields,
        rubric=meta.get("rubric", ""),
        path=task_dir,
    )


def discover_tasks(tasks_dir: Path = TASKS_DIR, ids: list[str] | None = None) -> list[Task]:
    tasks = []
    for d in sorted(tasks_dir.iterdir()):
        if d.is_dir() and (d / "task.json").exists():
            if ids and d.name not in ids:
                continue
            tasks.append(load_task(d))
    return tasks
