# データベース設計

## 接続情報

| 項目 | 値 |
|------|------|
| ホスト | db (Docker内) / localhost (外部) |
| ポート | 3306 |
| DB名 | elearning |
| ユーザー | root |
| パスワード | .envファイル参照 |
| 文字コード | utf8mb4 |

## アカウント構造

```
parents (親)  ──M:N──  children (子供)
              via parent_children

- 親はメールアドレス+パスワードで登録
- 親が子供プロフィールを作成（名前・学年・PIN）
- 子供は「名前選択 → 4桁PIN入力」でログイン
- 1人の子供を複数の親が管理可能（両親対応）
- 1人の親が複数の子供を管理可能（兄弟対応）
```

## ER図（テーブル関係）

```
parents (M)──(N) children       ... via parent_children
parents (1)──(N) materials
parents (1)──(N) notification_settings

children (1)──(N) learning_sessions
children (1)──(N) answer_history
children (1)──(N) point_history
children (1)──(N) child_badges

materials (1)──(N) questions
materials (1)──(N) learning_sessions

questions (1)──(N) answer_history

learning_sessions (1)──(N) answer_history
learning_sessions (1)──(N) point_history

badges (1)──(N) child_badges
```

## DB設計ルール

### バイリンガルマスターデータ規約

マスターテーブル（badges 等、システム定義のマスターデータを持つテーブル）のテキストカラムは、必ず `_en` / `_ja` のサフィックス付きで英語・日本語の両方を持つこと。

```
-- 例: badges テーブル
name_en  VARCHAR(100)  -- 英語名
name_ja  VARCHAR(100)  -- 日本語名
description_en TEXT    -- 英語説明
description_ja TEXT    -- 日本語説明
```

**アプリ側での参照方法:**
```python
# lang = 'en' or 'ja'
badge_name = badge[f'name_{lang}']
badge_desc = badge[f'description_{lang}']
```

**対象テーブル:** badges（今後マスターテーブルが増えた場合も同様に適用）

## テーブル一覧

| テーブル名 | 説明 |
|------------|------|
| parents | 親アカウント |
| children | 子供プロフィール |
| parent_children | 親子関係（多対多） |
| materials | 学習素材 |
| questions | 問題 |
| learning_sessions | 学習セッション |
| answer_history | 回答履歴 |
| point_history | ポイント履歴 |
| badges | バッジ定義 |
| child_badges | 子供×バッジ（取得済み） |
| notification_settings | 通知設定 |

## テーブル詳細

### parents
| カラム | 型 | 説明 |
|--------|-----|------|
| parent_id | INT PK | 親ID |
| email | VARCHAR(255) UNIQUE | メールアドレス |
| password_hash | VARCHAR(255) | パスワードハッシュ |
| display_name | VARCHAR(100) | 表示名 |

### children
| カラム | 型 | 説明 |
|--------|-----|------|
| child_id | INT PK | 子供ID |
| display_name | VARCHAR(100) | 表示名（ニックネーム） |
| grade | TINYINT | 学年 (1-6:小学, 7-9:中学) |
| avatar | VARCHAR(50) | アバター識別子 |
| pin_code | VARCHAR(255) | ハッシュ化された4桁PIN |
| total_points | INT | 累計ポイント |
| level | INT | レベル |
| streak_count | INT | 連続学習日数 |
| last_study_date | DATE | 最終学習日 |
| created_by | INT FK | 最初に作成した親 |

### parent_children
| カラム | 型 | 説明 |
|--------|-----|------|
| id | INT PK | ID |
| parent_id | INT FK | 親ID |
| child_id | INT FK | 子供ID |
| role | ENUM('owner','caretaker') | owner=作成者, caretaker=共同管理者 |

### materials
| カラム | 型 | 説明 |
|--------|-----|------|
| material_id | INT PK | マテリアルID |
| title | VARCHAR(255) | タイトル |
| description | TEXT | 説明 |
| source_type | ENUM('text','url') | ソース種別 |
| source_content | LONGTEXT | テキスト本文 or URL |
| subject | VARCHAR(100) | 教科 |
| difficulty | ENUM('easy','normal','hard') | 難易度 |
| created_by | INT FK | 作成した親 |

### questions
| カラム | 型 | 説明 |
|--------|-----|------|
| question_id | INT PK | 問題ID |
| material_id | INT FK | マテリアルID |
| question_type | ENUM('multiple_choice','true_false','fill_blank') | 問題種別 |
| question_text | TEXT | 問題文 |
| options | JSON | 選択肢 [{"label":"A","text":"..."},...] |
| correct_answer | VARCHAR(10) | 正解ラベル (A/B/C/D) |
| explanation | TEXT | 解説 |
| difficulty | ENUM('easy','normal','hard') | 難易度 |
| points_value | INT | 基本ポイント (default: 10) |

### learning_sessions
| カラム | 型 | 説明 |
|--------|-----|------|
| session_id | INT PK | セッションID |
| child_id | INT FK | 子供ID |
| material_id | INT FK | マテリアルID |
| started_at | DATETIME | 開始日時 |
| completed_at | DATETIME | 完了日時 |
| total_questions | INT | 総問題数 |
| correct_answers | INT | 正解数 |
| total_points_earned | INT | 獲得ポイント合計 |
| time_spent_seconds | INT | 所要時間（秒） |

### answer_history
| カラム | 型 | 説明 |
|--------|-----|------|
| answer_id | INT PK | 回答ID |
| session_id | INT FK | セッションID |
| question_id | INT FK | 問題ID |
| child_id | INT FK | 子供ID |
| user_answer | VARCHAR(10) | 回答ラベル |
| is_correct | TINYINT(1) | 正解フラグ |
| points_earned | INT | 獲得ポイント |
| time_spent_seconds | INT | 回答時間（秒） |

### point_history
| カラム | 型 | 説明 |
|--------|-----|------|
| point_id | INT PK | ポイントID |
| child_id | INT FK | 子供ID |
| points | INT | ポイント数 |
| reason | VARCHAR(255) | 付与理由 |
| reason_type | ENUM | 理由種別 |
| session_id | INT FK | セッションID |

### reason_type一覧
| 値 | 説明 |
|----|------|
| correct_answer | 正解ポイント |
| speed_bonus | スピードボーナス |
| weakness_clear | 苦手克服ボーナス |
| streak_bonus | 連続正解ボーナス |
| badge_bonus | バッジ獲得ボーナス |
| manual_adjust | 手動調整 |

### badges (マスターテーブル)
| カラム | 型 | 説明 |
|--------|-----|------|
| badge_id | INT PK | バッジID |
| name_en | VARCHAR(100) | バッジ名（英語） |
| name_ja | VARCHAR(100) | バッジ名（日本語） |
| description_en | TEXT | 説明（英語） |
| description_ja | TEXT | 説明（日本語） |
| icon | VARCHAR(50) | Font Awesomeアイコン名 |
| color | VARCHAR(20) | バッジカラー |
| condition_type | VARCHAR(50) | 達成条件の種類 |
| condition_value | INT | 達成条件の値 |

### child_badges
| カラム | 型 | 説明 |
|--------|-----|------|
| id | INT PK | ID |
| child_id | INT FK | 子供ID |
| badge_id | INT FK | バッジID |
| earned_at | DATETIME | 獲得日時 |

### notification_settings
| カラム | 型 | 説明 |
|--------|-----|------|
| setting_id | INT PK | 設定ID |
| parent_id | INT FK | 親ID |
| notify_on_complete | TINYINT(1) | 学習完了時に通知 |
| notify_weekly_report | TINYINT(1) | 週次レポート |

## SQLファイル

| ファイル | 説明 |
|----------|------|
| sql/01_schema.sql | テーブル定義 |
| sql/02_master_data.sql | 初期マスターデータ（バッジ等） |
