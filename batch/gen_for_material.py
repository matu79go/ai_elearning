"""指定したmaterial の全chunk に drill + test 問題を生成。

Usage:
    docker exec elearn_app python batch/gen_for_material.py --material 280 --drill 5 --test 15
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--material', type=int, required=True)
    ap.add_argument('--drill', type=int, default=5)
    ap.add_argument('--test', type=int, default=15)
    ap.add_argument('--test-mc', type=int, default=10)
    ap.add_argument('--test-fr', type=int, default=5)
    ap.add_argument('--sleep', type=float, default=1.5)
    args = ap.parse_args()

    with app.app_context():
        material = db.session.get(Material, args.material)
        if material is None:
            print(f'material {args.material} not found')
            return 1
        chunks = MaterialChunk.query.filter_by(material_id=args.material).order_by(MaterialChunk.sort_order).all()
        total = len(chunks)
        print(f'Material {args.material}: {material.title} ({total} chunks)')
        print(f'Per chunk: drill={args.drill}, test={args.test} (MC={args.test_mc}, FR={args.test_fr})')
        print()

        tot_drill = 0
        tot_test = 0
        failures = []

        for i, chunk in enumerate(chunks, 1):
            print(f'[{i}/{total}] chunk {chunk.chunk_id} {chunk.title[:60]}')

            # drill
            try:
                rows = materialize_drill_llm(
                    chunk_id=chunk.chunk_id, count=args.drill,
                    material_id=material.material_id, difficulty='normal',
                )
                db.session.commit()
                print(f'  drill: {len(rows)}')
                tot_drill += len(rows)
            except Exception as e:
                db.session.rollback()
                print(f'  drill FAILED: {str(e)[:100]}')
                failures.append((chunk.chunk_id, 'drill', str(e)))

            time.sleep(args.sleep)

            # test
            try:
                rows = generate_test_questions(
                    chunk, material,
                    count=args.test, mc_count=args.test_mc, fr_count=args.test_fr,
                )
                db.session.commit()
                print(f'  test:  {len(rows)}')
                tot_test += len(rows)
            except Exception as e:
                db.session.rollback()
                print(f'  test FAILED: {str(e)[:100]}')
                failures.append((chunk.chunk_id, 'test', str(e)))

            time.sleep(args.sleep)

        print()
        print('=' * 50)
        print(f'Total drill: {tot_drill}, test: {tot_test}')
        if failures:
            print(f'Failures: {len(failures)}')
            for cid, kind, err in failures:
                print(f'  chunk {cid} {kind}: {err[:120]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
