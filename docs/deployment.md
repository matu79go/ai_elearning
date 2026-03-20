# デプロイ手順

## 本番環境

| 項目 | 値 |
|------|-----|
| サーバー | さくらVPS 2GBプラン |
| IP | 153.126.192.71 |
| ドメイン | ai-elearning.net |
| OS | Ubuntu 24.04 |
| SSH鍵 | `~/.ssh/github_matu79go` |
| SSHユーザー | ubuntu |
| アプリパス | `/home/ubuntu/ai_elearning` |
| ブランチ | `feature/child-ui-prototype` |
| HTTPS | Caddy + Let's Encrypt（自動更新） |

## コンテナ構成

| コンテナ | 役割 | ポート |
|---------|------|--------|
| elearn_app | Flask + gunicorn (2 workers) | 127.0.0.1:5000 |
| elearn_mysql | MySQL 8.0 | 127.0.0.1:3306 |
| Caddy (ホスト) | リバースプロキシ + HTTPS | 80, 443 |

## デプロイコマンド

```bash
# 通常デプロイ（コード変更のみ）
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "cd ~/ai_elearning && git pull origin feature/child-ui-prototype && sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build"

# アプリのみ再起動（コード変更なし）
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "sudo docker restart elearn_app"
```

## DB操作（本番）

```bash
# SQLクエリ
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "sudo docker exec elearn_mysql mysql -uroot -pEL3arn_Pr0d_2026! elearning -e 'SQL文'"

# ローカルDBダンプ → 本番インポート
docker exec elearn_mysql mysqldump -uroot -p${MYSQL_ROOT_PASSWORD} elearning 2>/dev/null | gzip > /tmp/elearning_dump.sql.gz
scp -i ~/.ssh/github_matu79go /tmp/elearning_dump.sql.gz ubuntu@153.126.192.71:/tmp/
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "gunzip -c /tmp/elearning_dump.sql.gz | sudo docker exec -i elearn_mysql mysql -uroot -pEL3arn_Pr0d_2026! elearning"
```

## ログ確認

```bash
# アプリログ
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 "sudo docker logs elearn_app --tail 50"

# Caddy ログ
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 "sudo journalctl -u caddy --no-pager -n 30"
```

## 設定ファイル（本番）

- `.env.prod` — 環境変数（DB パスワード、APIキー等）
- `docker-compose.prod.yml` — 本番用Docker構成
- `/etc/caddy/Caddyfile` — リバースプロキシ設定
- `credentials/gdrive_token.json` — Google Drive OAuth トークン

## 初期セットアップ（完了済み）

1. VPS契約（さくらVPS 2GB、Ubuntu 24.04）
2. SSH鍵設定（GitHub公開鍵でインストール）
3. sudo パスワードなし設定
4. Docker + Docker Compose + git インストール
5. パケットフィルター開放（22, 80, 443）
6. git clone + ブランチ切替
7. `.env.prod` 作成、credentials 配置
8. Docker build & up
9. ローカルDB → 本番にインポート
10. ドメイン取得（ai-elearning.net）+ DNS Aレコード設定
11. Caddy インストール + HTTPS 自動化
