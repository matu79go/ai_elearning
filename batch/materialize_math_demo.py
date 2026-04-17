"""Demo: generate 10 rule-based questions for a chunk and store them.

Usage (inside container):
    docker exec elearn_app python batch/materialize_math_demo.py --chunk 2057 --count 10
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from services.math_generator import materialize_chunk_pool


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, required=True)
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true", help="roll back instead of committing")
    args = ap.parse_args()

    with app.app_context():
        rows = materialize_chunk_pool(chunk_id=args.chunk, count=args.count)
        if not rows:
            print(f"no templates defined for chunk {args.chunk}")
            return 1
        if args.dry_run:
            print(f"[dry-run] would insert {len(rows)} questions; rolling back")
            db.session.rollback()
            return 0
        db.session.commit()
        print(f"inserted {len(rows)} rule-based questions for chunk {args.chunk}:")
        for r in rows:
            print(
                f"  qid={r.question_id}  tpl={r.template_id}  "
                f"correct={r.correct_answer}  text={r.question_text[:60]!r}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
