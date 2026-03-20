# 009: セッション記録・バッジシステム・管理画面強化

**日付:** 2026-03-19 〜 2026-03-20

## 概要

学習セッション/回答履歴のDB記録、バッジ自動付与システム、管理画面の大幅強化（子供ヘッダー改善、ポイント/レベル/ストリーク編集、招待コード）を実装。さらに週間/月間進捗ウィジェットと教科別フィルター機能を追加した。

## 実施内容

### 1. 学習セッション・回答履歴の記録

クイズ完了時に `learning_sessions` と `answer_history` にデータを記録するようにした。

- `LearningSession`: child_id, material_id, started_at, completed_at, total_questions, correct_answers, total_points_earned
- `AnswerHistory`: session_id, question_id, child_id, user_answer, is_correct, points_earned, answered_at
- レベル自動更新（100ptごとにレベルアップ）
- ストリーク自動計算（連続学習日数）

### 2. バッジシステム

#### 自動付与
クイズ完了時にバッジ条件を自動チェック:
- `first_correct` — 初めて1問正解
- `streak` — 連続学習日数が条件値以上
- `total_answers` — 累計回答数が条件値以上
- `total_points` — 累計ポイントが条件値以上

#### 管理画面からのバッジ管理
子供詳細画面にバッジ操作UIを追加:
- **取り消し** — 獲得済みバッジの個別取り消し（child_badges削除）
- **手動付与** — 未獲得バッジの手動付与
- **全リセット** — この子供の全バッジ一括取り消し
- 取り消し後も条件を満たせば次回学習時に自動再付与される設計

### 3. 管理画面の強化

#### 子供ヘッダー
- ポイント・レベル・ストリーク・習得率のカード表示
- 各値のインライン編集（ポイント調整、レベル調整、ストリーク調整）

#### 子供詳細画面
- 教科 > ユニット > セクション > 問題のツリービュー（進捗バー付き）
- セクション単位の問題マスタリーリセット機能
- 保護者招待コード生成（48時間有効、6文字英数字）

### 4. 週間/月間進捗ウィジェット

#### 子供ダッシュボード
- **Today's Goal** — 今日の回答数 / 目標数、プログレスバー付き
- **週間バーチャート** — 曜日+日付、バーの高さ=回答数、下に獲得ポイント（`4pt`）
- **教科フィルター** — ピル型ボタンでAll / 各教科を切替（JSでリアルタイム更新）
- **前週/次週ナビ** — 過去の週も閲覧可能

#### 親管理画面
- **週間バーチャート** — 同上 + Daily Goal設定フォーム
- **月間テーブル** — 日別の回答数・正解数・獲得ポイント一覧
- **教科フィルター** — 週間・月間の両方を同時にフィルター
- **前月/翌月ナビ** — 月単位で過去履歴を閲覧

#### データソース
- `answer_history.answered_at` をJOINで `materials.subject` と紐づけ
- 新テーブル不要、既存データの集計のみ
- `children.daily_goal` カラム追加（デフォルト10問/日）

### 5. Google Drive動画配信

- セクション画面にGoogle Drive埋め込みプレーヤー追加
- `material_chunks.video_drive_id` にドライブファイルIDを格納
- Oak APIプロキシ方式からの移行（帯域削減）

### 6. その他の改善

- 管理ダッシュボードに招待コード受理フォーム追加
- 家族コード表示の改善
- クイズ結果画面にバッジ獲得アニメーション
- 子供プロフィール画面にアバター選択機能

## 技術メモ

### 進捗データのクエリ設計
```python
# 教科別・日別の集計（1クエリで取得）
db.session.query(
    func.date(AnswerHistory.answered_at),
    Material.subject,
    func.count(AnswerHistory.answer_id),
    func.sum(case((AnswerHistory.is_correct == True, 1), else_=0)),
).join(Question).join(Material).filter(...)
.group_by(func.date(AnswerHistory.answered_at), Material.subject)
```

### フィルターのJS設計
- 各バーに `data-by-subject='{"Science": {"total": 5, "correct": 3}, ...}'` をJSON埋め込み
- ピルクリック時にJSで全バーの高さ・値・ポイントを再計算
- ページリロード不要でサクサク切替

### バッジ再付与の設計判断
バッジ取り消し後の再付与について検討した結果、**条件を満たせば再付与される**仕様が正しいと判断。
- 例: First Stepを取り消し → 次にクイズで1問正解 → 再獲得
- 例: 5 Day Streakを取り消し → streak_countが5以上なら次回クイズで即再獲得
- 裏データ（streak_count, total_points）はバッジ取り消しで変更しない

## ファイル変更一覧

| ファイル | 変更内容 |
|---------|---------|
| `models/child.py` | `daily_goal` カラム追加 |
| `models/parent.py` | `ChildInvite` モデル追加 |
| `routes/admin_children.py` | バッジ管理、進捗ウィジェット、Daily Goal、招待コード |
| `routes/child_dashboard.py` | 週間/月間進捗ヘルパー、教科別集計 |
| `routes/child_learn.py` | セッション記録、バッジ自動付与、ストリーク計算 |
| `templates/admin/child_detail.html` | 週間/月間ウィジェット、バッジ管理UI |
| `templates/child/dashboard.html` | Today's Goal、バーチャート、フィルター |
| `translations/en.json` / `ja.json` | 進捗・バッジ関連の翻訳キー追加 |
