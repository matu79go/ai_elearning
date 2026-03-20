#!/usr/bin/env python3
"""
Oak動画をGoogle Driveにアップロードするバッチスクリプト

Usage:
    # 初回認証（ブラウザが開く → Googleアカウントで許可）
    python batch/upload_videos_gdrive.py --auth

    # ドライラン（アップロードせず対象を確認）
    docker exec elearn_app python batch/upload_videos_gdrive.py --dry-run

    # Year 7 Science のみ
    docker exec elearn_app python batch/upload_videos_gdrive.py --year 7 --subject science

    # 全対象（video_status='none' のチャンクすべて）
    docker exec elearn_app python batch/upload_videos_gdrive.py

    # 失敗したものを再試行
    docker exec elearn_app python batch/upload_videos_gdrive.py --retry-errors

前提:
    - credentials/google_drive_oauth.json に OAuth クライアントIDを配置
    - 初回は --auth でブラウザ認証 → credentials/gdrive_token.json が生成される
    - .env に GOOGLE_DRIVE_FOLDER_ID を設定
"""

import os
import sys
import json
import time
import argparse
import tempfile
import urllib.request

# Flask app context
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CREDENTIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'credentials')
OAUTH_PATH = os.path.join(CREDENTIALS_DIR, 'google_drive_oauth.json')
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, 'gdrive_token.json')

OAK_API_BASE = 'https://open-api.thenational.academy/api/v0'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Oak API rate limit: 1000 req/hour → 3.6s interval, use 4s to be safe
REQUEST_INTERVAL = 4


def do_auth():
    """OAuth2 認証フロー（初回のみ、ホストマシンで実行）"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    print(f"認証成功！トークン保存先: {TOKEN_PATH}")
    return creds


def get_drive_service():
    """Google Drive API サービスを初期化（OAuth2トークン使用）"""
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_PATH):
        print(f"ERROR: トークンファイルが見つかりません: {TOKEN_PATH}")
        print("ホストマシンで先に認証を実行してください:")
        print("  python batch/upload_videos_gdrive.py --auth")
        sys.exit(1)

    creds = OAuthCredentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # トークンが期限切れなら自動更新
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def get_lesson_slug(title):
    """チャンクタイトルから Oak lesson slug を生成"""
    slug = title.lower()
    for ch in "',.():":
        slug = slug.replace(ch, "")
    return '-'.join(slug.split())


def check_video_available(lesson_slug, api_key):
    """Oak API で動画アセットが存在するか確認"""
    url = f'{OAK_API_BASE}/lessons/{lesson_slug}/assets'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'OakAPIClient/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return any(a.get('type') == 'video' for a in data.get('assets', []))
    except Exception:
        return False


def download_video(lesson_slug, api_key, dest_path):
    """Oak API から動画をダウンロード"""
    url = f'{OAK_API_BASE}/lessons/{lesson_slug}/assets/video'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'OakAPIClient/1.0',
    })
    with urllib.request.urlopen(req, timeout=300) as resp:
        with open(dest_path, 'wb') as f:
            while True:
                data = resp.read(65536)  # 64KB chunks
                if not data:
                    break
                f.write(data)
    return os.path.getsize(dest_path)


def upload_to_drive(service, file_path, filename, folder_id):
    """Google Drive にファイルをアップロードし、公開リンクを設定"""
    from googleapiclient.http import MediaFileUpload

    file_metadata = {
        'name': filename,
        'parents': [folder_id],
    }
    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
    ).execute()

    file_id = file.get('id')

    # 誰でも閲覧可能に設定（動画ストリーミング用）
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
    ).execute()

    return file_id


def format_size(size_bytes):
    """バイト数を人間が読める形式に変換"""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(description='Oak動画をGoogle Driveにアップロード')
    parser.add_argument('--auth', action='store_true', help='OAuth2認証を実行（初回のみ）')
    parser.add_argument('--dry-run', action='store_true', help='対象を表示するだけ')
    parser.add_argument('--year', type=int, help='対象Year (例: 7)')
    parser.add_argument('--subject', type=str, help='対象教科 (例: science)')
    parser.add_argument('--limit', type=int, default=0, help='処理件数上限 (0=無制限)')
    parser.add_argument('--retry-errors', action='store_true', help='error状態のものを再試行')
    args = parser.parse_args()

    # 認証モード（ホストマシンで実行）
    if args.auth:
        do_auth()
        return

    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')
    api_key = os.environ.get('OAK_API_KEY', '')

    if not api_key:
        print("ERROR: OAK_API_KEY が未設定です")
        sys.exit(1)

    if not args.dry_run:
        if not folder_id:
            print("ERROR: GOOGLE_DRIVE_FOLDER_ID が未設定です")
            sys.exit(1)

    from app import app
    from models import db
    from models.material import Material, MaterialChunk

    with app.app_context():
        # 対象チャンクを取得
        query = db.session.query(MaterialChunk).join(Material)

        if args.retry_errors:
            query = query.filter(MaterialChunk.video_status == 'error')
        else:
            query = query.filter(MaterialChunk.video_status == 'none')

        if args.year:
            query = query.filter(Material.year_group == args.year)
        if args.subject:
            query = query.filter(Material.subject.ilike(f'%{args.subject}%'))

        query = query.order_by(Material.year_group, Material.subject, MaterialChunk.sort_order)
        chunks = query.all()

        if args.limit > 0:
            chunks = chunks[:args.limit]

        print(f"\n対象チャンク: {len(chunks)} 件")

        if not chunks:
            print("処理対象がありません")
            return

        if args.dry_run:
            print("\n[ドライラン] アップロード対象:")
            for i, chunk in enumerate(chunks, 1):
                mat = db.session.get(Material, chunk.material_id)
                slug = get_lesson_slug(chunk.title)
                print(f"  {i:3d}. [{mat.subject} Y{mat.year_group}] {chunk.title}")
                print(f"       slug: {slug}")
            print(f"\n合計 {len(chunks)} 件のレッスン動画が対象です")
            return

        # Google Drive サービス初期化
        drive_service = get_drive_service()
        print("Google Drive API 接続OK\n")

        uploaded = 0
        skipped = 0
        errors = 0
        total_bytes = 0

        for i, chunk in enumerate(chunks, 1):
            mat = db.session.get(Material, chunk.material_id)
            slug = get_lesson_slug(chunk.title)
            prefix = f"[{i}/{len(chunks)}] {mat.subject} Y{mat.year_group} - {chunk.title}"

            print(f"{prefix}")

            # 動画が存在するか確認
            print(f"  動画チェック中... ", end='', flush=True)
            has_video = check_video_available(slug, api_key)
            time.sleep(REQUEST_INTERVAL)

            if not has_video:
                print("動画なし → スキップ")
                chunk.video_status = 'none'
                db.session.commit()
                skipped += 1
                continue

            print("あり")

            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                print(f"  ダウンロード中... ", end='', flush=True)
                chunk.video_status = 'pending'
                db.session.commit()

                size = download_video(slug, api_key, tmp_path)
                print(f"{format_size(size)}")
                time.sleep(REQUEST_INTERVAL)

                # Google Drive にアップロード
                filename = f"{mat.subject}_Y{mat.year_group}_{slug}.mp4"
                print(f"  Google Driveアップロード中... ", end='', flush=True)
                file_id = upload_to_drive(drive_service, tmp_path, filename, folder_id)
                print(f"OK (ID: {file_id})")

                # DB更新
                chunk.video_drive_id = file_id
                chunk.video_status = 'uploaded'
                db.session.commit()

                uploaded += 1
                total_bytes += size

            except Exception as e:
                print(f"  ERROR: {e}")
                chunk.video_status = 'error'
                db.session.commit()
                errors += 1

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        print(f"\n{'='*50}")
        print(f"完了: {uploaded} 件アップロード, {skipped} 件スキップ, {errors} 件エラー")
        print(f"合計サイズ: {format_size(total_bytes)}")


if __name__ == '__main__':
    main()
