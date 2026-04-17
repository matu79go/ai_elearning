-- Migration: drill (小テスト) 用テーブル3つ
-- 2026-04-17
--
-- ドリルは通常テスト(questions/answer_history)と完全分離:
-- - 問題プールは drill_questions (Oakは入らない。LLM生成 or ルールベースのみ)
-- - セッションは drill_sessions, 回答は drill_answer_history

CREATE TABLE drill_questions (
  drill_question_id INT PRIMARY KEY AUTO_INCREMENT,
  chunk_id INT NOT NULL,
  material_id INT NOT NULL,
  question_text TEXT NOT NULL,
  options JSON NOT NULL,
  correct_answer VARCHAR(10) NOT NULL,
  explanation TEXT,
  source ENUM('llm_generated', 'rule_based') NOT NULL,
  template_id VARCHAR(100) NULL,
  generated_payload JSON NULL,
  difficulty ENUM('easy', 'normal', 'hard') NOT NULL DEFAULT 'normal',
  status ENUM('draft', 'published') NOT NULL DEFAULT 'published',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_chunk (chunk_id),
  INDEX idx_material (material_id),
  INDEX idx_template (template_id),
  FOREIGN KEY (chunk_id) REFERENCES material_chunks(chunk_id) ON DELETE CASCADE,
  FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE drill_sessions (
  drill_session_id INT PRIMARY KEY AUTO_INCREMENT,
  child_id INT NOT NULL,
  chunk_id INT NOT NULL,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  mastered BOOLEAN NOT NULL DEFAULT FALSE,
  total_questions INT NOT NULL DEFAULT 0,
  correct_answers INT NOT NULL DEFAULT 0,
  max_streak INT NOT NULL DEFAULT 0,
  points_earned INT NOT NULL DEFAULT 0,
  INDEX idx_child (child_id),
  INDEX idx_chunk (chunk_id),
  INDEX idx_started (started_at),
  FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
  FOREIGN KEY (chunk_id) REFERENCES material_chunks(chunk_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE drill_answer_history (
  drill_answer_id INT PRIMARY KEY AUTO_INCREMENT,
  drill_session_id INT NOT NULL,
  drill_question_id INT NOT NULL,
  child_id INT NOT NULL,
  user_answer VARCHAR(10) NOT NULL,
  is_correct BOOLEAN NOT NULL DEFAULT FALSE,
  time_spent_seconds INT NOT NULL DEFAULT 0,
  answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_session (drill_session_id),
  INDEX idx_question (drill_question_id),
  INDEX idx_child (child_id),
  FOREIGN KEY (drill_session_id) REFERENCES drill_sessions(drill_session_id) ON DELETE CASCADE,
  FOREIGN KEY (drill_question_id) REFERENCES drill_questions(drill_question_id) ON DELETE CASCADE,
  FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
