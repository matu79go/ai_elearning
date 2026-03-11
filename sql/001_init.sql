-- AI e-Learning システム 初期スキーマ
-- 文字コード: utf8mb4 (日本語対応)

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ユーザーテーブル（親・子供共通）
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    role ENUM('child', 'parent', 'admin') NOT NULL DEFAULT 'child',
    parent_id INT NULL COMMENT '子供アカウントの場合、親のuser_id',
    avatar_url VARCHAR(500) NULL,
    total_points INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- マテリアル（学習素材）テーブル
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
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 問題テーブル
CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'fill_blank', 'short_answer') NOT NULL,
    question_text TEXT NOT NULL,
    options JSON COMMENT '選択肢（multiple_choiceの場合）',
    correct_answer TEXT NOT NULL,
    explanation TEXT COMMENT '解説',
    difficulty ENUM('easy', 'normal', 'hard') NOT NULL DEFAULT 'normal',
    points_value INT NOT NULL DEFAULT 10 COMMENT '基本獲得ポイント',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 学習セッションテーブル
CREATE TABLE IF NOT EXISTS learning_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    material_id INT NOT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    total_questions INT NOT NULL DEFAULT 0,
    correct_answers INT NOT NULL DEFAULT 0,
    total_points_earned INT NOT NULL DEFAULT 0,
    time_spent_seconds INT NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 回答履歴テーブル
CREATE TABLE IF NOT EXISTS answer_history (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    question_id INT NOT NULL,
    user_id INT NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct TINYINT(1) NOT NULL DEFAULT 0,
    points_earned INT NOT NULL DEFAULT 0,
    time_spent_seconds INT NOT NULL DEFAULT 0,
    answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ポイント履歴テーブル
CREATE TABLE IF NOT EXISTS point_history (
    point_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    points INT NOT NULL,
    reason VARCHAR(255) NOT NULL COMMENT '付与理由',
    reason_type ENUM('correct_answer', 'speed_bonus', 'weakness_clear', 'streak_bonus', 'badge_bonus', 'manual_adjust') NOT NULL,
    session_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- バッジテーブル
CREATE TABLE IF NOT EXISTS badges (
    badge_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon_url VARCHAR(500),
    condition_type VARCHAR(50) NOT NULL COMMENT '達成条件の種類',
    condition_value INT NOT NULL COMMENT '達成条件の値',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ユーザーバッジ（取得済みバッジ）テーブル
CREATE TABLE IF NOT EXISTS user_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    earned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_badge (user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 通知設定テーブル
CREATE TABLE IF NOT EXISTS notification_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '親ユーザーのID',
    notify_on_complete TINYINT(1) NOT NULL DEFAULT 1 COMMENT '問題完了時にメール通知',
    notify_email VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 初期バッジデータ
INSERT INTO badges (name, description, icon_url, condition_type, condition_value) VALUES
('はじめの一歩', '初めて問題に正解した！', NULL, 'first_correct', 1),
('連続正解マスター', '5問連続で正解した！', NULL, 'streak', 5),
('がんばり屋さん', '合計50問に回答した！', NULL, 'total_answers', 50),
('ポイントハンター', '合計500ポイント獲得！', NULL, 'total_points', 500),
('スピードスター', '制限時間の半分以内で正解した！', NULL, 'speed_clear', 1),
('苦手克服', '苦手な分野で3問連続正解した！', NULL, 'weakness_clear', 3);
