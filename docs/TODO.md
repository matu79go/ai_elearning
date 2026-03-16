# TODO

## Next: Oak API 切り替え

- [ ] Oak National Academy 公式APIへの切り替え（APIキー取得済み）
  - 現在のスクレイピング方式 → 公式API (Bearer認証) に移行
  - エンドポイント調査・実装
  - 既存データとの整合性確認

## Backlog

### 学習機能
- [ ] 学習セッションのDB記録（開始・完了・スコア）— モデル定義済み、記録ロジック未実装
- [ ] 回答履歴のDB記録 — モデル定義済み、記録ロジック未実装
- [ ] レベル自動更新（ポイントに応じてlevelを自動計算）
- [ ] ストリーク（連続学習日数）自動計算
- [ ] 苦手分野検知 → 追加問題の自動生成

### バッジ
- [ ] バッジ獲得条件の自動判定
- [ ] バッジ獲得時のアニメーション・通知

### 管理画面
- [ ] 問題の個別編集・削除UI
- [ ] バッジ管理（追加・条件編集）

### 通知
- [ ] メール通知（学習完了時）
- [ ] 週次レポートメール

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



## 完了済み

- [x] 管理画面: マテリアル登録UI（テキスト入力 or URL入力）
- [x] マテリアル一覧・編集・削除UI（Year > Subject > Unit 階層ナビ）
- [x] LLM連携: マテリアルからの問題自動生成（Gemini 3.1 Flash Lite）
- [x] 生成された問題の確認UI（管理画面、セクション別グループ表示）
- [x] 問題を教科(subject)・難易度(difficulty)で分類
- [x] Oak National Academy からのデータ取り込み（Science, Maths, English, History, Geography, Computing, Spanish）
- [x] 管理者ロール（parents.role = admin）
- [x] DB設計: materials, material_chunks, questions拡張, question_mastery
- [x] 子供用学習画面 2カラムUI刷新（child_base.html共通テンプレート）
- [x] 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果 の全画面
- [x] クイズ: 確定→答え合わせ方式に再設計（JS状態管理 + 一括採点API）
- [x] 自由回答のLLM採点（GPT-5 Nano + spaCyフォールバック）
- [x] 4択選択肢のランダム並び替え（Fisher-Yates + originalLabel保持）
- [x] 管理画面からのpublish/unpublish機能（デフォルトpublished）
- [x] 全教科のマテリアルをpublishして子供画面に反映
- [x] ポイント配分: mastery制（初回正解=1pt、再回答=0pt）確認済み
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