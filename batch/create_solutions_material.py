"""Y7 Science: Solutions, Acids and Alkalis マテリアルを手動構築。

Claude が mock/material/Y7/Solution, Acids and Alkalis/ 配下の5 PDFsを読んで、
最適なチャンク構造で Material + MaterialChunks を作成する。

Usage:
    docker exec elearn_app python batch/create_solutions_material.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk


CHUNKS = [
    {
        'title': 'Unit Overview: Solutions, Acids and Alkalis',
        'summary': "This unit covers the properties of solutions, the effect of temperature on solubility, and the chemistry of acids and alkalis. You will learn key vocabulary, carry out experiments, analyse data with graphs, and understand the pH scale.",
        'content': """Unit: MYP1E - Solutions, Acids and Alkalis (Year 7 Science)

Statement of Inquiry (SOI):
Materials with differing properties helped to create today's global society and may hold the answers to some of the problems of the future.

Inquiry Question:
How have the interactions between chemical solutions transformed society for both the better and the worse?

Key Concept: Change
Related Concepts: Interactions, Transformations
Global Context: Globalisation and sustainability

What you will learn:

Topic 1 — Solutions
- Explain the terms solute, solvent and solution
- Describe what is meant by the terms soluble and insoluble
- Describe the effect of saturation on dissolving
- Investigate the effect of temperature on solubility

Topic 4 — Acids and Alkalis
- Name and write the chemical formulas for common acids and alkalis
- Describe the pH scale in terms of concentration of hydrogen ions
- Describe how litmus paper and universal indicator can be used as indicators

Skills practised:
- Critical thinking: gather and organise information to formulate an argument
- Research: locate, evaluate, synthesise information from multiple sources
- Experimental: design and perform an investigation, record results, plot graphs
""",
    },
    {
        'title': 'What is a Solution? (Key Terms)',
        'summary': "Introduces the three core words used when substances mix with liquids: solute, solvent, and solution. Also covers what it means for something to be soluble or insoluble.",
        'content': """Key Terms

Solution:
A special type of mixture formed when a solid dissolves in a liquid.

Solute:
The solid part of a solution — the substance that dissolves.

Solvent:
The liquid in which a solute dissolves. The most common solvent is water, but some solutes dissolve in other solvents such as oil or nail varnish remover.

Soluble:
A substance is soluble if it dissolves in a liquid (usually water).

Insoluble:
A substance is insoluble if it does not dissolve easily.

Example — fill in the blanks
"When a solid dissolves in a liquid it makes a special type of mixture called a SOLUTION. The solid part of the solution is called the SOLUTE and the liquid it dissolves in is called the SOLVENT. The most common type of solvent is water, but some solutes dissolve in other solvents such as oil or NAIL VARNISH REMOVER. A substance which dissolves in water is called SOLUBLE; a substance which does not dissolve easily is called INSOLUBLE."

Visualising particles
When a solute dissolves, its particles spread out between the solvent's particles. In a labelled diagram you should show both types of particles mixed together.
""",
    },
    {
        'title': 'Sorting Soluble and Insoluble Substances',
        'summary': "Practice identifying whether common substances dissolve in water. Also covers a real-world example: brine, the salt-water solution found in tinned tuna.",
        'content': """Classify each substance as SOLUBLE or INSOLUBLE in water

Substances to classify:
- salt
- sand
- flour
- sugar
- oil
- copper sulphate
- iron filings

Answers
Soluble (dissolves in water):  salt, sugar, copper sulphate
Insoluble (does NOT dissolve in water):  sand, flour, oil, iron filings

Real-world solution: Brine
Brine is a common solution found in food (e.g. tinned tuna) and in salted water used for cooking or preserving food.
- Solute:  salt (sodium chloride, NaCl)
- Solvent: water

Extension question
If you put too many spoonfuls of sugar into your tea, not all of it dissolves. Why?
Answer idea: The water (solvent) can only hold a limited number of sugar particles between its own particles. Once all the spaces are filled, the water is said to be SATURATED and no more sugar can dissolve. The extra sugar sinks to the bottom as undissolved solid.
""",
    },
    {
        'title': 'The Effect of Temperature on Solubility (Experiment)',
        'summary': "A hands-on investigation of how temperature changes the solubility of ammonium chloride. Covers apparatus, safety, and the step-by-step procedure.",
        'content': """Introduction
Most solid substances that are soluble in water are more soluble in hot water than in cold water. This experiment examines solubility at various temperatures using ammonium chloride.

Equipment
Apparatus:
- Eye protection
- Boiling tubes
- Beaker (to act as ice bath), 250 cm³
- Beaker (to act as hot water bath), 250 cm³
- Stirring thermometer (-10 to 110 °C)
- Measuring cylinder or graduated pipette, 250 cm³
- Wooden tongs (to hold the hot boiling tube)

Chemicals:
- Ammonium chloride
- Ice

Health and Safety
- Always wear eye protection.
- Ammonium chloride is harmful if swallowed and is an eye irritant (CLEAPSS Hazcard HC009a).
- Use wooden tongs when handling hot boiling tubes.

Procedure
1. Set up a hot water bath and an ice bath.
2. Put 2.6 g of ammonium chloride into a boiling tube. Add 4 cm³ of water.
3. Warm the boiling tube in the hot water bath until the solid dissolves.
4. Put the boiling tube in the ice bath and stir with the thermometer. Use wooden tongs to hold it if necessary.
5. Note the temperature at which crystals FIRST appear. Record this "crystallisation temperature" in the data table.
6. Add 1 cm³ more water. Warm the solution again, stirring until all the crystals dissolve.
7. Repeat the cooling and note the new crystallisation temperature.
8. Repeat until a total of 10 cm³ of water has been used.
""",
    },
    {
        'title': 'Solubility Data Analysis and Graphing',
        'summary': "Use the experimental data to construct a solubility-versus-temperature graph and answer analysis questions about variables, trends, and particle theory.",
        'content': """Part 1 — Data Table
From the experiment, you should have data similar to this:

| Volume of water (cm³) | Solubility (g/dm³) | Crystallisation Temp (°C) |
|---|---|---|
| 4  | 650 | 72 |
| 5  | 520 | 63 |
| 6  | 433 | 55 |
| 7  | 371 | 48 |
| 8  | 325 | 42 |
| 9  | 289 | 37 |
| 10 | 260 | 33 |

Part 2 — Construct the Graph
- X-axis: Temperature (°C)
- Y-axis: Solubility (g/dm³)
- Plot the data points and draw a best-fit curve.

Part 3 — Analysis Questions
1. What is meant by "solubility"?
2. Identify the independent and dependent variables in this experiment.
3. Describe the relationship between temperature and solubility.
4. Use your graph to estimate the solubility at 50 °C.
5. Use your graph to estimate the temperature at which solubility is 400 g/dm³.
6. Explain the trend using particle theory (how do particles behave at higher temperatures?).
7. Between which pair of temperatures does solubility increase the most?
8. Is the relationship linear or curved? Explain how you can tell from the graph.
9. Suggest TWO possible sources of error in the experiment.
10. Suggest ONE improvement to the method.
11. Predict the solubility at 80 °C by extrapolating your graph.

Key vocabulary from this worksheet:
- Independent variable: the one you change (temperature)
- Dependent variable: the one you measure (solubility)
- Extrapolation: extending the graph line beyond measured data points to predict values
""",
    },
    {
        'title': 'Acids and Alkalis: Key Terms',
        'summary': "Key terms: acid, alkali, base, neutral, neutralisation. These define the core chemistry you need to know for this unit.",
        'content': """Core Definitions

acid:
An acid has a pH value of LESS than 7. A strong acid will turn universal indicator RED.

alkali:
An alkali has a pH value of MORE than 7. A strong alkali will turn universal indicator BLUE or PURPLE.

base:
A substance that will NEUTRALISE an acid. Unlike an alkali, a base does NOT dissolve in water.
(All alkalis are bases, but not all bases are alkalis.)

neutral:
A solution with a pH value of exactly 7. Water is a good example of a neutral substance.

neutralisation:
The reaction that happens when an alkali is added to an acid, producing a neutral solution.
Acid + Alkali → Neutral solution (salt + water)
""",
    },
    {
        'title': 'The pH Scale and Indicators',
        'summary': "Key terms: pH scale, indicator, litmus paper, universal indicator. How scientists measure and identify acids and alkalis.",
        'content': """The pH Scale

pH scale:
A number scale used to determine whether a solution is acidic, neutral, or alkaline.
- pH 0–6 → acidic (lower = stronger acid)
- pH 7 → neutral
- pH 8–14 → alkaline (higher = stronger alkali)

Indicators

indicator:
A substance that changes colour to show whether a solution is acidic or alkaline.

litmus paper:
Paper strips that act as indicators. There are two types:
- Blue litmus turns RED in acid.
- Red litmus turns BLUE in alkali.
- Neither colour changes in neutral solutions.

universal indicator:
A mixture of dyes that changes through a range of colours to show the actual pH value, not just acid or alkali. Often comes as a paper strip or liquid with a matching colour chart.

How to use indicators
1. Add a few drops of universal indicator to the solution (or dip a test strip).
2. Compare the resulting colour to the pH chart.
3. Read off the pH number and classify as acid / neutral / alkali.
""",
    },
    {
        'title': 'Common Laboratory Acids and Alkalis',
        'summary': "Key chemicals you will meet in school science experiments, including their formulas and everyday examples.",
        'content': """Common Acids

hydrochloric acid (HCl):
A strong acid often used in school science experiments.

sulphuric acid (H₂SO₄):
Another strong acid commonly used in labs, also found in car batteries.

citric acid:
A weak acid found naturally in lemons, limes, and other citrus fruits. Used in cooking and cleaning.

Common Alkali

sodium hydroxide (NaOH):
A strong alkali often used in school science experiments. Also found in some drain cleaners and in soap making.

Why formulas matter
Chemical formulas tell you which elements are in a substance and in what proportion. For example, H₂SO₄ means the molecule contains 2 hydrogen atoms, 1 sulphur atom, and 4 oxygen atoms.

Quick reference
| Chemical | Formula | Classification |
|---|---|---|
| Hydrochloric acid | HCl | Strong acid |
| Sulphuric acid | H₂SO₄ | Strong acid |
| Citric acid | — | Weak acid |
| Sodium hydroxide | NaOH | Strong alkali |
""",
    },
    {
        'title': 'Laboratory Equipment and Safety',
        'summary': "Key terms for the glassware, measuring tools, and safety concepts used in the Solutions and Acids & Alkalis topics.",
        'content': """Glassware and Measuring Apparatus

burette:
A long glass tube with a tap at one end. Used to measure out a precise volume of liquid (commonly used in titrations).

boiling tube:
A long glass tube used for heating or holding liquids during experiments.

beaker:
A cylindrical glass container for stirring, mixing, or holding liquids. Can also be used as a water bath.

measuring cylinder:
Apparatus used to measure the volume of a liquid accurately.

graduated pipette:
A slender tube used for transferring or measuring small amounts of liquid.

stirring thermometer:
A thermometer that can also be used to stir a solution while measuring its temperature.

Safety Equipment

eye protection:
Safety goggles that must be worn whenever using chemicals or heating liquids.

wooden tongs:
Used to hold hot equipment safely (e.g. a hot boiling tube taken out of a water bath).

hazard symbols:
Symbols on chemical containers that warn of potential dangers (e.g. corrosive, toxic, flammable).

corrosive:
A substance labelled "corrosive" may dissolve or burn skin, eyes, or other materials on contact.

Concentration Terms

concentrated:
A solution has a high proportion of solute compared to solvent (a lot of the solute in a small amount of solvent).

dilute:
A solution has a small amount of solute compared to solvent. A concentrated solution can be diluted by adding more water.
""",
    },
]


def main() -> int:
    with app.app_context():
        # 既存の同名 material をチェック
        existing = Material.query.filter_by(
            title='MYP1E - Solutions, Acids and Alkalis',
            year_group=7,
        ).first()
        if existing:
            print(f'Material already exists: id={existing.material_id}. Deleting first.')
            # chunks + related を先に掃除
            from models.drill import DrillQuestion
            from models.material import Question
            from models.youtube_video import ChunkYoutubeVideo
            chunk_ids = [c.chunk_id for c in MaterialChunk.query.filter_by(material_id=existing.material_id).all()]
            if chunk_ids:
                ChunkYoutubeVideo.query.filter(ChunkYoutubeVideo.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
                DrillQuestion.query.filter(DrillQuestion.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
                Question.query.filter(Question.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
                MaterialChunk.query.filter_by(material_id=existing.material_id).delete(synchronize_session=False)
            db.session.delete(existing)
            db.session.commit()

        # 管理者を取得
        from models.parent import Parent
        admin = Parent.query.filter_by(role='admin').first()
        if not admin:
            print('No admin parent found. Aborting.')
            return 1

        material = Material(
            title='MYP1E - Solutions, Acids and Alkalis',
            subject='Science',
            year_group=7,
            description='Year 7 Science unit covering solutions, solubility, and the basics of acids and alkalis. Based on MYP1E syllabus with student experiments and a glossary.',
            source_type='pdf',
            source_content='(curated from 5 PDFs in mock/material/Y7/Solution, Acids and Alkalis/)',
            material_type='lesson',
            status='published',
            difficulty='normal',
            language='en',
            sort_order=999,
            created_by=admin.parent_id,
        )
        db.session.add(material)
        db.session.flush()
        print(f'Created Material id={material.material_id}')

        for i, c in enumerate(CHUNKS, 1):
            chunk = MaterialChunk(
                material_id=material.material_id,
                title=c['title'],
                summary=c['summary'],
                content=c['content'],
                sort_order=i,
            )
            db.session.add(chunk)
            print(f'  chunk {i}: {c["title"]}')

        db.session.commit()
        print(f'\nDone. material_id={material.material_id}, {len(CHUNKS)} chunks.')
        print(f'URL: http://localhost:5000/admin/materials/{material.material_id}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
