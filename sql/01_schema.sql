-- AI e-Learning スキーマ定義
-- 文字コード: utf8mb4 (日本語対応)

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- =============================================
-- 親アカウント
-- =============================================
CREATE TABLE IF NOT EXISTS parents (
    parent_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    family_code VARCHAR(10) NOT NULL UNIQUE COMMENT '家族コード（子供ログイン用）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 子供プロフィール
-- =============================================
CREATE TABLE IF NOT EXISTS children (
    child_id INT AUTO_INCREMENT PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    grade TINYINT UNSIGNED NULL COMMENT '学年 (1-6: 小学, 7-9: 中学)',
    avatar VARCHAR(50) NOT NULL DEFAULT 'default' COMMENT 'アバター識別子',
    pin_code VARCHAR(255) NOT NULL COMMENT 'ハッシュ化された4桁PIN',
    total_points INT NOT NULL DEFAULT 0,
    level INT NOT NULL DEFAULT 1,
    streak_count INT NOT NULL DEFAULT 0,
    last_study_date DATE NULL,
    created_by INT NOT NULL COMMENT '最初に作成した親',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES parents(parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 親子関係（多対多: 両親 ↔ 複数の子供）
-- =============================================
CREATE TABLE IF NOT EXISTS parent_children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    child_id INT NOT NULL,
    role ENUM('owner', 'caretaker') NOT NULL DEFAULT 'owner' COMMENT 'owner=作成者, caretaker=共同管理者',
    linked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_parent_child (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES parents(parent_id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES children(child_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- マテリアル（学習素材）
-- =============================================
CREATE TABLE IF NOT EXISTS materials (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_type ENUM('text', 'url') NOT NULL,
    source_content LONGTEXT NOT NULL COMMENT 'テキスト本文 or URL',
    subject VARCHAR(100) COMMENT '教科・カテゴリ',
    difficulty ENUM('easy', 'normal', 'hard') NOT NULL DEFAULT 'normal',
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES parents(parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 問題
-- =============================================
CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'fill_blank') NOT NULL,
    question_text TEXT NOT NULL,
    options JSON COMMENT '選択肢 [{"label":"A","text":"東京"},...]',
    correct_answer VARCHAR(10) NOT NULL COMMENT '正解ラベル (A/B/C/D or true/false)',
    explanation TEXT COMMENT '解説',
    difficulty ENUM('easy', 'normal', 'hard') NOT NULL DEFAULT 'normal',
    points_value INT NOT NULL DEFAULT 10 COMMENT '基本獲得ポイント',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 学習セッション
-- =============================================
CREATE TABLE IF NOT EXISTS learning_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    material_id INT NOT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    total_questions INT NOT NULL DEFAULT 0,
    correct_answers INT NOT NULL DEFAULT 0,
    total_points_earned INT NOT NULL DEFAULT 0,
    time_spent_seconds INT NOT NULL DEFAULT 0,
    FOREIGN KEY (child_id) REFERENCES children(child_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 回答履歴
-- =============================================
CREATE TABLE IF NOT EXISTS answer_history (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    question_id INT NOT NULL,
    child_id INT NOT NULL,
    user_answer VARCHAR(10) NOT NULL COMMENT '回答ラベル (A/B/C/D etc)',
    is_correct TINYINT(1) NOT NULL DEFAULT 0,
    points_earned INT NOT NULL DEFAULT 0,
    time_spent_seconds INT NOT NULL DEFAULT 0,
    answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id),
    FOREIGN KEY (child_id) REFERENCES children(child_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- ポイント履歴
-- =============================================
CREATE TABLE IF NOT EXISTS point_history (
    point_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    points INT NOT NULL,
    reason VARCHAR(255) NOT NULL COMMENT '付与理由',
    reason_type ENUM('correct_answer', 'speed_bonus', 'weakness_clear', 'streak_bonus', 'badge_bonus', 'manual_adjust') NOT NULL,
    session_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(child_id),
    FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- バッジ定義
-- =============================================
CREATE TABLE IF NOT EXISTS badges (
    badge_id INT AUTO_INCREMENT PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_ja VARCHAR(100) NOT NULL,
    description_en TEXT NOT NULL,
    description_ja TEXT NOT NULL,
    icon VARCHAR(50) NOT NULL DEFAULT 'fa-award' COMMENT 'Font Awesome アイコン名',
    color VARCHAR(20) NOT NULL DEFAULT '#6366f1' COMMENT 'バッジカラー',
    condition_type VARCHAR(50) NOT NULL COMMENT '達成条件の種類',
    condition_value INT NOT NULL COMMENT '達成条件の値',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 子供×バッジ（取得済み）
-- =============================================
CREATE TABLE IF NOT EXISTS child_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    badge_id INT NOT NULL,
    earned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_child_badge (child_id, badge_id),
    FOREIGN KEY (child_id) REFERENCES children(child_id),
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =============================================
-- 通知設定（親単位）
-- =============================================
CREATE TABLE IF NOT EXISTS notification_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    notify_on_complete TINYINT(1) NOT NULL DEFAULT 1 COMMENT '学習完了時にメール通知',
    notify_weekly_report TINYINT(1) NOT NULL DEFAULT 0 COMMENT '週次レポート',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
