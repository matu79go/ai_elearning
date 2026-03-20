# Oak API インポート進捗

## 概要

- 方式: 公式API (`batch/import_oak_api.py`)
- レート制限: 1000 req/hour → 3.6秒間隔
- 全体見積もり: ~955ユニット, ~7,600レッスン, ~23,800 API calls, 約24時間

## 進捗

### KS1 (Year 1-2)

| Subject | Year 1 | Year 2 | Status |
|---------|--------|--------|--------|
| Science | - | - | 未 |
| Maths | - | - | 未 |
| English | - | - | 未 |
| History | - | - | 未 |
| Geography | - | - | 未 |
| Computing | - | - | 未 |
| Spanish | N/A | N/A | N/A |

### KS2 (Year 3-6)

| Subject | Year 3 | Year 4 | Year 5 | Year 6 | Status |
|---------|--------|--------|--------|--------|--------|
| Science | - | ✅ 9u/90l/1196q | - | - | Year 4 完了 |
| Maths | - | ✅ 25u/165l/2575q | - | - | Year 4 完了 |
| English | - | ✅ 42u/201l/3132q | - | - | Year 4 完了（著作権ブロック多数） |
| History | - | ✅ 6u/36l/467q | - | - | Year 4 完了 |
| Geography | - | ✅ 6u/37l/173q | - | - | Year 4 完了（著作権ブロック多数） |
| Computing | - | ✅ 6u/36l/401q | - | - | Year 4 完了 |
| Spanish | - | ✅ 6u/29l/422q | - | - | Year 4 完了 |

### KS3 (Year 7-9)

| Subject | Year 7 | Year 8 | Year 9 | Status |
|---------|--------|--------|--------|--------|
| Science | ✅ 13u/96l/1345q | - | - | Year 7 完了 |
| Maths | ✅ 10u/97l/1522q | - | - | Year 7 完了 |
| English | ✅ 7u/63l/838q | - | - | Year 7 完了 |
| History | ✅ 14u/75l/945q | - | - | Year 7 完了 |
| Geography | ✅ 7u/70l/474q | - | - | Year 7 完了 |
| Computing | ✅ 6u/36l/228q | - | - | Year 7 完了 |
| Spanish | ✅ 14u/71l/1003q | - | - | Year 7 完了 |

### KS4 (Year 10-11)

| Subject | Year 10 | Year 11 | Status |
|---------|---------|---------|--------|
| Science | N/A | N/A | N/A |
| Maths | - | - | 未 |
| English | - | - | 未 |
| History | - | - | 未 |
| Geography | - | - | 未 |
| Computing | - | - | 未 |
| Spanish | - | - | 未 |

## 実行ログ

| 日付 | 対象 | ユニット | レッスン | 問題数 | 時間 | メモ |
|------|------|---------|---------|--------|------|------|
| 2026-03-16 | KS3 Science Year 7 | 13 | 96 | 1,345 | ~19分 | 完了。match問題はfree_response（次回再インポートでMC化） |
| 2026-03-17 | KS3 全7教科 Year 7 | 71 | 508 | 6,355 | - | Year 7 全教科完了 |
| 2026-03-19 | KS2 Science Year 4 | 9 | 90 | 1,196 | - | 5u既存+1u追加 |
| 2026-03-19 | KS2 Maths Year 4 | 25 | 165 | 2,575 | - | 1レッスンAPI 500エラー |
| 2026-03-19 | KS2 English Year 4 | 42 | 201 | 3,132 | - | 著作権ブロック多数（reading/poetry系） |
| 2026-03-19 | KS2 History Year 4 | 6 | 36 | 467 | - | 完了 |
| 2026-03-19 | KS2 Geography Year 4 | 6 | 37 | 173 | - | 著作権ブロック多数 |
| 2026-03-19 | KS2 Computing Year 4 | 6 | 36 | 401 | - | 完了 |
| 2026-03-19 | KS2 Spanish Year 4 | 6 | 29 | 422 | - | 一部API 500エラー |
