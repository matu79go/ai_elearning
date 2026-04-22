"""material 283 (Acids and Alkalis in Industry) と 284 (Unit 6 - Measures of Central Tendency)
をすべての関連データ込みで本番向けにエクスポート。

- materials 行
- material_chunks 行
- drill_questions 行 (chart_svg 含む)
- questions 行 (chart_svg 含む)

ID は auto_increment 任せにするため、INSERT 時に除外。
chunk 紐付けは material 内での sort_order で後処理する。

Usage:
    docker exec elearn_app python batch/export_materials_283_284.py > /tmp/prod_materials.sql
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk, Question
from models.drill import DrillQuestion


TARGET_MATERIAL_IDS = [283, 284]


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


def main() -> int:
    out = sys.stdout
    out.write('-- Material 280 (Solutions+AcidsAlkalis) + 282 (Graphs) import.\n')
    out.write('-- Uses LAST_INSERT_ID() to chain material → chunks → questions.\n\n')
    out.write('SET FOREIGN_KEY_CHECKS=0;\n\n')

    with app.app_context():
        for mid in TARGET_MATERIAL_IDS:
            mat = db.session.get(Material, mid)
            if mat is None:
                out.write(f'-- material {mid} not found\n\n')
                continue

            out.write(f'-- ============================================================\n')
            out.write(f'-- material_id={mid}: {mat.title}\n')
            out.write(f'-- ============================================================\n')

            # 削除 (既に同タイトルがある場合のクリーン)
            out.write(
                f"DELETE FROM drill_answer_history WHERE drill_question_id IN "
                f"(SELECT dq.drill_question_id FROM drill_questions dq "
                f"JOIN material_chunks c ON dq.chunk_id=c.chunk_id "
                f"JOIN materials m ON c.material_id=m.material_id "
                f"WHERE m.title={_sql_val(mat.title)} AND m.year_group={mat.year_group});\n"
            )
            out.write(
                f"DELETE dq FROM drill_questions dq "
                f"JOIN material_chunks c ON dq.chunk_id=c.chunk_id "
                f"JOIN materials m ON c.material_id=m.material_id "
                f"WHERE m.title={_sql_val(mat.title)} AND m.year_group={mat.year_group};\n"
            )
            out.write(
                f"DELETE q FROM questions q "
                f"JOIN material_chunks c ON q.chunk_id=c.chunk_id "
                f"JOIN materials m ON c.material_id=m.material_id "
                f"WHERE m.title={_sql_val(mat.title)} AND m.year_group={mat.year_group};\n"
            )
            out.write(
                f"DELETE c FROM material_chunks c "
                f"JOIN materials m ON c.material_id=m.material_id "
                f"WHERE m.title={_sql_val(mat.title)} AND m.year_group={mat.year_group};\n"
            )
            out.write(
                f"DELETE FROM materials WHERE title={_sql_val(mat.title)} "
                f"AND year_group={mat.year_group};\n\n"
            )

            # Material (created_by は本番に合わせて 1 にする or 元 parent_id)
            mat_cols = [
                'title', 'description', 'source_type', 'material_type',
                'source_content', 'file_path', 'subject', 'year_group',
                'difficulty', 'language', 'status', 'sort_order',
                'created_by', 'created_at', 'updated_at',
            ]
            # 本番に admin parent_id=1 と仮定 (念のため MIN(parent_id) でも代替可)
            vals = []
            for c in mat_cols:
                if c == 'created_by':
                    vals.append(1)  # 本番の admin parent_id (変更必要なら要確認)
                else:
                    vals.append(getattr(mat, c, None))
            out.write(
                f"INSERT INTO materials ({', '.join(mat_cols)}) VALUES "
                f"({', '.join(_sql_val(v) for v in vals)});\n"
            )
            out.write("SET @mid := LAST_INSERT_ID();\n\n")

            # Chunks
            chunks = MaterialChunk.query.filter_by(material_id=mid)\
                .order_by(MaterialChunk.sort_order).all()
            for ch in chunks:
                ch_cols = [
                    'material_id', 'title', 'content', 'summary',
                    'page_start', 'page_end', 'sort_order',
                    'video_drive_id', 'video_youtube_id', 'video_status',
                    'created_at',
                ]
                ch_vals = ['@mid' if c == 'material_id' else _sql_val(getattr(ch, c, None)) for c in ch_cols]
                out.write(
                    f"INSERT INTO material_chunks ({', '.join(ch_cols)}) VALUES "
                    f"({', '.join(ch_vals)});\n"
                )
                out.write(f"SET @cid_{ch.sort_order} := LAST_INSERT_ID();\n")
            out.write('\n')

            # Questions (test) — chunk.sort_order で @cid_N を参照
            test_rows = Question.query.filter_by(material_id=mid).all()
            for tr in test_rows:
                # このquestion の chunk が見つからなければスキップ
                ch = next((c for c in chunks if c.chunk_id == tr.chunk_id), None)
                if ch is None:
                    continue
                q_cols = [
                    'material_id', 'question_type', 'question_text', 'options',
                    'correct_answer', 'explanation', 'chart_svg', 'reference_answer',
                    'max_score', 'scoring_rubric', 'hint', 'chunk_id',
                    'source', 'template_id', 'generated_payload', 'difficulty',
                    'points_value', 'created_at',
                ]
                q_vals = []
                for c in q_cols:
                    if c == 'material_id':
                        q_vals.append('@mid')
                    elif c == 'chunk_id':
                        q_vals.append(f'@cid_{ch.sort_order}')
                    else:
                        q_vals.append(_sql_val(getattr(tr, c, None)))
                out.write(
                    f"INSERT INTO questions ({', '.join(q_cols)}) VALUES "
                    f"({', '.join(q_vals)});\n"
                )
            out.write('\n')

            # Drill questions
            drill_rows = DrillQuestion.query.filter_by(material_id=mid).all()
            for dr in drill_rows:
                ch = next((c for c in chunks if c.chunk_id == dr.chunk_id), None)
                if ch is None:
                    continue
                dq_cols = [
                    'chunk_id', 'material_id', 'question_text', 'options',
                    'correct_answer', 'explanation', 'chart_svg', 'source',
                    'template_id', 'generated_payload', 'difficulty',
                    'status', 'created_at',
                ]
                dq_vals = []
                for c in dq_cols:
                    if c == 'material_id':
                        dq_vals.append('@mid')
                    elif c == 'chunk_id':
                        dq_vals.append(f'@cid_{ch.sort_order}')
                    else:
                        dq_vals.append(_sql_val(getattr(dr, c, None)))
                out.write(
                    f"INSERT INTO drill_questions ({', '.join(dq_cols)}) VALUES "
                    f"({', '.join(dq_vals)});\n"
                )
            out.write('\n\n')

    out.write('SET FOREIGN_KEY_CHECKS=1;\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
