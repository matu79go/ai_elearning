# Blog #006: クイズ調整・進捗管理・親子デュアルセッション・UI共通化

**Date:** 2026-03-16

## Overview

クイズの細かい調整（選択肢ランダム化、スキップ機能、離脱確認）、親向け管理画面の進捗管理システム、親子同時ログイン対応、子供画面のUI共通化を一気に実装した。

---

## 1. クイズ調整

### 4択選択肢のランダム並び替え

問題のoptionsがDB上はA/B/C/D固定順だったため、毎回同じ並び順で表示されていた。

**実装:** クライアント側（quiz.html JS）でFisher-Yatesシャッフルを適用。`originalLabel`を保持してサーバー送信時はDB上のラベルで採点する。

```javascript
// Fisher-Yates shuffle + originalLabel保持
q.options = shuffled.map((opt, idx) => ({
    ...opt,
    originalLabel: opt.label,  // 元のA/B/C/Dを保持
    label: LABELS[idx],        // 表示用に振り直し
}));
```

採点結果表示時も`originalLabel`でマッチングするため、正解ハイライトが正しく動作する。

### 正解済み問題のスキップ機能

`mastery_map`（サーバーからの習得状態）をJS側に渡し、mastered問題にはバッジ表示 + Skipボタンを追加。

- **Skipボタン:** `answers[idx] = { answer: '__skipped__', locked: true, skipped: true }`
- **Check Answers:** skipped問題はサーバーに送信せず、クライアント側で「Already mastered」として結果に追加
- **スコアバナー:** skipped問題を除外して正解率を計算、skipped数も別途表示

### クイズ離脱確認

`beforeunload` + Backボタンの`onclick`で、回答途中なら確認ダイアログを表示。採点済み（checkResults != null）の場合は警告しない。

---

## 2. Publish/Unpublish機能

### デフォルトpublished方式

当初はdraft→ready→publishedの3段階ワークフローを想定していたが、運用上「登録したらすぐ公開」がシンプルなので、Materialモデルのデフォルトを`published`に変更。

- `models/material.py`: `default='published'`
- DB: `ALTER TABLE materials ALTER COLUMN status SET DEFAULT 'published'`
- 既存88件を一括UPDATE

管理画面にはUnpublishボタンも用意し、個別に非公開にもできる。

---

## 3. 親子デュアルセッション

### 問題

Flask-Loginは`session['_user_id']`を1つしか保持できない。同一ブラウザで子供ログイン→親の管理画面にアクセスするとクラッシュしていた。

### 解決策

`session['_parent_uid']`と`session['_child_uid']`を別々に保持し、`before_request`でURLパスに応じて`_user_id`を切り替える。

```python
@app.before_request
def _dual_session_swap():
    clean = request.path.lstrip('/ja').lstrip('/')
    if clean.startswith('admin') or clean.startswith('parent'):
        uid = session.get('_parent_uid')
    elif clean.startswith('child'):
        uid = session.get('_child_uid')
    # ...
    if uid:
        session['_user_id'] = uid
```

**ポイント:** この`before_request`をFlask-Login初期化の**前**に登録する。Flask-Loginの`_load_user`より先に実行されるため、正しいユーザーがロードされる。

ログアウトは自分の側のキーだけクリアし、もう片方のセッションは維持。

---

## 4. 進捗管理システム（管理画面）

### 階層的進捗ツリー

`/admin/children/<id>` に Subject > Material > Chunk の3階層進捗ツリーを実装。

SQLAlchemyで全問題 + マスタリー状態を一括取得し、Python側でOrderedDictの階層構造に組み立てる。各階層でmastered/total/パーセントを集計。

### セクション別問題管理

チャンク行クリックで `/admin/children/<id>/section/<chunk_id>` に遷移。問題ごとにチェックボックスで選択してマスタリーをリセットできる。

**設計判断:** 当初はリセット時にポイントも自動減算していたが、「子供のポイントを勝手に減らしたくない」要件から、「Also deduct points」オプションチェックボックス（デフォルトOFF）に変更。

### ダッシュボード

`/admin/dashboard` に実データを表示。子供カード内に教科別進捗バーを表示し、全体の習得率もmastered/全問題数ベースで正確に計算。

---

## 5. 子供画面UI共通化

### 共通コンポーネント化

以下を`templates/child/components/`に切り出し、6ページ（dashboard, subjects, units, section, quiz, profile）で`{% include %}`：

| コンポーネント | 内容 |
|---|---|
| `sidebar_profile.html` | アバター + 名前 + Streak + Levelゲージ |
| `sidebar_nav.html` | Menu（Home / Subjects / Badges / Profile / Logout） |

`child_base.html`のデフォルトブロックでヘッダー（アバター + 名前 + ポイント）を共通定義し、全ページで自動表示。

### アバター選択

絵文字8パターン（👦👧🧑👩🐱🐶🦊🐼）をプロフィール画面で選択可能。AJAXで即時反映（POST → DB更新 → UI更新、リロード不要）。

### スマホ最適化

- `html, body`に`overflow-x: hidden; max-width: 100vw`
- モバイルStatsパネル削除（重複排除）
- ヘッダー: アバター + 名前 + ポイントのコンパクト表示

---

## 6. 技術的なポイント

### 共通ヘルパー関数

`_build_child_stats(child_id)` — 教科別のtotal/mastered/pctを一括算出。dashboard, children一覧の両方から呼び出し。

### 管理画面の共通コンポーネント

| コンポーネント | 内容 |
|---|---|
| `admin/components/child_header.html` | アバター + 名前 + Flash + Stats Cards |
| `admin/components/child_header_css.html` | 共通CSS |
| `admin/components/child_card.html` | 子供カード（教科別進捗バー付き） |
| `admin/components/child_card_css.html` | カードCSS |

child_detail, child_section, children一覧, dashboardで使い回し。

---

## Files Changed

### Routes
- `routes/admin_materials.py` — publish/unpublishルート追加
- `routes/admin_children.py` — child detail, section, points, reset ルート追加、_build_child_stats
- `routes/admin_dashboard.py` — 実データ表示、parent_required
- `routes/child_learn.py` — publishedフィルタ追加、チャンク別進捗データ
- `routes/child_dashboard.py` — プロフィール画面、アバター変更API
- `routes/auth.py` — デュアルセッション対応
- `app.py` — _dual_session_swap, unauthorized_handler

### Templates (新規)
- `templates/admin/child_detail.html` — 子供詳細（進捗ツリー + ポイント編集）
- `templates/admin/child_section.html` — セクション別問題管理
- `templates/child/profile.html` — プロフィール画面
- `templates/child/components/sidebar_profile.html` — 共通サイドバー
- `templates/child/components/sidebar_nav.html` — 共通ナビ
- `templates/admin/components/child_header.html` — 共通ヘッダー
- `templates/admin/components/child_card.html` — 共通子供カード

### Models
- `models/material.py` — LearningSession, AnswerHistory, PointHistory追加、デフォルトpublished

### Translations
- `translations/en.json` / `ja.json` — 30+キー追加
