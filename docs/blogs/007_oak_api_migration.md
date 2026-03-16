# Blog #007: Oak National Academy 公式API移行

**Date:** 2026-03-16

## Overview

Oak National Academy のデータ取得方式を、HTMLスクレイピングから公式Open APIに移行した。APIキー取得、エンドポイント調査、インポートスクリプト刷新、動画埋め込み・読み上げ機能のプロトタイプまでを1日で実施。

---

## 1. 背景

これまでOakのデータは `__NEXT_DATA__` タグからのHTMLスクレイピングで取得していた。

- サイト構造変更で壊れるリスク
- 問題データの取りこぼし（multiple-choiceが取得できていなかった）
- レート制限を自主的に2〜5秒/リクエストに設定

Oak が公式API (https://open-api.thenational.academy/api/v0) を公開しており、APIキーを申請・取得済みだったので移行を実施。

---

## 2. API調査

### 認証

```
Authorization: Bearer {OAK_API_KEY}
```

### 主要エンドポイント

| 用途 | エンドポイント |
|------|-------------|
| 単元一覧 | `GET /key-stages/{ks}/subject/{subject}/units` |
| レッスン一覧 | `GET /key-stages/{ks}/subject/{subject}/lessons?unit=xxx` |
| レッスン要約 | `GET /lessons/{lesson}/summary` |
| トランスクリプト | `GET /lessons/{lesson}/transcript` |
| クイズ | `GET /lessons/{lesson}/quiz` |
| アセット（動画等） | `GET /lessons/{lesson}/assets` |

### レート制限

- 1,000 req/hour
- Cloudflare経由のため、連続リクエストで間欠的に401が返ることがある（キーは有効でも）
- リトライ機能（3回、5秒間隔）で対処

### レスポンス構造の違い（スクレイピング版 vs API版）

クイズの正解判定ロジックが異なる：

```
スクレイピング版: answer_is_default=false → 正解
API版:           distractor=false → 正解
```

---

## 3. データ品質の比較

同じレッスン（Animal cell structures and their functions）で比較：

| 項目 | スクレイピング版 | API版 |
|------|---------------|-------|
| 取得できた問題数 | 4問 | **12問** |
| 問題タイプ | free_response のみ | **multiple-choice, short-answer, match, ordering** |
| 正解バリエーション | 1〜2個 | **4〜5個**（大文字/小文字/省略形/同義語） |
| ユニット数（Science Y7） | 7 | **13**（Oak側でコンテンツ追加） |

**結論: API版の方がデータ品質が大幅に高い。**

---

## 4. インポートスクリプト刷新

### 旧: `import_oak.py` / `import_oak_all.py`

- KS3固定、Year 7固定
- Science用と他教科用で2ファイルに分離
- HTMLスクレイピング + `__NEXT_DATA__` パース

### 新: `import_oak_api.py`

- 全Key Stage (KS1-KS4)、全学年 (Year 1-11) 対応
- CLIオプション: `--key-stages`, `--years`, `--subjects`, `--all-subjects`, `--dry-run`
- 問題タイプ変換:

| Oak API questionType | DB question_type | 変換方法 |
|---------------------|------------------|---------|
| multiple-choice | multiple_choice | distractor=false が正解 |
| short-answer | free_response | 全answersが許容バリエーション |
| match | **multiple_choice** | 全correctChoiceを選択肢にした4択 |
| ordering | free_response | orderフィールドで正順を組み立て |

match問題の変換は当初free_responseにしていたが、「Match: climate → average weather conditions...」では意味が分かりにくいため、multiple_choiceに変更。全定義を選択肢にして「climate is...」→ 正しい定義を選ぶ形式に。

### 実行結果（Science Year 7）

```
13 units, 96 lessons, 1,345 questions
```

旧版（7 units, 60 lessons, 144 questions）と比較して問題数が約9倍に。

---

## 5. 動画・読み上げ機能（プロトタイプ）

### Oak動画の埋め込み

APIの `/lessons/{lesson}/assets` エンドポイントで動画URLが取得可能。ただしBearer認証が必要なため、サーバー側でプロキシルートを実装。

```python
# routes/child_learn.py
@dual_route(child_learn_bp, '/child/oak-video/<int:chunk_id>')
def child_oak_video(chunk_id):
    # chunk.title → lesson slug を推定
    # Oak APIから動画をストリーミングプロキシ
```

- 動画は MP4、1レッスンあたり約77MB
- `x-frame-options: DENY` のため iframe 不可 → プロキシ方式が必須

### Web Speech API 読み上げ

セクション画面にSummaryテキストの読み上げボタンを追加。

```javascript
const utterance = new SpeechSynthesisUtterance(summaryText);
utterance.lang = 'en-GB';
utterance.rate = 0.9;  // やや遅め（子供向け）
speechSynthesis.speak(utterance);
```

- 無料、APIキー不要
- Chrome/Safari/Edge対応
- 英語の発音品質は子供向けとして十分

---

## 6. ドキュメント整理

API関連ドキュメントが3ファイルに重複していたのを整理：

| ファイル | 役割 |
|---------|------|
| `docs/oak_api_reference.md` | API仕様の本体（エンドポイント、レスポンス例） |
| `docs/oak_import.md` | インポート手順（スクリプトの使い方） |
| `docs/oak_import_progress.md` | 全KS×教科×学年の進捗管理テーブル |
| `.claude/skills/oak-api/SKILL.md` | Claude Codeスキル（ドキュメント参照用） |

---

## 7. 残タスク

1. 動画・読み上げの動作確認（コンテナ再起動が必要）
2. match問題の再インポート（Science Year 7）
3. 全学年・全教科の段階的インポート（推定24時間、分割実行）
4. セクション画面のハードコード文言を翻訳辞書に移行

---

## 技術メモ

- Cloudflare 401: 連続リクエストで出る一時エラー。リトライで対処。パニック不要
- `.claude/skills/` のスキルファイルは `{name}/SKILL.md` のディレクトリ構造が必要（フラットな `.md` では認識されない）
- 全学年インポートの見積もり: KS1(144u) + KS2(370u) + KS3(221u) + KS4(220u) = 955ユニット
