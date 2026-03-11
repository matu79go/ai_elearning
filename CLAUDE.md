## プロジェクト概要

**プロジェクト名:** AI e-Learning システム
**目的:** マテリアル（テキスト/URL）からLLMで問題を自動生成する子供向けe-learningサイト

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python 3.11 |
| Web FW | Flask 3.x |
| DB | MySQL 8.0 (Docker) |
| CSS | Tailwind CSS + オープンソースUI |
| コンテナ | Docker / Docker Compose |
| 本番 | さくらVPS |

---

## ⚠️ 基本ルール

1. **勝手にpushしない** — commit/pushは必ずユーザーの指示を待つ
2. **データベース操作はmysqlコマンドで直接実行する**（下記参照）
3. **設計ドキュメントは `docs/` 以下を参照**
4. **CLAUDE.mdは簡潔に保つ** — 詳細はdocs/以下に記載
5. **画面の文言はすべて辞書ファイル（`translations/en.json`, `translations/ja.json`）で管理する** — テンプレートにテキストをベタ打ちしない。`{{ t.xxx }}` で参照すること
6. **日英両対応必須** — 新しい画面・文言追加時は必ず `en.json` と `ja.json` の両方に追加する
7. **マルチデバイス最適化必須** — 全画面でスマホ・タブレット・PC表示を考慮する。`base.html` の共通レスポンシブクラス（`page-container`, `responsive-grid-2`, `h-scroll`, `text-responsive-*`, `px-responsive`, `bottom-nav-shared`）を活用し、各ページ固有のCSSでは重複定義しないこと。ブレークポイント: `sm:640px` / `md:768px` / `lg:1024px`
8. **作業ログを `docs/blogs/` に記録する** — 技術ブログとして公開するため、作業の経緯をドキュメント化
9. **DB設計ルールは `docs/database.md` を参照** — マスターテーブルのバイリンガル規約（`_en`/`_ja` カラム必須）等、DB関連のルールはすべて `docs/database.md` に記載

---

## ⚠️ データベース操作

```bash
# 基本形
docker exec elearn_mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} elearning -e "SQL文" 2>&1 | grep -v Warning

# パスワード: .envファイル参照
# データベース名: elearning
# 文字コード: utf8mb4 設定済み
```

---

## ディレクトリ構成

```
ai_elearning/
├── CLAUDE.md          # 基本ルール（このファイル）
├── docs/              # 設計ドキュメント
├── app.py             # Flaskアプリ初期化 + i18n（薄く保つ）
├── config.py          # DB接続等の設定
├── requirements.txt   # Pythonパッケージ
├── models/            # SQLAlchemyモデル（機能単位で分割）
├── routes/            # Blueprintルート（機能単位で分割）
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml  # ローカル開発用(phpMyAdmin)
├── entrypoint.sh
├── mysql-config/      # MySQL設定
├── sql/               # SQLスクリプト
├── batch/             # バッチ処理
├── translations/      # i18n辞書ファイル（en.json, ja.json）
├── templates/         # Jinja2テンプレート
│   ├── child/         # 子供用画面
│   ├── admin/         # 管理画面（親用）
│   └── components/    # 共通コンポーネント
├── static/            # 静的ファイル
│   ├── css/
│   ├── js/
│   ├── sounds/        # 効果音
│   └── images/
├── tests/             # テスト
└── docs/blogs/        # 開発ブログ（作業ログ）
```

---

## 本番環境（さくらVPS）

※ 詳細は `docs/deployment.md` に記載予定

```bash
# デプロイ（git経由）
ssh -i ~/.ssh/sakura_key ubuntu@<VPS_IP> "cd ~/ai_elearning && git pull && sudo docker-compose restart app"
```

---

## 参照ドキュメント

- `docs/requirements.md` — 要件定義
- `docs/design.md` — システム設計
- `docs/database.md` — DB設計
- `docs/deployment.md` — デプロイ手順（予定）
