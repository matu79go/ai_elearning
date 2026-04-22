-- ============================================================
-- Y7 Science: Acids and Alkalis in Industry (Research)
-- Y7 Maths: Unit 6 - Measures of Central Tendency (Averages)
-- Source: mock/material/Y7/*.pdf (uploaded 2026-04-22)
-- ============================================================

-- ------------------------------------------------------------
-- Material 1: Science - Acids and Alkalis in Industry (Research)
-- ------------------------------------------------------------
INSERT INTO materials (title, description, source_type, material_type, source_content, file_path, subject, year_group, difficulty, language, status, sort_order, created_by)
VALUES (
  'MYP1E - Acids and Alkalis in Industry (Research)',
  'Year 7 MYP Science research sheet on industrial applications of acids and alkalis, covering fertilisers, soap, mining, and paper production, and their links to separation methods (crystallisation, filtration, evaporation).',
  'pdf',
  'lesson',
  '(curated from mock/material/Y7/Jo SUZUKI - year7_myp_science_research_sheet.pdf)',
  'mock/material/Y7/Jo SUZUKI - year7_myp_science_research_sheet.pdf',
  'Science',
  7,
  'normal',
  'en',
  'published',
  999,
  2
);

SET @sci_id = LAST_INSERT_ID();

INSERT INTO material_chunks (material_id, title, content, sort_order) VALUES
(@sci_id, 'Research Overview & Tips',
'Topic: Acids and Alkalis in Industry\n\nHow to use this research sheet\nStart with the recommended websites, then answer the guiding questions in your own words. Look for key science vocabulary such as acid, alkali, neutralisation, solution, filtration, evaporation, crystallisation, soluble, and insoluble.\n\nResearch goal\nExplain both the science process and the real-world impact of each topic.\n\nGeneral Research Tips\n1. Start simple - Use BBC Bitesize or Science Revision first before moving to harder websites.\n2. Search smart - Use keywords from this sheet to find the exact part you need.\n3. Use diagrams - Pictures and process diagrams often explain the science more clearly than long paragraphs.\n4. Think about impact - For each topic, find one benefit and one possible environmental or social problem.',
1),

(@sci_id, 'Sulfuric Acid and Fertilisers (Crystallisation)',
'Focus Question\nHow is a saturated solution of ammonium sulfate used to create solid fertiliser, and how does crystallisation (separation) impact food production?\n\nKeywords\nammonium sulfate, sulfuric acid, fertiliser, saturated solution, evaporation, crystallisation, neutralisation, crop growth, food production\n\nThe Science\nAmmonium sulfate is made by neutralising sulfuric acid with ammonia solution. The resulting salt is dissolved in water to form a saturated solution (a solution that cannot dissolve any more solute at that temperature). Evaporating water from the solution leaves crystals behind - this is called crystallisation. The solid crystals are collected and used as fertiliser.\n\nGuiding questions\n- What substances react together to make ammonium sulfate?\n- What does the word "saturated" mean in a solution?\n- How does evaporation help crystals begin to form?\n- Why is crystallisation a useful separation method for making a solid fertiliser?\n- How do fertilisers help farmers grow more food?\n- What could happen if too much fertiliser is used in the environment?\n\nHelpful idea\nCrystallisation changes a dissolved substance in solution into solid crystals that can be collected and used.',
2),

(@sci_id, 'Potassium Hydroxide and Soap (Saponification)',
'Focus Question\nHow does an alkali act as a solvent to dissolve fats, and which separation method is used to recover the pure soap from the mixture?\n\nKeywords\npotassium hydroxide, alkali, fats, oils, soap, saponification, mixture, separation, liquid soap, solid soap\n\nThe Science\nPotassium hydroxide (KOH) is a strong alkali. When mixed with fats and oils it breaks them down in a reaction called saponification, producing soap. The soap then has to be separated and purified from the rest of the mixture. Because potassium hydroxide makes a softer soap than sodium hydroxide, it is often used to make liquid soaps.\n\nGuiding questions\n- What is potassium hydroxide, and why is it called an alkali?\n- How does an alkali react with fats and oils to help make soap?\n- What is the name of the reaction that turns fats into soap?\n- How can soap be separated from the rest of the mixture?\n- Why is potassium hydroxide often used for softer or liquid soaps?\n- What are the advantages of using soap for cleaning oily substances?\n\nHelpful idea\nThe alkali helps break down fats, and then the soap must be separated and purified from the mixture.',
3),

(@sci_id, 'Hydrochloric Acid in Mining (Filtration)',
'Focus Question\nHow is acid used to dissolve metals into a solution, and how does filtration help remove the insoluble rock waste?\n\nKeywords\nhydrochloric acid, mining, metal solution, dissolve, filtration, insoluble, rock waste, extraction, slurry\n\nThe Science\nIn mining, hydrochloric acid (HCl) is used to dissolve useful metals out of rock. The metals form a solution while the rock that will not dissolve (insoluble rock waste) stays as a solid. Filtration separates the liquid containing the dissolved metal from the solid rock waste: the liquid passes through the filter, and the larger solid particles are trapped. Handling acids and waste safely is important to protect workers and the environment.\n\nGuiding questions\n- How can acid help dissolve useful metals into a liquid solution?\n- Why does some rock stay behind instead of dissolving?\n- What does the word "insoluble" mean?\n- How does filtration separate solid rock waste from the liquid?\n- Why might filtering waste be important for safety and the environment?\n- What are some risks of using acids in mining?\n\nHelpful idea\nFiltration allows the liquid containing dissolved metal to pass through, while larger insoluble solids are trapped.',
4),

(@sci_id, 'Sodium Hydroxide in Paper (Concentration Control)',
'Focus Question\nHow is the concentration of alkali solutions controlled to break down wood pulp, and how are chemicals separated to prevent environmental harm?\n\nKeywords\nsodium hydroxide, paper, wood pulp, concentration, lignin, chemical recovery, alkali, pollution prevention\n\nThe Science\nSodium hydroxide (NaOH) is used in paper making to break down wood pulp and remove lignin so that the fibres can be turned into paper. The concentration of the alkali solution (how much NaOH is dissolved in the water) must be controlled carefully - too strong and it damages the fibres, too weak and it will not break down the wood properly. After use, chemicals are recovered or treated rather than released, to stop harmful substances entering rivers and soil.\n\nGuiding questions\n- Why is sodium hydroxide used in breaking down wood to make paper pulp?\n- What does "concentration" mean when talking about a solution?\n- Why must the concentration be carefully controlled?\n- What chemicals or waste products need to be separated out?\n- How can chemical recovery reduce pollution?\n- Why is it important to stop harmful chemicals entering rivers and soil?\n\nHelpful idea\nScience links to sustainability: chemicals are often recovered, reused, or treated before disposal.',
5),

(@sci_id, 'Vocabulary Bank and Research Reminders',
'Useful Vocabulary Bank\n\nacid\nA substance that can react with metals, alkalis, or other chemicals.\n\nalkali\nA soluble base that can neutralise acids.\n\nsolution\nA mixture formed when a substance dissolves in a liquid.\n\nsaturated\nA solution that cannot dissolve any more solute at that temperature.\n\nfiltration\nA method used to separate an insoluble solid from a liquid.\n\ncrystallisation\nA method used to obtain a dissolved solid from a solution.\n\nsoluble\nA substance that can dissolve.\n\ninsoluble\nA substance that does not dissolve.\n\nStudent research reminders\n- Use your own words instead of copying whole sentences.\n- Write down at least one scientific process and one real-world impact for each topic.\n- Use diagrams when possible to help explain separation methods.\n- Check more than one website so your facts are reliable.',
6);


-- ------------------------------------------------------------
-- Material 2: Maths - Unit 6 - Measures of Central Tendency (Averages)
-- ------------------------------------------------------------
INSERT INTO materials (title, description, source_type, material_type, source_content, file_path, subject, year_group, difficulty, language, status, sort_order, created_by)
VALUES (
  'Unit 6 - Measures of Central Tendency (Averages)',
  'Year 7 Maths unit on averages: range, mode, median, mean, and reverse mean. Covers bimodal data, no-mode cases, and comparing averages (pros and cons of mean/median/mode/range).',
  'pdf',
  'lesson',
  '(curated from mock/material/Y7/Kami Export - Unit 6 - Measures of Central Tendency (5 & 6).pdf)',
  'mock/material/Y7/Kami Export - Unit 6 - Measures of Central Tendency (5 & 6).pdf',
  'Maths',
  7,
  'normal',
  'en',
  'published',
  999,
  2
);

SET @maths_id = LAST_INSERT_ID();

INSERT INTO material_chunks (material_id, title, content, sort_order) VALUES
(@maths_id, 'Introduction to Averages',
'Unit 6 - Measures of Central Tendency (Year 7 Maths)\n\nWhat is an average?\nAn average is a single value that represents a set of data. It gives us a quick way to describe what is "typical" in the data.\n\nIn this unit you will learn four different measures:\n- Range - how spread out the data is (the difference between the largest and smallest value)\n- Mode - the most common value\n- Median - the middle value when data is in order\n- Mean - the total of all values divided by the number of values\n\nKeywords\naverage, data, mode, range, median, mean, order, midpoint, reverse\n\nLearning Objectives\n- I can find the range of a given set of data.\n- I can work out the mode from a given set of data.\n- I can order data in size order and work out the median.\n- I can work out the mean and reverse mean questions from the list of data given.\n- I can decide which average is the best to describe a set of data.',
1),

(@maths_id, 'Range',
'The Range\nThe range is the difference between the highest and the lowest data item.\n\nFormula\nrange = highest value - lowest value\n\nExample 1\nFind the range of: 4, 8, 1, 2, 2, 4, 7, 5, 2, 7\nHighest = 8, Lowest = 1\nRange = 8 - 1 = 7\n\nMore examples\n- 9, 15, 27, 14  ->  range = 27 - 9 = 18\n- 6, 25, 23, 12  ->  range = 25 - 6 = 19\n- 80, 65, 70  ->  range = 80 - 65 = 15\n- -3, 8, 14, 1  ->  range = 14 - (-3) = 17\n- 4, 7, 5, 8  ->  range = 8 - 4 = 4\n\nWorking backwards\nIf you know the smallest value and the range, you can find the largest value:\nlargest value = smallest value + range\n\nIf you know the largest value and the range, you can find the smallest value:\nsmallest value = largest value - range\n\nExample 2\nSmallest value = 2, range = 11  ->  largest value = 2 + 11 = 13\nLargest value = 25, range = 13  ->  smallest value = 25 - 13 = 12',
2),

(@maths_id, 'Mode (including Bimodal and No Mode)',
'The Mode\nThe mode is the most common piece of data - the value (or values) that appears most often.\n\nExample 1\nFind the mode of: 4, 8, 1, 2, 2, 4, 7, 5, 2, 7\nThe number 2 appears three times - more than any other number.\nMode = 2\n\nMore examples\n- 18, 5, 6, 5, 10, 8  ->  mode = 5\n- 18, 6, 8, 2, 3, 5, 2, 3, 1, 3  ->  mode = 3\n- 8, -5, 1, 0, 0, -5, 1, 9, 9, 0  ->  mode = 0\n- 3, 6, 7, -3, 0, 4, 6  ->  mode = 6\n- -4, -3, -1, -7, -4, 3, 7, 0  ->  mode = -4\n\nSpecial cases\n1. No mode: If no value is repeated, there is no mode.\n   Example: 3, 7, 91, 2, 0, 5, 6  ->  No mode\n   Example: 56, 72, 83, 91, 108  ->  No mode\n\n2. Bimodal: If two different values are tied for most common, the data is bimodal (two modes).\n   Example: 3, 4, 7, 8, 3, 2, 7, 10  ->  modes = 3 and 7\n\n3. Multiple modes: Data can have more than two modes.\n   Example: 2.3, 7.1, 3.8, 1.3, 7.1, 2.3, 3.8  ->  modes = 2.3, 3.8, 7.1\n\nMode from a frequency table\nThe mode is the category with the highest frequency.\nExample: Green = 15, Blue = 12, Red = 12, Yellow = 8  ->  mode = Green (highest frequency).',
3),

(@maths_id, 'Median (Odd and Even Data Sets)',
'The Median\nThe median is the middle number when the data is arranged in order of size.\n\nSteps\n1. Put the numbers in order from smallest to largest.\n2. Cross off numbers from each end until you are left with the middle.\n3. If two numbers are left in the middle, the median is the value halfway between them (add them and divide by 2).\n\nExample 1 (odd number of values)\nFind the median of: 5, 7, 9, 4, 1, 3, 7, 4, 6\nIn order: 1, 3, 4, 4, 5, 6, 7, 7, 9\nCrossing off from each end leaves 5 in the middle.\nMedian = 5\n\nExample 2 (even number of values)\nFind the median of: 6, 8, 3, 7, 5, 3, 7, 2\nIn order: 2, 3, 3, 5, 6, 7, 7, 8\nCrossing off from each end leaves 5 and 6 in the middle.\nMedian = (5 + 6) / 2 = 5.5\n\nKey points\n- Always put the data in order first.\n- With an odd count, the median is one of the data values.\n- With an even count, the median is the midpoint of the two middle values and may not be a value from the data.',
4),

(@maths_id, 'Mean',
'The Mean\nThe mean is the most commonly used average. To calculate the mean:\n1. Add together all the values.\n2. Divide by the number of values.\n\nFormula\nmean = sum of values / number of values\n\nExample 1\nFind the mean of 1, 2, 2, 2, 3.\nSum = 1 + 2 + 2 + 2 + 3 = 10\nNumber of values = 5\nMean = 10 / 5 = 2\n\nExample 2 - with range\nMr Brook ate these numbers of chocolates each day: 2, 3, 3, 4, 5, 6, 7, 10\nRange = 10 - 2 = 8\nSum = 40, Number of values = 8\nMean = 40 / 8 = 5\n\nMore practice\n- 2, 3, 3, 4  ->  mean = 12 / 4 = 3\n- 3, 5, 7, 9, 11  ->  mean = 35 / 5 = 7\n- 10, 15, 20, 25, 30  ->  mean = 100 / 5 = 20\n- 1.7, 3.4, 2.3, 2.6  ->  mean = 10 / 4 = 2.5\n- 2.1, 6.2, 7.3, 9.9, 12  ->  mean = 37.5 / 5 = 7.5\n- 0.7, 0.4, 0.6, 0.7, 0.9, 1.1, 1.2, 1.4  ->  mean = 7 / 8 = 0.875',
5),

(@maths_id, 'Reverse Mean',
'Reverse Mean\nSometimes you are given the mean and asked to find a missing value or to work out a new mean when more data is added.\n\nKey idea\nTotal = mean x number of values\n\nExample 1 - Missing value\nResults for five students: 5, 8, 4, 3, ?\nThe mean is 6. Find the missing number.\nTotal = 6 x 5 = 30\nKnown sum = 5 + 8 + 4 + 3 = 20\nMissing number = 30 - 20 = 10 ...  (hint: set up equation total of all = mean x count, then solve)\n\nExample 2 - New person joins\n4 people took a test and had a mean score of 24. A fifth person then takes the test and the new mean becomes 25. What did the fifth person score?\nTotal for the 4 people = 4 x 24 = 96\nTotal for the 5 people = 5 x 25 = 125\nThe 5th person scored = 125 - 96 = 29\n\nExample 3 - Combining groups\n20 students in class A had a mean of 41.\nAll 35 students (A and B together) had a mean of 40.\nFind the mean of class B (15 students).\nTotal for all 35 = 35 x 40 = 1400\nTotal for class A = 20 x 41 = 820\nTotal for class B = 1400 - 820 = 580\nMean of class B = 580 / 15 = 38.67 (or 38 2/3)\n\nPractice answers\n- 9 people had a mean of 11, a 10th gave a mean of 15. The 10th score = 10 x 15 - 9 x 11 = 150 - 99 = 51.\n- 4 people had a mean of 21, a 5th gave a mean of 25. The 5th score = 5 x 25 - 4 x 21 = 125 - 84 = 41.\n- 5 people had a mean of 20, a 6th gave a mean of 24. The 6th score = 6 x 24 - 5 x 20 = 144 - 100 = 44.',
6),

(@maths_id, 'Best Average (Pros and Cons)',
'Which average is best?\nDifferent averages suit different types of data. You should choose the one that best describes the data.\n\nMean - pros and cons\nPros: Uses every value in the data set.\nCons: Can be pulled by very large or very small values (outliers).\n\nMedian - pros and cons\nPros: Not affected by extreme values (outliers).\nCons: Does not use all the data - only the middle value(s).\n\nMode - pros and cons\nPros: Works for non-numerical (categorical) data like colours or names. Easy to spot in a frequency table.\nCons: There may be no mode, or more than one.\n\nRange - pros and cons\n(Range is a measure of spread, not a measure of average.)\nPros: Shows how spread out the data is.\nCons: Only uses two values (highest and lowest) - outliers make it misleading.\n\nExample 1 - Salaries\n9 office workers and their manager earn:\n11,000, 11,000, 11,000, 11,000, 11,000, 14,000, 21,000, 21,000, 21,000, 57,000\nMode = 11,000   Median = 12,500   Mean = 18,900   Range = 46,000\nThe mean is pulled up by the manager''s 57,000 salary, so it does not describe a typical worker well. The median (12,500) is the best average here.\n\nExample 2 - Siblings\n2, 2, 2, 3, 3, 4, 6\nMode = 2   Median = 3   Mean = 3.1   Range = 4\nMode or median are both good choices - numbers of siblings are whole numbers, so mean = 3.1 is a bit awkward.\n\nExample 3 - Test marks\n1, 2, 3, 4, 5, 6, 7, 8, 9, 10\nNo mode. Median = 5.5, Mean = 5.5, Range = 9.\nMean or median both work well as there are no extreme values.\n\nExample 4 - Favourite colour\nRed, blue, red, blue, yellow, blue, blue, green, blue\nOnly the mode works for non-numerical data. Mode = blue.\n\nRule of thumb\n- Numerical data with no extreme values -> mean.\n- Numerical data with extreme values (outliers) -> median.\n- Categorical data or most common value needed -> mode.',
7);

-- ------------------------------------------------------------
-- Verify results
-- ------------------------------------------------------------
SELECT 'New materials created:' AS info;
SELECT material_id, title, subject, year_group, material_type FROM materials WHERE material_id IN (@sci_id, @maths_id);

SELECT 'Science chunks:' AS info;
SELECT chunk_id, sort_order, title FROM material_chunks WHERE material_id = @sci_id ORDER BY sort_order;

SELECT 'Maths chunks:' AS info;
SELECT chunk_id, sort_order, title FROM material_chunks WHERE material_id = @maths_id ORDER BY sort_order;
