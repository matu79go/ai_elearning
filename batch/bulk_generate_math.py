"""Phase A: chunks 2057-2061 に小テスト+最終テストの問題を一括生成。

Usage:
    docker exec elearn_app python batch/bulk_generate_math.py
    docker exec elearn_app python batch/bulk_generate_math.py --drill 30 --test 50
    docker exec elearn_app python batch/bulk_generate_math.py --chunks 2057,2058
    docker exec elearn_app python batch/bulk_generate_math.py --dry-run
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from services.math_generator import materialize_chunk_pool, templates_for_chunk
from services.drill_generator import materialize_drill_rule_based

DEFAULT_CHUNKS = [2057, 2058, 2059, 2060, 2061]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--drill', type=int, default=30, help='drill questions per chunk')
    ap.add_argument('--test', type=int, default=50, help='test (questions table) questions per chunk')
    ap.add_argument('--chunks', default=','.join(str(c) for c in DEFAULT_CHUNKS))
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    chunk_ids = [int(c) for c in args.chunks.split(',') if c.strip()]

    with app.app_context():
        summary = []
        for cid in chunk_ids:
            tpls = templates_for_chunk(cid)
            if not tpls:
                print(f'  [skip] chunk {cid}: no rule-based templates')
                summary.append((cid, 0, 0, 'skipped'))
                continue
            print(f'=== chunk {cid} ({len(tpls)} templates) ===')

            # Drill
            drill_rows = materialize_drill_rule_based(chunk_id=cid, count=args.drill)
            print(f'  drill:  generated {len(drill_rows)} / requested {args.drill}')

            # Test (通常 questions)
            test_rows = materialize_chunk_pool(chunk_id=cid, count=args.test)
            print(f'  test:   generated {len(test_rows)} / requested {args.test}')

            summary.append((cid, len(drill_rows), len(test_rows), 'ok'))

        if args.dry_run:
            print('\n[dry-run] rolling back')
            db.session.rollback()
        else:
            db.session.commit()
            print('\ncommitted.')

        print('\n--- summary ---')
        total_drill = sum(d for _, d, _, _ in summary)
        total_test = sum(t for _, _, t, _ in summary)
        for cid, d, t, status in summary:
            print(f'  chunk {cid}: drill={d}, test={t} ({status})')
        print(f'  TOTAL: drill={total_drill}, test={total_test}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
