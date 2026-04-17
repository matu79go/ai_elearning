"""任意の科目/学年の全 chunk に対し LLM で小テスト+最終テスト問題を一括生成。

Usage:
    docker exec elearn_app python batch/bulk_generate_llm.py --subject Science --year 7
    docker exec elearn_app python batch/bulk_generate_llm.py --subject Science --year 7 --drill 5 --test 10
    docker exec elearn_app python batch/bulk_generate_llm.py --subject Science --year 7 --limit 3  # 最初3chunkだけ
    docker exec elearn_app python batch/bulk_generate_llm.py --subject Science --year 7 --resume  # 既に問題がある chunk をスキップ
"""
import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk, Question
from models.drill import DrillQuestion
from services.drill_generator import materialize_drill_llm
from services.llm import generate_questions


def generate_test_questions(chunk, material, count=10, mc_count=7, fr_count=3, difficulty='normal'):
    """最終テスト問題を LLM で生成 → questions テーブルに追加"""
    ref_rows = Question.query.filter(
        Question.chunk_id == chunk.chunk_id,
        Question.source.in_(['oak', 'llm_generated']),
    ).limit(5).all()
    oak_examples = [
        {
            'question_type': r.question_type,
            'question_text': r.question_text,
            'options': r.options,
            'correct_answer': r.correct_answer,
            'reference_answer': r.reference_answer,
        } for r in ref_rows
    ]

    questions = generate_questions(
        summary=chunk.summary or chunk.content,
        subject=material.subject,
        year_group=material.year_group,
        oak_examples=oak_examples,
        count=count, mc_count=mc_count, fr_count=fr_count,
        difficulty=difficulty,
    )

    rows = []
    for q in questions:
        if not q.get('question_text'):
            continue
        qtype = q.get('question_type')
        if qtype == 'multiple_choice':
            if not q.get('options') or not q.get('correct_answer'):
                continue
        elif qtype == 'free_response':
            if not q.get('reference_answer'):
                continue
        else:
            continue
        row = Question(
            material_id=material.material_id,
            chunk_id=chunk.chunk_id,
            question_type=qtype,
            question_text=q['question_text'],
            options=q.get('options'),
            correct_answer=q.get('correct_answer', ''),
            explanation=q.get('explanation'),
            chart_svg=q.get('chart_svg'),
            reference_answer=q.get('reference_answer'),
            max_score=q.get('max_score', 10),
            scoring_rubric=q.get('scoring_rubric'),
            difficulty=q.get('difficulty', difficulty),
            source='llm_generated',
        )
        db.session.add(row)
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', required=True, help='e.g. Science')
    ap.add_argument('--year', type=int, required=True, help='e.g. 7')
    ap.add_argument('--drill', type=int, default=5, help='drill MC per chunk')
    ap.add_argument('--test', type=int, default=10, help='test total per chunk')
    ap.add_argument('--test-mc', type=int, default=7)
    ap.add_argument('--test-fr', type=int, default=3)
    ap.add_argument('--limit', type=int, default=0, help='max chunks to process (0=all)')
    ap.add_argument('--resume', action='store_true',
                    help='skip chunks that already have LLM-generated drill or test questions')
    ap.add_argument('--sleep', type=float, default=1.5, help='seconds between LLM calls')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with app.app_context():
        chunks_q = db.session.query(MaterialChunk, Material).join(
            Material, MaterialChunk.material_id == Material.material_id,
        ).filter(
            Material.subject == args.subject,
            Material.year_group == args.year,
        ).order_by(Material.sort_order, MaterialChunk.sort_order)
        chunks = chunks_q.all()
        if args.limit:
            chunks = chunks[:args.limit]

        total = len(chunks)
        print(f'Target: {args.subject} Y{args.year} — {total} chunks')
        print(f'Per chunk: drill={args.drill}, test={args.test} (MC={args.test_mc}, FR={args.test_fr})')
        print(f'Sleep between calls: {args.sleep}s  |  resume={args.resume}  |  dry-run={args.dry_run}')
        print()

        total_drill = 0
        total_test = 0
        failures = []
        skipped = 0

        for i, (chunk, material) in enumerate(chunks, 1):
            tag = f'[{i}/{total}] chunk {chunk.chunk_id}'
            print(f'{tag}  {chunk.title[:60]}...', flush=True)

            if args.resume:
                drill_n = DrillQuestion.query.filter_by(chunk_id=chunk.chunk_id).count()
                test_n = Question.query.filter_by(
                    chunk_id=chunk.chunk_id, source='llm_generated',
                ).count()
                if drill_n > 0 and test_n > 0:
                    print(f'  skip (drill={drill_n}, llm_test={test_n} already present)')
                    skipped += 1
                    continue

            # 1) drill
            try:
                drill_rows = materialize_drill_llm(
                    chunk_id=chunk.chunk_id, count=args.drill,
                    material_id=material.material_id, difficulty='normal',
                )
                if not args.dry_run:
                    db.session.commit()
                else:
                    db.session.rollback()
                print(f'  drill: {len(drill_rows)} generated')
                total_drill += len(drill_rows)
            except Exception as e:
                db.session.rollback()
                print(f'  drill: FAILED ({e.__class__.__name__}: {str(e)[:100]})')
                failures.append((chunk.chunk_id, 'drill', str(e)))

            time.sleep(args.sleep)

            # 2) test
            try:
                test_rows = generate_test_questions(
                    chunk, material,
                    count=args.test, mc_count=args.test_mc, fr_count=args.test_fr,
                )
                if not args.dry_run:
                    db.session.commit()
                else:
                    db.session.rollback()
                print(f'  test:  {len(test_rows)} generated')
                total_test += len(test_rows)
            except Exception as e:
                db.session.rollback()
                print(f'  test:  FAILED ({e.__class__.__name__}: {str(e)[:100]})')
                failures.append((chunk.chunk_id, 'test', str(e)))

            time.sleep(args.sleep)

        print()
        print('=' * 60)
        print(f'Processed: {total} chunks')
        print(f'Skipped (resume): {skipped}')
        print(f'Drill total: {total_drill}')
        print(f'Test total:  {total_test}')
        if failures:
            print(f'Failures: {len(failures)}')
            for cid, kind, err in failures[:20]:
                print(f'  chunk {cid} {kind}: {err[:120]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
