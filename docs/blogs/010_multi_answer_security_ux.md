# 010: 複数回答対応・セキュリティ・UX改善

**日付:** 2026-03-24

## 概要

Oak API由来のMC問題で複数正解が失われていた問題を修正し、クイズUIを複数選択対応に。あわせてLLMレートリミット、子供管理の編集機能、Year表示バグ修正、ナビゲーション改善など広範なUX強化を実施した。

## 実施内容

### 1. Year表示バグ修正（YEAR_GROUP=7 ハードコード問題）

子供画面のルート（`child_learn.py`, `child_dashboard.py`）で `YEAR_GROUP = 7` がハードコードされていた。

- **表示:** テンプレート3箇所で `Year {{ 7 }}` → `Year {{ current_user.grade or '?' }}`
- **データフィルタリング:** 定数を `_year_group()` 関数に置換。`current_user.grade` を使用し、未設定時は7にフォールバック
- **影響:** Year 4 の Ryu が Year 7 の教材を見ていた問題が解消

### 2. 複数回答（Multi-Answer）対応

Oak APIの `multiple-choice` 問題で `distractor: false` が複数ある場合、最後の1つしか `correct_answer` に保存されていなかった。

**インポート修正:**
- `correct_label`（単一変数）→ `correct_labels`（リスト）に変更
- `correct_answer` をカンマ区切りで保存（例: `"A,C,D"`）

**既存データ修正バッチ:**
- `--fix-multi-answer` オプションを `import_oak_api.py` に追加
- Oak APIから再取得して question_text でマッチング、correct_answer を更新
- Year 7: 899問修正、Year 4 Maths/Science/Spanish: 462問修正（合計1,339問）

**クイズUI:**
- `multiAnswer` フラグをJS側に渡し、該当問題はチェックボックス式UIに
- 「Select All That Apply」バッジ + 問題文下に指示テキスト表示
- `toggleOption()` 関数で複数選択/解除
- 回答はカンマ区切りで送信、採点はソートして完全一致比較

**Admin画面:**
- チャンク詳細で複数正解を全てハイライト表示
- KaTeX（数式レンダリング）をadmin base.htmlに追加

### 3. LLMレートリミッター

外部公開に伴うLLM API濫用対策として `services/rate_limiter.py` を新規作成。

| 制限 | 値 |
|------|-----|
| ユーザー別/時間 | 20回 |
| ユーザー別/日 | 50回 |
| グローバル/日 | 500回 |
| ヒントチャット/問 | 5回 |

**適用箇所:**
- `POST /child/hint/<id>` — ヒント自動生成 + AIチャット
- `_llm_grade()` — free_response のLLM採点（超過時はfuzzy matchフォールバック）
- `_generate_explanations()` — 解説一括生成（超過時はスキップ）

**管理画面:** ダッシュボードに「AI Usage (today)」カード追加。

### 4. Family Code 編集機能

`/admin/children` でFamily Codeをインライン編集可能に。

- ペンアイコンで編集モードに切替
- フロント: HTML pattern + JS で英数字5〜10文字バリデーション
- バックエンド: `POST /admin/family-code` で重複チェック + 大文字変換

### 5. 子供アカウント編集機能

`/admin/children` で各子供のインライン編集を追加。

- カードにホバーで編集・削除ボタン表示
- 編集: 名前、Year（必須）、PIN（空欄なら変更なし）
- `POST /admin/children/<id>/edit` JSON API
- Year（grade）は新規作成・編集とも必須化

### 6. ナビゲーション・UX改善

**ダッシュボード → 教科ページ連携:**
- 「Start Playing」クリックで `/child/subjects/Maths?unit=184&focus=1548` に遷移
- 該当ユニットのアコーディオン自動展開 + チャンクをハイライト
- 初回ユーザー: 「Start here」、継続ユーザー: 「Continue here」バッジ

**Mastered問題のUX:**
- 緑バナーで「Already mastered! No points awarded for mastered questions.」表示
- Skipボタンを緑系に変更、テキストを「Skip (mastered)」に

**教科の表示順:**
- アルファベット順 → カリキュラム順（Science, Maths, English, History, Geography, Computing, Spanish, French, German）
- `/child/profile`, `/child/subjects`, サイドバー教科一覧に適用

**Material sort_order修正:**
- Year 4 の全教科（97マテリアル）の sort_order を Oak API から更新
- `--fix-sort-order` バッチオプションを追加
- 今後のインポートでも `import_unit()` に sort_order パラメータを渡すよう修正

### 7. ヒント自動生成

`POST /child/hint/<id>` で hint カラムが空の場合、LLM で自動生成してDBに保存。以降は保存済みヒントを返す。

## 技術メモ

- **レートリミッター:** メモリ内カウンター（threading.Lock使用）。Redis不要、アプリ再起動でリセットされるが、コスト保護には十分
- **Oak API レート制限:** 1000 req/hour。2バッチ同時実行で429エラー発生。1つずつ順番に実行する必要がある
- **Oak API 著作権制限:** Computing、一部English/Geography/Historyで HTTP 400 (copyright restrictions)
- **asciiエンコードエラー:** `_get_lesson_slug()` がcurly quotes（`'` `'`）を処理できない。English系タイトルに多い。要修正
- **CLAUDE.md ルール追加:** #10 sort_order必須、#11 複数正解対応必須

## 変更ファイル

- `services/rate_limiter.py` — 新規（LLMレートリミッター）
- `batch/import_oak_api.py` — fix-multi-answer, fix-sort-order, sort_order対応
- `routes/child_learn.py` — Year動的化、複数回答採点、レートリミット適用
- `routes/child_dashboard.py` — Year動的化、教科ソート、next_section改善
- `routes/admin_children.py` — Family Code編集、子供編集API
- `routes/admin_dashboard.py` — LLM統計表示
- `templates/child/quiz.html` — 複数選択UI、mastered banner
- `templates/child/units.html` — focus/highlight機能
- `templates/child/dashboard.html` — Start Playing リンク改善
- `templates/admin/children.html` — Family Code編集、子供編集UI
- `templates/admin/base.html` — KaTeX追加
- `templates/admin/material_chunk_detail.html` — 複数正解表示
- `translations/en.json`, `translations/ja.json` — 新規キー追加
