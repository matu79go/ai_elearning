"""SVG チャート付き問題のサンプルを既存 chunk に投入するデモ。

Usage:
    docker exec elearn_app python batch/demo_svg_question.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import MaterialChunk
from models.drill import DrillQuestion
from services.chart_svg import pie_chart


def main() -> int:
    with app.app_context():
        # material 282 の chunk 5 (Introduction to Pie Charts) を対象に
        chunk = MaterialChunk.query.filter_by(material_id=282, sort_order=5).first()
        if chunk is None:
            print('chunk not found')
            return 1

        # Quality Street pie chart
        data = [
            {'label': 'Strawberry', 'value': 5},
            {'label': 'Orange', 'value': 3},
            {'label': 'Purple', 'value': 6},
            {'label': 'Green', 'value': 2},
            {'label': 'Other', 'value': 2},
        ]
        svg = pie_chart(data, size=320)

        q = DrillQuestion(
            chunk_id=chunk.chunk_id,
            material_id=chunk.material_id,
            question_text='Look at the pie chart. Each person in the survey is worth 20° (since 360° ÷ 18 = 20°). How many degrees does the "Purple" slice represent?',
            options=[
                {'label': 'A', 'text': '60°'},
                {'label': 'B', 'text': '100°'},
                {'label': 'C', 'text': '120°'},
                {'label': 'D', 'text': '40°'},
            ],
            correct_answer='C',
            explanation='The Purple slice has frequency 6. Multiply by the "degrees per item" (20°): 6 × 20° = 120°.',
            chart_svg=svg,
            source='rule_based',  # manually constructed
            template_id='pie_degrees_manual_demo',
            difficulty='normal',
        )
        db.session.add(q)
        db.session.commit()
        print(f'Inserted DrillQuestion id={q.drill_question_id} in chunk {chunk.chunk_id}')
        print(f'View: http://localhost:5000/admin/materials/282/chunks/{chunk.chunk_id}#drill')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
