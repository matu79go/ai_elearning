"""Preview generated questions from math_templates.yaml.

Usage:
    python batch/preview_math_templates.py [--count 5] [--template ID] [--lang en|ja]

Run inside the app container:
    docker exec elearn_app python batch/preview_math_templates.py --count 5
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.math_generator import generate_batch, load_templates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5, help="samples per template")
    ap.add_argument("--template", help="only this template id")
    ap.add_argument("--lang", choices=["en", "ja"], default="en")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    templates = load_templates()
    ids = [args.template] if args.template else list(templates.keys())

    for tid in ids:
        if tid not in templates:
            print(f"?? unknown template: {tid}")
            continue
        tpl = templates[tid]
        print("=" * 72)
        print(
            f"[{tpl.id}]  material={tpl.material_id}  chunk={tpl.chunk_id}  "
            f"topic={tpl.topic}  difficulty={tpl.difficulty}"
        )
        print("-" * 72)
        batch = generate_batch(tpl, count=args.count, seed_base=args.seed)
        for i, q in enumerate(batch, 1):
            question = q.question_en if args.lang == "en" else q.question_ja
            print(f"  Q{i}: {question}")
            for idx, choice in enumerate(q.choices):
                mark = "*" if idx == q.correct_index else " "
                label = chr(ord("A") + idx)
                print(f"        {mark} {label}) {choice}")
            print(f"        [correct: {q.correct_value}, payload={q.payload}]")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
