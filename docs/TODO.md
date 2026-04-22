# TODO

優先度の凡例:
- 🔴 **P0**: 最優先（毎日回す、絶対やる）
- 🟠 **P1**: 高優先（近日中）
- 🟡 **P2**: 中優先（余裕できたら）
- 🟢 **P3**: 低優先（将来）

---

## 🔴 P0 — 最優先

### 🎥 YouTube動画マッピング（日次 ~100 chunk ずつ、quotaリセット待ち）

**なぜ P0**: ユーザー視点で動画品質が最重要。Oak動画がつまらないので YouTube に置き換え中。無料枠消化ベースで日次継続。

**運用コマンド**:
```bash
docker exec elearn_app python batch/find_youtube_videos.py --subject <科目> --year <学年> --resume
```

**quota**: YouTube Data API v3 = 10,000 units/日、search = 100 units → **99 chunks/日**。  
**リセット**: 毎日 PST 0:00 = 日本時間 17:00（冬時間）。

- **Y7 は手作業で search するため以降バッチ対象外**
- [ ] **要整理**: material_id=179 と 180 が "KS2 Science - More about food chains" で重複インポート (同一タイトル・同一チャンク構成)
- [ ] Y4 English / History / Geography / Computing / Spanish
- 終わったら Y5/6/8-11 も同じ要領

---

## 🟠 P1 — 高優先

### 小テスト Phase 3（運用開始後すぐ欲しい機能）
- [ ] ダッシュボードにドリル履歴表示（今日の完了数、ストリーク等）
- [ ] ドリル専用バッジ (Drill Master、3日連続ドリル達成 等)
- [ ] 進捗可視化（chunk別ドリルクリア状況）

### SRS 残件
- [ ] `answer_history` に `next_review_at` 追加（Leitner box or SM-2 簡易版）
- [ ] 選択肢の並び順を毎回シャッフル（quiz側、drill側は実装済）

### LLM問題生成の残り展開
- [x] Y7 Science / Spanish / English, Y4 Maths / Science 完了
- [ ] Y7 Maths 残り 101 chunk (ルールベース外)
- [ ] Y7 History / Geography / Computing
- [ ] 他学年 (Y5/6, Y8-11) の Maths と Science

---

## 🟡 P2 — 中優先

### マスタリー自動進級
- [ ] chunk 内の全問題を一定回数/精度で正解したら「mastered」フラグ
- [ ] mastered chunk はダッシュボードで完了表示、次chunkへの導線
- [ ] unit全体完了で「レベルアップ」通知/バッジ
- [ ] 「このチャンクは復習期」/「新規学習期」の状態遷移
- **注**: SRS の next_review_at 機構と連動

### カリキュラム予習機能
- [ ] `user_curriculum` テーブル: 生徒 × (year_group, subject, unit)
- [ ] Oak curriculum データと連動
- [ ] 「次やるべき material」自動提示

### 教材インポート（Oak API）— 追加Year
- [ ] Year 8-11 の段階的インポート
- [ ] 進捗管理: `docs/oak_import_progress.md`

---

## 🟢 P3 — 低優先 / 将来

### PDF → 講義動画変換
- [ ] PDF → テキスト抽出（PyMuPDF）
- [ ] LLMで講義スクリプト生成
- [ ] MVP: スライド（Marp/HTML）+ TTS音声
- [ ] 将来: AI動画（Sora / Runway 等）— コスト・著作権見極めてから

### 動画アップロード（Google Drive）— 追加Year
- [ ] Year 8-11 の動画もGoogle Driveにアップロード（段階的に）

---

## Backlog

### 学習機能
- [ ] 苦手分野検知 → 追加問題の自動生成

### 問題生成・品質
- [ ] LLM生成Free Response問題の品質向上
  - 現状Oak問題は穴埋め1語のみ、本格的な自由回答問題がない
  - Generate QuestionsのFree Responseで文章回答型を生成
  - LLM採点しやすい問題設計（明確な正解基準、キーワードリスト付きreference_answer）
  - 生成プロンプトの調整が必要

### バッジ
- [ ] Speed Star / Overcomer 等の追加バッジタイプ

### 管理画面
- [ ] 問題の個別編集・削除UI

### 通知
- [ ] メール通知（学習完了時）
- [ ] 週次レポートメール

### インフラ
- [ ] バックアップ戦略（MySQL定期dump等）

### その他
- [ ] PDF教材アップロード + テキスト抽出 + 自動チャンク化
- [ ] プロフィール画像のカスタムアップロード（自分の好きな画像に設定）

---

## 完了済み

### 2026-04-22 完了

#### 宿題 (Assignment) 機能
- [x] `questions.is_assignment` フラグ追加 (ローカル + 本番)
- [x] 管理画面: chunk detail / material detail に Assignment タブ
- [x] Y7 Averages PDF から 63 問抽出 (chunks 範囲/最頻値/中央値/平均/逆平均/最適平均)
- [x] Y7 Graphs PDF から 10 問抽出 (棒グラフ読取 + 円グラフ扇形角度 + SVG図付き)
- [x] 子供画面: `/child/chunks/<c>/assignment`、`/child/materials/<m>/assignment`、`/child/subjects/<s>/assignment`
- [x] 1セッション 15 問 (未マスタリー優先、再走で別の組合せ)
- [x] 導線: subjects アコーディオンのUnit行ボタン + 教科上部バナー + chunk画面の宿題カード
- [x] Schedule 拡張: `study_deadlines.material_id`/`chunk_id` 追加、homework kind で subject→material→chunk カスケードドロップダウン、子供 schedule 画面から直接プレイ
- [x] ポイント仕様は既存 quiz と共通 (初回正解 +1pt、再正解 0pt、マスタリー連動)
- [x] Mojibake 一括修正 (`−`→`-`、`×`→`x`、`°`/`£` 復元など)
- [x] 本番反映: DB migration + 73 問インポート (prod material 279 + 281)

#### Y7 教材追加 (Week 2026-04-22 宿題対応)
- [x] material 283 "MYP1E - Acids and Alkalis in Industry (Research)" 5 chunk, drill 25問 + test 73問
- [x] material 284 "Unit 6 - Measures of Central Tendency (Averages)" 7 chunk, drill 35問 + test 105問
- [x] YouTube 動画マッピング (12 chunk × 5 本、58 件保存 / 一部 primary 要調整)
- [x] 本番反映 (prod material 280 + 281)

#### chunk 生成UI 不具合修正
- [x] 質問 0 件 chunk で Generate ボタンが表示されない問題を修正
- [x] MC/FR ドロップダウンに 0 オプション追加 (片方だけ生成可能に、両方 0 はサーバー側でガード)

#### YouTube マッピング継続
- [x] Y4 Science 本番直接実行、**90/90 chunk 完了** (403 videos saved、8件既存スキップ)

### 2026-04-21 完了

#### YouTube マッピング
- [x] Y4 Maths 残り 81 chunk 完了 (本番直接実行、397 videos saved、165/165)
- [x] Y4 Science material 180 "KS2 Science - More about food chains" 8/10 chunk (残り 2 件 chunk 1519, 1525 は quota 切れ)
- [x] Y7 Science 82/96 (2026-04-17 着手、残り 14 件 quota 切れ)

### 2026-04-20 完了

#### 学習スケジュール機能 (親 + 子)
- [x] `study_plans` / `study_deadlines` テーブル追加 (migration: `sql/09_add_schedule_tables.sql`)
- [x] モデル: `models/schedule.py`
- [x] 親画面: `/admin/children/<id>/schedule` フル月カレンダー (追加/編集/削除/ステータス切替、日 DnD なしのシンプル実装)
- [x] 親画面: `/admin/children/<id>` に今月+来月サマリ (教科別集計バー + 締切リスト + subject/material/chunk 直リンク)
- [x] 子画面: `/child/dashboard` に今月+来月プレビューカード (教科バー + 締切トップ2)
- [x] 子画面: `/child/schedule` フル月カレンダー + アイテムリスト (44px の「できた！」トグル、モバイル最適化)
- [x] 子画面: サイドバー/ボトムナビに Schedule リンク追加
- [x] material_id のみの予定は `/child/subjects/<subject>?unit=<material_id>` で対象ユニット自動展開

#### admin child_section タブ統一
- [x] Drill/YouTube/共通CSS を `components/chunk_tab_{drill,youtube,tabs_css}.html` に抽出
- [x] material_chunk_detail と child_section で再利用 (Progress / Lesson / Drill / Q&A / YouTube)

#### year_group フィルタ不備修正
- [x] `_build_child_stats` と `admin_children_detail` を子の学年で絞り込み (Y7 児童に Y4 教材が混入する問題を解消)
- [x] スケジュール追加モーダルの教材 select も学年フィルタ

#### YouTube マッピング継続
- [x] Y4 Maths 84/165 chunk 処理 (420 動画、quota 切れで残り 81)
- [x] 本番 DB に `chunk_youtube_videos` を INSERT IGNORE でインポート

### 2026-04-17 完了

#### ルールベース算数問題生成 (Y7 Math, material 276/277)
- [x] `config/math_templates.yaml` テンプレDSL (変数レンジ、answer_expr、distractor、各種答え型: integer/fraction/mixed/algebraic_over_x)
- [x] ast ベース安全式評価 (`services/math_generator.py`)
- [x] ジェネレーター: Fraction対応、distractor生成、seed再現性
- [x] 14テンプレ投入: 分数加減乗除/混合数/量の分数/代数分数(同分母/異分母x-2x/欠損値)/一次方程式 (chunks 2057-2061)
- [x] 単体テスト 12件 PASS (`tests/test_math_generator.py`)
- [x] `questions` スキーマ拡張: `template_id`, `generated_payload`, source enum に `rule_based` (migration: `sql/03_add_rule_based_questions.sql`)
- [x] 既存の Oak imports を `source='manual'` → `source='oak'` にマイグレート (125問)
- [x] `materialize_question` / `materialize_chunk_pool` — DB書き込みヘルパ
- [x] admin chunk detail に 小テスト/Questionsタブ、問題作成(AI)/(ルール) chipボタン、ソースフィルタタブ
- [x] Y7 Math chunks 2057-2061 に一括投入 (小テスト150問+最終テスト250問, `batch/bulk_generate_math.py`)

#### 小テスト (ドリル) モード — Phase 1 + Phase 2
- [x] 新テーブル3つ作成: `drill_questions`, `drill_sessions`, `drill_answer_history` (migration: `sql/04_add_drill_tables.sql`)
- [x] モデル: `models/drill.py`
- [x] config: `DRILL_STREAK_TO_MASTER=3`, `DRILL_COMPLETION_POINTS=5` (config.py、可変)
- [x] 生成サービス: `services/drill_generator.py` (rule-based / LLM)
- [x] admin: drill タブ、問題生成ダイアログ、削除機能
- [x] child drill UI (`templates/child/drill.html`, `/child/drill/<chunk_id>`)
  - 1問ずつ即時判定、ストリーク表示、不正解時は正解+解説
  - イントロ画面で「Nストリークで完了、Xpt獲得」説明
  - 完了画面: トロフィー + ポイント表示 + 「テストに挑戦」導線
- [x] セクション画面CTA再設計: ドリル未達成時は最終テストをロック、達成後は解放
- [x] ハードロック: `/child/quiz/<id>` 直URL でも drill 未達成ならdrillへリダイレクト
- [x] `point_history.reason_type` に `drill_complete` 追加 (migration: `sql/05_add_drill_point_reason.sql`)
- [x] PC/タブレット 2カラム構成 (サイドバーに streak進捗+セッション統計)

#### SRS (A+B)
- [x] 1テスト = 10問固定 (config可変: `QUIZ_QUESTIONS_PER_SESSION`)
- [x] 当日回答済み問題は自動除外
- [x] プール不足時は rule_based 自動生成で補充
- [x] 3日ローテーション: 直近3日で誤答した rule_based template_id は別インスタンスで優先出題
- [x] 「もう一度」ボタン: 全問リフレッシュ (retry=X,Y パラメータ廃止)
- [x] クイズ結果画面: 直近セッションで出題された問題のみ表示 (全問ではない)

#### LLMプロンプト改善 + 追加機能
- [x] `generate_questions` シグネチャ刷新: subject/year_group/summary/oak_examples を受ける (決め打ち "KS3 science teacher, Year 7" を廃止)
- [x] Oak問題を5件までサンプリングして参考スタイルに渡す (重複回避指示付き)
- [x] admin: LLM/ルール生成ボタンを chip 化、位置を最適化 (フィルタタブ右)
- [x] admin chunk detail: Content/小テスト/Questions の3タブ構成
- [x] Y7 Science 全96 chunk に小テスト5+最終テスト10 を LLM 一括投入 (`batch/bulk_generate_llm.py`、resume/sleep対応)

### 2026-03-20 完了
- [x] 週間/月間進捗ウィジェット（子供・親画面、教科別フィルター、バーチャート）
- [x] Today's Goal（子供画面に今日の目標表示、親画面からgoal設定）
- [x] バッジ管理UI（親画面から取り消し・手動付与・全リセット）
- [x] 動画配信改善: Google Drive → Flaskプロキシ（Range Request対応、即再生+シーク可）
- [x] YouTube動画アップロードバッチ（`batch/upload_videos_youtube.py`）※クォータ制限で保留
- [x] Year 4 動画 Google Driveアップロード完了（479件/約52.7GB、115件動画なしスキップ）
- [x] さくらVPSデプロイ完了（2GBプラン、Ubuntu 24.04、Docker）
- [x] ドメイン取得（ai-elearning.net）+ HTTPS自動化（Caddy + Let's Encrypt）
- [x] 本番DB移行（ローカル → VPS）
- [x] デプロイ手順ドキュメント（`docs/deployment.md`）

### 2026-03-19 完了
- [x] Year 4 全7教科インポート完了（100ユニット、8,366問題）
- [x] 本番用docker-compose（`docker-compose.prod.yml`）+ `.env.prod.example` + gunicorn追加
- [x] 効果音（Web Audio API: confirm/correct/wrong/fanfare/sparkle/levelUp）
- [x] Confetti紙吹雪アニメーション（クイズ完了70%以上、バッジ獲得時、結果画面）
- [x] 画像型選択肢（Oak問題）の表示対応 + 真っ白画面バグ修正
- [x] Year 7 動画Google Driveアップロード完了（292件/約30GB）

### 2026-03-18 完了
- [x] Oak動画をGoogle Driveにキャッシュして配信（OAuth2 + iframe embed方式）
  - `batch/upload_videos_gdrive.py` バッチアップロード、Year 7 全507件処理中
- [x] セクション画面のラベル文言を翻訳辞書に移行（section.html → `{{ t.child.section_xxx }}`）
- [x] レベル自動更新（100ptごとにレベルアップ、クイズ採点時に自動計算）
- [x] ストリーク（連続学習日数）自動計算（last_study_dateベース）
- [x] 学習セッションのDB記録（クイズ採点時にLearningSession自動作成）
- [x] 回答履歴のDB記録（クイズ採点時にAnswerHistory自動記録）
- [x] admin child_header: Level/Streak編集モーダル追加、Level進捗バー表示
- [x] admin child_header: ポイント編集時にレベル自動連動
- [x] 親同士の共同管理（caretaker招待フロー）— child_invitesテーブル、招待コード生成+受理
- [x] admin dashboard: Quick ActionsのLearning Progress → Badge Managementに変更
- [x] admin dashboard: Accept Inviteセクション追加
- [x] バッジ獲得条件の自動判定（クイズ採点時に自動チェック・付与）
- [x] バッジ獲得時のアニメーション（共通コンポーネント化: components/badge_animation.html）
- [x] admin バッジ管理画面（/admin/badges — 追加・削除・一覧・プレビュー）
- [x] 子供ダッシュボードのバッジ表示を動的化（獲得済み/未獲得）
- [x] admin child_detail にバッジセクション追加（プレビュー付き）
- [x] バッジマスターデータ: ×2段階（streak 2-1024日, answers 10-5120問, points 100-51200pt）

### 2026-03-17 完了
- [x] Oak動画プロキシ動作確認（ストリーミング配信OK、Cloudflare 403対策）
- [x] 動画プロキシのchild制限解除、admin画面にも動画プレーヤー追加
- [x] セクション画面にSummary/Full Transcriptタブ切り替え追加
- [x] match問題再インポート（Science Year 7: 359問 free_response→multiple_choice）
- [x] `import_oak_api.py` に `--reimport-quiz` オプション追加
- [x] インポートスクリプトのデフォルトstatusを `published` に修正
- [x] Year 7 全7教科インポート完了（71ユニット、6,355問題）
- [x] 採点時にLLMで解説を一括生成（GPT-5 mini、DB保存キャッシュ付き）
- [x] 不正解時の正解表示改善（ラベル+選択肢テキスト表示）
- [x] 結果画面に正解・解説の展開表示
- [x] Skip済み問題にも正解・選択肢・解説を表示
- [x] クイズPC表示の最適化（カード高さ制限、選択肢スクロール）
- [x] mastery制の動作確認（初回正解=1pt、再回答=0pt）
- [x] KaTeX導入（Maths等のLaTeX数式表示対応）
- [x] `{{ }}`穴埋めプレースホルダーの`______`変換（Jinja2衝突対策含む）
- [x] ユニット教育的順序対応（sequences APIのunitOrderをDB保存、全画面sort_order反映）
- [x] 子供画面パンくずナビ追加（section, quiz, quiz_result, units）
- [x] 子供画面サイドバー改善（教科リスト統合、ユニットツリー、他ユニット導線）
- [x] units画面のアコーディオン自動展開（?unit=パラメータ対応）
- [x] ダッシュボードの教科ソート改善（進行中→未着手→完了、最終学習日時順）
- [x] admin画面パンくずナビ追加（child_detail, child_section, material_detail）
- [x] admin画面サイドバー改善（children/materialsコンテキストサブナビ）
- [x] admin child_section に3タブ追加（Progress / Lesson / Q&A）
- [x] ポイント編集モーダル化（child_headerのPointsカードからワンクリック）
- [x] admin material_detail 簡略化（チャンクはリンクのみ、タブ廃止）
- [x] NEW: admin material_chunk_detail 画面（Contents/Questionsタブ、チャンク単位Generate）
- [x] adminサイドメニュー整理（不要項目削除、Badges残存）
- [x] docker-compose.yml に OAK_API_KEY, LLM_MODEL_EXPLAIN 追加

### それ以前の完了
- [x] 管理画面: マテリアル登録UI（テキスト入力 or URL入力）
- [x] マテリアル一覧・編集・削除UI（Year > Subject > Unit 階層ナビ）
- [x] LLM連携: マテリアルからの問題自動生成（Gemini 3.1 Flash Lite）
- [x] 生成された問題の確認UI（管理画面、セクション別グループ表示）
- [x] 問題を教科(subject)・難易度(difficulty)で分類
- [x] Oak National Academy 公式APIへの切り替え
- [x] Science Year 7 インポート完了（13ユニット, 96レッスン, 1,345問題）
- [x] 管理者ロール（parents.role = admin）
- [x] DB設計: materials, material_chunks, questions拡張, question_mastery
- [x] 子供用学習画面 2カラムUI刷新（child_base.html共通テンプレート）
- [x] 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果 の全画面
- [x] クイズ: 確定→答え合わせ方式に再設計（JS状態管理 + 一括採点API）
- [x] 自由回答のLLM採点（GPT-5 Nano + spaCyフォールバック）
- [x] 4択選択肢のランダム並び替え（Fisher-Yates + originalLabel保持）
- [x] 管理画面からのpublish/unpublish機能（デフォルトpublished）
- [x] ポイント配分: mastery制（初回正解=1pt、再回答=0pt）
- [x] 正解済み問題のスキップ機能（Masteredバッジ + Skipボタン）
- [x] クイズ離脱時の確認ダイアログ（beforeunload + Back確認）
- [x] セクション要約: TranscriptのLLM要約を初回アクセス時に生成・キャッシュ
- [x] ヒント機能: 固定ヒント + AIチャットヒント（Gemini）
- [x] ポイント計算エンジン（マスタリー制ベース: 1問正解=1pt）
- [x] 学習状況ダッシュボード（Subject > Material > Chunk 階層進捗ツリー）
- [x] ポイント手動調整（管理画面 /admin/children/<id> から）
- [x] 学習進捗リセット（セクション単位・問題単位で選択式、ポイント連動オプション付き）
- [x] 親子デュアルセッション（同一ブラウザで親・子供同時ログイン可能）
- [x] 管理画面のアクセス制御（parent_required / admin_required デコレータ）
- [x] 子供プロフィール画面（アバター選択、教科別進捗、ログアウト）
- [x] 子供画面UI共通化（sidebar_profile, sidebar_nav, header の共通コンポーネント）
- [x] アバター選択機能（絵文字8パターン、AJAX即時反映）
- [x] 子供画面のスマホ最適化（overflow修正、レスポンシブ対応）
- [x] 子供画面の進捗バー表示（units, section, quiz 各画面で進捗可視化）
- [x] 採点時LLM解説生成（GPT-5 mini、DB保存キャッシュ付き）
