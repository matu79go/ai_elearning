-- Migration: chunk_youtube_videos — 上位5本のYouTube動画を保存するテーブル
-- 2026-04-17
--
-- 従来: material_chunks.video_youtube_id が1本だけ
-- 新規: 1 chunk あたり複数のYouTube動画候補を保持、1本を primary として選定
--       child UI: メイン動画 + 切替サムネ、admin UI: 並び替え/削除/手動追加

CREATE TABLE chunk_youtube_videos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  chunk_id INT NOT NULL,
  video_id VARCHAR(20) NOT NULL,
  title VARCHAR(255),
  channel VARCHAR(100),
  duration_seconds INT NULL,
  thumbnail_url VARCHAR(500),
  description TEXT,
  rank_position INT NOT NULL DEFAULT 99,   -- 1=最上位(primary候補)、小さいほど優先 (rankは予約語のため_position付き)
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  source ENUM('api_search', 'llm_pick', 'manual') NOT NULL DEFAULT 'api_search',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_chunk_video (chunk_id, video_id),
  INDEX idx_chunk (chunk_id, rank_position),
  INDEX idx_primary (chunk_id, is_primary),
  FOREIGN KEY (chunk_id) REFERENCES material_chunks(chunk_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
