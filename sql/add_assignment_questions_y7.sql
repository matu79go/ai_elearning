-- ============================================================
-- Y7 Assignment Questions (Week 2026-04-22)
--   Material 284: Averages (all 7 chunks)
--   Material 282: Graphs (selected numerical problems)
-- ============================================================
-- is_assignment=1 marks these as homework practice.
-- Questions mirror the PDF homework (numbers varied where appropriate).
-- ============================================================

SET @chunk_intro := 2105;
SET @chunk_range := 2106;
SET @chunk_mode := 2107;
SET @chunk_median := 2108;
SET @chunk_mean := 2109;
SET @chunk_reverse := 2110;
SET @chunk_best := 2111;
SET @mat_avg := 284;

-- ============================================================
-- Chunk 2106: Range
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_range, 'multiple_choice',
 'What is the range of: 4, 8, 1, 2, 2, 4, 7, 5, 2, 7?',
 '[{"label":"A","text":"5"},{"label":"B","text":"7"},{"label":"C","text":"8"},{"label":"D","text":"9"}]',
 'B', 'Range = highest − lowest = 8 − 1 = 7.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: 9, 15, 27, 14.',
 '[{"label":"A","text":"13"},{"label":"B","text":"15"},{"label":"C","text":"18"},{"label":"D","text":"27"}]',
 'C', 'Range = 27 − 9 = 18.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: 6, 25, 23, 12.',
 '[{"label":"A","text":"13"},{"label":"B","text":"19"},{"label":"C","text":"23"},{"label":"D","text":"25"}]',
 'B', 'Range = 25 − 6 = 19.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: 80, 65, 70.',
 '[{"label":"A","text":"5"},{"label":"B","text":"10"},{"label":"C","text":"15"},{"label":"D","text":"80"}]',
 'C', 'Range = 80 − 65 = 15.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: −3, 8, 14, 1.',
 '[{"label":"A","text":"11"},{"label":"B","text":"14"},{"label":"C","text":"17"},{"label":"D","text":"−17"}]',
 'C', 'Range = 14 − (−3) = 17.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: 4, 7, 5, 8.',
 '[{"label":"A","text":"3"},{"label":"B","text":"4"},{"label":"C","text":"5"},{"label":"D","text":"8"}]',
 'B', 'Range = 8 − 4 = 4.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'The smallest value in a data set is 2 and the range is 11. What is the largest value?',
 '[{"label":"A","text":"9"},{"label":"B","text":"11"},{"label":"C","text":"13"},{"label":"D","text":"22"}]',
 'C', 'Largest = smallest + range = 2 + 11 = 13.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'The largest value in a data set is 25 and the range is 13. What is the smallest value?',
 '[{"label":"A","text":"10"},{"label":"B","text":"12"},{"label":"C","text":"13"},{"label":"D","text":"38"}]',
 'B', 'Smallest = largest − range = 25 − 13 = 12.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'Calculate the range of: 11, 7, 19, 4, 22.',
 '[{"label":"A","text":"15"},{"label":"B","text":"18"},{"label":"C","text":"22"},{"label":"D","text":"26"}]',
 'B', 'Range = 22 − 4 = 18.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_range, 'multiple_choice',
 'The smallest value is −5 and the range is 14. What is the largest value?',
 '[{"label":"A","text":"9"},{"label":"B","text":"14"},{"label":"C","text":"19"},{"label":"D","text":"−19"}]',
 'A', 'Largest = −5 + 14 = 9.',
 'manual', 1, 'hard', 10, 10);

-- ============================================================
-- Chunk 2107: Mode
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_mode, 'multiple_choice',
 'What is the mode of: 4, 8, 1, 2, 2, 4, 7, 5, 2, 7?',
 '[{"label":"A","text":"2"},{"label":"B","text":"4"},{"label":"C","text":"7"},{"label":"D","text":"No mode"}]',
 'A', '2 appears three times — more than any other number.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 18, 5, 6, 5, 10, 8.',
 '[{"label":"A","text":"5"},{"label":"B","text":"6"},{"label":"C","text":"8"},{"label":"D","text":"10"}]',
 'A', '5 appears twice; others appear once.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 18, 6, 8, 2, 3, 5, 2, 3, 1, 3.',
 '[{"label":"A","text":"2"},{"label":"B","text":"3"},{"label":"C","text":"5"},{"label":"D","text":"18"}]',
 'B', '3 appears three times.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 8, −5, 1, 0, 0, −5, 1, 9, 9, 0.',
 '[{"label":"A","text":"0"},{"label":"B","text":"1"},{"label":"C","text":"9"},{"label":"D","text":"−5"}]',
 'A', '0 appears three times; 1, 9 and −5 each appear twice.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 3, 7, 91, 2, 0, 5, 6.',
 '[{"label":"A","text":"3"},{"label":"B","text":"6"},{"label":"C","text":"91"},{"label":"D","text":"No mode"}]',
 'D', 'Every number appears exactly once, so there is no mode.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 3, 6, 7, −3, 0, 4, 6.',
 '[{"label":"A","text":"−3"},{"label":"B","text":"6"},{"label":"C","text":"7"},{"label":"D","text":"No mode"}]',
 'B', '6 appears twice; others appear once.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: 56, 72, 83, 91, 108.',
 '[{"label":"A","text":"56"},{"label":"B","text":"83"},{"label":"C","text":"108"},{"label":"D","text":"No mode"}]',
 'D', 'All values appear once — no mode.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode(s) of: 3, 4, 7, 8, 3, 2, 7, 10.',
 '[{"label":"A","text":"3 only"},{"label":"B","text":"7 only"},{"label":"C","text":"3 and 7 (bimodal)"},{"label":"D","text":"No mode"}]',
 'C', 'Both 3 and 7 appear twice — the data is bimodal.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode(s) of: 2.3, 7.1, 3.8, 1.3, 7.1, 2.3, 3.8.',
 '[{"label":"A","text":"2.3, 3.8, 7.1"},{"label":"B","text":"1.3 only"},{"label":"C","text":"2.3 only"},{"label":"D","text":"No mode"}]',
 'A', 'Each of 2.3, 3.8 and 7.1 appears twice — three modes.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'Find the mode of: −4, −3, −1, −7, −4, 3, 7, 0.',
 '[{"label":"A","text":"−7"},{"label":"B","text":"−4"},{"label":"C","text":"0"},{"label":"D","text":"No mode"}]',
 'B', '−4 appears twice.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mode, 'multiple_choice',
 'From a frequency table: Green=15, Blue=12, Red=12, Yellow=8. What is the mode?',
 '[{"label":"A","text":"Green"},{"label":"B","text":"Blue"},{"label":"C","text":"Red"},{"label":"D","text":"Yellow"}]',
 'A', 'The mode is the category with the highest frequency — Green (15).',
 'manual', 1, 'easy', 10, 10);

-- ============================================================
-- Chunk 2108: Median (Odd and Even)
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 5, 7, 9, 4, 1, 3, 7, 4, 6.',
 '[{"label":"A","text":"4"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"7"}]',
 'B', 'In order: 1, 3, 4, 4, 5, 6, 7, 7, 9 — middle value is 5.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 6, 8, 3, 7, 5, 3, 7, 2.',
 '[{"label":"A","text":"5"},{"label":"B","text":"5.5"},{"label":"C","text":"6"},{"label":"D","text":"6.5"}]',
 'B', 'In order: 2, 3, 3, 5, 6, 7, 7, 8. Middle two are 5 and 6 → (5+6)/2 = 5.5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 5, 3, 8, 1, 8.',
 '[{"label":"A","text":"3"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"8"}]',
 'B', 'In order: 1, 3, 5, 8, 8 — middle value is 5.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 1, 8, 9, 3, 7.',
 '[{"label":"A","text":"3"},{"label":"B","text":"7"},{"label":"C","text":"8"},{"label":"D","text":"9"}]',
 'B', 'In order: 1, 3, 7, 8, 9 — middle value is 7.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 34, 2, 7, 8, 5.',
 '[{"label":"A","text":"5"},{"label":"B","text":"7"},{"label":"C","text":"8"},{"label":"D","text":"34"}]',
 'B', 'In order: 2, 5, 7, 8, 34 — middle value is 7.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 10, 12, 8, 6.',
 '[{"label":"A","text":"8"},{"label":"B","text":"9"},{"label":"C","text":"10"},{"label":"D","text":"11"}]',
 'B', 'In order: 6, 8, 10, 12. Middle two are 8 and 10 → (8+10)/2 = 9.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 6, 3, 9, 2.',
 '[{"label":"A","text":"3"},{"label":"B","text":"4"},{"label":"C","text":"4.5"},{"label":"D","text":"5"}]',
 'C', 'In order: 2, 3, 6, 9. Middle two are 3 and 6 → (3+6)/2 = 4.5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 34, 7, 4, 3.',
 '[{"label":"A","text":"4"},{"label":"B","text":"5.5"},{"label":"C","text":"7"},{"label":"D","text":"11"}]',
 'B', 'In order: 3, 4, 7, 34. Middle two are 4 and 7 → (4+7)/2 = 5.5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 6, 9, −3, 5, −7.',
 '[{"label":"A","text":"−3"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"9"}]',
 'B', 'In order: −7, −3, 5, 6, 9 — middle value is 5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_median, 'multiple_choice',
 'Find the median of: 0.82, 0.5, 0.9.',
 '[{"label":"A","text":"0.5"},{"label":"B","text":"0.82"},{"label":"C","text":"0.86"},{"label":"D","text":"0.9"}]',
 'B', 'In order: 0.5, 0.82, 0.9 — middle value is 0.82.',
 'manual', 1, 'hard', 10, 10);

-- ============================================================
-- Chunk 2109: Mean
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 1, 2, 2, 2, 3.',
 '[{"label":"A","text":"2"},{"label":"B","text":"2.5"},{"label":"C","text":"3"},{"label":"D","text":"10"}]',
 'A', '(1+2+2+2+3)/5 = 10/5 = 2.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 2, 3, 3, 4.',
 '[{"label":"A","text":"2"},{"label":"B","text":"3"},{"label":"C","text":"3.5"},{"label":"D","text":"4"}]',
 'B', '(2+3+3+4)/4 = 12/4 = 3.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 3, 5, 7, 9, 11.',
 '[{"label":"A","text":"5"},{"label":"B","text":"7"},{"label":"C","text":"9"},{"label":"D","text":"11"}]',
 'B', '(3+5+7+9+11)/5 = 35/5 = 7.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 3, 5, 6, 7, 7, 8.',
 '[{"label":"A","text":"5"},{"label":"B","text":"6"},{"label":"C","text":"7"},{"label":"D","text":"36"}]',
 'B', '(3+5+6+7+7+8)/6 = 36/6 = 6.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 10, 15, 20, 25, 30.',
 '[{"label":"A","text":"15"},{"label":"B","text":"20"},{"label":"C","text":"25"},{"label":"D","text":"100"}]',
 'B', '(10+15+20+25+30)/5 = 100/5 = 20.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 8, 12, 5, 5, 5.',
 '[{"label":"A","text":"5"},{"label":"B","text":"6"},{"label":"C","text":"7"},{"label":"D","text":"8"}]',
 'C', '(8+12+5+5+5)/5 = 35/5 = 7.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 100, 200, 400, 100.',
 '[{"label":"A","text":"100"},{"label":"B","text":"200"},{"label":"C","text":"250"},{"label":"D","text":"400"}]',
 'B', '(100+200+400+100)/4 = 800/4 = 200.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 4, 6, 7, 9, 11, 12, 14.',
 '[{"label":"A","text":"7"},{"label":"B","text":"8"},{"label":"C","text":"9"},{"label":"D","text":"10"}]',
 'C', '(4+6+7+9+11+12+14)/7 = 63/7 = 9.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 1.7, 3.4, 2.3, 2.6.',
 '[{"label":"A","text":"2.3"},{"label":"B","text":"2.5"},{"label":"C","text":"2.6"},{"label":"D","text":"10"}]',
 'B', '(1.7+3.4+2.3+2.6)/4 = 10/4 = 2.5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Find the mean of 2.1, 6.2, 7.3, 9.9, 12.',
 '[{"label":"A","text":"6.2"},{"label":"B","text":"7.3"},{"label":"C","text":"7.5"},{"label":"D","text":"12"}]',
 'C', '(2.1+6.2+7.3+9.9+12)/5 = 37.5/5 = 7.5.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_mean, 'multiple_choice',
 'Mr Brook ate these numbers of chocolates each day: 2, 3, 3, 4, 5, 6, 7, 10. What is the mean?',
 '[{"label":"A","text":"4"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"40"}]',
 'B', 'Sum = 40, count = 8. Mean = 40/8 = 5.',
 'manual', 1, 'normal', 10, 10);

-- ============================================================
-- Chunk 2110: Reverse Mean
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'The numbers 5, 8, 4, 3, ? have a mean of 6. What is the missing number?',
 '[{"label":"A","text":"8"},{"label":"B","text":"10"},{"label":"C","text":"12"},{"label":"D","text":"15"}]',
 'B', 'Total = 6 × 5 = 30. Known sum = 20. Missing = 30 − 20 = 10.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'The numbers 2, 7, 4, 2, ? have a mean of 4. What is the missing number?',
 '[{"label":"A","text":"4"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"7"}]',
 'B', 'Total = 4 × 5 = 20. Known sum = 15. Missing = 20 − 15 = 5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'The numbers 2, ?, 4, 3, 11, 5 have a mean of 6. What is the missing number?',
 '[{"label":"A","text":"9"},{"label":"B","text":"10"},{"label":"C","text":"11"},{"label":"D","text":"12"}]',
 'C', 'Total = 6 × 6 = 36. Known sum = 25. Missing = 36 − 25 = 11.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'The numbers 5, 7, 9, 2, ?, 8, 10 have a mean of 8. What is the missing number?',
 '[{"label":"A","text":"12"},{"label":"B","text":"13"},{"label":"C","text":"14"},{"label":"D","text":"15"}]',
 'D', 'Total = 8 × 7 = 56. Known sum = 41. Missing = 56 − 41 = 15.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'Four cards show 9, 1, 3, 5. A fifth card is added so the mean of all five cards is 5. What is the fifth card?',
 '[{"label":"A","text":"5"},{"label":"B","text":"6"},{"label":"C","text":"7"},{"label":"D","text":"8"}]',
 'C', 'Total = 5 × 5 = 25. Known = 18. Fifth = 25 − 18 = 7.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'Four cards show 3, 3, 5, 5. A fifth card is added so the mean of all five cards is 4.2. What is the fifth card?',
 '[{"label":"A","text":"4"},{"label":"B","text":"5"},{"label":"C","text":"6"},{"label":"D","text":"7"}]',
 'B', 'Total = 4.2 × 5 = 21. Known = 16. Fifth = 21 − 16 = 5.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 '9 people took a test with a mean of 11. A 10th person joins and the mean becomes 15. What did the 10th person score?',
 '[{"label":"A","text":"21"},{"label":"B","text":"41"},{"label":"C","text":"51"},{"label":"D","text":"61"}]',
 'C', 'Old total = 9 × 11 = 99. New total = 10 × 15 = 150. 10th = 150 − 99 = 51.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 '4 people had a mean score of 21. After a 5th person takes the test the mean is 25. What was the 5th person''s score?',
 '[{"label":"A","text":"21"},{"label":"B","text":"25"},{"label":"C","text":"41"},{"label":"D","text":"45"}]',
 'C', 'Old total = 84, new total = 125. 5th = 125 − 84 = 41.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 '5 people had a mean of 20. A 6th person joins and the mean becomes 24. What did the 6th person score?',
 '[{"label":"A","text":"24"},{"label":"B","text":"40"},{"label":"C","text":"44"},{"label":"D","text":"48"}]',
 'C', 'Old total = 100, new total = 144. 6th = 144 − 100 = 44.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 '20 Class A students had a mean of 41. All 35 students (A+B) had a mean of 40. What was Class B''s mean?',
 '[{"label":"A","text":"35"},{"label":"B","text":"38 2/3"},{"label":"C","text":"39"},{"label":"D","text":"40"}]',
 'B', 'Total all = 1400. A total = 820. B total = 580. B mean = 580/15 = 38 2/3.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_reverse, 'multiple_choice',
 'Set A (25 students) mean = 42. Sets A+B (50 students) mean = 37. Find Set B''s mean.',
 '[{"label":"A","text":"28"},{"label":"B","text":"30"},{"label":"C","text":"32"},{"label":"D","text":"37"}]',
 'C', 'Total all = 1850. A total = 1050. B total = 800. B mean = 800/25 = 32.',
 'manual', 1, 'hard', 10, 10);

-- ============================================================
-- Chunk 2111: Best Average (Pros and Cons)
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_best, 'multiple_choice',
 '9 office workers earn around £11,000–£21,000, but their manager earns £57,000. Which average best describes a typical worker''s salary?',
 '[{"label":"A","text":"Mean (£18,900)"},{"label":"B","text":"Median (£12,500)"},{"label":"C","text":"Mode (£11,000)"},{"label":"D","text":"Range (£46,000)"}]',
 'B', 'The manager''s salary is an outlier, pulling the mean up. The median is more representative of typical workers.',
 'manual', 1, 'hard', 10, 10),

(@mat_avg, @chunk_best, 'multiple_choice',
 'A survey of people''s favourite colour: Red, Blue, Red, Blue, Yellow, Blue, Blue, Green, Blue. Which average applies?',
 '[{"label":"A","text":"Mean"},{"label":"B","text":"Median"},{"label":"C","text":"Mode"},{"label":"D","text":"Range"}]',
 'C', 'Colours are categorical (non-numerical). Only the mode (Blue) can be calculated.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_best, 'multiple_choice',
 'Which average is most affected by an extreme outlier (a very high or very low value)?',
 '[{"label":"A","text":"Mean"},{"label":"B","text":"Median"},{"label":"C","text":"Mode"},{"label":"D","text":"All equally"}]',
 'A', 'The mean uses every value, so a single outlier pulls it up or down.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_best, 'multiple_choice',
 'For the test marks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 — which statement is TRUE?',
 '[{"label":"A","text":"The mode is 5"},{"label":"B","text":"There is no mode"},{"label":"C","text":"The median is 5"},{"label":"D","text":"The mean is 4"}]',
 'B', 'Every mark appears once, so there is no mode. The median and mean are both 5.5.',
 'manual', 1, 'normal', 10, 10),

(@mat_avg, @chunk_best, 'multiple_choice',
 'Siblings of 7 people: 2, 2, 2, 3, 3, 4, 6. Which average is least useful here?',
 '[{"label":"A","text":"Mean (3.1)"},{"label":"B","text":"Median (3)"},{"label":"C","text":"Mode (2)"},{"label":"D","text":"All are useful"}]',
 'A', 'Number of siblings is a whole number, so 3.1 feels awkward. Mode (2) or median (3) give a cleaner picture.',
 'manual', 1, 'hard', 10, 10);

-- ============================================================
-- Chunk 2105: Introduction to Averages (concept MCs)
-- ============================================================
INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

(@mat_avg, @chunk_intro, 'multiple_choice',
 'Which of these is NOT an average?',
 '[{"label":"A","text":"Mean"},{"label":"B","text":"Median"},{"label":"C","text":"Mode"},{"label":"D","text":"Range"}]',
 'D', 'The range is a measure of spread, not an average.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_intro, 'multiple_choice',
 'The "middle" value when the data is in order is called the:',
 '[{"label":"A","text":"Mean"},{"label":"B","text":"Median"},{"label":"C","text":"Mode"},{"label":"D","text":"Range"}]',
 'B', 'Median = middle value.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_intro, 'multiple_choice',
 'The value that appears most often in a set of data is called the:',
 '[{"label":"A","text":"Mean"},{"label":"B","text":"Median"},{"label":"C","text":"Mode"},{"label":"D","text":"Range"}]',
 'C', 'Mode = most common value.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_intro, 'multiple_choice',
 'To calculate the mean you should:',
 '[{"label":"A","text":"Find the middle value after ordering"},{"label":"B","text":"Pick the most common value"},{"label":"C","text":"Add all values and divide by the number of values"},{"label":"D","text":"Subtract the smallest from the largest"}]',
 'C', 'Mean = sum ÷ count.',
 'manual', 1, 'easy', 10, 10),

(@mat_avg, @chunk_intro, 'multiple_choice',
 'The range tells you:',
 '[{"label":"A","text":"The most common value"},{"label":"B","text":"How spread out the data is"},{"label":"C","text":"The middle value"},{"label":"D","text":"The average value"}]',
 'B', 'The range (largest − smallest) measures how spread out the data is.',
 'manual', 1, 'easy', 10, 10);


-- ============================================================
-- Material 282 (Graphs): selected numerical assignment questions
-- ============================================================
SET @chunk_pie_intro := 2095;
SET @chunk_pie_m1 := 2096;
SET @chunk_pie_m2 := 2097;
SET @chunk_pie_read := 2098;
SET @chunk_bar := 2092;
SET @mat_graph := 282;

INSERT INTO questions (material_id, chunk_id, question_type, question_text, options, correct_answer, explanation, source, is_assignment, difficulty, max_score, points_value) VALUES

-- Pie chart reading (PDF page 13: online habits pie chart; no image — described in text)
(@mat_graph, @chunk_pie_read, 'multiple_choice',
 'A pie chart shows online habits: 60% "Several times a day", 10% "Once a day", 25% "Almost constantly", 4% "Once a week", 1% "Less than once a week". What is the most common category?',
 '[{"label":"A","text":"Several times a day"},{"label":"B","text":"Once a day"},{"label":"C","text":"Almost constantly"},{"label":"D","text":"Once a week"}]',
 'A', 'Several times a day (60%) is the largest slice.',
 'manual', 1, 'easy', 10, 10),

-- Pie chart sector angles (PDF page 14 answers)
(@mat_graph, @chunk_pie_m1, 'multiple_choice',
 'In a pie chart, what sector angle represents a 60% category?',
 '[{"label":"A","text":"120°"},{"label":"B","text":"180°"},{"label":"C","text":"216°"},{"label":"D","text":"60°"}]',
 'C', '60% × 360° = 216°.',
 'manual', 1, 'normal', 10, 10),

(@mat_graph, @chunk_pie_m1, 'multiple_choice',
 'In a pie chart, what sector angle represents a 10% category?',
 '[{"label":"A","text":"10°"},{"label":"B","text":"36°"},{"label":"C","text":"45°"},{"label":"D","text":"90°"}]',
 'B', '10% × 360° = 36°.',
 'manual', 1, 'easy', 10, 10),

(@mat_graph, @chunk_pie_m1, 'multiple_choice',
 'In a pie chart, what sector angle represents a 25% category?',
 '[{"label":"A","text":"25°"},{"label":"B","text":"45°"},{"label":"C","text":"90°"},{"label":"D","text":"100°"}]',
 'C', '25% × 360° = 90°.',
 'manual', 1, 'easy', 10, 10),

(@mat_graph, @chunk_pie_m1, 'multiple_choice',
 'In a pie chart, what sector angle represents a 4% category?',
 '[{"label":"A","text":"4°"},{"label":"B","text":"14.4°"},{"label":"C","text":"24°"},{"label":"D","text":"40°"}]',
 'B', '4% × 360° = 14.4°.',
 'manual', 1, 'normal', 10, 10),

(@mat_graph, @chunk_pie_m1, 'multiple_choice',
 'In a pie chart, what sector angle represents a 1% category?',
 '[{"label":"A","text":"1°"},{"label":"B","text":"3.6°"},{"label":"C","text":"10°"},{"label":"D","text":"36°"}]',
 'B', '1% × 360° = 3.6°.',
 'manual', 1, 'normal', 10, 10),

-- Bar chart reading (PDF page 10-12: drink preferences)
(@mat_graph, @chunk_bar, 'multiple_choice',
 'A bar graph of drink preferences shows: tea 10, coffee 16, soft drink 5, water 23, juice 11, smoothie 15. What is the most popular drink?',
 '[{"label":"A","text":"Tea"},{"label":"B","text":"Coffee"},{"label":"C","text":"Water"},{"label":"D","text":"Smoothie"}]',
 'C', 'Water has the highest bar at 23.',
 'manual', 1, 'easy', 10, 10),

(@mat_graph, @chunk_bar, 'multiple_choice',
 'Using the drink preferences (tea 10, coffee 16, soft drink 5, water 23, juice 11, smoothie 15), how many students prefer juice?',
 '[{"label":"A","text":"10"},{"label":"B","text":"11"},{"label":"C","text":"15"},{"label":"D","text":"23"}]',
 'B', 'The juice bar is at 11.',
 'manual', 1, 'easy', 10, 10),

(@mat_graph, @chunk_bar, 'multiple_choice',
 'Using the drink preferences (tea 10, coffee 16, soft drink 5, water 23, juice 11, smoothie 15), how many students prefer tea or coffee?',
 '[{"label":"A","text":"16"},{"label":"B","text":"20"},{"label":"C","text":"26"},{"label":"D","text":"30"}]',
 'C', '10 (tea) + 16 (coffee) = 26.',
 'manual', 1, 'normal', 10, 10),

(@mat_graph, @chunk_bar, 'multiple_choice',
 'Using the drink preferences (tea 10, coffee 16, soft drink 5, water 23, juice 11, smoothie 15), how many students were surveyed in total?',
 '[{"label":"A","text":"60"},{"label":"B","text":"70"},{"label":"C","text":"80"},{"label":"D","text":"90"}]',
 'C', '10 + 16 + 5 + 23 + 11 + 15 = 80.',
 'manual', 1, 'normal', 10, 10);


-- ============================================================
-- Verification
-- ============================================================
SELECT '=== Assignment question counts per chunk ===' AS info;
SELECT q.chunk_id, c.title, COUNT(*) AS count
FROM questions q JOIN material_chunks c ON q.chunk_id = c.chunk_id
WHERE q.is_assignment = 1
GROUP BY q.chunk_id, c.title
ORDER BY q.chunk_id;
