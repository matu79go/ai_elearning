# Blog #004: マテリアル管理システム・LLM問題生成・子供用学習画面

**Date:** 2026-03-14

## Overview

教材データの取り込みからLLMによる問題自動生成、子供の学習画面まで一気通貫で構築した。データソースにはUK政府公認のOak National Academyを採用し、著作権をクリアした形で教材を確保した。

---

## 1. 設計フェーズ

### 要件整理

ユーザー（親）のお子さんはインターナショナルスクールのYear 7で、CGP KS3 Science Workbookを使用中。以下の要件が出た：

- マテリアルは日英で分けて登録
- 教科書データをDBに取り込み、LLMが動的に問題生成
- 問題形式は**4択 + 自由回答**のハイブリッド
- 自由回答はLLMが採点（部分点対応）
- 苦手分野を検知して追加問題を自動生成

### LLMモデル選定

採点・問題生成に使うLLMのコスト比較を実施：

| モデル | Input/1M | Output/1M | 1回答あたり |
|--------|----------|-----------|------------|
| Gemini 3.1 Flash Lite | $0.25 | $1.50 | ~0.05円 |
| GPT-5 nano | $0.05 | $0.40 | ~0.02円 |

→ **Gemini 3.1 Flash Lite** を採用（プレビュー中は無料枠あり）。`.env`で`LLM_PROVIDER`を切り替えればOpenAIにも対応可能な設計。

### 設計ドキュメント

`docs/material_design.md` に全体設計を記載：
- 全体フロー（データソース → マテリアル → チャンク → 問題生成 → 採点）
- 管理画面のUIフロー（ワイヤーフレーム付き）
- 子供用学習画面のフロー
- ポイントシステム（マスタリー制）
- ヒント機能（固定ヒント + AIチャット）
- DB設計変更

---

## 2. データソース: Oak National Academy

### 経緯

CGPの教科書は著作権があるため直接使えない。オープンソースの教材を探した結果、Oak National Academyが最適と判明：

- UK政府公認の教育プラットフォーム
- KS3（Year 7-9）の全21教科が無料
- **Open Government Licence v3.0**（非商業・教育目的OK）
- 各レッスンにスライド・ワークシート・クイズ・動画が付属

### データ連携

Oak National Academyの公式API（https://open-api.thenational.academy/）を利用してデータを取得する。OGLライセンスで公開されたコンテンツに、APIキーでアクセスする形。

APIで取得できるデータ：
- **Lesson Summary**: レッスンタイトル、Key Learning Points、Keywords、Misconceptions
- **Lesson Transcript**: 授業の書き起こし（約20,000-25,000文字/レッスン）
- **Quiz Questions**: Starter Quiz / Exit Quiz（問題・選択肢・正解）
- **Assets**: スライドデッキ、ワークシートPDF等

### インポート結果（Year 7）

| 教科 | 単元数 | セクション数 | 問題数 |
|------|--------|-------------|--------|
| Science | 7 | 60 | 144 |
| Maths | 12 | 173 | 680 |
| English | 8 | 78 | 63 |
| History | 8 | - | - |
| Geography | 進行中 | - | - |
| Computing | 進行中 | - | - |
| Spanish | 進行中 | - | - |

APIキー申請済み、取り込みバッチスクリプトも作成済み。詳細は `docs/oak_import.md` に記載。

---

## 3. DB設計変更

### 変更したテーブル

- **`parents`**: `role` カラム追加（`parent`/`admin`、デフォルト`parent`）
- **`materials`**: `language`, `year_group`, `status`, `file_path` 追加。`source_type` に `pdf` 追加
- **`questions`**: `free_response` タイプ追加、`reference_answer`, `max_score`, `scoring_rubric`, `hint`, `source`, `chunk_id` 追加。`correct_answer` を VARCHAR(255) に拡張
- **`material_chunks`**: `summary` カラム追加（LLM生成の要約キャッシュ）

### 新規テーブル

- **`material_chunks`**: マテリアルをセクション（レッスン）単位で分割管理
- **`question_mastery`**: 子供×問題ごとの習得状態（マスタリー制）

---

## 4. 管理画面（親/管理者用）

### マテリアル管理

`admin` ロールのみアクセス可能。階層ナビゲーション：

```
/admin/materials          → Year選択（Year 7, 8, 9）
/admin/materials/year/7   → 教科選択（Science, Maths, ...）
/admin/materials/year/7/Science → 単元一覧
/admin/materials/9        → 単元詳細（コンテンツタブ + 問題タブ）
```

### LLM問題生成

単元詳細画面の「問題を生成する」ボタンから：
1. 問題数（4択/自由回答それぞれ指定）
2. 難易度（easy/normal/hard）
3. 対象セクション（全選択 or 個別選択）

を設定してLLMに生成依頼。ローディング中はスピナー表示。

生成された問題は `source='llm_generated'`（紫バッジ）、Oakからの問題は `source='oak'`（緑バッジ）で区別。

### LLMラッパー（services/llm.py）

- `LLM_PROVIDER` 環境変数でGemini/OpenAIを切り替え
- `LLM_MODEL_GENERATE` / `LLM_MODEL_SCORING` で用途別にモデル指定可能
- JSONパース: コードブロック抽出 + 配列検出のフォールバック

---

## 5. 子供用学習画面

### 画面フロー

```
ダッシュボード → 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果
```

### セクション要約画面

チャンクデータを構造化して表示：
- **What you'll learn** — Key Learning Points
- **Key Words** — キーワード+定義（カード形式）
- **Watch out!** — よくある誤解
- **Summary** — Transcript のLLM要約（初回生成、DB キャッシュ）

### クイズ画面

- 4択問題: 選択肢をタップ → 即時フィードバック（正解/不正解 + 解説）
- 自由回答: テキスト入力 → 送信（現状は完全一致判定、将来LLM採点に置き換え）
- プログレスバーで進捗表示
- 全問解答後に結果画面へ遷移

### ヒント機能

2段階構成：
1. **固定ヒント**: `questions.hint` に保存されたテキストを即表示（API不要）
2. **AIチャット**: スティッキーパネルで自由質問。LLMは答えを絶対に言わず、ヒントだけ返す

### ポイントシステム（マスタリー制）

- 未習得の問題に正解 → **1pt**（習得済みに変更）
- 習得済みの問題を再回答 → **0pt**（練習は可能）
- ポイントは全問解答後にまとめて確定

---

## 6. 技術的な課題と対応

### Gemini モデル名

`gemini-3.1-flash-lite` ではなく `gemini-3.1-flash-lite-preview` が正しいモデルID。`-preview` サフィックスが必要。

### LLM JSON出力の不安定さ

長いプロンプト（transcript 25,000文字）を送るとJSONが壊れる問題。対策：
- プロンプトを簡潔化（例示を最小限に）
- Key Points等の構造化部分を優先し、transcriptは15,000文字に制限
- `_extract_json()` でJSON配列の開始`[`/終了`]`を検出するフォールバック

### Docker環境変数

LLM関連の環境変数（`GOOGLE_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`等）が`docker-compose.yml`に未登録だった。追加して`docker compose up -d`で反映。

### テンプレートのblock名

`base.html` は `{% block body %}` を使っているが、新テンプレートを `{% block content %}` で作ってしまい白画面になった。`{% block body %}` に統一して解決。

---

## 7. 次回TODO

- [ ] 子供用学習画面のUIリデザイン（study.htmlの2カラムレイアウト参考）
- [ ] 残りの教科インポート完了（Geography, Computing, Spanish）
- [ ] 自由回答のLLM採点実装
- [ ] 問題生成時にhintも同時生成
- [ ] セクション要約のLLM生成（初回アクセス時）
- [ ] 管理画面からのpublish/unpublish機能
- [ ] 作業ブログ（この記事）をdocs/blogs/に配置
