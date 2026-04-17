"""Drill (小テスト) 向け問題生成サービス。

通常 questions テーブルとは分離して drill_questions に INSERT する。
- 算数 (chunks 2057-2061 等): math_generator のルールベース
- その他教科: LLM (既存の generate_questions を再利用、4択のみ)

Oak問題はdrillには使わない。Oakは最終テスト専用。
"""
from __future__ import annotations

import random
from typing import List


def _build_options_json(choices: list[str]) -> list[dict]:
    """choices list -> UIが期待するoptions JSON 形式"""
    return [{"label": chr(ord("A") + i), "text": c} for i, c in enumerate(choices)]


def materialize_drill_rule_based(
    chunk_id: int,
    count: int,
    material_id: int | None = None,
) -> list:
    """ルールベースのdrill問題をcount個、drill_questionsに追加。
    重複は question_text で避ける。commit は呼び出し側で。
    """
    from models import db
    from models.drill import DrillQuestion
    from models.material import MaterialChunk
    from services.math_generator import generate, templates_for_chunk

    tpls = templates_for_chunk(chunk_id)
    if not tpls:
        return []

    if material_id is None:
        chunk = db.session.get(MaterialChunk, chunk_id)
        if chunk is None:
            raise ValueError(f"unknown chunk: {chunk_id}")
        material_id = chunk.material_id

    rng = random.Random()
    rows = []
    seen_texts: set[str] = set()
    existing = db.session.query(DrillQuestion.question_text).filter_by(chunk_id=chunk_id).all()
    for (t,) in existing:
        seen_texts.add(t)

    max_attempts = count * 10
    attempts = 0
    while len(rows) < count and attempts < max_attempts:
        attempts += 1
        tpl = rng.choice(tpls)
        q = generate(tpl, seed=rng.randrange(2**31))
        text = q.question_en
        if text in seen_texts:
            continue
        seen_texts.add(text)

        row = DrillQuestion(
            chunk_id=chunk_id,
            material_id=material_id,
            question_text=text,
            options=_build_options_json(q.choices),
            correct_answer=chr(ord("A") + q.correct_index),
            explanation=None,  # ルールベースは解説なし、正解のみでOK
            source="rule_based",
            template_id=tpl.id,
            generated_payload={"seed": q.seed, "vars": q.payload},
            difficulty="normal",
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows


def materialize_drill_llm(
    chunk_id: int,
    count: int,
    material_id: int | None = None,
    difficulty: str = "normal",
) -> list:
    """LLMでdrill問題をcount個生成してdrill_questionsに追加。
    4択のみ(drillはMC固定)。既存のOak/LLM問題を参考スタイルに渡す。
    """
    from models import db
    from models.drill import DrillQuestion
    from models.material import MaterialChunk, Material, Question
    from services.llm import generate_questions

    chunk = db.session.get(MaterialChunk, chunk_id)
    if chunk is None:
        raise ValueError(f"unknown chunk: {chunk_id}")
    if material_id is None:
        material_id = chunk.material_id
    material = db.session.get(Material, material_id)

    # 参考: 同chunkのOak/LLM問題
    ref_rows = Question.query.filter(
        Question.chunk_id == chunk_id,
        Question.source.in_(['oak', 'llm_generated']),
    ).limit(5).all()
    oak_examples = [
        {
            'question_type': r.question_type,
            'question_text': r.question_text,
            'options': r.options,
            'correct_answer': r.correct_answer,
            'reference_answer': r.reference_answer,
        }
        for r in ref_rows
    ]

    generated = generate_questions(
        summary=chunk.summary or chunk.content,
        subject=material.subject if material else "science",
        year_group=material.year_group if material else 7,
        oak_examples=oak_examples,
        count=count,
        mc_count=count,  # drill は全てMC
        fr_count=0,
        difficulty=difficulty,
    )

    rows = []
    for q in generated:
        if q.get('question_type') != 'multiple_choice':
            continue
        if not q.get('options') or not q.get('correct_answer'):
            continue
        row = DrillQuestion(
            chunk_id=chunk_id,
            material_id=material_id,
            question_text=q['question_text'],
            options=q['options'],
            correct_answer=q['correct_answer'],
            explanation=q.get('explanation'),
            source="llm_generated",
            difficulty=q.get('difficulty', difficulty),
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows
