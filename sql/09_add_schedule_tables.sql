-- Migration: study_plans / study_deadlines — 子供ごとの学習スケジュール
-- 2026-04-20
--
-- study_plans:     「この日に subject/material/chunk をやる」 割当
-- study_deadlines: テストや宿題の締切

CREATE TABLE study_plans (
  id INT PRIMARY KEY AUTO_INCREMENT,
  child_id INT NOT NULL,
  planned_date DATE NOT NULL,
  subject VARCHAR(50) NULL,
  material_id INT NULL,
  chunk_id INT NULL,
  title VARCHAR(255) NULL,
  note TEXT NULL,
  status ENUM('planned', 'done', 'skipped') NOT NULL DEFAULT 'planned',
  color VARCHAR(20) NULL,
  created_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_child_date (child_id, planned_date),
  FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
  FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE SET NULL,
  FOREIGN KEY (chunk_id) REFERENCES material_chunks(chunk_id) ON DELETE SET NULL,
  FOREIGN KEY (created_by) REFERENCES parents(parent_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE study_deadlines (
  id INT PRIMARY KEY AUTO_INCREMENT,
  child_id INT NOT NULL,
  due_date DATE NOT NULL,
  kind ENUM('test', 'homework', 'other') NOT NULL DEFAULT 'other',
  title VARCHAR(255) NOT NULL,
  subject VARCHAR(50) NULL,
  note TEXT NULL,
  done BOOLEAN NOT NULL DEFAULT FALSE,
  color VARCHAR(20) NULL,
  created_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_child_date (child_id, due_date),
  FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE,
  FOREIGN KEY (created_by) REFERENCES parents(parent_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
