"""chunk に対し YouTube 動画を検索→ランク付け→DB保存。

Usage:
    docker exec elearn_app python batch/find_youtube_videos.py --chunks 974,947
    docker exec elearn_app python batch/find_youtube_videos.py --subject Science --year 7
    docker exec elearn_app python batch/find_youtube_videos.py --subject Science --year 7 --resume
    docker exec elearn_app python batch/find_youtube_videos.py --subject Science --year 7 --limit 3 --dry-run
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk
from models.youtube_video import ChunkYoutubeVideo
from services.youtube_finder import find_and_save_videos


def process_chunk(chunk: MaterialChunk, material: Material, max_results: int, dry_run: bool) -> int:
    try:
        rows = find_and_save_videos(
            chunk_id=chunk.chunk_id,
            title=chunk.title,
            subject=material.subject,
            year_group=material.year_group,
            max_results=max_results,
        )
        if dry_run:
            print(f'  [dry-run] would save {len(rows)} videos')
            for r in rows:
                print(f'    #{r.rank_position} [{"PRIMARY" if r.is_primary else "      "}] '
                      f'{r.video_id}  [{r.channel}]  {r.title[:70]}')
            db.session.rollback()
        else:
            db.session.commit()
            print(f'  saved {len(rows)} videos')
            for r in rows[:3]:
                mark = 'PRIMARY' if r.is_primary else '       '
                print(f'    #{r.rank_position} [{mark}] [{r.channel}] {r.title[:70]}')
        return len(rows)
    except Exception as e:
        db.session.rollback()
        print(f'  FAILED: {e.__class__.__name__}: {str(e)[:100]}')
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunks', help='comma-separated chunk IDs')
    ap.add_argument('--subject', help='filter by subject')
    ap.add_argument('--year', type=int, help='filter by year_group')
    ap.add_argument('--max-results', type=int, default=5)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--resume', action='store_true', help='skip chunks that already have videos')
    ap.add_argument('--sleep', type=float, default=0.5, help='seconds between API calls')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with app.app_context():
        if args.chunks:
            ids = [int(c) for c in args.chunks.split(',')]
            pairs = []
            for cid in ids:
                ch = db.session.get(MaterialChunk, cid)
                if ch:
                    mat = db.session.get(Material, ch.material_id)
                    pairs.append((ch, mat))
        else:
            if not (args.subject and args.year):
                print('specify --chunks or --subject+--year')
                return 1
            q = db.session.query(MaterialChunk, Material).join(
                Material, MaterialChunk.material_id == Material.material_id,
            ).filter(
                Material.subject == args.subject,
                Material.year_group == args.year,
            ).order_by(Material.sort_order, MaterialChunk.sort_order)
            pairs = q.all()

        if args.limit:
            pairs = pairs[:args.limit]

        total = len(pairs)
        print(f'Target: {total} chunks  |  max_results={args.max_results}  '
              f'|  resume={args.resume}  |  dry-run={args.dry_run}')
        print()

        total_saved = 0
        skipped = 0

        for i, (chunk, material) in enumerate(pairs, 1):
            print(f'[{i}/{total}] chunk {chunk.chunk_id} ({material.subject} Y{material.year_group}): '
                  f'{chunk.title[:60]}')
            if args.resume:
                n = ChunkYoutubeVideo.query.filter_by(chunk_id=chunk.chunk_id).count()
                if n > 0:
                    print(f'  skip (already {n} videos)')
                    skipped += 1
                    continue
            saved = process_chunk(chunk, material, args.max_results, args.dry_run)
            total_saved += saved
            time.sleep(args.sleep)

        print()
        print('=' * 60)
        print(f'Processed: {total}  |  saved: {total_saved}  |  skipped: {skipped}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
