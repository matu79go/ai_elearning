"""Rule-based math question generator.

Loads templates from config/math_templates.yaml and generates concrete questions
by sampling variable values and evaluating expressions with Python's Fraction.

Core entry points:
    load_templates(path=None) -> dict[str, Template]
    generate(template, seed=None) -> GeneratedQuestion
    generate_batch(template, count, seed_base=None) -> list[GeneratedQuestion]

Safety: expressions are parsed via `ast` and only whitelisted nodes are evaluated.
No `eval` / `exec` on raw strings. Only arithmetic on ints and Fractions.
"""
from __future__ import annotations

import ast
import operator
import random
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Safe expression evaluator
# ---------------------------------------------------------------------------

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CMPOPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_BOOLOPS = {ast.And: all, ast.Or: any}

_ALLOWED_CALLS = {
    "F": Fraction,
    "Fraction": Fraction,
    "abs": abs,
    "max": max,
    "min": min,
    "int": int,
}


def safe_eval(expr: str, variables: dict[str, Any]) -> Any:
    """Evaluate a math expression string in a restricted AST sandbox.

    Only arithmetic, comparisons, boolean ops, conditional expressions, and
    calls to a small whitelist (F/Fraction/abs/max/min/int) are permitted.
    Variables come from the provided dict.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"invalid expression: {expr!r}") from e
    return _eval_node(tree.body, variables)


def _eval_node(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"disallowed constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _ALLOWED_CALLS:
            return _ALLOWED_CALLS[node.id]
        raise ValueError(f"unknown name: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_node(node.left, env), _eval_node(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_node(node.operand, env))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_CALLS:
            raise ValueError("only whitelisted function calls are allowed")
        fn = _ALLOWED_CALLS[node.func.id]
        args = [_eval_node(a, env) for a in node.args]
        return fn(*args)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, env)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval_node(comp, env)
            if type(op) not in _CMPOPS:
                raise ValueError("disallowed comparator")
            if not _CMPOPS[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp) and type(node.op) in _BOOLOPS:
        values = [_eval_node(v, env) for v in node.values]
        return _BOOLOPS[type(node.op)](values)
    if isinstance(node, ast.IfExp):
        return (
            _eval_node(node.body, env)
            if _eval_node(node.test, env)
            else _eval_node(node.orelse, env)
        )
    raise ValueError(f"disallowed AST node: {type(node).__name__}")


# ---------------------------------------------------------------------------
# Template model
# ---------------------------------------------------------------------------


@dataclass
class Template:
    id: str
    material_id: int | None
    chunk_id: int | None
    topic: str
    difficulty: int
    template_en: str
    template_ja: str
    variables: dict[str, dict]
    compute: dict[str, str]
    constraint: str | None
    answer_expr: str
    answer_type: str
    answer_wrap_en: str | None
    answer_wrap_ja: str | None
    distractor_exprs: list[str]
    raw: dict = field(repr=False, default_factory=dict)


def load_templates(path: str | Path | None = None) -> dict[str, Template]:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "math_templates.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    out: dict[str, Template] = {}
    for t in data.get("templates", []):
        tpl = Template(
            id=t["id"],
            material_id=t.get("material_id"),
            chunk_id=t.get("chunk_id"),
            topic=t.get("topic", ""),
            difficulty=int(t.get("difficulty", 1)),
            template_en=t["template_en"],
            template_ja=t["template_ja"],
            variables=t.get("variables", {}),
            compute=t.get("compute", {}),
            constraint=t.get("constraint"),
            answer_expr=t["answer_expr"],
            answer_type=t.get("answer_type", "integer"),
            answer_wrap_en=t.get("answer_wrap_en"),
            answer_wrap_ja=t.get("answer_wrap_ja"),
            distractor_exprs=list(t.get("distractor_exprs", [])),
            raw=t,
        )
        out[tpl.id] = tpl
    return out


# ---------------------------------------------------------------------------
# Variable sampling
# ---------------------------------------------------------------------------


def _sample_variable(spec: dict, env: dict[str, Any], rng: random.Random) -> int:
    if "in" in spec:
        return rng.choice(list(spec["in"]))
    lo = spec.get("min")
    hi = spec.get("max")
    if "min_expr" in spec:
        lo = int(safe_eval(spec["min_expr"], env))
    if "max_expr" in spec:
        hi = int(safe_eval(spec["max_expr"], env))
    if lo is None or hi is None:
        raise ValueError(f"variable spec missing min/max: {spec}")
    if hi < lo:
        hi = lo
    for _ in range(50):
        v = rng.randint(lo, hi)
        if spec.get("nonzero") and v == 0:
            continue
        distinct = spec.get("distinct_from", [])
        if any(v == env.get(name) for name in distinct):
            continue
        return v
    return rng.randint(lo, hi)


def _sample_once(tpl: Template, rng: random.Random) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for name, spec in tpl.variables.items():
        env[name] = _sample_variable(spec, env, rng)
    for name, expr in tpl.compute.items():
        env[name] = safe_eval(expr, env)
    return env


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _format_signed(value: int) -> str:
    if value >= 0:
        return f"+ {value}"
    return f"- {abs(value)}"


def _apply_placeholders(template: str, env: dict[str, Any]) -> str:
    """Replace {name} and {name:signed} placeholders. Jinja-safe — only handles
    the small format-spec vocabulary we need.
    """
    out = []
    i = 0
    while i < len(template):
        ch = template[i]
        if ch != "{":
            out.append(ch)
            i += 1
            continue
        end = template.index("}", i)
        token = template[i + 1 : end]
        if ":" in token:
            name, spec = token.split(":", 1)
        else:
            name, spec = token, ""
        value = env[name]
        if spec == "signed":
            out.append(_format_signed(int(value)))
        elif spec == "":
            out.append(str(value))
        else:
            out.append(format(value, spec))
        i = end + 1
    return "".join(out)


def _render_fraction(f: Fraction, mode: str) -> str:
    """Render a Fraction as a display string based on answer_type."""
    if mode == "integer":
        if f.denominator != 1:
            # Fall back to fraction display but flag
            return f"{f.numerator}/{f.denominator}"
        return str(f.numerator)
    if mode == "fraction":
        if f.denominator == 1:
            return str(f.numerator)
        return f"{f.numerator}/{f.denominator}"
    if mode == "mixed":
        if f.denominator == 1:
            return str(f.numerator)
        if abs(f) < 1:
            return f"{f.numerator}/{f.denominator}"
        sign = "-" if f < 0 else ""
        n = abs(f.numerator)
        d = f.denominator
        whole, rem = divmod(n, d)
        if rem == 0:
            return f"{sign}{whole}"
        return f"{sign}{whole} {rem}/{d}"
    if mode == "algebraic_over_x":
        # Fraction(n, d) means answer = n / (d * x). Simplify d=1 -> n/x.
        n = f.numerator
        d = f.denominator
        if d == 1:
            return f"{n}/x"
        return f"{n}/({d}x)"
    return str(f)


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------


@dataclass
class GeneratedQuestion:
    template_id: str
    question_en: str
    question_ja: str
    choices: list[str]        # 4 display strings
    correct_index: int        # 0..3
    correct_value: str        # display form of answer (for logging)
    payload: dict[str, Any]   # variable values used (for reproducibility)
    seed: int


def _wrap_value(value_str: str, wrap: str | None) -> str:
    if not wrap:
        return value_str
    return wrap.replace("{value}", value_str)


def _to_fraction(x: Any) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        return Fraction(x).limit_denominator(10**6)
    raise TypeError(f"cannot convert {type(x)} to Fraction")


def generate(tpl: Template, seed: int | None = None, max_tries: int = 100) -> GeneratedQuestion:
    """Generate one concrete question from a template.

    Retries up to max_tries on constraint violations or on inability to build
    4 distinct choices.
    """
    rng = random.Random(seed)
    last_err: Exception | None = None
    for _ in range(max_tries):
        attempt_seed = rng.randrange(2**31)
        attempt_rng = random.Random(attempt_seed)
        try:
            env = _sample_once(tpl, attempt_rng)
            if tpl.constraint and not safe_eval(tpl.constraint, env):
                continue
            answer = _to_fraction(safe_eval(tpl.answer_expr, env))
            distractors: list[Fraction] = []
            seen = {answer}
            for expr in tpl.distractor_exprs:
                try:
                    v = _to_fraction(safe_eval(expr, env))
                except (ZeroDivisionError, ValueError):
                    continue
                if v in seen:
                    continue
                seen.add(v)
                distractors.append(v)
                if len(distractors) == 3:
                    break
            if len(distractors) < 3:
                # fill with simple perturbations. For integer answers, use only
                # integer offsets so distractors stay integers.
                if tpl.answer_type == "integer" and answer.denominator == 1:
                    offsets = [Fraction(1), Fraction(-1), Fraction(2), Fraction(-2), Fraction(3)]
                else:
                    offsets = [Fraction(1), Fraction(-1), Fraction(1, 2), Fraction(2)]
                for off in offsets:
                    v = answer + off
                    if v not in seen:
                        seen.add(v)
                        distractors.append(v)
                    if len(distractors) == 3:
                        break
            if len(distractors) < 3:
                continue

            all_values = [answer] + distractors
            attempt_rng.shuffle(all_values)
            correct_index = all_values.index(answer)
            choices_display = [
                _wrap_value(_render_fraction(v, tpl.answer_type), tpl.answer_wrap_en)
                for v in all_values
            ]
            correct_display = _wrap_value(
                _render_fraction(answer, tpl.answer_type), tpl.answer_wrap_en
            )
            question_en = _apply_placeholders(tpl.template_en, env)
            question_ja = _apply_placeholders(tpl.template_ja, env)
            payload = {k: (str(v) if isinstance(v, Fraction) else v) for k, v in env.items()}
            return GeneratedQuestion(
                template_id=tpl.id,
                question_en=question_en,
                question_ja=question_ja,
                choices=choices_display,
                correct_index=correct_index,
                correct_value=correct_display,
                payload=payload,
                seed=attempt_seed,
            )
        except (ZeroDivisionError, ValueError) as e:
            last_err = e
            continue
    raise RuntimeError(
        f"failed to generate question for template {tpl.id!r} after {max_tries} tries: {last_err}"
    )


def generate_batch(
    tpl: Template, count: int, seed_base: int | None = None
) -> list[GeneratedQuestion]:
    rng = random.Random(seed_base)
    out = []
    seen_keys: set[str] = set()
    tries = 0
    while len(out) < count and tries < count * 20:
        tries += 1
        q = generate(tpl, seed=rng.randrange(2**31))
        key = q.question_en
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(q)
    return out


# ---------------------------------------------------------------------------
# Chunk -> templates index
# ---------------------------------------------------------------------------

_TEMPLATES_CACHE: dict[str, Template] | None = None


def get_templates() -> dict[str, Template]:
    """Load templates once per process."""
    global _TEMPLATES_CACHE
    if _TEMPLATES_CACHE is None:
        _TEMPLATES_CACHE = load_templates()
    return _TEMPLATES_CACHE


def templates_for_chunk(chunk_id: int) -> list[Template]:
    return [t for t in get_templates().values() if t.chunk_id == chunk_id]


def templates_for_material(material_id: int) -> list[Template]:
    return [t for t in get_templates().values() if t.material_id == material_id]


# ---------------------------------------------------------------------------
# DB materialization
# ---------------------------------------------------------------------------


def _build_options_json(q: GeneratedQuestion) -> list[dict]:
    """Convert 4 choices into the options JSON shape used by the questions table.

    Existing Oak/LLM questions store options as: [{"label": "A", "text": "..."}, ...]
    We follow the same shape so the quiz UI renders rule-based questions identically.
    """
    return [
        {"label": chr(ord("A") + i), "text": choice}
        for i, choice in enumerate(q.choices)
    ]


def _build_question_row(
    q: GeneratedQuestion,
    tpl: Template,
    material_id: int,
    chunk_id: int | None,
    language: str,
    difficulty: str,
):
    """Build a Question SQLAlchemy instance (not yet added to session)."""
    from models.material import Question

    question_text = q.question_en if language == "en" else q.question_ja
    correct_label = chr(ord("A") + q.correct_index)
    return Question(
        material_id=material_id,
        chunk_id=chunk_id if chunk_id is not None else tpl.chunk_id,
        question_type="multiple_choice",
        question_text=question_text,
        options=_build_options_json(q),
        correct_answer=correct_label,
        source="rule_based",
        template_id=tpl.id,
        generated_payload={"seed": q.seed, "vars": q.payload},
        difficulty=difficulty,
        points_value=10,
    )


def materialize_question(
    template_id: str,
    material_id: int,
    chunk_id: int | None = None,
    seed: int | None = None,
    language: str = "en",
    difficulty: str = "normal",
):
    """Generate one question from the named template and INSERT into `questions`.

    Adds to db.session and flushes (populates question_id) but does NOT commit.
    Caller controls transaction boundary.
    """
    from models import db

    tpl = get_templates().get(template_id)
    if tpl is None:
        raise ValueError(f"unknown template: {template_id}")

    q = generate(tpl, seed=seed)
    row = _build_question_row(q, tpl, material_id, chunk_id, language, difficulty)
    db.session.add(row)
    db.session.flush()
    return row


def materialize_chunk_pool(
    chunk_id: int,
    count: int = 10,
    material_id: int | None = None,
    language: str = "en",
) -> list:
    """Generate `count` unique questions for a chunk, distributing across templates.

    De-duplicates by question_text before INSERT (so DB never sees dupes).
    Returns [] if the chunk has no rule-based templates.
    """
    from models import db
    from models.material import MaterialChunk

    tpls = templates_for_chunk(chunk_id)
    if not tpls:
        return []

    if material_id is None:
        chunk = db.session.get(MaterialChunk, chunk_id)
        if chunk is None:
            raise ValueError(f"unknown chunk: {chunk_id}")
        material_id = chunk.material_id

    rng = random.Random()
    generated: list[tuple[GeneratedQuestion, Template]] = []
    seen_texts: set[str] = set()
    max_attempts = count * 10
    attempts = 0
    while len(generated) < count and attempts < max_attempts:
        attempts += 1
        tpl = rng.choice(tpls)
        q = generate(tpl, seed=rng.randrange(2**31))
        key = q.question_en if language == "en" else q.question_ja
        if key in seen_texts:
            continue
        seen_texts.add(key)
        generated.append((q, tpl))

    rows = []
    for q, tpl in generated:
        row = _build_question_row(q, tpl, material_id, chunk_id, language, "normal")
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows
