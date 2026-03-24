---
name: oak-api
description: Check Oak National Academy API documentation, playground, and endpoints
user_invocable: true
---

Oak National Academy Open API の仕様確認・テストを行います。

## ローカルドキュメント

- API仕様リファレンス: `docs/oak_api_reference.md`
- インポート手順: `docs/oak_import.md`
- インポート進捗: `docs/oak_import_progress.md`

まずローカルドキュメントを確認し、最新情報が必要な場合は以下の公式URLから WebFetch で取得してください。

## 公式ドキュメントURL

1. API Overview: https://open-api.thenational.academy/docs/about-oaks-api/api-overview
2. API Limits: https://open-api.thenational.academy/docs/about-oaks-api/api-limits
3. Versioning: https://open-api.thenational.academy/docs/about-oaks-api/versioning
4. Playground: https://open-api.thenational.academy/playground
5. Lists: https://open-api.thenational.academy/docs/api-endpoints/lists
6. Lesson Data: https://open-api.thenational.academy/docs/api-endpoints/lesson-data
7. Unit/Curriculum: https://open-api.thenational.academy/docs/api-endpoints/unit-and-curriculum-data
8. Quiz Questions: https://open-api.thenational.academy/docs/api-endpoints/quiz-questions
9. Search: https://open-api.thenational.academy/docs/api-endpoints/search

## ⚠️ 複数正解（multi-answer）ルール【重要】

Oak API の multiple-choice 問題には **複数の正解がある場合がある**。`answers` 配列で `distractor: false` の選択肢が2つ以上存在するケース。

- **correct_answer はカンマ区切り**で保存する（例: `"A,C,D"`）
- インポート時: `correct_labels` リストに全正解を集め、`','.join(correct_labels)` で保存
- クイズUI: correct_answer に `,` が含まれる場合はチェックボックス式（複数選択）にする
- 採点: ユーザーの回答（カンマ区切り）をソートして比較
- 既存データの修正: `python batch/import_oak_api.py --fix-multi-answer --key-stages ks3 --years 7 --all-subjects`

## インポート時の sort_order ルール

- **Material の sort_order**: `/key-stages/{ks}/subject/{subject}/units` の返却順（カリキュラム順）でセットする。`import_unit()` の `sort_order` パラメータを使用
- **MaterialChunk の sort_order**: `/key-stages/{ks}/subject/{subject}/lessons?unit={unit}` の返却順でセットする（`enumerate(lessons)` の `i + 1`）
- 既存データの修正: `python batch/import_oak_api.py --fix-sort-order --key-stages ks2 --years 4 --all-subjects`
- **注意**: KS2 の units API はアルファベット順で返す場合がある（KS3 はカリキュラム順）。Oak API 側の制約

## API テスト

```bash
source /mnt/c/workspace/ai_elearning/.env
curl -s "https://open-api.thenational.academy/api/v0/{endpoint}" \
  -H "Authorization: Bearer $OAK_API_KEY" | python3 -m json.tool
```
