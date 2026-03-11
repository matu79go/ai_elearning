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

## ER図（テーブル関係）

```
users (1)──(N) materials
users (1)──(N) learning_sessions
users (1)──(N) answer_history
users (1)──(N) point_history
users (1)──(N) user_badges
users (1)──(1) notification_settings
users (parent) (1)──(N) users (child)

materials (1)──(N) questions
materials (1)──(N) learning_sessions

questions (1)──(N) answer_history

learning_sessions (1)──(N) answer_history
learning_sessions (1)──(N) point_history

badges (1)──(N) user_badges
```

## テーブル一覧

| テーブル名 | 説明 |
|------------|------|
| users | ユーザー（親・子供共通） |
| materials | 学習素材 |
| questions | 問題 |
| learning_sessions | 学習セッション |
| answer_history | 回答履歴 |
| point_history | ポイント履歴 |
| badges | バッジ定義 |
| user_badges | ユーザーバッジ（取得済み） |
| notification_settings | 通知設定 |

## テーブル詳細

### users
| カラム | 型 | 説明 |
|--------|-----|------|
| user_id | INT PK | ユーザーID |
| username | VARCHAR(50) UNIQUE | ユーザー名 |
| email | VARCHAR(255) UNIQUE | メールアドレス |
| password_hash | VARCHAR(255) | パスワードハッシュ |
| display_name | VARCHAR(100) | 表示名 |
| role | ENUM('child','parent','admin') | 役割 |
| parent_id | INT FK | 親のuser_id |
| avatar_url | VARCHAR(500) | アバター画像URL |
| total_points | INT | 累計ポイント |

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
| created_by | INT FK | 作成者 |

### questions
| カラム | 型 | 説明 |
|--------|-----|------|
| question_id | INT PK | 問題ID |
| material_id | INT FK | マテリアルID |
| question_type | ENUM | 問題種別 |
| question_text | TEXT | 問題文 |
| options | JSON | 選択肢 |
| correct_answer | TEXT | 正答 |
| explanation | TEXT | 解説 |
| difficulty | ENUM | 難易度 |
| points_value | INT | 基本ポイント |

### point_history
| カラム | 型 | 説明 |
|--------|-----|------|
| point_id | INT PK | ポイントID |
| user_id | INT FK | ユーザーID |
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
