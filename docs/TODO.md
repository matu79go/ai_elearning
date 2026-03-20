# TODO

## Next: 次にやること

### 1. 教材インポート（Oak API）— 追加Year
- [ ] Year 8-11 の段階的インポート
- [ ] 進捗管理: `docs/oak_import_progress.md`

### 2. 動画アップロード（Google Drive）— 追加Year
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
