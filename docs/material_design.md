# マテリアル・問題生成・採点 設計書

## 1. 全体フロー

```
[データソース] Oak National Academy（OGLライセンス）
  ↓
[親] 管理画面からマテリアル登録（テキスト入力 / URL / PDF）
  ↓
[システム] テキスト抽出 → セクション単位でチャンク化 → DB保存
  ↓
[LLM] チャンクを読み → 4択問題 + 自由回答問題を生成 → DB保存
  ↓
[子供] 問題を解く
  ↓
  ├─ 4択 → DB照合で即採点（API不要）
  └─ 自由回答 → LLMが採点（部分点あり）
  ↓
[システム] 苦手分野を検知 → その分野の問題を追加生成
```

---

## 2. データソース

### 2-1. Oak National Academy（主要データソース）

UK政府公認の教育プラットフォーム。KS3（Year 7-9）の全教科が無料で利用可能。

**ライセンス:** Open Government Licence v3.0（2022年9月以降のコンテンツ）
- コピー、配布、改変OK
- 非商業的な教育目的での利用が条件
- 帰属表示（Oak National Academy）が必要

**URL:** https://www.thenational.academy/teachers/key-stages/ks3/subjects

#### 対応教科一覧（KS3 全21教科）

| カテゴリ | 教科 |
|----------|------|
| 主要教科 | **Science**, **Maths**, **English** |
| 人文 | History, Geography, Religious education, Citizenship |
| 語学 | French, Spanish, German, Latin |
| 技術 | Computing, Design and technology |
| 芸術 | Art and design, Music, Drama |
| 生活 | Cooking and nutrition, Physical education, Financial education, RSHE (PSHE) |

#### Science Year 7 単元

| 分野 | 単元 | レッスン数 |
|------|------|-----------|
| Biology | Cells | 7 |
| Biology | Ecosystems | 9 |
| Chemistry | Solutions | 11 |
| Physics | Forces | 10 |
| Physics | Solid, liquid, gas states and changes of state | 7 |
| Physics | Our solar system and beyond | 8 |
| Physics | Sound, light and vision | 8 |

#### Maths Year 7 単元（一部）

| 単元 | レッスン数 |
|------|-----------|
| Place value | 11 |
| Properties of number: factors, multiples, squares and cubes | 19 |
| Arithmetic procedures with integers and decimals | 17 |
| Expressions and equations | 17 |
| ほか複数単元あり | — |

各レッスンには**スライド・ワークシートPDF・クイズ2種・動画**が付属。
これらのコンテンツをマテリアルとして取り込み、LLMで問題を生成する。

### 2-2. 将来的な追加データソース

| ソース | 用途 |
|--------|------|
| OpenStax | 高校・大学レベルの理数系（無料・CC BY） |
| BBC Bitesize | 補助参照（スクレイピングは利用規約確認が必要） |
| 手動テキスト入力 | 親が任意の教材から入力 |

---

## 3. マテリアル管理

### 3-1. マテリアルの種類

| 種別 | 説明 | 例 |
|------|------|----|
| text | テキスト直接入力 | Oak Academy のスライド内容を転記 |
| url | URL指定 | Oak Academy のレッスンページURL |
| pdf | PDFアップロード | ワークシートPDF（将来対応） |

### 3-2. 言語対応

マテリアルは **言語別に登録**する。

- `language = 'en'`: 英語マテリアル（Oak National Academy, CGP等）
- `language = 'ja'`: 日本語マテリアル

問題文・選択肢・解説もマテリアルの言語で生成される。

### 3-3. チャンク化

教科書をそのままLLMに渡すとコンテキストが大きすぎるため、セクション/トピック単位で分割して保存する。

```
Material (教科書1冊 or 1単元)
  └── MaterialChunk (セクション単位)
        ├── chunk 1: "Cells - Animal and Plant Cells"
        ├── chunk 2: "Cells - Specialised Cells"
        ├── chunk 3: "Respiration"
        └── ...
```

- テキストの場合: 親が手動でセクション分けして登録、または一括登録→自動分割
- URLの場合: スクレイピング→テキスト抽出→自動分割
- PDFの場合: ページ単位 or 見出し単位で自動分割（Phase 5）

---

## 3. 問題形式

### 3-1. 4択問題 (multiple_choice)

従来通り。DBに正解を保持し、API呼び出しなしで採点。

```json
{
  "question_type": "multiple_choice",
  "question_text": "What is the function of mitochondria?",
  "options": [
    {"label": "A", "text": "Photosynthesis"},
    {"label": "B", "text": "Protein synthesis"},
    {"label": "C", "text": "Aerobic respiration"},
    {"label": "D", "text": "Cell division"}
  ],
  "correct_answer": "C",
  "explanation": "Mitochondria are the site of aerobic respiration."
}
```

### 3-2. 自由回答問題 (free_response)

生徒が自分の言葉で回答。LLMが採点。

```json
{
  "question_type": "free_response",
  "question_text": "Describe the process of photosynthesis.",
  "reference_answer": "Plants absorb light energy using chlorophyll in chloroplasts. They use carbon dioxide from the air and water from the soil to produce glucose and oxygen. The word equation is: carbon dioxide + water → glucose + oxygen.",
  "max_score": 10,
  "scoring_rubric": "light energy(1), chlorophyll/chloroplasts(1), CO2(1), water(1), glucose(1), oxygen(1), word equation(2), clarity(2)"
}
```

---

## 4. LLM採点（自由回答）

### 4-1. 採点フロー

```
[子供の回答テキスト]
  + [問題文]
  + [模範解答]
  + [採点ルーブリック]
      ↓
  [LLM API呼び出し]
      ↓
  JSON で返却:
  {
    "score": 7,
    "max_score": 10,
    "is_correct": false,
    "is_partial": true,
    "feedback": "光合成の過程はよく説明できています。ただし生成物として酸素の記述が抜けています。",
    "breakdown": [
      {"criterion": "light energy", "awarded": true},
      {"criterion": "oxygen", "awarded": false}
    ]
  }
```

### 4-2. 使用モデル

| 用途 | モデル | コスト目安 |
|------|--------|-----------|
| 問題生成 | Gemini 3.1 Flash Lite | ~0.05円/問 |
| 自由回答の採点 | Gemini 3.1 Flash Lite | ~0.05円/回答 |

**.env で切り替え可能:**

```env
LLM_PROVIDER=gemini              # gemini or openai
LLM_MODEL_SCORING=gemini-3.1-flash-lite
LLM_MODEL_GENERATE=gemini-3.1-flash-lite
GOOGLE_API_KEY=xxx
OPENAI_API_KEY=xxx               # 切り替え時用
```

### 4-3. LLMラッパー設計

```python
# services/llm.py

class LLMService:
    """LLMプロバイダーを抽象化。.envの設定で切り替え"""

    def generate_questions(self, chunk_text, language, question_types, count):
        """チャンクテキストから問題を生成"""

    def score_free_response(self, question, reference_answer, rubric, student_answer):
        """自由回答を採点。JSON構造で返却"""
```

内部で `LLM_PROVIDER` を見て Google Generative AI SDK / OpenAI SDK を切り替える。

---

## 5. 管理画面 UI フロー

### 5-1. 全体の画面遷移

```
マテリアル一覧  →  マテリアル登録  →  マテリアル詳細（プレビュー）  →  問題生成  →  問題一覧（プレビュー）
 /admin/materials    /admin/materials/new  /admin/materials/:id         ボタン押下      /admin/materials/:id/questions
```

### 5-2. 画面詳細

#### (A) マテリアル一覧 `/admin/materials`

マテリアルをカード or テーブルで一覧表示。

| 表示項目 | 説明 |
|----------|------|
| タイトル | マテリアル名 |
| 教科 | Science, Maths 等 |
| 言語 | EN / JA バッジ |
| チャンク数 | 登録済みセクション数 |
| 問題数 | 生成済み問題数 |
| ステータス | draft / ready / published |
| 操作 | 詳細 / 編集 / 削除 |

**ステータスの意味:**
- `draft`: マテリアル登録済みだが問題未生成
- `ready`: 問題生成済み、親が確認待ち
- `published`: 親が確認OK、子供の学習画面に公開

上部に「+ マテリアル登録」ボタン。

#### (B) マテリアル登録 `/admin/materials/new`

フォーム入力画面。

| フィールド | 入力方式 | 必須 |
|------------|----------|------|
| タイトル | テキスト | Yes |
| 教科 | セレクト（Science / Maths / English 等） | Yes |
| 言語 | ラジオ（EN / JA） | Yes |
| 難易度 | セレクト（easy / normal / hard） | Yes |
| 説明 | テキストエリア | No |
| ソース種別 | ラジオ（テキスト入力 / URL） | Yes |
| ソース内容 | テキストエリア or URL入力 | Yes |

登録後 → マテリアル詳細画面へ遷移。

#### (C) マテリアル詳細（プレビュー） `/admin/materials/:id`

マテリアルの中身を確認する画面。2つのタブ構成。

**[タブ1: コンテンツ]**
```
┌──────────────────────────────────────────────┐
│ 📄 Cells - KS3 Science Year 7          [編集] │
│ Science | EN | normal | draft                │
├──────────────────────────────────────────────┤
│ セクション一覧                     [+ 追加]   │
│                                              │
│ ┌─ 1. Animal and Plant Cells ────────────┐  │
│ │ All living organisms are made of cells. │  │
│ │ Animal cells have a nucleus, cell       │  │
│ │ membrane, cytoplasm and mitochondria... │  │
│ │                          [編集] [削除]  │  │
│ └─────────────────────────────────────────┘  │
│ ┌─ 2. Specialised Cells ─────────────────┐  │
│ │ Some cells are specialised to carry     │  │
│ │ out particular functions...             │  │
│ │                          [編集] [削除]  │  │
│ └─────────────────────────────────────────┘  │
│                                              │
│         [🤖 問題を生成する]                    │
└──────────────────────────────────────────────┘
```

- セクション（チャンク）を折りたたみ式で表示
- 各セクションの内容をプレビュー
- セクションの追加・編集・削除・並び替え
- 「問題を生成する」ボタン → LLMに問題生成を依頼

**[タブ2: 問題]** （問題生成後に表示）
```
┌──────────────────────────────────────────────┐
│ 生成済み問題 (8問)        [🤖 追加生成] [公開] │
├──────────────────────────────────────────────┤
│                                              │
│ ┌─ Q1 [4択] セクション: Animal Cells ────┐   │
│ │ What is the function of mitochondria?  │   │
│ │ A) Photosynthesis                      │   │
│ │ B) Protein synthesis                   │   │
│ │ ✅ C) Aerobic respiration              │   │
│ │ D) Cell division                       │   │
│ │ 解説: Mitochondria are the site of...  │   │
│ │                          [編集] [削除] │   │
│ └─────────────────────────────────────────┘  │
│                                              │
│ ┌─ Q2 [自由回答] セクション: Animal Cells ┐   │
│ │ Describe the differences between       │   │
│ │ animal and plant cells.                │   │
│ │                                        │   │
│ │ 📝 模範解答:                            │   │
│ │ Animal cells have a nucleus, cell      │   │
│ │ membrane, cytoplasm and mitochondria.  │   │
│ │ Plant cells also have a cell wall,     │   │
│ │ chloroplasts and a vacuole...          │   │
│ │                                        │   │
│ │ 📊 配点: 10点                           │   │
│ │ ルーブリック: nucleus(1), cell          │   │
│ │ membrane(1), cytoplasm(1), ...         │   │
│ │                          [編集] [削除] │   │
│ └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

- 生成された問題を一覧表示（4択は正解をハイライト、自由回答は模範解答+ルーブリック表示）
- 各問題を個別に編集・削除可能
- 「追加生成」で特定セクションの問題を増やせる
- 「公開」ボタンで status を published に → 子供の学習画面に表示

### 5-3. 問題生成時の操作フロー

```
親が「問題を生成する」ボタンを押す
  ↓
生成オプションダイアログ表示:
  - 問題数: [5] [10] [15] [20]
  - 問題タイプ: [✅ 4択] [✅ 自由回答]
  - 対象セクション: [✅ 全セクション] or 個別選択
  ↓
「生成開始」押下
  ↓
ローディング表示（LLM API呼び出し中）
  ↓
生成完了 → 問題タブに結果表示
  ↓
親が内容を確認・必要に応じて編集
  ↓
「公開」ボタンで子供に公開
```

### 5-4. ルーティング

| パス | メソッド | 説明 |
|------|----------|------|
| `/admin/materials` | GET | マテリアル一覧 |
| `/admin/materials/new` | GET | 登録フォーム表示 |
| `/admin/materials` | POST | マテリアル登録実行 |
| `/admin/materials/:id` | GET | 詳細（プレビュー）— コンテンツ+問題タブ |
| `/admin/materials/:id/edit` | GET/POST | 編集 |
| `/admin/materials/:id/delete` | POST | 削除 |
| `/admin/materials/:id/chunks` | POST | チャンク追加 |
| `/admin/materials/:id/chunks/:chunk_id` | POST/DELETE | チャンク編集/削除 |
| `/admin/materials/:id/generate` | POST | LLM問題生成 |
| `/admin/materials/:id/publish` | POST | 公開 |
| `/admin/materials/:id/questions/:qid/edit` | POST | 問題個別編集 |
| `/admin/materials/:id/questions/:qid/delete` | POST | 問題個別削除 |

---

## 6. 子供用学習画面

### 6-1. 画面フロー

```
教科選択         →  単元一覧           →  セクション要約      →  問題画面        →  結果画面
/child/subjects     /child/subjects/     /child/section/        /child/quiz/       /child/result/
                    Science              :chunk_id              :chunk_id          :session_id
                                         (スキップ可能)
```

### 6-2. セクション要約画面

チャンクのKey Points / Keywords / Misconceptionsをそのまま表示。
TranscriptはLLMで200-300文字に要約し、`material_chunks.summary`に保存（初回生成、以降キャッシュ）。

構成：
1. **What you'll learn** — Key Learning Points
2. **Key Words** — キーワード＋定義（カード形式）
3. **Watch out!** — Misconceptions
4. **Summary** — Transcriptの要約
5. **Start Quiz ボタン** + マスタリー進捗バー

### 6-3. ポイントシステム — マスタリー制

問題ごとに習得状態を管理。

| 状態 | ポイント |
|------|---------|
| 未習得の問題に正解 | **1pt** |
| 未習得の問題に不正解 → 後日正解 | **1pt**（習得時に付与） |
| 習得済みの問題を再回答 | **0pt**（練習は可能） |

習得条件: 1回正解
ポイント確定: セッション内の全問解答後にまとめて付与

### 6-4. ヒント機能

**レベル1: 固定ヒント（DBキャッシュ、API不要）**
- 問題生成時にLLMがヒントも一緒に生成 → `questions.hint` に保存
- 「💡 Hint」ボタンで即表示

**レベル2: AIチャット（LLMリアルタイム）**
- 「もっと聞く」でスティッキーなチャットUIが開く
- 子供が自由入力で質問できる
- LLMは**答えは絶対に言わない**、ヒントだけ返す
- 使用モデル: Gemini 3.1 Flash Lite（~0.05円/往復）

プロンプト制約:
```
You are a friendly tutor helping a Year 7 student.
- NEVER reveal the answer directly
- Give progressive hints, guiding them to think
- Use simple English appropriate for age 11-12
- Be encouraging
```

### 6-5. 子供用ルーティング

| パス | メソッド | 説明 |
|------|----------|------|
| `/child/subjects` | GET | 教科選択（Year 7） |
| `/child/subjects/:subject` | GET | 単元一覧 |
| `/child/section/:chunk_id` | GET | セクション要約（学習ページ） |
| `/child/quiz/:chunk_id` | GET | 問題画面（セクション内の全問） |
| `/child/quiz/answer` | POST | 回答送信（Ajax） |
| `/child/quiz/:chunk_id/result` | GET | 結果画面 |
| `/child/hint/:question_id` | POST | AIチャットヒント（Ajax） |

---

## 7. 苦手分野の検知と追加問題生成

### ロジック

```
answer_history から直近N問の正答率をチャンク（トピック）単位で集計
  ↓
正答率が閾値（例: 50%）以下のトピックを「苦手」と判定
  ↓
該当チャンクから追加問題をLLMで生成
```

- 自動生成のタイミング: 学習セッション完了時 or バッチ処理
- 生成される問題数: 苦手トピックにつき3〜5問（設定可能）

---

## 6. DB設計変更

### 6-1. 変更するテーブル

#### materials（変更）
| カラム | 型 | 変更内容 |
|--------|----|----------|
| language | ENUM('en','ja') | **追加** — マテリアルの言語 |
| source_type | ENUM('text','url','pdf') | **変更** — pdfを追加 |
| file_path | VARCHAR(500) | **追加** — PDFファイルのパス |

#### questions（変更）
| カラム | 型 | 変更内容 |
|--------|----|----------|
| question_type | ENUM | **変更** — 'free_response'を追加 |
| reference_answer | TEXT | **追加** — 自由回答の模範解答 |
| max_score | INT | **追加** — 最大スコア（デフォルト10） |
| scoring_rubric | TEXT | **追加** — 採点ルーブリック |
| chunk_id | INT FK | **追加** — 出題元チャンクへの参照 |

#### answer_history（変更）
| カラム | 型 | 変更内容 |
|--------|----|----------|
| user_answer | TEXT | **変更** — VARCHAR(10)→TEXT（自由回答対応） |
| score | INT | **追加** — 獲得スコア（部分点対応） |
| max_score | INT | **追加** — 最大スコア |
| llm_feedback | TEXT | **追加** — LLMからのフィードバック |

### 6-2. 追加するテーブル

#### material_chunks（新規）
| カラム | 型 | 説明 |
|--------|----|------|
| chunk_id | INT PK | チャンクID |
| material_id | INT FK | マテリアルID |
| title | VARCHAR(255) | セクション名 |
| content | LONGTEXT | チャンク本文 |
| page_start | INT | 開始ページ（PDF用） |
| page_end | INT | 終了ページ（PDF用） |
| sort_order | INT | 表示順 |
| created_at | DATETIME | 作成日時 |

---

## 7. 実装順序

### Phase 1: マテリアル登録UI
1. Material モデル + MaterialChunk モデル作成
2. 管理画面: マテリアル一覧・登録（テキスト入力）
3. 管理画面: マテリアル編集・削除
4. チャンク手動登録（セクション追加UI）

### Phase 2: LLM問題生成
5. LLMラッパー（services/llm.py）— Gemini / OpenAI 切り替え
6. チャンクから問題生成（4択 + 自由回答）
7. 生成された問題の確認・編集UI

### Phase 3: 学習画面連携
8. 子供の学習画面をDB連携（デモデータ→実データ）
9. 4択の採点（DB照合）
10. 自由回答の採点（LLM）
11. ポイント計算（部分点対応）

### Phase 4: 適応学習
12. 苦手分野検知ロジック
13. 追加問題の自動生成

### Phase 5: PDF対応
14. PDFアップロード + テキスト抽出
15. 自動チャンク化
