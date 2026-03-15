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
| `/child/subjects/<subject>` | GET | 単元一覧 |
| `/child/section/<chunk_id>` | GET | セクション要約（学習コンテンツ） |
| `/child/quiz/<chunk_id>` | GET | クイズ画面 |
| `/child/quiz/<chunk_id>/check` | POST | 一括採点API（答え合わせ） |
| `/child/quiz/<chunk_id>/result` | GET | 結果表示 |
| `/child/hint/<question_id>` | POST | ヒント取得（固定 or AIチャット） |
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
| `/api/points/<user_id>` | GET | ポイント取得 |

---

## 4. フロントエンド設計方針

### 子供用画面

**レイアウト**: 全画面で統一2カラムレイアウト（`child_base.html`）
- 背景: 紫グラデーション (`#667eea → #764ba2`)
- PC/タブレット (768px+): glassmorphicサイドバー + 白コンテンツカード
- スマホ: 1カラム + アコーディオンパネル

**デザイン**: カラフルで親しみやすい
- Tailwind CSSでレスポンシブ対応
- CSSアニメーション（pop, shake, slideUp, sparkle, pointFly）
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

## 6. クイズフロー

### 回答フェーズ（JSのみ、サーバー通信なし）
1. 問題表示 → 回答選択 → [Confirm] で確定 → 次の未回答問題へ自動遷移
2. サイドバーで任意の問題にジャンプ可能
3. 確定済み問題 → [Change] でロック解除 → 再回答可能
4. 全問確定 → [Check Answers!] ボタン出現

### 答え合わせフェーズ（一括サーバー送信）
1. `POST /child/quiz/<chunk_id>/check` に全回答を送信
2. サーバーで一括採点 → 各問題の正誤・解説・ポイントを返却
3. DB更新（question_mastery, children.total_points）
4. 結果画面へ遷移

### 自由回答の採点（3段階フォールバック）

```
1) correct_answer と完全一致 → 正解
2) reference_answer のカンマ区切り候補と一致 → 正解
3) GPT-5 Nano で模範解答との一致率判定 → 30%以上で正解
   API障害時 → spaCy NLPキーワードマッチにフォールバック
```

---

## 7. ポイント計算ロジック（マスタリー制）

### 現行ルール（シンプル）
- 未習得の問題に正解 → **1pt**（mastered = True に変更）
- 習得済みの問題に再回答 → **0pt**（練習は可能）
- ポイントは答え合わせ時にまとめて確定

### 将来拡張（案）
```python
# スピードボーナス: 想定時間の半分以下なら+50%
# 苦手克服ボーナス: 過去に不正解だった問題に正解で2倍
# 連続正解ボーナス: 3問以上連続で+20%ずつ加算
```

※ 数値は後日調整
