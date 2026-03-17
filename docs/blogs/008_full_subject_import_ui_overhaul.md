# 008: Year 7全教科インポート & UI大幅改善

**日付:** 2026-03-17

## 概要

Year 7の全7教科をOak APIからインポート完了し、子供画面・管理画面双方のUI/UXを大幅改善。動画配信、LLM解説生成、数式表示など多くの機能を追加した。

## 実施内容

### 1. Year 7 全教科インポート

Oak公式APIから7教科・71ユニット・6,355問題をインポート。

| 教科 | ユニット | 問題数 |
|------|---------|--------|
| Science | 13 | 1,345 |
| Maths | 10 | 1,522 |
| English | 7 | 838 |
| History | 14 | 945 |
| Geography | 7 | 474 |
| Computing | 6 | 228 |
| Spanish | 14 | 1,003 |

- match問題 → multiple_choice変換（`--reimport-quiz`オプション追加）
- デフォルトstatus を `published` に修正
- 一部レッスンは著作権制限（400エラー）でスキップ

### 2. ユニット教育的順序

Oak APIの`/sequences/{seq}/units`エンドポイントから`unitOrder`を取得し、materialsテーブルに`sort_order`カラムを追加。全画面で教育的に正しい順序で表示。

### 3. 動画配信

- Oak APIの動画プロキシ実装（8KBチャンクストリーミング）
- Cloudflare 403対策: `User-Agent`ヘッダー追加
- docker-compose.ymlに`OAK_API_KEY`追加
- child/admin両画面で動画視聴可能

### 4. LLM解説生成

採点（Check Answers）時にGPT-5 miniで全問の解説を一括生成:
- 1回のAPI呼び出しで全問をバッチ処理（コスト効率）
- 生成した解説は`question.explanation`にDB保存
- 2回目以降はキャッシュ参照（LLM呼び出しなし）
- 結果画面でも各問題をタップで正解・解説を展開表示
- Skip済み問題にも正解・解説を表示

### 5. KaTeX数式表示

Maths問題に含まれるLaTeX記法（`$$\frac{2}{3}$$`等）をKaTeXでレンダリング:
- base.htmlにKaTeX CDN追加（全画面対応）
- クイズ画面ではJS動的挿入後に`renderMathInElement()`で再レンダリング
- `{{ }}`穴埋めプレースホルダーは`______`に変換
- Jinja2テンプレート構文との衝突対策（RegExpの構築方法変更）

### 6. ナビゲーション改善

**パンくず追加:**
- 子供画面: section, quiz, quiz_result, units
- 管理画面: child_detail, child_section, material_detail, material_chunk_detail

**サイドバー改善:**
- 子供画面: sidebar_nav.htmlに教科サブメニュー統合、セクション画面にユニットツリー
- 管理画面: children/materialsにコンテキストサブナビ

**アコーディオン自動展開:**
- `?unit=`パラメータで該当ユニットを自動展開・スクロール
- `?subject=`パラメータで教科ツリーを自動展開

### 7. 管理画面リファクタリング

- material_detail: チャンクはリンクのみに簡略化（アコーディオン廃止）
- NEW: material_chunk_detail画面（Contents/Questionsタブ、チャンク単位Generate）
- child_section: 3タブ構成（Progress / Lesson / Q&A）
- ポイント編集: 下部フォーム → ヘッダーカードクリックでモーダル
- サイドメニュー: 不要項目削除（Dashboard / Children / Materials / Badges のみ）

### 8. ダッシュボード改善

教科ソート順を変更: 進行中（最終学習日時降順）→ 未着手 → 完了

### 9. セクション画面

- Summary/Full Transcriptタブ切り替え
- Summaryテキストの改行表示修正（`white-space: pre-line`）

### 10. クイズ画面

- PC表示最適化（カード高さ制限、選択肢スクロール、ボタン常時表示）
- 不正解時の正解表示に選択肢テキストを追加

## 技術的なポイント

- **Cloudflare対策**: コンテナ内のPython urllibはデフォルトUser-Agent (`Python-urllib/3.11`)がCloudflareにブロックされる。カスタムUser-Agentで解決。
- **Jinja2とLaTeXの衝突**: `{{ }}`がJinja2テンプレート構文と衝突。JSコメント内でも検出される。`new RegExp()`で動的にパターン構築して回避。
- **SQLAlchemyのサイレント無視**: モデルに定義されていないカラムへの代入はエラーにならず無視される。DB変更時はモデル定義を先に更新すべき。

## 次のステップ

1. Science以外の教科のmatch問題再インポート
2. セクション画面の翻訳辞書移行
3. Year 8-11のインポート（sort_order自動取得含む）
