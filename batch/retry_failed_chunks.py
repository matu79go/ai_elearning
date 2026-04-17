"""失敗した chunk の drill / test を個別にリトライ。

各 chunk に対し:
  - drill: 既に drill_questions があれば skip、無ければ 5問生成
  - test:  既に llm_generated の questions があれば skip、無ければ 10問生成

Usage:
    docker exec elearn_app python batch/retry_failed_chunks.py
    docker exec elearn_app python batch/retry_failed_chunks.py --attempts 3
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk, Question
from models.drill import DrillQuestion
from services.drill_generator import materialize_drill_llm
from batch.bulk_generate_llm import generate_test_questions


# (chunk_id, missing: 'drill' | 'test' | 'both')
FAILED = [
    # Y7 Science
    (1023, 'test'),
    (1038, 'test'),
    # Y7 Spanish
    (1410, 'test'),
    (1411, 'test'),
    (1415, 'test'),
    (1416, 'both'),
    (1418, 'test'),
    (1424, 'test'),
    # Y4 Maths
    (1589, 'test'),
    (1661, 'test'),
    (1668, 'test'),
    (1675, 'drill'),
]


def retry_chunk(chunk_id: int, need: str, attempts: int, sleep_between: float):
    with app.app_context():
        chunk = db.session.get(MaterialChunk, chunk_id)
        if chunk is None:
            print(f'  chunk {chunk_id}: NOT FOUND')
            return
        material = db.session.get(Material, chunk.material_id)

        # skip if already present
        drill_n = DrillQuestion.query.filter_by(chunk_id=chunk_id).count()
        test_n = Question.query.filter_by(chunk_id=chunk_id, source='llm_generated').count()
        print(f'  chunk {chunk_id} ({material.subject} Y{material.year_group}): '
              f'have drill={drill_n}, test={test_n}')

        do_drill = (need in ('drill', 'both')) and drill_n == 0
        do_test = (need in ('test', 'both')) and test_n == 0

        if do_drill:
            for attempt in range(1, attempts + 1):
                try:
                    rows = materialize_drill_llm(
                        chunk_id=chunk_id, count=5,
                        material_id=material.material_id, difficulty='normal',
                    )
                    db.session.commit()
                    print(f'    drill: generated {len(rows)} (attempt {attempt})')
                    break
                except Exception as e:
                    db.session.rollback()
                    print(f'    drill attempt {attempt}: {e.__class__.__name__}: {str(e)[:80]}')
                    time.sleep(sleep_between * attempt)
            else:
                print(f'    drill: STILL FAILING after {attempts} attempts')

        time.sleep(sleep_between)

        if do_test:
            for attempt in range(1, attempts + 1):
                try:
                    rows = generate_test_questions(
                        chunk, material, count=10, mc_count=7, fr_count=3, difficulty='normal',
                    )
                    db.session.commit()
                    print(f'    test:  generated {len(rows)} (attempt {attempt})')
                    break
                except Exception as e:
                    db.session.rollback()
                    print(f'    test attempt {attempt}: {e.__class__.__name__}: {str(e)[:80]}')
                    time.sleep(sleep_between * attempt)
            else:
                print(f'    test:  STILL FAILING after {attempts} attempts')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempts', type=int, default=3)
    ap.add_argument('--sleep', type=float, default=2.0)
    args = ap.parse_args()

    print(f'Retrying {len(FAILED)} failed chunks (attempts={args.attempts})')
    print('=' * 60)
    for chunk_id, need in FAILED:
        retry_chunk(chunk_id, need, args.attempts, args.sleep)
    print()
    print('Done.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
