# システム設計書

## 1. アーキテクチャ

```
[ブラウザ] → [Flask (Python)] → [MySQL 8.0]
                   ↓
              [LLM API]
              (問題自動生成)
```

### コンテナ構成
- **elearn_app**: Flask アプリケーション (Python 3.11)
- **elearn_mysql**: MySQL 8.0 (utf8mb4)
- **elearn_phpmyadmin**: phpMyAdmin (ローカル開発のみ)

---

## 2. 技術スタック

| レイヤー | 技術 |
|----------|------|
| フロントエンド | Jinja2 + Tailwind CSS + 軽量JS |
| バックエンド | Flask 3.x + SQLAlchemy |
| DB | MySQL 8.0 (utf8mb4, InnoDB) |
| 認証 | Flask-Login + bcrypt |
| LLM | Anthropic Claude API / OpenAI API |
| コンテナ | Docker / Docker Compose |
| 本番 | さくらVPS (Ubuntu) |

---

## 3. ルーティング設計

### 共通
| パス | メソッド | 説明 |
|------|----------|------|
| `/` | GET | トップページ |
| `/login` | GET/POST | ログイン |
| `/logout` | GET | ログアウト |

### 子供用 (`/child/`)
| パス | メソッド | 説明 |
|------|----------|------|
| `/child/dashboard` | GET | ダッシュボード |
| `/child/subjects` | GET | 教科一覧 |
| `/child/study/<material_id>` | GET | 学習開始 |
| `/child/answer` | POST | 回答送信 |
| `/child/result/<session_id>` | GET | 結果表示 |
| `/child/badges` | GET | バッジ一覧 |
| `/child/history` | GET | 学習履歴 |

### 管理画面 (`/admin/`)
| パス | メソッド | 説明 |
|------|----------|------|
| `/admin/dashboard` | GET | ダッシュボード |
| `/admin/materials` | GET/POST | マテリアル管理 |
| `/admin/materials/<id>` | GET/PUT/DELETE | マテリアル詳細 |
| `/admin/questions` | GET | 問題一覧 |
| `/admin/questions/<id>` | GET/PUT/DELETE | 問題編集 |
| `/admin/generate` | POST | 問題生成（LLM） |
| `/admin/points` | GET/POST | ポイント管理 |
| `/admin/badges` | GET/POST | バッジ管理 |
| `/admin/settings` | GET/POST | 通知設定 |

### API (`/api/`)
| パス | メソッド | 説明 |
|------|----------|------|
| `/api/generate-questions` | POST | LLMで問題生成 |
| `/api/submit-answer` | POST | 回答送信(Ajax) |
| `/api/points/<user_id>` | GET | ポイント取得 |

---

## 4. フロントエンド設計方針

### 子供用画面
- **カラフル**で**親しみやすい**デザイン
- Tailwind CSSでレスポンシブ対応
- 正解/不正解時に軽量な効果音（HTML5 Audio API）
- CSSアニメーションで視覚的フィードバック
  - 正解: バウンスアニメーション + 星エフェクト
  - 不正解: シェイクアニメーション
  - バッジ獲得: スケールインアニメーション
- **重くならないように**簡潔な実装

### 管理画面
- シンプルで機能的なデザイン
- ダッシュボードでKPIを一目で確認
- テーブルベースのデータ管理

---

## 5. LLM問題生成フロー

```
1. 親がマテリアル登録（テキスト or URL）
2. URLの場合はスクレイピングでテキスト抽出
3. テキストをLLM APIに送信
4. プロンプトで問題形式・難易度・問題数を指定
5. LLMが問題・選択肢・正答・解説を生成
6. JSONで返却→DBに保存
7. 親が確認・編集後に公開
```

---

## 6. ポイント計算ロジック（案）

```python
base_points = question.points_value  # 基本ポイント（デフォルト10）

# スピードボーナス: 想定時間の半分以下なら+50%
if time_spent < expected_time / 2:
    bonus += base_points * 0.5

# 苦手克服ボーナス: 過去に不正解だった問題に正解
if was_previously_wrong:
    bonus += base_points * 1.0  # 2倍

# 連続正解ボーナス: 3問以上連続で+20%ずつ加算
if streak >= 3:
    bonus += base_points * 0.2 * (streak - 2)

total_points = base_points + bonus
```

※ 数値は後日調整
