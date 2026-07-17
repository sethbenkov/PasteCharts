"""Grader unit tests: JSON extraction, tolerance logic, formatted-number parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.graders import extract_json_answer, grade_field, grade_numeric
from bench.schema import FieldSpec, discover_tasks


def test_extract_fenced_json():
    text = 'Some reasoning...\n```json\n{"a": 1, "b": 2.5}\n```\nDone.'
    assert extract_json_answer(text) == {"a": 1, "b": 2.5}


def test_extract_last_of_multiple_blocks():
    text = '```json\n{"a": 1}\n```\n later corrected: ```json\n{"a": 2}\n```'
    assert extract_json_answer(text) == {"a": 2}


def test_extract_bare_json():
    text = 'The answer is {"revenue": 1234.5, "note": "ok"} as computed.'
    assert extract_json_answer(text) == {"revenue": 1234.5, "note": "ok"}


def test_extract_none():
    assert extract_json_answer("no json here at all") is None


def test_number_tolerance():
    spec = FieldSpec("x", rel_tol=0.005, abs_tol=0.01)
    assert grade_field(spec, 1000.0, 1004.9)
    assert not grade_field(spec, 1000.0, 1006.0)
    assert grade_field(spec, 0.0, 0.005)  # abs_tol saves near-zero
    assert grade_field(spec, -500.0, -498.0)


def test_number_formats_accepted():
    spec = FieldSpec("x")
    assert grade_field(spec, 1234567.0, "$1,234,567")
    assert grade_field(spec, -450.0, "(450)")
    assert grade_field(spec, 42.5, "42.5%")
    assert not grade_field(spec, 42.5, "not a number")


def test_string_field():
    spec = FieldSpec("x", type="string")
    assert grade_field(spec, "EMEA Ops", "  emea ops ")
    assert not grade_field(spec, "A", "B")


def test_integer_field():
    spec = FieldSpec("x", type="integer")
    assert grade_field(spec, 7, "7")
    assert grade_field(spec, 7, 7.0)
    assert not grade_field(spec, 7, 8)


def test_end_to_end_grade_perfect_answer():
    """A response containing the exact answer key must score 1.0 on every numeric task."""
    import json
    for task in discover_tasks():
        if task.grading != "numeric":
            continue
        response = "Here are my results:\n```json\n" + json.dumps(task.answer_key) + "\n```"
        result = grade_numeric(task, response)
        assert result.score == 1.0, f"{task.task_id} scored {result.score} on its own key"
        assert result.parsed


def test_grade_garbage_answer_scores_zero():
    task = next(t for t in discover_tasks() if t.grading == "numeric")
    result = grade_numeric(task, "I refuse to answer in the requested format.")
    assert result.score == 0.0
    assert not result.parsed
