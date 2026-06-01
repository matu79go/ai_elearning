"""Y7 体積/表面積マテリアル (283, 284) のテスト問題を、図(SVG)付きで作り直す。

方針: 各チャンクの test (questions) を 15 問に作り直す。
  - 図が適する計算問題 → ラベル付き立体 SVG を添付 (services.shape_svg)
  - 概念/文章題 → テキストのみ
数値も図も Python が同時に決めるので、図と答えは必ず一致する。
drill (練習) は触らない。

対象チャンク:
  2096 Volume of a Cuboid          2097 Missing Length & Cubes
  2098 Real-life Volume            2099 Surface Area of Cuboids
  2100 Surface Area of Prisms      2101 Real-life Surface Area

Usage:
    docker exec elearn_app python batch/generate_shape_questions.py
    docker exec elearn_app python batch/generate_shape_questions.py --chunks 2096,2099
    docker exec elearn_app python batch/generate_shape_questions.py --dry-run
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import MaterialChunk, Question, AnswerHistory
from services.shape_svg import cuboid_svg, triangular_prism_svg

rng = random.Random(20260601)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def fmt(n):
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f'{n:g}'


def vol_unit(u):
    return {'cm': 'cm³', 'm': 'm³', 'mm': 'mm³'}[u]


def area_unit(u):
    return {'cm': 'cm²', 'm': 'm²', 'mm': 'mm²'}[u]


def build_mc(correct_val, distractors, unit_fmt):
    """correct + 3 distinct distractors を A-D にシャッフルして返す。"""
    seen = {round(correct_val, 3)}
    chosen = []
    for d in distractors:
        if d is None or d <= 0:
            continue
        r = round(d, 3)
        if r in seen:
            continue
        seen.add(r)
        chosen.append(d)
        if len(chosen) == 3:
            break
    step = max(1, round(abs(correct_val) * 0.1)) or 1
    mul = 2
    while len(chosen) < 3:
        cand = correct_val + step * mul
        if round(cand, 3) not in seen and cand > 0:
            seen.add(round(cand, 3))
            chosen.append(cand)
        mul += 1
    vals = [correct_val] + chosen
    order = list(range(4))
    rng.shuffle(order)
    labels = 'ABCD'
    options, correct_label = [], None
    for i, idx in enumerate(order):
        options.append({'label': labels[i], 'text': unit_fmt(vals[idx])})
        if idx == 0:
            correct_label = labels[i]
    return options, correct_label


def Q(text, options, correct, expl, svg=None):
    return {
        'question_text': text, 'options': options, 'correct_answer': correct,
        'explanation': expl, 'chart_svg': svg,
    }


def text_mc(text, opts, correct, expl):
    """テキストのみ概念問題。opts: list[(label,text)]"""
    options = [{'label': l, 'text': t} for l, t in opts]
    return Q(text, options, correct, expl, None)


# ---------------------------------------------------------------------------
# parametric question builders
# ---------------------------------------------------------------------------
def q_cuboid_volume(l, w, h, u='cm', counting=False):
    V = l * w * h
    svg = cuboid_svg(f'{l}{"" if counting else " "+u}', f'{w}{"" if counting else " "+u}',
                     f'{h}{"" if counting else " "+u}', wv=l, hv=w, dv=h)
    uf = (lambda v: f'{fmt(v)} cubes') if counting else (lambda v: f'{fmt(v)} {vol_unit(u)}')
    options, correct = build_mc(V, [l + w + h, l * w, 2 * (l*w + l*h + w*h), l * h], uf)
    if counting:
        text = 'This cuboid is built from 1 cm³ cubes. How many small cubes does it contain?'
        expl = f'Count along the three directions and multiply: {l} × {w} × {h} = {V} cubes.'
    else:
        text = 'Work out the volume of this cuboid.'
        expl = f'Volume = length × width × height = {l} × {w} × {h} = {V} {vol_unit(u)}.'
    return Q(text, options, correct, expl, svg)


def q_cuboid_missing(l, w, ans, u='cm'):
    V = l * w * ans
    svg = cuboid_svg(f'{l} {u}', f'{w} {u}', '? ' + u, wv=l, hv=w, dv=max(2, ans),
                     face_label=f'V = {V} {vol_unit(u)}')
    uf = lambda v: f'{fmt(v)} {u}'
    options, correct = build_mc(ans, [round(V / l), round(V / w), l * w, ans + l], uf)
    text = f'The volume of this cuboid is {V} {vol_unit(u)}. Work out the missing length.'
    expl = f'Divide the volume by the two known sides: {V} ÷ {l} ÷ {w} = {ans} {u}.'
    return Q(text, options, correct, expl, svg)


def q_cube_volume(s, u='cm'):
    V = s ** 3
    svg = cuboid_svg(f'{s} {u}', f'{s} {u}', f'{s} {u}', wv=s, hv=s, dv=s)
    uf = lambda v: f'{fmt(v)} {vol_unit(u)}'
    options, correct = build_mc(V, [6 * s * s, 3 * s, s * s, 12 * s], uf)
    text = 'Work out the volume of this cube.'
    expl = f'Volume of a cube = side³ = {s}³ = {V} {vol_unit(u)}.'
    return Q(text, options, correct, expl, svg)


def q_cube_side(s, u='cm'):
    V = s ** 3
    svg = cuboid_svg('? ' + u, '? ' + u, '? ' + u, wv=s, hv=s, dv=s,
                     face_label=f'V = {V} {vol_unit(u)}')
    uf = lambda v: f'{fmt(v)} {u}'
    options, correct = build_mc(s, [round(V / 3), round(V / 6), s * s, V], uf)
    text = f'This cube has a volume of {V} {vol_unit(u)}. Work out the length of one side.'
    expl = f'Take the cube root of the volume: ∛{V} = {s} {u} (because {s} × {s} × {s} = {V}).'
    return Q(text, options, correct, expl, svg)


def q_cuboid_sa(l, w, h, u='cm'):
    SA = 2 * (l*w + l*h + w*h)
    svg = cuboid_svg(f'{l} {u}', f'{w} {u}', f'{h} {u}', wv=l, hv=w, dv=h)
    uf = lambda v: f'{fmt(v)} {area_unit(u)}'
    options, correct = build_mc(SA, [l*w*h, (l*w + l*h + w*h), 2 * (l + w + h), l*w*2], uf)
    text = 'Work out the total surface area of this cuboid.'
    expl = (f'Surface area = 2(lw + lh + wh) = 2({l}×{w} + {l}×{h} + {w}×{h}) '
            f'= 2({l*w} + {l*h} + {w*h}) = {SA} {area_unit(u)}.')
    return Q(text, options, correct, expl, svg)


def q_cube_sa(s, u='cm'):
    SA = 6 * s * s
    svg = cuboid_svg(f'{s} {u}', f'{s} {u}', f'{s} {u}', wv=s, hv=s, dv=s)
    uf = lambda v: f'{fmt(v)} {area_unit(u)}'
    options, correct = build_mc(SA, [s**3, 6 * s, s * s, 4 * s * s], uf)
    text = 'Work out the total surface area of this cube.'
    expl = f'Surface area of a cube = 6 × side² = 6 × {s}² = {SA} {area_unit(u)}.'
    return Q(text, options, correct, expl, svg)


def q_tri_prism_sa(a, b, c, L, u='cm'):
    """直角三角形断面 (脚 a=底辺, b=高さ, 斜辺 c) の三角柱の表面積。"""
    area = 0.5 * a * b
    SA = 2 * area + (a + b + c) * L
    svg = triangular_prism_svg(f'{a} {u}', f'{b} {u}', f'{c} {u}', f'{L} {u}',
                               bv=a, hv=b, lv=L)
    uf = lambda v: f'{fmt(v)} {area_unit(u)}'
    options, correct = build_mc(SA, [area * L, (a + b + c) * L, 2 * area + (a + b + c),
                                     a * b * L], uf)
    text = 'Work out the total surface area of this triangular prism.'
    expl = (f'SA = 2 × (½ × {a} × {b}) + ({a}+{b}+{c}) × {L} '
            f'= {fmt(2*area)} + {fmt((a+b+c)*L)} = {fmt(SA)} {area_unit(u)}.')
    return Q(text, options, correct, expl, svg)


def q_realvol_cuboid(context, l, w, h, u='cm'):
    V = l * w * h
    svg = cuboid_svg(f'{l} {u}', f'{w} {u}', f'{h} {u}', wv=l, hv=w, dv=h)
    uf = lambda v: f'{fmt(v)} {vol_unit(u)}'
    options, correct = build_mc(V, [l + w + h, 2 * (l*w + l*h + w*h), l * w, l * h], uf)
    expl = f'Volume = {l} × {w} × {h} = {V} {vol_unit(u)}.'
    return Q(context, options, correct, expl, svg)


def q_real_sa_cuboid(context, l, w, h, u='cm', expl_extra=''):
    SA = 2 * (l*w + l*h + w*h)
    svg = cuboid_svg(f'{l} {u}', f'{w} {u}', f'{h} {u}', wv=l, hv=w, dv=h)
    uf = lambda v: f'{fmt(v)} {area_unit(u)}'
    options, correct = build_mc(SA, [l*w*h, (l*w + l*h + w*h), 2 * (l + w + h)], uf)
    expl = (f'Surface area = 2({l}×{w} + {l}×{h} + {w}×{h}) = {SA} {area_unit(u)}. {expl_extra}').strip()
    return Q(context, options, correct, expl, svg)


# ---------------------------------------------------------------------------
# per-chunk assembly  (each -> exactly 15)
# ---------------------------------------------------------------------------
def chunk_2096():
    qs = []
    qs.append(text_mc(
        'Which unit is used to measure the volume of a 3D shape?',
        [('A', 'cm'), ('B', 'cm²'), ('C', 'cm³'), ('D', 'cm⁴')], 'C',
        'Volume is 3-dimensional, so it is measured in cubic units such as cm³.'))
    qs.append(text_mc(
        'What is the formula for the volume of a cuboid?',
        [('A', 'length + width + height'), ('B', 'length × width × height'),
         ('C', '2(lw + lh + wh)'), ('D', 'length × width')], 'B',
        'Volume of a cuboid = length × width × height (V = l × w × h).'))
    qs.append(q_cuboid_volume(4, 3, 5, counting=True))
    qs.append(q_cuboid_volume(2, 3, 4, counting=True))
    for (l, w, h) in [(5, 3, 4), (6, 2, 5), (4, 4, 3), (7, 3, 2), (8, 5, 2),
                      (10, 3, 3), (6, 6, 4), (9, 2, 4), (5, 5, 6), (12, 2, 3), (7, 4, 5)]:
        qs.append(q_cuboid_volume(l, w, h))
    return qs


def chunk_2097():
    qs = []
    qs.append(text_mc(
        'You know the volume of a cuboid and two of its sides. How do you find the third side?',
        [('A', 'Divide the volume by the two known sides'),
         ('B', 'Add the two known sides'),
         ('C', 'Multiply the volume by the two sides'),
         ('D', 'Subtract the two sides from the volume')], 'A',
        'V = l × w × h, so the missing side = V ÷ (one side) ÷ (the other side).'))
    for (l, w, ans) in [(7, 3, 4), (5, 2, 6), (4, 3, 5), (6, 2, 7), (8, 3, 2),
                        (10, 2, 4), (9, 2, 3), (5, 4, 3)]:
        qs.append(q_cuboid_missing(l, w, ans))
    for s in [3, 5, 4]:
        qs.append(q_cube_volume(s))
    for s in [2, 4, 5]:
        qs.append(q_cube_side(s))
    return qs


def chunk_2099():
    qs = []
    qs.append(text_mc(
        'In which units is surface area measured?',
        [('A', 'cm'), ('B', 'cm²'), ('C', 'cm³'), ('D', 'litres')], 'B',
        'Surface area is an area, so it is measured in square units such as cm².'))
    qs.append(text_mc(
        'What is the formula for the surface area of a cuboid?',
        [('A', 'l × w × h'), ('B', '2(lw + lh + wh)'),
         ('C', '6 × side'), ('D', 'l + w + h')], 'B',
        'A cuboid has 3 pairs of equal faces: SA = 2(lw + lh + wh).'))
    for (l, w, h) in [(4, 3, 2), (5, 4, 3), (6, 2, 4), (8, 5, 2), (7, 3, 3),
                      (10, 4, 2), (6, 6, 3), (9, 4, 5), (5, 5, 8), (12, 3, 2), (7, 6, 4)]:
        qs.append(q_cuboid_sa(l, w, h))
    for s in [3, 5]:
        qs.append(q_cube_sa(s))
    return qs


def chunk_2100():
    qs = []
    qs.append(text_mc(
        'How do you find the surface area of any prism?',
        [('A', '2 × area of cross-section + perimeter of cross-section × length'),
         ('B', 'area of cross-section × length'),
         ('C', '2 × perimeter × length'),
         ('D', 'length × width × height')], 'A',
        'A prism = the two end faces (2 × cross-section) plus the rectangles wrapping '
        'around (perimeter of cross-section × length).'))
    # 直角三角形断面の三角柱 (a=底辺, b=高さ, c=斜辺はピタゴラス数)
    for (a, b, c, L) in [(4, 3, 5, 7), (8, 6, 10, 5), (12, 5, 13, 7), (6, 8, 10, 9),
                        (12, 9, 15, 4), (8, 15, 17, 3), (3, 4, 5, 10), (5, 12, 13, 6),
                        (15, 8, 17, 5)]:
        qs.append(q_tri_prism_sa(a, b, c, L))
    # 「その他の角柱」= 直方体(長方形断面)の表面積
    for (l, w, h) in [(5, 4, 3), (6, 3, 2), (8, 4, 5), (7, 5, 2), (10, 3, 4)]:
        qs.append(q_cuboid_sa(l, w, h))
    return qs


def chunk_2098():
    qs = []
    # 図付き — 単一の直方体の実生活問題
    qs.append(q_realvol_cuboid('A fridge is shaped like a cuboid. Work out its volume.', 30, 45, 120))
    qs.append(q_realvol_cuboid('A storage box is a cuboid. Work out its volume.', 40, 30, 25))
    qs.append(q_realvol_cuboid('A fish tank is a cuboid. Work out the volume of water it can hold.', 50, 40, 30))
    qs.append(q_realvol_cuboid('A wooden block is a cuboid. Work out its volume.', 20, 10, 8))
    qs.append(q_realvol_cuboid('A drawer is shaped like a cuboid. Work out its volume.', 60, 40, 20))
    qs.append(q_realvol_cuboid('A cuboid water trough. Work out its volume.', 100, 30, 40))
    qs.append(q_realvol_cuboid('A chest freezer is shaped like a cuboid. Work out its volume.', 80, 60, 50))
    # テキスト — 多段階/容量/単位換算の文章題
    qs.append(text_mc(
        'A box of tea measures 8 cm × 6 cm × 12 cm. A carton measures 56 cm × 30 cm × 36 cm '
        'and is completely filled with boxes. How many boxes fit in one carton?',
        [('A', '105'), ('B', '95'), ('C', '210'), ('D', '60')], 'A',
        'Carton 56×30×36 = 60 480 cm³, box 8×6×12 = 576 cm³, so 60 480 ÷ 576 = 105 boxes.'))
    qs.append(text_mc(
        'How many cubic centimetres are there in 1 litre?',
        [('A', '100 cm³'), ('B', '1000 cm³'), ('C', '10 cm³'), ('D', '10 000 cm³')], 'B',
        '1 litre = 1000 cm³.'))
    qs.append(text_mc(
        '8 litres of juice is poured into a container measuring 10 cm × 9 cm × 40 cm. '
        'How much juice is left over? (1 litre = 1000 cm³)',
        [('A', '4400 cm³'), ('B', '3600 cm³'), ('C', '8000 cm³'), ('D', '400 cm³')], 'A',
        '8 L = 8000 cm³; container = 10×9×40 = 3600 cm³; left over = 8000 − 3600 = 4400 cm³.'))
    qs.append(text_mc(
        'Work out the volume of a cuboid measuring 8 m × 5 m × 400 cm. '
        '(Convert to the same unit first.)',
        [('A', '160 m³'), ('B', '16 000 m³'), ('C', '40 m³'), ('D', '160 cm³')], 'A',
        '400 cm = 4 m, so volume = 8 × 5 × 4 = 160 m³.'))
    qs.append(text_mc(
        'A Rubik\'s cube has a side length of 10 cm. What is its volume?',
        [('A', '1000 cm³'), ('B', '100 cm³'), ('C', '300 cm³'), ('D', '600 cm³')], 'A',
        'Volume of a cube = side³ = 10³ = 1000 cm³.'))
    qs.append(text_mc(
        'A cube-shaped box has a side length of 3 mm. What is its volume?',
        [('A', '27 mm³'), ('B', '9 mm³'), ('C', '6 mm³'), ('D', '12 mm³')], 'A',
        'Volume of a cube = side³ = 3³ = 27 mm³.'))
    qs.append(text_mc(
        'A cuboid has a base length of 30 m, a height of 16 m and a breadth of 10 m. '
        'What is its volume?',
        [('A', '4800 m³'), ('B', '480 m³'), ('C', '56 m³'), ('D', '8000 m³')], 'A',
        'Volume = 30 × 16 × 10 = 4800 m³.'))
    qs.append(text_mc(
        'A container measures 10 cm × 10 cm × 10 cm. What is its capacity in litres? '
        '(1 litre = 1000 cm³)',
        [('A', '1 litre'), ('B', '10 litres'), ('C', '100 litres'), ('D', '0.1 litre')], 'A',
        'Volume = 10×10×10 = 1000 cm³ = 1 litre.'))
    return qs


def chunk_2101():
    qs = []
    # 図付き — 単一の立体の実生活問題
    qs.append(q_real_sa_cuboid('A cardboard box is a cuboid. How much card is needed to cover '
                               'all its faces (its surface area)?', 5, 4, 3))
    qs.append(q_real_sa_cuboid('A gift box is a cuboid. Work out its surface area.', 8, 6, 4))
    qs.append(q_real_sa_cuboid('A metal tank (closed) is a cuboid. Work out its total surface area.', 10, 5, 4))
    qs.append(q_real_sa_cuboid('A wooden crate is a cuboid. Work out its surface area.', 6, 6, 5))
    qs.append(q_real_sa_cuboid('A jewellery box is a cuboid. Work out the area of material '
                               'needed to cover all its faces.', 7, 5, 3))
    qs.append({**q_tri_prism_sa(8, 6, 10, 14),
               'question_text': 'A tent is shaped like a triangular prism. How much fabric '
                                '(surface area) is needed to make it?'})
    qs.append({**q_tri_prism_sa(12, 5, 13, 7),
               'question_text': 'A chocolate bar is a triangular prism. Work out the surface '
                                'area of its wrapper.'})
    # テキスト — 被覆量/複合/文章題
    qs.append(text_mc(
        'Tracy has 8 wooden bookends. Each one has a surface area of 364 cm². '
        'What is the total surface area of all 8 bookends?',
        [('A', '2912 cm²'), ('B', '372 cm²'), ('C', '364 cm²'), ('D', '1456 cm²')], 'A',
        'Total = 8 × 364 = 2912 cm².'))
    qs.append(text_mc(
        '50 ml of varnish covers 2000 cm². How much varnish is needed to cover an area '
        'of 2912 cm²?',
        [('A', '72.8 ml'), ('B', '50 ml'), ('C', '116.5 ml'), ('D', '58.2 ml')], 'A',
        '2912 ÷ 2000 × 50 = 72.8 ml.'))
    qs.append(text_mc(
        'How many faces does a cuboid have?',
        [('A', '6'), ('B', '4'), ('C', '8'), ('D', '12')], 'A',
        'A cuboid has 6 faces, which form 3 matching pairs.'))
    qs.append(text_mc(
        'Why is the floor sometimes NOT included when finding the surface area of a '
        'real object such as a garden shed?',
        [('A', 'Because it sits on the ground and that face is not covered in material'),
         ('B', 'Because the floor has no area'),
         ('C', 'Because the floor is always the largest face'),
         ('D', 'Because surface area never includes the bottom')], 'A',
        'For an open-bottomed object resting on the ground, the floor face is left out.'))
    qs.append(text_mc(
        'The sloping side of a right-angled triangular cross-section is not given. '
        'Which rule helps you find it?',
        [('A', 'Pythagoras\' theorem (a² + b² = c²)'),
         ('B', 'Volume = l × w × h'),
         ('C', 'Area = ½ × base × height'),
         ('D', 'Circumference = π × d')], 'A',
        'The hypotenuse of the right triangle is found with Pythagoras: c = √(a² + b²).'))
    qs.append(text_mc(
        'A metal sheet costs $15 per square metre. A shed needs 64 m² of sheeting. '
        'What is the total cost?',
        [('A', '$960'), ('B', '$79'), ('C', '$640'), ('D', '$15')], 'A',
        'Cost = 64 × $15 = $960.'))
    qs.append(text_mc(
        'A company changes a box from 10×2×5 cm to 11×3×6 cm. Using a larger box for the '
        'same product mainly leads to which environmental impact?',
        [('A', 'More cardboard used and more waste'),
         ('B', 'Less material used'),
         ('C', 'No change at all'),
         ('D', 'Less transport needed')], 'A',
        'A larger box has more surface area and volume, so it uses more material and creates more waste.'))
    qs.append(text_mc(
        'A handbag is shaped like a triangular prism. How many rectangular faces does it have '
        '(the parts that wrap around the triangle)?',
        [('A', '3'), ('B', '2'), ('C', '4'), ('D', '5')], 'A',
        'A triangular prism has 2 triangular ends and 3 rectangular faces, one for each side of the triangle.'))
    return qs


BUILDERS = {
    2096: chunk_2096, 2097: chunk_2097, 2098: chunk_2098,
    2099: chunk_2099, 2100: chunk_2100, 2101: chunk_2101,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunks', default=','.join(str(c) for c in BUILDERS))
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    target = [int(c) for c in args.chunks.split(',') if c.strip()]

    with app.app_context():
        for cid in target:
            chunk = db.session.get(MaterialChunk, cid)
            if chunk is None or cid not in BUILDERS:
                print(f'chunk {cid}: skip (not a target)')
                continue
            qs = BUILDERS[cid]()
            print(f'chunk {cid} ({chunk.title[:50]}): building {len(qs)} questions', end='')

            # 既存 test を入れ替え (answer_history は念のため先に削除)
            old = Question.query.filter_by(chunk_id=cid).all()
            old_ids = [q.question_id for q in old]
            if old_ids:
                AnswerHistory.query.filter(AnswerHistory.question_id.in_(old_ids))\
                    .delete(synchronize_session=False)
            for q in old:
                db.session.delete(q)
            db.session.flush()

            n_svg = 0
            for d in qs:
                if d.get('chart_svg'):
                    n_svg += 1
                row = Question(
                    material_id=chunk.material_id,
                    chunk_id=cid,
                    question_type='multiple_choice',
                    question_text=d['question_text'],
                    options=d['options'],
                    correct_answer=d['correct_answer'],
                    explanation=d['explanation'],
                    chart_svg=d.get('chart_svg'),
                    difficulty='normal',
                    points_value=10,
                    max_score=10,
                    source='rule_based',
                    template_id='shape_svg',
                )
                db.session.add(row)
            print(f'  (replaced {len(old)} old; {n_svg}/{len(qs)} with diagrams)')

        if args.dry_run:
            db.session.rollback()
            print('\n[dry-run] rolled back')
        else:
            db.session.commit()
            print('\ncommitted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
