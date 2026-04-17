-- Migration: 問題に図 (SVG) を埋め込めるように
-- 2026-04-17
-- drill_questions と questions 両方に chart_svg カラム追加
-- MEDIUMTEXT: 最大 16MB まで格納可能 (1問=数KBなので十分)

ALTER TABLE questions
  ADD COLUMN chart_svg MEDIUMTEXT NULL AFTER explanation;

ALTER TABLE drill_questions
  ADD COLUMN chart_svg MEDIUMTEXT NULL AFTER explanation;
