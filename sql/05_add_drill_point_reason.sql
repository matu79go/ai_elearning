-- Migration: point_history.reason_type に 'drill_complete' を追加
-- 2026-04-17
-- Drill完了時のポイント付与用

ALTER TABLE point_history
  MODIFY COLUMN reason_type ENUM(
    'correct_answer','speed_bonus','weakness_clear','streak_bonus',
    'badge_bonus','manual_adjust','drill_complete'
  ) NOT NULL;
