-- AI e-Learning マスターデータ
-- ルール: マスターテーブルはすべて _en / _ja のバイリンガルカラムを持つ
SET NAMES utf8mb4;

-- =============================================
-- バッジ初期データ
-- =============================================
INSERT INTO badges (name_en, name_ja, description_en, description_ja, icon, color, condition_type, condition_value) VALUES
('First Step',      'はじめの一歩',       'Got your first correct answer!',              '初めて問題に正解した！',                 'fa-shoe-prints', '#10b981', 'first_correct',  1),
('Streak Master',   'れんぞくマスター',   'Got 5 correct answers in a row!',             '5問連続で正解した！',                   'fa-fire',        '#ef4444', 'streak',         5),
('Hard Worker',     'がんばり屋さん',     'Answered 50 questions in total!',              '合計50問に回答した！',                   'fa-dumbbell',    '#f59e0b', 'total_answers',  50),
('Point Hunter',    'ポイントハンター',   'Earned 500 points in total!',                 '合計500ポイント獲得！',                  'fa-coins',       '#6366f1', 'total_points',   500),
('Speed Star',      'スピードスター',     'Answered correctly in half the time limit!',   '制限時間の半分以内で正解した！',          'fa-bolt',        '#3b82f6', 'speed_clear',    1),
('Overcomer',       'にがて克服',         'Got 3 correct answers in a weak subject!',     '苦手な分野で3問連続正解した！',           'fa-mountain',    '#8b5cf6', 'weakness_clear', 3);
