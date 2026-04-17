"""SVG チャート全種類 (bar / line / function) のサンプル問題を投入。

Usage:
    docker exec elearn_app python batch/demo_svg_questions_all.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import MaterialChunk
from models.drill import DrillQuestion
from services.chart_svg import bar_chart, line_chart, function_plot


DEMOS = [
    # --- Bar chart ---
    {
        'chunk_sort_order': 3,  # Bar Graphs, Line Graphs (material 282 chunk 3)
        'material_id': 282,
        'question_text': 'The bar chart shows favourite fruit in a Year 7 class. How many more pupils chose Bananas than Oranges?',
        'svg': bar_chart([
            {'label': 'Apples', 'value': 8},
            {'label': 'Bananas', 'value': 12},
            {'label': 'Oranges', 'value': 5},
            {'label': 'Grapes', 'value': 10},
        ], x_label='Fruit', y_label='Frequency'),
        'options': [
            {'label': 'A', 'text': '3'},
            {'label': 'B', 'text': '5'},
            {'label': 'C', 'text': '7'},
            {'label': 'D', 'text': '12'},
        ],
        'correct': 'C',
        'explain': 'Bananas = 12, Oranges = 5. Difference = 12 - 5 = 7.',
    },
    # --- Line / Time series ---
    {
        'chunk_sort_order': 4,  # Plotting Time Series (material 282 chunk 4)
        'material_id': 282,
        'question_text': "The line graph shows a company's quarterly sales (in thousands). Describe the overall trend.",
        'svg': line_chart([
            ('Q1\'12', 10), ('Q2\'12', 30), ('Q3\'12', 40), ('Q4\'12', 25),
            ('Q1\'13', 15), ('Q2\'13', 45), ('Q3\'13', 55), ('Q4\'13', 35),
            ('Q1\'14', 20), ('Q2\'14', 60), ('Q3\'14', 70), ('Q4\'14', 45),
        ], x_label='Quarter', y_label='Sales (thousands)', title='Quarterly Sales 2012-2014'),
        'options': [
            {'label': 'A', 'text': 'Rising trend with seasonal variation'},
            {'label': 'B', 'text': 'Falling trend'},
            {'label': 'C', 'text': 'Level trend'},
            {'label': 'D', 'text': 'No pattern'},
        ],
        'correct': 'A',
        'explain': 'Overall the peaks and troughs get higher each year (rising), but within each year Q1 is low and Q3 is high (seasonal).',
    },
    # --- Function plot (quadratic, preview for later years) ---
    # material 276 (Operations on fractions) じゃなく 281/282 のどこかに置く
    {
        'chunk_sort_order': 1,  # Types of Data chunk for material 282 (demo)
        'material_id': 282,
        'question_text': 'Look at the graph of y = x² - 2x - 3. Where does the curve cross the x-axis?',
        'svg': function_plot('x**2 - 2*x - 3', x_min=-3, x_max=5, title='y = x² - 2x - 3'),
        'options': [
            {'label': 'A', 'text': 'x = 1 and x = -3'},
            {'label': 'B', 'text': 'x = 3 and x = -1'},
            {'label': 'C', 'text': 'x = 0 and x = 2'},
            {'label': 'D', 'text': 'x = -3 only'},
        ],
        'correct': 'B',
        'explain': 'Factorise: x² - 2x - 3 = (x - 3)(x + 1). Zeros at x = 3 and x = -1.',
    },
]


def main() -> int:
    with app.app_context():
        for demo in DEMOS:
            chunk = MaterialChunk.query.filter_by(
                material_id=demo['material_id'],
                sort_order=demo['chunk_sort_order'],
            ).first()
            if chunk is None:
                print(f'  chunk sort_order={demo["chunk_sort_order"]} not found, skip')
                continue
            q = DrillQuestion(
                chunk_id=chunk.chunk_id,
                material_id=chunk.material_id,
                question_text=demo['question_text'],
                options=demo['options'],
                correct_answer=demo['correct'],
                explanation=demo['explain'],
                chart_svg=demo['svg'],
                source='rule_based',
                template_id='svg_demo',
                difficulty='normal',
            )
            db.session.add(q)
            db.session.flush()
            print(f'  chunk {chunk.chunk_id} "{chunk.title[:40]}...": added drill id={q.drill_question_id}')
        db.session.commit()
        print('Done.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
