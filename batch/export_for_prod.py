"""ローカルDBから本番へ転送するデータをSQLファイルにエクスポート。

エクスポート内容:
  1. UPDATE questions SET source='oak' WHERE source='manual'  (legacy fix)
  2. INSERT questions (rule_based + llm_generated) — question_id は除外して auto_increment
  3. INSERT drill_questions — drill_question_id 除外、chunk_id / material_id は維持
  4. INSERT chunk_youtube_videos — id 除外、chunk_id は維持

drill_sessions, drill_answer_history は転送しない (ローカル開発時のテストデータ)

Usage:
    docker exec elearn_app python batch/export_for_prod.py > /tmp/prod_import.sql
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Question
from models.drill import DrillQuestion
from models.youtube_video import ChunkYoutubeVideo


def _sql_val(v):
    if v is None:
        return 'NULL'
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False).replace("\\", "\\\\").replace("'", "''")
        return f"'{s}'"
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


def _insert_batch(rows, table, columns, out, batch_size=100):
    """INSERT を batch 単位で出力。"""
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values = []
        for r in batch:
            vals = ', '.join(_sql_val(r[c]) for c in columns)
            values.append(f'({vals})')
        sql = f'INSERT INTO {table} ({", ".join(columns)}) VALUES\n' + ',\n'.join(values) + ';\n'
        out.write(sql)


def main() -> int:
    out = sys.stdout
    out.write('-- Production import generated from local DB\n')
    out.write('SET FOREIGN_KEY_CHECKS=0;\n')
    out.write('SET UNIQUE_CHECKS=0;\n')
    out.write('START TRANSACTION;\n\n')

    with app.app_context():
        # 1) legacy fix: manual→oak (if any)
        out.write("-- 1. Legacy fix: source='manual' → 'oak' for Oak imports\n")
        out.write("UPDATE questions SET source='oak' WHERE source='manual';\n\n")

        # 2) rule_based + llm_generated questions (without question_id)
        cols = [
            'material_id', 'question_type', 'question_text', 'options',
            'correct_answer', 'explanation', 'reference_answer',
            'max_score', 'scoring_rubric', 'hint', 'chunk_id',
            'source', 'template_id', 'generated_payload', 'difficulty',
            'points_value', 'created_at',
        ]
        rows = []
        for q in Question.query.filter(Question.source.in_(['rule_based', 'llm_generated'])).all():
            rows.append({c: getattr(q, c) for c in cols})
        out.write(f'-- 2. New questions: rule_based + llm_generated ({len(rows)} rows)\n')
        _insert_batch(rows, 'questions', cols, out)
        out.write('\n')

        # 3) drill_questions
        dcols = [
            'chunk_id', 'material_id', 'question_text', 'options',
            'correct_answer', 'explanation', 'source', 'template_id',
            'generated_payload', 'difficulty', 'status', 'created_at',
        ]
        drows = []
        for dq in DrillQuestion.query.all():
            drows.append({c: getattr(dq, c) for c in dcols})
        out.write(f'-- 3. drill_questions ({len(drows)} rows)\n')
        _insert_batch(drows, 'drill_questions', dcols, out)
        out.write('\n')

        # 4) chunk_youtube_videos
        ycols = [
            'chunk_id', 'video_id', 'title', 'channel', 'duration_seconds',
            'thumbnail_url', 'description', 'rank_position', 'is_primary',
            'source', 'created_at',
        ]
        yrows = []
        for yv in ChunkYoutubeVideo.query.all():
            yrows.append({c: getattr(yv, c) for c in ycols})
        out.write(f'-- 4. chunk_youtube_videos ({len(yrows)} rows)\n')
        _insert_batch(yrows, 'chunk_youtube_videos', ycols, out)
        out.write('\n')

    out.write('COMMIT;\n')
    out.write('SET FOREIGN_KEY_CHECKS=1;\n')
    out.write('SET UNIQUE_CHECKS=1;\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
