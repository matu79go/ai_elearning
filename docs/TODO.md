# TODO

## Next: 次にやること

### 1. match問題の再インポート（Science以外の教科）
- [ ] Year 7 Maths, English, History 等のmatch問題をMC変換
- [ ] `--reimport-quiz` で一括実行

### 2. セクション画面のラベル文言を翻訳辞書に移行
- [ ] section.html のハードコード文言（"What you'll learn", "Key Words", "Watch out!" 等）を `{{ t.xxx }}` に置換
- [ ] en.json / ja.json に追加

### 3. Year 8-11 の段階的インポート
- [ ] 1000 req/hour 制限のため分割実行
- [ ] 進捗管理: `docs/oak_import_progress.md`
- [ ] インポート時にsequences APIからsort_orderも自動取得する仕組み

---

## Backlog

### 学習機能
- [ ] 学習セッションのDB記録（開始・完了・スコア）— モデル定義済み、記録ロジック未実装
- [ ] 回答履歴のDB記録 — モデル定義済み、記録ロジック未実装
- [ ] レベル自動更新（ポイントに応じてlevelを自動計算）
- [ ] ストリーク（連続学習日数）自動計算
- [ ] 苦手分野検知 → 追加問題の自動生成

### 問題生成・品質
- [ ] LLM生成Free Response問題の品質向上
  - 現状Oak問題は穴埋め1語のみ、本格的な自由回答問題がない
  - Generate QuestionsのFree Responseで文章回答型を生成
  - LLM採点しやすい問題設計（明確な正解基準、キーワードリスト付きreference_answer）
  - 生成プロンプトの調整が必要

### バッジ
- [ ] バッジ獲得条件の自動判定
- [ ] バッジ獲得時のアニメーション・通知

### 管理画面
- [ ] 問題の個別編集・削除UI

### 通知
- [ ] メール通知（学習完了時）
- [ ] 週次レポートメール

### 動画配信
- [ ] Oak動画をGoogle Driveにキャッシュして配信（OGL v3.0で許可済み）
  - 現状: Oak APIからリアルタイムプロキシ（77MB/レッスン、シーク未対応）
  - 案: バッチでDL → Google Driveアップ → DBにファイルID保存 → 直リンク配信
  - 全教科だと数百GBになるため段階的に

### インフラ・デプロイ
- [ ] さくらVPSへのデプロイ設定
- [ ] 本番用docker-compose（phpMyAdmin除外）
- [ ] HTTPS / ドメイン設定
- [ ] バックアップ戦略

### その他
- [ ] PDF教材アップロード + テキスト抽出 + 自動チャンク化
- [ ] プロフィール画像のカスタムアップロード（自分の好きな画像に設定）
- [ ] 効果音・アニメーション強化
- [ ] 親同士の共同管理（caretaker招待フロー）

---

## 完了済み

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
