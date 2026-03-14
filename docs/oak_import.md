# Oak National Academy データ取り込み手順

## 概要

Oak National Academy（UK政府公認の教育プラットフォーム）から KS3 の教材データをスクレイピングで取得し、DBに登録する。

**ライセンス:** Open Government Licence v3.0（非商業・教育目的、帰属表示必須）
**URL:** https://www.thenational.academy/

---

## 取得方法

### データソース

Oak のWebページは Next.js で構成されており、各ページの `<script id="__NEXT_DATA__">` タグ内に教材データがJSON形式で埋め込まれている。APIキー不要でアクセス可能。

### 取得するデータ

各レッスンページから以下を抽出：

| データ | JSON パス | 用途 |
|--------|-----------|------|
| レッスン名 | `lessonTitle` | チャンクのタイトル |
| 学習目標 | `pupilLessonOutcome` | チャンク本文 |
| Key Learning Points | `keyLearningPoints[].keyLearningPoint` | チャンク本文 |
| キーワード＋定義 | `lessonKeywords[].keyword / .description` | チャンク本文 |
| よくある誤解 | `misconceptionsAndCommonMistakes[].misconception / .response` | チャンク本文 |
| 授業トランスクリプト | `transcriptSentences[]` | チャンク本文（メイン教材） |
| Starter Quiz | `starterQuiz[]` | 問題（source=oak） |
| Exit Quiz | `exitQuiz[]` | 問題（source=oak） |

### URL構造

```
# 単元一覧
https://www.thenational.academy/teachers/programmes/{programme}/units

# レッスン一覧
https://www.thenational.academy/teachers/programmes/{programme}/units/{unit}/lessons

# レッスン詳細（データ取得元）
https://www.thenational.academy/teachers/programmes/{programme}/units/{unit}/lessons/{lesson}
```

### DB登録の対応関係

```
1教科 = N個の Material（単元単位）
1 Material = N個の MaterialChunk（レッスン単位）
1 MaterialChunk = N個の Question（starter/exit quiz から抽出）
```

---

## プログラムslug一覧（KS3 全教科）

| 教科 | プログラムslug | インポート状況 |
|------|---------------|---------------|
| Science | `science-secondary-ks3` | ✅ 済（import_oak.py） |
| Maths | `maths-secondary-ks3` | ✅ 済 |
| English | `english-secondary-ks3` | ✅ 済 |
| History | `history-secondary-ks3` | ✅ 済 |
| Geography | `geography-secondary-ks3` | ✅ 済 |
| Computing | `computing-secondary-ks3` | ✅ 済 |
| Spanish | `spanish-secondary-ks3` | ✅ 済 |
| French | `french-secondary-ks3` | 未 |
| German | `german-secondary-ks3` | 未 |
| Latin | `latin-secondary-ks3-l` | 未 |
| Art and design | `art-secondary-ks3` | 未 |
| Citizenship | `citizenship-secondary-ks3` | 未 |
| Cooking and nutrition | `cooking-nutrition-secondary-ks3` | 未 |
| Design and technology | `design-technology-secondary-ks3` | 未 |
| Drama | `drama-secondary-ks3-l` | 未 |
| Financial education | `financial-education-secondary-ks3` | 未 |
| Music | `music-secondary-ks3` | 未 |
| Physical education | `physical-education-secondary-ks3` | 未 |
| Religious education | `religious-education-secondary-ks3` | 未 |
| RSHE (PSHE) | `rshe-pshe-secondary-ks3` | 未 |

---

## 実行方法

### Science のみ

```bash
docker exec elearn_app python batch/import_oak.py
```

### その他の教科（Maths, English, History, Geography, Computing, Spanish）

```bash
docker exec elearn_app python batch/import_oak_all.py
```

### 追加教科をインポートする場合

`batch/import_oak_all.py` の `SUBJECTS` 辞書に教科を追加してから実行する。
既にインポート済みの教科は自動スキップされる。

---

## レート制限

サーバー負荷を避けるため以下の間隔を設けている：

| 間隔 | 秒数 |
|------|------|
| リクエスト間 | 2秒 |
| 単元間 | 3秒 |
| 教科間 | 5秒 |

User-Agent: `OakContentImporter/1.0 (personal education project)`

---

## 注意事項

- Oak National Academy の公式API（https://open-api.thenational.academy/）のキーが取得できたら、スクレイピングではなくAPIに切り替えること
- APIキー申請済み（2026-03-14）、承認待ち
- `__NEXT_DATA__` の構造は Oak のサイト更新で変わる可能性がある
- トランスクリプトが存在しないレッスンもある（その場合 Key Points のみ）
