"""Grading: extract a JSON answer block from a model response and score it."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .schema import FieldSpec, Task


@dataclass
class FieldResult:
    name: str
    expected: object
    got: object
    correct: bool
    weight: float


@dataclass
class GradeResult:
    task_id: str
    score: float  # 0..1 weighted
    parsed: bool  # did we find a JSON answer at all
    fields: list[FieldResult] = field(default_factory=list)
    judge_notes: str = ""


def extract_json_answer(text: str) -> dict | None:
    """Find the last parseable JSON object in the response.

    Prefers fenced ```json blocks; falls back to any {...} blob scanned from the end.
    """
    fenced = re.findall(r"```(?:json)?\s*\n(.*?)```", text, flags=re.DOTALL)
    for block in reversed(fenced):
        try:
            obj = json.loads(block)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    # Fallback: scan for balanced top-level braces from the end of the text.
    for start in range(len(text) - 1, -1, -1):
        if text[start] != "{":
            continue
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : end + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        pass
                    break
    return None


def _to_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("$", "").replace("%", "").strip()
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def grade_field(spec: FieldSpec, expected: object, got: object) -> bool:
    if got is None:
        return False
    if spec.type == "number":
        e, g = _to_number(expected), _to_number(got)
        if e is None or g is None:
            return False
        return abs(g - e) <= max(spec.abs_tol, spec.rel_tol * abs(e))
    if spec.type == "integer":
        e, g = _to_number(expected), _to_number(got)
        return e is not None and g is not None and round(e) == round(g)
    # string: case/whitespace-insensitive exact match
    return str(got).strip().lower() == str(expected).strip().lower()


def grade_numeric(task: Task, response_text: str) -> GradeResult:
    answer = extract_json_answer(response_text)
    key = task.answer_key
    results: list[FieldResult] = []
    total_w = sum(f.weight for f in task.fields) or 1.0
    earned = 0.0
    for spec in task.fields:
        expected = key.get(spec.name)
        got = answer.get(spec.name) if answer else None
        ok = grade_field(spec, expected, got)
        if ok:
            earned += spec.weight
        results.append(FieldResult(spec.name, expected, got, ok, spec.weight))
    return GradeResult(
        task_id=task.task_id,
        score=earned / total_w,
        parsed=answer is not None,
        fields=results,
    )


JUDGE_PROMPT = """You are grading a piece of FP&A / strategic-finance writing produced by an AI model.

## Task the model was given
{prompt}

## Rubric
{rubric}

## Ground-truth facts (computed from the data; the response should be consistent with these)
{facts}

## Model's response
<response>
{response}
</response>

Score the response against each rubric criterion. Be a strict, senior finance reviewer:
factual errors against the provided data, unsupported claims, or missing required elements
should cost points. Reply with ONLY a JSON object:
{{"criteria": [{{"name": "...", "max_points": N, "points": N, "note": "..."}}], "total_points": N, "max_total": N}}
"""


def grade_with_judge(task: Task, response_text: str, judge_call) -> GradeResult:
    """judge_call: callable(prompt_str) -> response_str (a model adapter's generate)."""
    prompt = JUDGE_PROMPT.format(
        prompt=task.render_prompt("chat"),
        rubric=task.rubric,
        facts=json.dumps(task.answer_key, indent=2),
        response=response_text,
    )
    judge_text = judge_call(prompt)
    parsed = extract_json_answer(judge_text)
    if not parsed or "total_points" not in parsed or "max_total" not in parsed:
        return GradeResult(task.task_id, 0.0, False, judge_notes="judge output unparseable")
    max_total = float(parsed["max_total"]) or 1.0
    score = max(0.0, min(1.0, float(parsed["total_points"]) / max_total))
    notes = json.dumps(parsed.get("criteria", []), indent=2)
    return GradeResult(task.task_id, score, True, judge_notes=notes)
