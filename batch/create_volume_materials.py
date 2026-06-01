"""Y7 Maths Unit 7 の続き — 2 つのマテリアルを手動構築。

mock/math/Y7/volume/ の 2 PDF に忠実な構成。
  1. Unit 7 - Volume of Cuboids        (Kami Export - Unit 7 - Volume-of-Cuboids)
  2. Unit 7 - Surface Area of a Prism   (Unit 7 - Surface Area of a Prism)

Volume と Surface Area は別トピックなので 2 マテリアルに分割。
チャンクは細かく分けず各 3 チャンク。

Usage:
    docker exec elearn_app python batch/create_volume_materials.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk, Question
from models.drill import DrillQuestion
from models.youtube_video import ChunkYoutubeVideo
from models.parent import Parent


# ============================================================
# Material A — Volume of Cuboids
# ============================================================
VOLUME_CHUNKS = [
    {
        'title': 'Counting Cubes and the Volume of a Cuboid',
        'summary': "What volume is, the units we measure it in (mm3, cm3, m3), counting unit cubes inside a cuboid, and the shortcut formula Volume = length x width x height.",
        'content': """Volume of Cuboids (Year 7 Maths, Unit 7)

What is volume?
VOLUME is the amount of 3-dimensional space an object occupies. Where length is 1D and area is 2D, volume is 3D.
Units of volume are "cubic" units: mm^3, cm^3, m^3 (and km^3). A volume of 1 cm^3 is a cube measuring 1 cm by 1 cm by 1 cm.
Tip: a volume answer must always be in cubic units. If your answer is in cm^2 you have found an area, not a volume.

Starter — counting cubes
You can find the volume of a shape made of unit cubes simply by counting the cubes. For example, cuboids built from 1 cm^3 cubes:
- a layer 2 x 2 with no extra height = 4 cubes
- a 2 x 2 x 2 cube = 8 cubes
- a 2 x 3 x 1 = 6 cubes
- a 4 x 3 x 1 = 12 cubes
- 16 cubes, 27 cubes (a 3 x 3 x 3 cube), 45 cubes, 64 cubes (a 4 x 4 x 4 cube).

Investigation: is there a quicker way than counting one cube at a time?
Yes. Count the cubes along three directions and MULTIPLY them.
- A cuboid 4 cubes long, 3 cubes high, 5 cubes deep: 4 x 3 x 5 = 60 cubes.
- A cuboid 7 cubes long, 4 cubes high, 6 cubes deep: 7 x 4 x 6 = 168 cubes.
Multiplying is much quicker than counting, and it always gives the same answer.

The formula for the volume of a cuboid
    Volume of a cuboid = length x width x height
    V = l x w x h
Because multiplication can be done in any order, it does not matter which side you call length, width or height — the product is the same.

Worked examples (each small cube = 1 cm^3)
- 4 x 2 x 3 = 24 cm^3
- 5 x 5 x 5 = 125 cm^3  (this is a cube, so all three sides are equal)
- 6 x 2 x 6 = 72 cm^3
- 6 x 10 x 4 = 240 cm^3
- 3 x 4 x 3 = 36 cm^3

Practice answers (Task 1)
- Cuboids: 60 cm^3, 160 cm^3, 120 cm^3, 112 m^3.
- Cubes:   3 cm cube = 27 cm^3,  4 cm cube = 64 cm^3,  6 cm cube = 216 cm^3.

Key habits
- Make sure all three measurements are in the SAME unit before multiplying.
- Always write cubic units (cm^3, m^3) in the final answer.
- A cube is a special cuboid where length = width = height, so its volume is side x side x side = side^3.
""",
    },
    {
        'title': 'Finding a Missing Length and the Volume of Cubes',
        'summary': "Rearranging V = l x w x h to find a missing side by dividing, finding the side of a cube from its volume using a cube root, and the NRICH packing investigation.",
        'content': """Working Backwards — Missing Lengths

If you know the volume of a cuboid and two of its sides, you can work out the third side by DIVIDING.
Starting from  V = l x w x h , divide the volume by the two sides you know:
    missing side = V / (known side x known side)

Worked example
A cuboid has volume 84 cm^3, with sides 7 cm and 3 cm. Find the missing length.
    84 / 7 / 3 = 4 cm
(Check: 7 x 3 x 4 = 84 cm^3.)

More missing-length answers (Task 2, cuboids)
- Volume 24 cm^3 with sides 3 cm and 4 cm -> missing side 2 cm.
- Volume 30 cm^3 with sides 2 cm and 3 cm -> missing side 5 cm.
- Volume 264 cm^3 with sides 4 cm and 6 cm -> missing side 11 cm.
- Volume 540 cm^3 with sides 6 cm and 15 cm -> missing side 6 cm.

Volume of a cube and the cube root
For a cube every side is the same length s, so:
    V = s x s x s = s^3
To go backwards from a volume to the side length you take the CUBE ROOT.
- Volume 8 cm^3   -> side = 2 cm  (because 2 x 2 x 2 = 8)
- Volume 64 cm^3  -> side = 4 cm  (4 x 4 x 4 = 64)
- Volume 125 cm^3 -> side = 5 cm  (5 x 5 x 5 = 125)
- Volume 1000 cm^3 -> side = 10 cm (10 x 10 x 10 = 1000)
Not every cube root is a whole number. A dice of volume 16 cm^3 has side = cube root of 16 = 2.520 cm (to 3 d.p.).

More backwards problems
- A cuboid has volume 180 cm^3 with a length of 5 cm and breadth of 4 cm. Height = 180 / 5 / 4 = 9 cm.

NRICH investigation
"What is the smallest cube you can put in a 12 cm x 10 cm x 8 cm box so that you cannot fit another the same one in?" — think about which cube size leaves too little room on every side for a second identical cube.

Key habits
- To find a missing side, DIVIDE the volume by the sides you already know.
- For a cube, volume = side^3, and side = cube root of the volume.
- Always check by multiplying your sides back together — you should get the original volume.
""",
    },
    {
        'title': 'Real-life Volume, Capacity and Unit Conversion',
        'summary': "Packing boxes into a carton, word problems about fridges and suitcases, converting measurements to the same unit before multiplying, and the link between volume and capacity (1 litre = 1000 cm3).",
        'content': """Real-life Volume Problems

Pattern 1 — how many small boxes fit in a big one?
Work out the volume of the big container and the volume of one small box, then divide.
Example: boxes of tea measure 8 cm x 6 cm x 12 cm; a carton measures 56 cm x 30 cm x 36 cm and is filled completely.
    box volume     = 8 x 6 x 12 = 576 cm^3
    carton volume  = 56 x 30 x 36 = 60 480 cm^3
    number of boxes = 60 480 / 576 = 105 boxes

Pattern 2 — straightforward word problems
- A fridge with base 30 cm, breadth 45 cm, height 120 cm: V = 30 x 45 x 120 = 162 000 cm^3.
- A cuboid with base length 30 m, height 16 m, breadth 10 m: V = 30 x 16 x 10 = 4800 m^3.
- A cube-shaped box of side 3 mm: V = 3^3 = 27 mm^3.
- A Rubik's cube of side 10 cm: V = 10^3 = 1000 cm^3.

Pattern 3 — convert to the SAME unit first
You can only multiply measurements that share a unit. Convert everything first (100 cm = 1 m, 10 mm = 1 cm).
- 8 m x 5 m x 400 cm: change 400 cm to 4 m, then 8 x 5 x 4 = 160 m^3.
- 35 cm x 12 cm x 1.5 mm: change 1.5 mm to 0.15 cm, then 35 x 12 x 0.15 = 63 cm^3.

Pattern 4 — "will it fit / is it allowed?"
Karmela's suitcase is 33.5 cm x 60.5 cm x 20.1 cm. The airline limit is 40 737 cm^3.
    V = 33.5 x 60.5 x 20.1 = 40 737.675 cm^3
This is over the limit by 0.675 cm^3, so NO, she cannot use the suitcase.

Volume and capacity
Capacity is how much liquid a container holds. The key conversion is:
    1 litre = 1000 cm^3
Example: 8 litres of apple juice (= 8000 cm^3) is poured into a container measuring 10 cm x 9 cm x 40 cm.
    container volume = 10 x 9 x 40 = 3600 cm^3
    juice left over  = 8000 - 3600 = 4400 cm^3 left in the jug.

Linking volume and surface area
A cuboid has volume 600 mm^3 with two sides 10 mm and 15 mm. The missing side is 600 / 10 / 15 = 4 mm.
Its surface area is then 2(10 x 15 + 10 x 4 + 15 x 4) = 2(150 + 40 + 60) = 500 mm^2.

Key habits
- Decide what is being asked: a volume, a number of items, or a capacity in litres.
- Check the units are all the same BEFORE multiplying; convert if they are not.
- Round sensibly: for "how many boxes/items" the answer is a whole number.
""",
    },
]


# ============================================================
# Material B — Surface Area of a Prism
# ============================================================
SURFACE_CHUNKS = [
    {
        'title': 'Surface Area of Cuboids',
        'summary': "What surface area means, why a cuboid has three pairs of equal faces, the formula SA = 2(lw + lh + wh), using nets, the surface area of a cube (6 x side^2), and a real-life cost example.",
        'content': """Surface Area of Cuboids (Year 7 Maths, Unit 7)

What is surface area?
The SURFACE AREA of a 3D shape is the TOTAL area of all of its faces added together. Because it is an area, it is measured in SQUARE units: mm^2, cm^2, m^2.
A good way to picture it is to "unfold" the solid into its NET — a flat diagram of all the faces — and add up the areas of the flat shapes.

A prism is a 3D shape with two congruent (identical), parallel faces called the bases, joined by rectangular (or parallelogram) faces. A cuboid is a rectangular prism.

Surface area of a cuboid
A cuboid has 6 faces that come in 3 matching pairs:
    top and bottom   -> each = length x width   (l x w)
    front and back   -> each = length x height  (l x h)
    two ends/sides   -> each = width x height   (w x h)
So:
    Surface area = 2 x (l x w) + 2 x (l x h) + 2 x (w x h)
                 = 2(lw + lh + wh)

Worked Example 1 — a 4 cm x 3 cm x 2 cm box
    A1 = 4 x 3 = 12 cm^2  (top and bottom)
    A2 = 4 x 2 = 8  cm^2  (front and back)
    A3 = 2 x 3 = 6  cm^2  (the two ends)
    Surface area = 2 x 12 + 2 x 8 + 2 x 6 = 24 + 16 + 12 = 52 cm^2

Surface area of a cube
A cube has 6 identical square faces, each of area side x side, so:
    Surface area of a cube = 6 x side^2
Example: a cube with side 9.8 mm has SA = 6 x 9.8^2 = 6 x 96.04 = 576.24 mm^2.

Real-life Example — cost of a garden shed
A rectangular garden shed is 6 m long, 4 m wide and 2 m high, made of metal sheeting costing $15 per square metre. (The shed sits on the ground, so the floor is not covered.)
    roof          A1 = 6 x 4 = 24 m^2
    two ends      A2 = 4 x 2 = 8  m^2 each
    front + back  A3 = 6 x 2 = 12 m^2 each
    total area = 24 + 2 x 8 + 2 x 12 = 64 m^2
    cost = 64 x $15 = $960

Practice answers
- Rectangular prism 95 m x 42 m x 3 m: SA = 2(95x42 + 95x3 + 42x3) = 8802 m^2.
- Cuboid 11 cm x 9 cm x 8 cm: SA = 2(99 + 88 + 72) = 518 cm^2.
- Cube of side 10 mm: SA = 6 x 10^2 = 600 mm^2.

Key habits
- Surface area is always in SQUARE units (cm^2, m^2).
- Find the three different face areas, then double each one (or use 2(lw + lh + wh)).
- Read the question: a real object like a shed or an open tank may be missing one or more faces.
""",
    },
    {
        'title': 'Surface Area of Triangular and Other Prisms',
        'summary': "The general rule SA of a prism = 2 x area of the cross-section + perimeter of the cross-section x length, drawing nets of triangular prisms, and a fully worked wedge example.",
        'content': """Surface Area of Any Prism

A prism has the SAME cross-section all the way along its length. To find its surface area there are two parts:
    1. the TWO end faces (the cross-section), and
    2. the rectangular faces that wrap around the sides.
This gives the general rule:
    Surface area of a prism = 2 x (area of cross-section) + (perimeter of cross-section) x length

Drawing a net helps you not to miss a face. For a TRIANGULAR prism the net is:
    - 2 triangles (the two ends), plus
    - 3 rectangles (one for each side of the triangle), each as long as the prism.

Worked Example 2 — a triangular "wedge"
The cross-section is a right-angled triangle with base 12 cm and height 5 cm (so the sloping side, by Pythagoras, is 13 cm). The prism is 7 cm long.
Net areas:
    A1 = 1/2 x b x h = 1/2 x 12 x 5 = 30 cm^2  (each triangular end)
    A2 = 7 x 5  = 35 cm^2   (rectangle on the 5 cm side)
    A3 = 12 x 7 = 84 cm^2   (rectangle on the 12 cm side)
    A4 = 13 x 7 = 91 cm^2   (rectangle on the 13 cm sloping side)
    total surface area = 2 x A1 + A2 + A3 + A4
                       = 2 x 30 + 35 + 84 + 91 = 270 cm^2
Notice this is exactly the rule above: 2 x (area of triangle) + (perimeter 5+12+13) x length 7 = 60 + 30 x 7 = 60 + 210 = 270 cm^2.

More worked surface areas
- A cuboid 4 in x 5.5 in x 12 in: SA = 2(4x5.5 + 4x12 + 5.5x12) = 2(22 + 48 + 66) = 272 in^2.
- A triangular prism with a 8 m base, 5 m height triangle (sloping sides 6.4 m) and length 14 m: SA = 2 x (1/2 x 8 x 5) + (6.4 + 6.4 + 8) x 14 = 40 + 20.8 x 14 = 331.2 m^2.

Key habits
- Identify the cross-section (the shape that is the same all along the prism).
- Find its area and its perimeter.
- Surface area = 2 x area + perimeter x length. Drawing the net is the safest way to be sure you have counted every face once.
- Use Pythagoras (a^2 + b^2 = c^2) when the sloping side of a triangular cross-section is not given.
""",
    },
    {
        'title': 'Real-life Surface Area Problems',
        'summary': "Applying surface area to real objects: varnishing bookends, a squash court playing surface, a leather handbag, and a large greenhouse where Pythagoras is needed to find the roof length.",
        'content': """Real-life Surface Area Problems

Surface area answers questions like "how much material / paint / glass do we need?". The recipe is usually: find the surface area, then multiply by an amount-per-square-unit, or divide by how much one tin/coat covers.

Bookends and varnish
Tracy owns 8 wooden bookends shaped like an L-prism. One bookend has a surface area of 364 cm^2.
- Total surface area of all 8 = 8 x 364 = 2912 cm^2.
- If 50 ml of varnish covers 2000 cm^2, the varnish needed = 2912 / 2000 x 50 = 72.8 ml.

Squash court playing area
A squash court is a cuboid room. You may have to add only SOME of the faces — for example the floor plus the walls below a line, but not the ceiling or a marked-off board. Always re-read which surfaces actually count, then add just those. (Worked answer for the textbook court: 167.4 m^2.)

Triangular-prism handbag
A handbag is a triangular prism: the base measures 28 cm across the front and 11 cm on the side, with a vertical height of 14 cm. Ignoring the strap and any overlap, the material needed is its surface area = 2 x (triangular end) + the wrap-around rectangles. (Worked answer: about 1304.3 cm^2.)

Packaging and the environment
When a company changes a box from 10 cm x 2 cm x 5 cm to 11 cm x 3 cm x 6 cm, both the volume AND the surface area change (here volume goes up by 98 cm^3 and surface area by 74 cm^2). More surface area means more cardboard, more printing and more waste — surface area is one way to judge the environmental cost of packaging.

A greenhouse made of glass (extension)
A commercial "Venlo" greenhouse has 10 equal peaked roof sections. It is 48 m deep, the walls are 5 m high, and each sloping roof piece is 2.2 m long and rises 1 m above the wall.
- Two side walls: 2 x (5 x 48) = 480 m^2.
- 20 sloping roof panels: 2.2 x 48 x 20 = 2112 m^2.
- Use Pythagoras for the base of one peak: 2 x sqrt(2.2^2 - 1^2) = 3.92 m, so the front length is 10 x 3.92 = 39.2 m.
- Front and back walls: 2 x (5 x 39.2) = 392 m^2.
- Total glass = 480 + 2112 + 392 = 2984 m^2.
- Growing capacity (volume, ignoring the roof) = 48 x 5 x 39.2 = 9408 m^3.

Key habits
- Decide exactly which faces the question wants (a real object may be open, or only partly covered).
- Surface area uses square units; multiply by cost-per-area or divide by coverage-per-tin as needed.
- Use Pythagoras to find any missing slant length before adding up the faces.
""",
    },
]


MATERIALS = [
    {
        'title': 'Unit 7 - Volume of Cuboids',
        'description': 'Year 7 Maths Unit 7: the volume of cuboids and cubes. Counting unit cubes, the formula V = l x w x h, finding a missing length by dividing, the volume of a cube and cube roots, and real-life problems on packing, capacity (litres) and unit conversion.',
        'source_content': '(curated from mock/math/Y7/volume/Kami Export - Unit 7 - Volume-of-Cuboids.pdf)',
        'sort_order': 1000,
        'chunks': VOLUME_CHUNKS,
    },
    {
        'title': 'Unit 7 - Surface Area of a Prism',
        'description': 'Year 7 Maths Unit 7: the surface area of prisms. Surface area of cuboids and cubes via 2(lw + lh + wh) and nets, the general prism rule (2 x cross-section + perimeter x length) for triangular and other prisms, and real-life applications (varnish, packaging, a glass greenhouse).',
        'source_content': '(curated from mock/math/Y7/volume/Unit 7 - Surface Area of a Prism.pdf)',
        'sort_order': 1001,
        'chunks': SURFACE_CHUNKS,
    },
]


def build_material(spec, admin_id) -> Material:
    title = spec['title']
    existing = Material.query.filter_by(title=title, year_group=7).first()
    if existing:
        print(f'Material "{title}" already exists (id={existing.material_id}). Deleting first.')
        chunk_ids = [c.chunk_id for c in MaterialChunk.query.filter_by(material_id=existing.material_id).all()]
        if chunk_ids:
            ChunkYoutubeVideo.query.filter(ChunkYoutubeVideo.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
            DrillQuestion.query.filter(DrillQuestion.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
            Question.query.filter(Question.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
            MaterialChunk.query.filter_by(material_id=existing.material_id).delete(synchronize_session=False)
        db.session.delete(existing)
        db.session.commit()

    material = Material(
        title=title,
        subject='Maths',
        year_group=7,
        description=spec['description'],
        source_type='pdf',
        source_content=spec['source_content'],
        material_type='lesson',
        status='published',
        difficulty='normal',
        language='en',
        sort_order=spec['sort_order'],
        created_by=admin_id,
    )
    db.session.add(material)
    db.session.flush()
    print(f'Created Material id={material.material_id}: {title}')

    for i, c in enumerate(spec['chunks'], 1):
        chunk = MaterialChunk(
            material_id=material.material_id,
            title=c['title'],
            summary=c['summary'],
            content=c['content'],
            sort_order=i,
        )
        db.session.add(chunk)
        db.session.flush()
        print(f'  chunk {i} (id={chunk.chunk_id}): {c["title"]}  ({len(c["content"])} chars)')

    return material


def main() -> int:
    with app.app_context():
        admin = Parent.query.filter_by(role='admin').first()
        if not admin:
            print('No admin parent found. Aborting.')
            return 1

        created = []
        for spec in MATERIALS:
            mat = build_material(spec, admin.parent_id)
            created.append(mat)

        db.session.commit()

        print('\n=== DONE ===')
        for mat in created:
            chunks = MaterialChunk.query.filter_by(material_id=mat.material_id)\
                .order_by(MaterialChunk.sort_order).all()
            cids = ','.join(str(c.chunk_id) for c in chunks)
            print(f'material_id={mat.material_id} "{mat.title}"  chunks=[{cids}]')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
