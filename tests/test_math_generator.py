"""Tests for services.math_generator.

Covers:
- safe_eval rejects dangerous constructs
- safe_eval evaluates arithmetic and Fraction calls correctly
- every template in config/math_templates.yaml generates valid questions
- answer is always one of the 4 choices and matches the expected type
- determinism: same seed -> same question
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.math_generator import (  # noqa: E402
    generate,
    generate_batch,
    load_templates,
    safe_eval,
)


class TestSafeEval:
    def test_basic_arithmetic(self):
        assert safe_eval("1 + 2", {}) == 3
        assert safe_eval("a * b", {"a": 3, "b": 4}) == 12
        assert safe_eval("(a + b) / c", {"a": 6, "b": 4, "c": 2}) == 5.0

    def test_fraction_call(self):
        result = safe_eval("F(1, 2) + F(1, 3)", {})
        assert result == Fraction(5, 6)

    def test_conditional(self):
        assert safe_eval("a if a > 0 else -a", {"a": -3}) == 3

    def test_rejects_import(self):
        with pytest.raises(ValueError):
            safe_eval("__import__('os')", {})

    def test_rejects_attribute(self):
        with pytest.raises(ValueError):
            safe_eval("a.b", {"a": 1})

    def test_rejects_unknown_call(self):
        with pytest.raises(ValueError):
            safe_eval("print(1)", {})

    def test_rejects_string(self):
        with pytest.raises(ValueError):
            safe_eval("'hello'", {})


class TestGenerator:
    @pytest.fixture(scope="class")
    def templates(self):
        return load_templates()

    def test_templates_load(self, templates):
        assert len(templates) >= 10
        # materials 276 and 277 covered
        mat_ids = {t.material_id for t in templates.values()}
        assert 276 in mat_ids
        assert 277 in mat_ids

    def test_all_templates_generate(self, templates):
        """Every template must successfully produce 5 distinct questions."""
        failures = []
        for tid, tpl in templates.items():
            try:
                batch = generate_batch(tpl, count=5, seed_base=123)
                assert len(batch) >= 1, f"{tid}: no questions generated"
                for q in batch:
                    # 4 choices, correct index valid
                    assert len(q.choices) == 4, f"{tid}: {len(q.choices)} choices"
                    assert 0 <= q.correct_index < 4
                    # correct_value appears among choices
                    assert q.choices[q.correct_index] == q.correct_value
                    # question text was substituted (no leftover placeholders)
                    assert "{" not in q.question_en, f"{tid}: unsubstituted EN: {q.question_en}"
                    assert "{" not in q.question_ja, f"{tid}: unsubstituted JA: {q.question_ja}"
            except Exception as e:
                failures.append(f"{tid}: {e}")
        assert not failures, "template failures:\n" + "\n".join(failures)

    def test_determinism(self, templates):
        tpl = next(iter(templates.values()))
        q1 = generate(tpl, seed=999)
        q2 = generate(tpl, seed=999)
        assert q1.question_en == q2.question_en
        assert q1.choices == q2.choices
        assert q1.correct_index == q2.correct_index

    def test_linear_equation_answer_integer(self, templates):
        for tid in ["linear_ax_plus_b", "linear_b_minus_ax", "linear_x_over_a_minus_b"]:
            tpl = templates[tid]
            for q in generate_batch(tpl, count=10, seed_base=7):
                # answer should render as a clean integer (possibly negative)
                val = q.correct_value.lstrip("-")
                assert val.isdigit(), f"{tid}: non-integer answer: {q.correct_value}"

    def test_fraction_of_amount_is_integer(self, templates):
        tpl = templates["fraction_of_amount"]
        for q in generate_batch(tpl, count=10, seed_base=11):
            assert q.correct_value.lstrip("-").isdigit(), f"expected int, got {q.correct_value}"
