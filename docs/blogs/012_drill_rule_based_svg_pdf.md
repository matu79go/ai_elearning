# 012: 小テスト + ルールベース算数 + YouTube + PDF + SVGチャート — 大統合リリース

**日付:** 2026-04-17

## 概要

運用を始めて判明した課題 ("間違えた問題をそのまま再出題させると答えを暗記してしまう" "Oak の動画がつまらない" "学校の PDF を取り込みたい") に対応するため、1日で以下を一気に実装した。

1. **ルールベース算数問題生成** — YAMLテンプレから無限に問題を生成
2. **小テスト (Drill) モード** — 1問ずつ即時判定、N連続正解で合格、ポイント獲得
3. **SRS (間隔反復) の簡易版** — 当日回答済み除外 + 誤答テンプレの3日ローテーション
4. **LLMプロンプト大改訂** — 教科/学年/Oak問題参考で高品質生成
5. **YouTube動画自動マッピング** — YouTube Data API + LLM ランキングで各 chunk に動画候補5本
6. **PDF → マテリアル自動化** — ドラッグ&ドロップ、メタデータ自動抽出、章立て自動分割
7. **SVGチャート生成** — pie/bar/line/function を Python 純正で描画、LLM 問題生成と統合
8. **Claude による手動マテリアル構築** — mock の PDF を Claude 自身が読んで MYP1 science/maths 教材を作成

生成された問題総数は LLM 7,700 + ルールベース 442 + 本日追加分 ~600 = **約 8,700問**。


## 背景 — 運用で見えた課題

### 課題1: 「間違い問題の再出題で答えを暗記する」
従来は chunk 内の全問題を出題していたため、間違えた問題が翌日もすぐ出て、内容理解なしに答えだけ覚えるケースが発生。

### 課題2: 「Oak 動画がつまらない」
Oak National Academy の講義動画は正確だが、子供のエンゲージメントを維持しにくかった。YouTube にはもっと手軽で魅力的な解説動画が多数あるが、手動で探すのは非現実的。

### 課題3: 「学校固有のプリントを取り込めない」
MYP1 (中1相当) の学校教材は Oak KS3 のカリキュラムとトピックが一致せず、特に算数の「ピーチャート」「棒グラフ」や理科の「酸とアルカリ」は Y7 KS3 に対応単元がない。学校配布 PDF をそのまま教材化したい。

---

## 実装内容

### 1. ルールベース算数問題生成

**動機:** LLM 呼び出しコストをかけず、算数ドリル用に無限に異なる問題を量産する。

**仕組み:**
- `config/math_templates.yaml` に DSL でテンプレ定義:
  ```yaml
  - id: frac_add_diff_denom
    template_en: "Calculate: {a}/{b} + {c}/{d}"
    variables:
      b: {type: int, min: 2, max: 10}
      d: {type: int, min: 2, max: 10, distinct_from: [b]}
      a: {type: int, min: 1, max_expr: "b - 1"}
      c: {type: int, min: 1, max_expr: "d - 1"}
    answer_expr: "F(a, b) + F(c, d)"
    answer_type: fraction
    distractor_exprs:
      - "F(a + c, b + d)"    # 分子分母を足してしまう典型ミス
      - "F(a + c, b * d)"
  ```
- `services/math_generator.py`:
  - `ast` ベースの安全な式評価 (`eval` 禁止、whitelist のみ)
  - Python `fractions.Fraction` で有理演算
  - `answer_type`: `integer` / `fraction` / `mixed` / `algebraic_over_x`
  - seed で決定性あり → answer_history に再現キー保存可

**投入結果 (Y7 Math chunks 2057-2061):**
- 14 テンプレ (分数加減乗除、混合数、量の分数、代数分数 a/x 系、一次方程式)
- chunk毎に 30 drill + 50 test 生成 (計 400問)

**難しかった点:**
- 代数分数 `17/2x` の表示で `Fraction(17,2)` を素朴に "/x" 付けると `17/2/x` になってしまうバグ。`algebraic_over_x` 専用レンダラー (`n/(2x)` 形式) を追加して解決。
- 「予約語 `rank`」トラップ: MySQL 8 では reserved。`rank_position` にリネーム。

### 2. 小テスト (Drill) モード

**設計方針:**
- **別テーブル** で完全分離 (`drill_questions`, `drill_sessions`, `drill_answer_history`)
- 1問ずつ即時判定、N連続正解 (config 可変、デフォルト3) で合格
- 合格でポイント 5pt (config 可変)
- **Oak問題は使わない**: Oak は最終テスト専用、ドリルは LLM or rule_based のみ
- ドリル未達成の chunk は **最終テストがロック** (`/child/quiz/<id>` 直URLでも drill にリダイレクト)

**子供向け UI:**
- イントロ画面で「3問連続正解で 5pt ゲット」説明
- ストリーク表示 (ドット + 数字)、PC では左サイドバーにもリアルタイム反映
- 不正解時は正解を緑でハイライト + 解説表示、「つぎへ」ボタン
- 完了画面: 🏆 + ポイントバッジ + 「テストに挑戦する」大きな CTA (drill_mastered=True で本番テスト解放)

**admin UI:**
- chunk detail に Content / **小テスト** / Questions の3タブ
- 「問題作成 (AI)」「問題作成 (ルール)」chip ボタン
- ポイント消費ハマり: `point_history.reason_type` ENUM に `drill_complete` を追加し忘れて最初の達成がロールバックされる不具合があった (migration 05 で追加)

### 3. SRS (間隔反復) 簡易版

**要件:**
- 当日回答済みの問題は出題プールから除外
- 直近3日で誤答した rule_based テンプレは、新しいインスタンス (別の乱数値) で優先出題
- 「テストは 10問固定」をconfigで定義 (`QUIZ_QUESTIONS_PER_SESSION`)

**実装:**
- `_answered_today_qids(child, chunk)` で今日の question_id セット取得
- `_recent_wrong_templates(child, chunk, days=3)` で直近3日誤答 template_id セット取得
- 誤答テンプレは `materialize_question()` で新インスタンス生成し「優先枠」(最大 limit/2) に入れる
- 残り枠は既存プールからランダムサンプリング
- プール不足時は `materialize_chunk_pool` で自動補充

**結果画面のバグも修正:**
chunk全問を表示していたのを、直近 `LearningSession` の answer_history 参照に変更 → 10問解いたら結果画面は 10問だけ表示。

### 4. LLMプロンプト大改訂

**Before (決め打ち):**
```python
prompt = "You are a KS3 science teacher. Create questions for Year 7 students..."
```
→ Maths や Y4 でも「science teacher, Year 7」として生成される

**After (動的):**
- `subject`, `year_group`, `summary`, `oak_examples` を引数化
- Oak既存問題を 5件サンプリングして「REFERENCE QUESTIONS — follow this style, do NOT duplicate」として添付
- 教科/学年ミスマッチ解消、Oak スタイルに寄せた自然な生成

**適用して一気に LLM 生成:**
- Y7 Science 96 chunks, Spanish 71, English 63, Y4 Math 165, Y4 Science 90
- chunk毎に drill 5 + test 10 (MC 7 + FR 3) = 15問
- 合計 **約 7,250問** 生成、失敗 13件 → リトライ script で全復旧 (JSON parse 失敗が主)

### 5. YouTube動画マッピング

**設計:**
- 新テーブル `chunk_youtube_videos` で 1 chunk に最大5本の候補を保持、1本を `is_primary=True`
- `services/youtube_finder.py`:
  - YouTube Data API v3 で search (100 units/call)
  - videos.list で duration 取得 (1 unit)
  - LLM (Gemini) に「教科別優先チャンネル (Free Science Lessons, Corbett Maths 等) を考慮してランキング」を依頼
  - 既存動画がある chunk では API 呼ばない (force=False で quota 節約)

**途中のハマり:**
- Gemini の "Google Search grounding" で URL 返させたら **全ハルシネーション** (`g2s6K_s-90w` など実在しない video_id を連発)。oembed で検証したら 404。**Gemini が URL 生成するのは信用できない**と学習。
- YouTube Data API v3 を有効化 (新規プロジェクト `ai-elearning-490608` で API Key 作成)
- 初回 Spanish クエリが 0件返却 → タイトルに特殊文字 (アポストロフィ等) が含まれ API が拒否。クエリ長短縮 + 特殊文字除去のフォールバック追加。

**子供画面:**
- Primary YouTube 動画を iframe で最上部に表示
- その下にサムネストリップ (他4本を横スクロールで切替可能)
- YouTube 動画が無い chunk は Oak Drive 動画に fallback

**admin 画面:**
- Content / 小テスト / Questions / **YouTube** の4タブ
- PRIMARY 切替、個別削除、手動 URL 追加、自動検索

**quota状況:**
- 無料枠 10,000 units/日 = ~99 chunks/日
- Y7 Science 96 chunks 実行で 82/96 成功、末尾 14 件 quota切れ (HTTP 403)
- TODO に「1日 ~100 chunks ずつ」の優先ロードマップを追加、P0 マーク

### 6. PDF → マテリアル自動化

**フロー:**
1. `/admin/materials/new` で「PDF アップロード」ラジオ選択
2. **ドラッグ&ドロップ** or クリックでファイル指定
3. **瞬時に LLM 解析** (背景で `/admin/materials/analyze-pdf` AJAX)
   - title, subject, difficulty, description, **material_type** (lesson/glossary/worksheet/assessment/other) を自動抽出してフォームに反映
   - 編集可能
4. Save 押すと:
   - `static/uploads/materials/material_<id>.pdf` に保存
   - PyMuPDF でテキスト抽出
   - LLM が **種別別プロンプト** で 3-8 章に分割 + 各章 summary 生成
5. Submit中は **半透明 overlay + スピナー + ステップ進捗** (30-60秒)
6. `/admin/materials/<id>` にリダイレクト、章一覧表示

**種別別プロンプト:**
- `lesson`: 普通のレッスン章立て
- `glossary`: "Key terms: A, B, C..." 形式の summary
- `worksheet`: "Task 1:" 形式で課題別に
- `assessment`: 評価観点別
- `other`: 汎用

**既存 material への追加:**
- material detail ページに「セクション追加」タブ 2 つ (手動 / PDFから)
- PDF アップロード時に **AI が種別を自動判定** (親 material の種別に引っ張られない)

**ハマった点:**
- `{% block content %}` と書いてたら base template が `main_content` を期待してて空画面。ブロック名ミス。
- 最初 chunks-from-pdf が親 material の material_type を継承してたため、Glossary material に Worksheet PDF 追加すると全部「用語集形式」で chunks 化されて混乱。PDF 毎の AI 種別判定に変更。

### 7. SVG チャート生成

**動機:** Pie Chart や Bar Chart を扱う単元では「図を見て答える」問題が必須。LLM のテキストだけでは図を提供できない。

**実装:** `services/chart_svg.py` (Python 純正、依存ゼロ)
- `pie_chart(data)` — 円グラフ、凡例、スライス内ラベル
- `bar_chart(data, x_label, y_label)` — gap 付き棒グラフ、gridline、値ラベル
- `line_chart(points, title)` — 折れ線、数値軸/カテゴリ軸自動判定
- `function_plot(expr, x_min, x_max)` — y = f(x) を safe_eval でサンプリング、x=0/y=0 軸線付き
  (Y7 では未使用だが、Y8-Y10 の二次関数/三次関数問題用に)

**LLM 統合:**
- `generate_questions()` のプロンプトに:
  > "For questions that genuinely need a chart, include `chart_type` + `chart_data`. Formats: pie/bar/line. Only include when question_text refers to it."
- LLM 出力を `_render_chart_if_valid()` で安全に SVG 化
- DB `questions.chart_svg` / `drill_questions.chart_svg` (MEDIUMTEXT) に保存

**結果 (material 282 = Unit 6 - Graphs and Data Handling):**
- 166 問中 30問 (18%) に chart 付き (LLM が必要性を判断)
- 「pie chart の Purple slice は何度？」→ Quality Street 円グラフ SVG 付き
- 「四半期売上グラフのトレンドは？」→ 時系列 line chart 付き
- 「棒グラフで Bananas は何人？」→ bar chart 付き

### 8. Claude による手動マテリアル構築

LLM (Gemini) に PDF を渡すと種別判定は当たっても、chunk の content が簡素になりがち。そこで **Claude (私) が直接 mock の PDF を読んで**、教材的な構造で chunks を書き下ろすフローも用意した。

**成果物:**
- `batch/create_solutions_material.py` → Y7 Science **MYP1E - Solutions, Acids and Alkalis** (9 chunks)
  - Target Sheet で MYP1 シラバスを骨格にし、HW1 / 実験シート / Data Analysis / Glossary の 5 PDFs から該当セクションを割り当て
- `batch/create_graphs_material.py` → Y7 Maths **Unit 6 - Graphs and Data Handling** (8 chunks)
  - Types of Graph PDF の Time series / 季節変動 / Examples 1-3 など詳細を拾う
  - Pie Charts PDF の Task 2 (Cleckheaton + TV ブランド) / Example 1 (住宅540軒) / Task 3 (科目+カフェ) / Task 4 を反映
  - Chunks 5-8 を pie charts 専用に (学校で現在学習中)

**失敗事例とフィードバック:**
- 最初「Types of Graph PDF 内容 1行しか読まず」chunks 書いて user に指摘された。以後、PDF 全文 (6,400 chars) 読み切ってから chunks 設計する方針に変更。
- MyiMaths / Transum の外部リンクは本アプリのドリル/テストで代替するため削除。

---

## デプロイ

**コード + DB:**
- commit 2本 (0d93436, f1c08bf) → GitHub push → VPS git pull → docker rebuild
- migrations 03-08 本番適用:
  - 03: questions に template_id / generated_payload / rule_based enum
  - 04: drill_questions / drill_sessions / drill_answer_history
  - 05: point_history に drill_complete
  - 06: chunk_youtube_videos
  - 07: materials に material_type
  - 08: questions / drill_questions に chart_svg
- .env.prod + docker-compose.prod.yml に `YOUTUBE_API_KEY` 追加

**データ:**
- ID 衝突回避: ローカル question_id (17668+) が prod の Oak 範囲 (〜17817) と重なるため、**question_id を除外して INSERT** (auto_increment 任せ)
- manual → oak 一括 UPDATE (125問、legacy import bug 修正)
- 本日分:
  - material 280/282 (ローカル) → 278/279 (本番) に自動採番
  - 91 drill + 255 test + 15 chart_svg 問題投入

---

## 学び

### 良かった判断

- **別テーブル (drill/questions) の完全分離**: テスト用の壊れていないOak問題に drill 生成問題が混入しない
- **ルールベース + LLM + 手動** の3層生成: 算数はルール、他は LLM、複雑な教材は Claude が書く — 質とコストのバランス◎
- **AI 自動判定 + ユーザー編集可能**: PDF種別は AI が判定するが、フォームに入れて override 可 (「一番頭がいいあなたにまかせたほうがいい」という user 発言が設計の根拠)
- **SVG 専用関数を書いた**: matplotlib を入れずに済んだ。依存ゼロで軽量

### ハマったポイント

- **Gemini の URL ハルシネーション**: 実在しない video_id を返す。検証 API (YouTube oembed) で確認する習慣が必要
- **Docker env 更新には `up --force-recreate`**: `restart` ではコンテナが env vars を再読込しない。`YOUTUBE_API_KEY` が反映されなくて 10分悩んだ
- **Jinja ブロック名**: 新規テンプレは既存テンプレのブロック名を確認してから書く (`main_content` vs `content`)
- **MySQL 予約語**: `rank` は 8.0 で予約。テストで初めて気づく。`rank_position` にリネーム
- **ENUM に値追加忘れ**: 新しい point_history reason (`drill_complete`) が ENUM に無く、ドリル達成が全ロールバックしていた

### UX フィードバック

- ユーザーから「サブミット中、画面が固まって送られたかわからない」→ overlay + スピナー + ステップ進捗を追加
- 「自動取得した種別が違ったら」→ ドロップダウンに自動選択、編集可能に
- 「ドラッグ&ドロップで PDF 上げたい」→ 4行JSで実装
- 「AIに任せるのがいい、画面からアップじゃなく」→ Claude 自身が PDF 読んで手動構築する batch script に分離

---

## 次のステップ (TODO P0 抜粋)

**🔴 最優先:**
- [ ] **YouTube動画マッピング 日次展開** (~100 chunks/日、無料枠)
  - 2026-04-17 Y7 Science 82/96 完了
  - 以降、Maths/Spanish/English/History/Geography/Computing と Y4 を1日1バッチずつ

**🟠 高優先:**
- [ ] 小テスト Phase 3 (ダッシュボード履歴、Drill Master バッジ)
- [ ] SRS 残件: `next_review_at` / 選択肢シャッフル (quiz側)
- [ ] Y7 Math 残り 101 chunks (ルールベース外) を LLM生成

**🟡 中優先:**
- [ ] マスタリー自動進級
- [ ] カリキュラム予習機能
- [ ] Y8-11 インポート

---

## コード統計 (本日)

- **新規コミット**: 2 本
- **新規ファイル**: 20+ (models, services, routes, templates, batch scripts, migrations)
- **新規テーブル**: 4 (drill×3 + chunk_youtube_videos)
- **新規 ENUM/カラム**: material_type, chart_svg, template_id, generated_payload, rule_based source, drill_complete reason
- **データ追加**: 約 8,700 問 (LLM 7,250 + ルール 442 + 手動/SVG 600+)
- **対応 subjects**: Math, Science, Spanish, English (Y7 + Y4)

1日でここまで詰め込めたのは、基盤 (Flask, SQLAlchemy, Docker, LLM接続) が整っていたおかげ。要件発見 → 設計 → 実装 → デプロイのサイクルを何度も回せた。
