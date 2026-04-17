-- Migration: materials.material_type — 資料種別 (講義/用語集/課題シート/評価)
-- 2026-04-17
-- 種別によって:
--   - LLM chunking 戦略を変える
--   - child 画面の表示を分岐 (lesson=動画+章立て, glossary=用語リスト, worksheet=問題/目標, assessment=評価)

ALTER TABLE materials
  ADD COLUMN material_type ENUM('lesson', 'glossary', 'worksheet', 'assessment', 'other')
    NOT NULL DEFAULT 'lesson'
    AFTER source_type,
  ADD INDEX idx_material_type (material_type);
