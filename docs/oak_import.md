# Oak National Academy データ取り込み手順

## 概要

Oak National Academy（UK政府公認の教育プラットフォーム）から教材データを取得し、DBに登録する。

- **ライセンス:** Open Government Licence v3.0
- **API仕様:** [docs/oak_api_reference.md](oak_api_reference.md) を参照
- **進捗管理:** [docs/oak_import_progress.md](oak_import_progress.md) を参照

---

## スクリプト

| 方式 | スクリプト | 状態 |
|------|-----------|------|
| 公式API（推奨） | `batch/import_oak_api.py` | 稼働中 |
| スクレイピング（旧） | `batch/import_oak.py`, `batch/import_oak_all.py` | 非推奨 |

---

## 実行方法

```bash
# デフォルト（KS3, 7教科, 全学年）
docker exec elearn_app python batch/import_oak_api.py

# 特定教科・Key Stage・学年を指定
docker exec elearn_app python batch/import_oak_api.py --subjects science --key-stages ks3 --years 7

# 全Key Stage、全教科
docker exec elearn_app python batch/import_oak_api.py --all-key-stages --all-subjects

# KS1+KS2 の Maths と English
docker exec elearn_app python batch/import_oak_api.py --key-stages ks1 ks2 --subjects maths english

# dry-run（API接続テスト、DB書き込みなし）
docker exec elearn_app python batch/import_oak_api.py --dry-run

# 利用可能な教科一覧
docker exec elearn_app python batch/import_oak_api.py --list-subjects
```

---

## DB登録の対応関係

```
1教科×1学年 = N個の Material（単元単位）
1 Material = N個の MaterialChunk（レッスン単位）
1 MaterialChunk = N個の Question（starter/exit quiz から抽出）
```

### Question の種類変換

| Oak API questionType | DB question_type | 変換方法 |
|---------------------|------------------|---------|
| multiple-choice | multiple_choice | distractor=false が正解 |
| short-answer | free_response | 全 answers が許容される正解バリエーション |
| match | free_response | matchOption → 問題文に追加、correctChoice → 正解 |
| ordering | free_response | order フィールドで正しい順番を組み立て |

---

## レート制限

| 制限 | 値 |
|------|-----|
| API上限 | 1000 req/hour |
| スクリプト間隔 | 3.6秒/リクエスト |
| User-Agent | `OakContentImporter/2.0 (personal education project)` |
| リトライ | 401エラー時 最大3回（Cloudflare一時エラー対策） |

---

## 注意事項

- タイトル重複チェックで既存データは自動スキップされる
- トランスクリプトが存在しないレッスンもある（Key Points のみ）
- 全Key Stage×全教科は約24時間かかるため分割実行を推奨
