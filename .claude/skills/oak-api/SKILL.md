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

## API テスト

```bash
source /mnt/c/workspace/ai_elearning/.env
curl -s "https://open-api.thenational.academy/api/v0/{endpoint}" \
  -H "Authorization: Bearer $OAK_API_KEY" | python3 -m json.tool
```
