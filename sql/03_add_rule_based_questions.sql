-- Migration: add rule-based question support to questions table.
-- 2026-04-17
--
-- - template_id: references YAML template (config/math_templates.yaml)
-- - generated_payload: variable values used to generate this instance (for audit/dedup)
-- - source enum extended with 'rule_based'
-- - idx_template for fast lookup when regenerating / filtering

ALTER TABLE questions
  ADD COLUMN template_id VARCHAR(100) NULL AFTER source,
  ADD COLUMN generated_payload JSON NULL AFTER template_id,
  ADD INDEX idx_template_id (template_id);

ALTER TABLE questions
  MODIFY COLUMN source ENUM('oak', 'llm_generated', 'manual', 'rule_based') NOT NULL DEFAULT 'manual';
