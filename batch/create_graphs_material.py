"""Y7 Maths: Unit 6 - Graphs and Data Handling マテリアルを手動構築。

PDFの実際の内容 (特に時系列グラフ + トレンド + 季節変動 + 各種Example) に忠実に構成。
  - Types of Graph PDF は 実は Time Series が主題
  - Pie Charts PDF で pie chart を深掘り

Usage:
    docker exec elearn_app python batch/create_graphs_material.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from models import db
from models.material import Material, MaterialChunk


CHUNKS = [
    {
        'title': 'Types of Data, Frequency Tables and Tally Charts',
        'summary': "Identify types of data, record observations with a tally chart, and summarise them in a frequency table — the starting point for every graph in this unit.",
        'content': """Unit 6 — Graphs and Data Handling (Year 7 Maths)

Types of Data
Data is information collected from a survey or experiment. There are two main types:

1. Qualitative (categorical) data — words or labels that describe categories.
   Examples: favourite colour, type of pet, chosen Quality Street sweet, blood type.

2. Quantitative (numerical) data — numbers you can measure or count. Two sub-types:
   (a) Discrete — whole numbers from counting (e.g. number of goals, siblings).
   (b) Continuous — any value on a scale, often measured (e.g. height, temperature).

Frequency Tables
A frequency table records how many times each category or value appears.
It has at least two columns:
- Category (or value)
- Frequency

Tally Charts
While collecting data, use a tally chart:
- Draw one vertical line for each observation.
- After four lines, cross them with a diagonal fifth line to make a group of five (||||).
- Count the groups of 5 and any leftover ticks to get the frequency.

Why totals matter
The total frequency is crucial — you will use it to decide bar heights (bar graphs) and to calculate slice angles (pie charts) in later sections.
""",
    },
    {
        'title': 'Bar Graphs, Line Graphs and Why Graphs Matter',
        'summary': "Bar graphs (with gaps) for categorical data, line graphs for continuous data, and the bigger picture — why graphs matter for predicting, comparing, and solving real problems.",
        'content': """Bar Graphs (gaps between bars)

Use a bar graph for CATEGORIES (qualitative) or discrete counts.
Rules:
1. Horizontal axis = categories, vertical axis = frequency (starts at 0).
2. Bars have the same WIDTH.
3. IMPORTANT: leave a GAP between bars — this shows categories are separate.
4. Label axes, give a title.

Why the gaps?
If the bars touched (no gaps), it would be a HISTOGRAM — used for continuous data in intervals.

Line Graphs
Line graphs connect points to show how a quantity changes across a CONTINUOUS variable (usually time). Ideal for:
- Temperature over a day
- Share prices over a week
- Plant height over several weeks
- COVID-19 cases each day

To draw:
1. Put the continuous variable on the x-axis.
2. Put the measured quantity on the y-axis.
3. Plot points and join them with straight lines.
4. Label both axes and give a title.

Discuss the SIGNIFICANCE of a graph
Why do graphs matter? They help us:
- PREDICT future outcomes by looking for patterns.
- Provide correct PREVENTATIVE CARE by redirecting resources where the trend is worsening.
- Compare on a GLOBAL level — see what other countries are doing.
- Answer "When will I ever need Maths?" — graphs solve real-life problems.
""",
    },
    {
        'title': 'Time Series Graphs: Definition and Trends',
        'summary': "A time-series graph is a sequence of discrete data observed over time. Learn to spot rising, falling, and level trends, and practise with real-world examples including COVID, UK elections, and gas bills.",
        'content': """What is a Time-Series Graph?
A time-series graph is a SEQUENCE of discrete data observed over a period of TIME.
Example: number of cars sold over 2008, 2009, 2010.

Real-world examples the class has seen
- COVID-19 case numbers monitored country-by-country (April 2020 onward).
- UK general election opinion polls using a 15-poll moving average (the larger circles at the end are the actual election results). Note: the PM resigned around June 2019.
- Mr Jones' gas bills over a 2-year period — his wife thought the bills were actually getting CHEAPER once you plot them as a time series.

Reading Trends
A general TREND is the way that data changes over time. A TREND LINE shows the general trend. Data can show:
- Rising trend (values increase over time)
- Falling trend (values decrease over time)
- Level trend — note this is NOT the same as "no trend"; it means values stay roughly constant.

Practice: Rising or Falling?
- The production of electricity over the last 100 years → RISING
- The cost of buying bread over the last 30 years → RISING
- Infant death rates in the UK over the past 50 years → FALLING
- The value of a car over a 10-year period → FALLING

True or False? (from class discussion on UK birth rates)
1. "The birth rates show a falling trend" → FALSE
2. "The birth rates increase by 20,000 from 2008 to 2013" → TRUE
3. "The population of Russia has increased over this period" → TRUE

Describing trends in words
When describing a time-series graph, always say:
- Is the overall trend rising, falling or level?
- Are there any sudden changes (spikes or dips)? When did they happen?
- Are there any seasonal/cyclical patterns? (more on this in the next section)

Life Expectancy Dataset (1905–2010)
Germany, Iraq, and UK data were compared over 100+ years. Key conclusions:
- All 3 countries show an INCREASING trend — life expectancy rises over time.
- UK and Germany trends are very SIMILAR.
- Iraq increased dramatically early on, but DECLINED in the 1980s (conflict affected life expectancy).
""",
    },
    {
        'title': 'Plotting Time Series, Seasonal Variations, and Analysis',
        'summary': "Plot time-series data, draw trend lines, recognise seasonal variations (4 seasons, weekly cycles), and calculate means to compare different periods.",
        'content': """Plotting Time Series Graphs

Example 1 — Company Profit over 11 years
Plot each year's profit as a point on a time series graph, join the points, and describe the overall trend. Look for a rising, falling, or level pattern.

Example 2 — Company Sales over 10 years
After plotting, the line shows a FALLING trend — sales are declining year on year.

Variations in a Time Series
A time-series graph can show TWO kinds of variation:
- A general TREND (rising / falling / level)
- SEASONAL variations — patterns that repeat within a fixed cycle
  · 4 seasons of the year (Spring/Summer/Autumn/Winter)
  · 7-day weekly cycle (days of the week)

Which of these show seasonal variations?
- The sale of breakfast cereals → NO (demand is roughly steady year-round)
- The number of bank accounts opened → NO
- The number of hours of sunshine → YES (more in summer, less in winter)
- The sale of swimsuits → YES (summer peak)
- Quarterly gas bills → YES (winter heating peak)

Example 3 — Quarterly Sales 2012–2014 (in 1000s)
A company's quarterly sales over 3 years were plotted. From the graph:
a) Trend = RISING (overall).
b) Each year's Q1 figure increases by about 5,000 year on year.
c) Mean 2012 = (10 + 30 + 40 + 25) ÷ 4 = 105 ÷ 4 = 26.25 (i.e. 26,250 units)
d) Mean 2014 = (20 + 60 + 70 + 45) ÷ 4 = 195 ÷ 4 = 48.75 (i.e. 48,750 units)
e) Conclusion: average sales have nearly DOUBLED in 3 years.

Task Walkthrough (Tasks 1–10 in the worksheet)

Task 1–4: For each data table (a) draw a time series graph, (b) draw a trend line.
- Some show a DECREASING trend line.
- Others show an INCREASING trend line.

Task 5: Complete the time series graph, draw a trend line, describe the trend, compare the sales in the first quarter of each year, calculate the mean sales over 3 years, and PREDICT the sales in the fourth quarter of 2015.
Worked answers:
- Trend line shows a DECREASING trend.
- 2012→2013 drop is only about 5,000, but 2013→2014 drop is 20,000.
- Mean = 780,000 ÷ 12 = 40,000.
- Prediction for Q4 2015 should be between 15,000 and 25,000 based on the falling trend.

Task 6: Read values from a time series graph showing websites online.
- 175,000,000 to 180,000,000 at the end.
- Year 2000 = 25,000,000 vs 2007 = 125,000,000 → increase of 100,000,000.
- From 2004 to 2010 is 6 years.

Tasks 7–10: further reading from graphs.
- UK 10,000 vs Africa 165,000 → find difference.
- UK 5,000 vs Africa 85,000 → difference 80,000.
- 1965: 240,000 and 1975: 220,000 → difference 196,000 (in the worked answer).

Skills you are practising
- Plotting points accurately from a data table.
- Drawing a trend line that best fits the data.
- Describing whether a trend is rising / falling / level.
- Spotting seasonal variations.
- Calculating means and predicting future values.
""",
    },
    {
        'title': 'Introduction to Pie Charts',
        'summary': "A pie chart (circle graph) divides a full circle (360°) into slices to show parts of a whole. This section introduces how a pie chart is built using a survey table.",
        'content': """Pie Charts (Circle Graphs)

A pie chart shows how a whole (100%, or a full circle of 360°) is split into parts.
Each slice represents one category. The bigger the slice, the larger that category's share.

Golden rule
A full circle = 360°.  Therefore the degrees of all the slices added together must equal 360°.

Starter example — "What is your favourite Quality Street?"

| Sweet            | Frequency | Degrees |
|------------------|-----------|---------|
| Strawberry Cream | 5         | 100°    |
| Orange Cream     | 3         | 60°     |
| Purple Hazelnut  | 6         | 120°    |
| Green Triangle   | 2         | 40°     |
| Other            | 2         | 40°     |
| TOTAL            | 18        | 360°    |

Notice that the frequencies add up to 18, and the degrees add up to 360°. Each person in the survey is worth 360° ÷ 18 = 20°. So a category with frequency 5 gets 5 × 20° = 100°, a category with frequency 3 gets 3 × 20° = 60°, and so on.

This "×20°" shortcut is the heart of Method 1 in the next section.

When to choose a pie chart
- You want to show SHARES of a total (e.g. how a budget is split, how a class voted).
- All parts add up to a single whole.
- The number of categories is small (usually 3–8) — too many slices are hard to read.
""",
    },
    {
        'title': 'Drawing Pie Charts — Method 1 (Degrees per Item)',
        'summary': "Method 1 works by finding the degrees per item (360° ÷ total frequency), then multiplying by each category's frequency. Best when the total divides nicely into 360.",
        'content': """Method 1 — Degrees per item

Easiest when the total frequency is a "friendly" number that divides into 360° exactly (e.g. 18, 24, 36, 60, 72, 90, 120, 180, 360).

Step-by-step
1. Add the frequencies to find the TOTAL.
2. Calculate the DEGREES PER ITEM by dividing 360° by the total: 360° ÷ Total.
3. Multiply each category's frequency by that "degrees-per-item" value to get its slice size.
4. Check: all slice sizes must add up to 360°.
5. Draw a circle, use a protractor to measure each slice, and label each with its category name.

Example A — Favourite Pies (Total = 60, each item = 360° ÷ 60 = 6°)

| Pie       | Frequency | Degrees = freq × 6° |
|-----------|-----------|---------------------|
| Apple     | 15        | 90°                 |
| Pork      | 12        | 72°                 |
| Banoffee  | 11        | 66°                 |
| Chocolate | 18        | 108°                |
| Other     | 4         | 24°                 |
| TOTAL     | 60        | 360° ✓              |

Example B — Favourite Pet (Total = 36, each item = 10°)

| Pet     | Frequency | Degrees |
|---------|-----------|---------|
| Cat     | 11        | 110°    |
| Dog     | 12        | 120°    |
| Fish    | 8         | 80°     |
| Hamster | 3         | 30°     |
| Rabbit  | 2         | 20°     |
| TOTAL   | 36        | 360° ✓  |

Example C — Goals Scored (Total = 24, each item = 15°)

| Goals    | Frequency | Degrees |
|----------|-----------|---------|
| 0        | 3         | 45°     |
| 1        | 5         | 75°     |
| 2        | 7         | 105°    |
| 3        | 5         | 75°     |
| 4 or more| 4         | 60°     |
| TOTAL    | 24        | 360° ✓  |

Task 1
Copy each table above, check you can reproduce the degree column, and then construct a fully labelled pie chart for each using a protractor.
""",
    },
    {
        'title': 'Drawing Pie Charts — Method 2 (Fraction of 360°)',
        'summary': "Method 2 uses fractions: each slice's angle is (frequency ÷ total) × 360°. Works for ANY total, even if it doesn't divide neatly into 360.",
        'content': """Method 2 — Fraction of 360°

Use this when the total does NOT divide neatly into 360 (totals of 50, 80, 90, 100, 250 etc.).

Formula
Angle for a category = (frequency ÷ total) × 360°.
Remember: the word "of" means multiply, so "14/80 of 360°" means "(14 ÷ 80) × 360°".

Example — Favourite Ice Cream (Total = 80)

| Flavour    | Frequency | Calculation        | Degrees |
|------------|-----------|--------------------|---------|
| Vanilla    | 14        | 14/80 × 360°       | 63°     |
| Mint       | 9         | 9/80 × 360°        | 40.5°   |
| Chocolate  | 21        | 21/80 × 360°       | 94.5°   |
| Strawberry | 19        | 19/80 × 360°       | 85.5°   |
| Orange     | 17        | 17/80 × 360°       | 76.5°   |
| TOTAL      | 80        |                    | 360° ✓  |

Tips
- If the result is not a whole number, keep one decimal place (e.g. 40.5°). Round only at the final step.
- Always check that your angles add up to 360° (allowing 1° for rounding).

When is Method 2 needed?
Any time the total frequency is NOT a factor of 360.
Examples:
- 50 students: 360 ÷ 50 = 7.2° per student.
- 100 people: 360 ÷ 100 = 3.6° per person (percentages work too — 1% = 3.6°).
- 250 votes: 360 ÷ 250 = 1.44° per vote.

Task 2 #1 — Traffic survey in Cleckheaton (Total = 270)

| Type       | Frequency | Calculation         | Degrees |
|------------|-----------|---------------------|---------|
| Cars       | 140       | 140/270 × 360°      | 187°    |
| Motorbikes | 70        | 70/270 × 360°       | 93°     |
| Vans       | 55        | 55/270 × 360°       | 73°     |
| Buses      | 5         | 5/270 × 360°        | 7°      |
| TOTAL      | 270       |                     | 360°    |

Tip: Because the "Buses" slice is so thin (only 7°), draw it LAST — start with the biggest slice for accuracy.

Task 2 #2 — Favourite TV brand (Total = 300)

| Brand      | Frequency | Calculation         | Degrees |
|------------|-----------|---------------------|---------|
| Samsung    | 89        | 89/300 × 360°       | 106.8°  |
| Sony       | 56        | 56/300 × 360°       | 67.2°   |
| LG         | 53        | 53/300 × 360°       | 63.6°   |
| Panasonic  | 78        | 78/300 × 360°       | 93.6°   |
| Toshiba    | 24        | 24/300 × 360°       | 28.8°   |
| TOTAL      | 300       |                     | 360°    |

Draw a fully labelled pie chart for each table.
""",
    },
    {
        'title': 'Reading and Interpreting Pie Charts',
        'summary': "Given a completed pie chart, work out how much each slice represents using percentages or angles. Essential for exam questions where you interpret a given chart.",
        'content': """Interpreting Pie Charts

When you are given a completed pie chart, you can work out how much each slice represents — either as a percentage OR directly in units (kg, £, people, etc.).

From percentage to amount
If a slice covers X% of the chart and the TOTAL amount is T, then:
Slice amount = (X ÷ 100) × T.

From degrees to amount
If a slice has an angle A° and the TOTAL amount is T, then:
Slice amount = (A ÷ 360) × T.

Example 1 — Housing Estate (540 houses total)
A pie chart shows types of housing on a new estate. Angles: Detached 90°, Semi-Detached 120°, Bungalows 40°, Terraced 110°.
  (a) Detached      → (90/360) × 540 = 135 houses
  (b) Semi-Detached → (120/360) × 540 = 180 houses
  (c) Bungalows     → (40/360) × 540 = 60 houses
  (d) Terraced      → (110/360) × 540 = 165 houses
  Total = 135 + 180 + 60 + 165 = 540 ✓

From percentage to amount
If a slice covers X% of the chart and the TOTAL amount is T, then:
Slice amount = (X ÷ 100) × T.

Example 2 — Human body composition (person weighing 50 kg)
Useful trick: find 10% first (5 kg), then scale.
  (a) Water (70%) = 7 × 5 = 35 kg.
  (b) Proteins (16%) = 16 × 0.5 = 8 kg.
  (c) Other dry elements (14%) = 14 × 0.5 = 7 kg.

Task 3 — Practice Reading Pie Charts

#1 — Favourite subject (900 pupils)
From the pie chart find how many voted for:
  (a) PE   (b) Science   (c) Maths.

#2 — Café drinks one weekend in Bedale (300 drinks sold)
From the pie chart find how many of each drink were sold:
  (a) Soft drinks   (b) Tea   (c) Hot chocolate   (d) Coffee.

#3 — Butter sales (450 kg across 7 days)
How many kg were sold on:
  (a) Monday  (b) Tuesday  (c) Wednesday  (d) Thursday  (e) Friday  (f) Saturday.

#4 — Train tickets (240 tickets)
Inspector's morning ticket counts:
  (a) Open return  (b) Season ticket  (c) Day return  (d) Travel pass.

Task 4 — Mixed interpretations

#1 — Book publishing costs (£1400)
Find the cost of: (a) Promotion  (b) Printing  (c) Paper  (d) Binding  (e) Royalties.

#2 — Overseas tourist traffic from India (20 million)
How many visited: (a) UK  (b) Others  (c) Japan  (d) USA.

#3 — New York share sales 2005 (1500 units total)
How many units were sold of: (a) HP  (b) Texas  (c) Apple  (d) Others  (e) IBM.

Why this matters
- Real-world reports (economics, elections, health surveys) are often shown as pie charts.
- Being able to read them accurately lets you check whether media claims match the data.
""",
    },
]


def main() -> int:
    with app.app_context():
        title = 'Unit 6 - Graphs and Data Handling'

        existing = Material.query.filter_by(title=title, year_group=7).first()
        if existing:
            print(f'Material "{title}" already exists (id={existing.material_id}). Deleting first.')
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

        from models.parent import Parent
        admin = Parent.query.filter_by(role='admin').first()
        if not admin:
            print('No admin parent found. Aborting.')
            return 1

        material = Material(
            title=title,
            subject='Maths',
            year_group=7,
            description='Year 7 Maths Unit 6: types of data, frequency tables, bar / line graphs, in-depth time-series analysis with trends and seasonal variations, followed by four focused sections on pie charts (introduction, two drawing methods, and interpretation).',
            source_type='pdf',
            source_content='(curated from 2 PDFs in mock/material/Y7/: Types of Graph + Pie Charts)',
            material_type='lesson',
            status='published',
            difficulty='normal',
            language='en',
            sort_order=999,
            created_by=admin.parent_id,
        )
        db.session.add(material)
        db.session.flush()
        print(f'Created Material id={material.material_id}: {title}')

        for i, c in enumerate(CHUNKS, 1):
            chunk = MaterialChunk(
                material_id=material.material_id,
                title=c['title'],
                summary=c['summary'],
                content=c['content'],
                sort_order=i,
            )
            db.session.add(chunk)
            print(f'  chunk {i}: {c["title"]}  ({len(c["content"])} chars)')

        db.session.commit()
        print(f'\nDone. material_id={material.material_id}, {len(CHUNKS)} chunks.')
        print(f'URL: http://localhost:5000/admin/materials/{material.material_id}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
