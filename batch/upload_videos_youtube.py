#!/usr/bin/env python3
"""
Google DriveキャッシュからYouTubeへ動画をアップロードするバッチスクリプト

Usage:
    # 初回認証（ブラウザが開く → Googleアカウントで許可）
    python batch/upload_videos_youtube.py --auth

    # ドライラン（対象を確認）
    docker exec elearn_app python batch/upload_videos_youtube.py --dry-run

    # 1件だけテスト
    docker exec elearn_app python batch/upload_videos_youtube.py --chunk-id 975

    # Year 7 Science のみ
    docker exec elearn_app python batch/upload_videos_youtube.py --year 7 --subject science

    # 全対象（video_drive_id あり & video_youtube_id なし）
    docker exec elearn_app python batch/upload_videos_youtube.py

    # 処理件数制限
    docker exec elearn_app python batch/upload_videos_youtube.py --limit 10

前提:
    - credentials/youtube_oauth.json に OAuth クライアントIDを配置
    - 初回は --auth でブラウザ認証 → credentials/youtube_token.json が生成される
    - YouTube Data API v3 が有効化済み
    - Google DriveにアップロードIDが既に入っている（video_drive_id）
"""

import os
import sys
import json
import time
import argparse
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CREDENTIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'credentials')
OAUTH_PATH = os.path.join(CREDENTIALS_DIR, 'youtube_oauth.json')
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, 'youtube_token.json')

# Google Drive OAuth（ダウンロード用）
DRIVE_TOKEN_PATH = os.path.join(CREDENTIALS_DIR, 'gdrive_token.json')

SCOPES_YT = ['https://www.googleapis.com/auth/youtube.upload']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.readonly']

# YouTube API daily upload quota is limited — be careful with large batches
UPLOAD_INTERVAL = 2  # seconds between uploads


def do_auth():
    """OAuth2 認証フロー（初回のみ、ホストマシンで実行）"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    # YouTube upload scope
    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_PATH, SCOPES_YT)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    print(f"YouTube認証成功！トークン保存先: {TOKEN_PATH}")
    return creds


def get_youtube_service():
    """YouTube API サービスを初期化"""
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_PATH):
        print(f"ERROR: YouTubeトークンファイルが見つかりません: {TOKEN_PATH}")
        print("ホストマシンで先に認証を実行してください:")
        print("  python batch/upload_videos_youtube.py --auth")
        sys.exit(1)

    creds = OAuthCredentials.from_authorized_user_file(TOKEN_PATH, SCOPES_YT)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)


def get_drive_service():
    """Google Drive API サービスを初期化（動画ダウンロード用）"""
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(DRIVE_TOKEN_PATH):
        print(f"ERROR: Google Driveトークンが見つかりません: {DRIVE_TOKEN_PATH}")
        sys.exit(1)

    creds = OAuthCredentials.from_authorized_user_file(DRIVE_TOKEN_PATH,
                                                        ['https://www.googleapis.com/auth/drive.file'])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(DRIVE_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def download_from_drive(drive_service, file_id, dest_path):
    """Google Driveからファイルをダウンロード"""
    from googleapiclient.http import MediaIoBaseDownload
    import io

    request = drive_service.files().get_media(fileId=file_id)

    with open(dest_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"\r  ダウンロード: {int(status.progress() * 100)}%", end='', flush=True)
    print()
    return os.path.getsize(dest_path)


def upload_to_youtube(youtube_service, file_path, title, description):
    """YouTubeに限定公開でアップロード"""
    from googleapiclient.http import MediaFileUpload

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': '27',  # Education
        },
        'status': {
            'privacyStatus': 'unlisted',  # 限定公開
            'selfDeclaredMadeForKids': True,
        },
    }

    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True,
                            chunksize=10 * 1024 * 1024)  # 10MB chunks

    request = youtube_service.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"\r  アップロード: {int(status.progress() * 100)}%", end='', flush=True)
    print()

    return response['id']


def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(description='Google Drive動画をYouTubeにアップロード')
    parser.add_argument('--auth', action='store_true', help='YouTube OAuth2認証を実行（初回のみ）')
    parser.add_argument('--dry-run', action='store_true', help='対象を表示するだけ')
    parser.add_argument('--chunk-id', type=int, help='特定のchunk_idのみ処理')
    parser.add_argument('--year', type=int, help='対象Year (例: 7)')
    parser.add_argument('--subject', type=str, help='対象教科 (例: science)')
    parser.add_argument('--limit', type=int, default=0, help='処理件数上限 (0=無制限)')
    args = parser.parse_args()

    if args.auth:
        do_auth()
        return

    from app import app
    from models import db
    from models.material import Material, MaterialChunk

    with app.app_context():
        # 対象チャンクを取得: Google Driveにあり、YouTubeにまだない
        query = db.session.query(MaterialChunk).join(Material)

        if args.chunk_id:
            query = query.filter(MaterialChunk.chunk_id == args.chunk_id)
        else:
            query = query.filter(
                MaterialChunk.video_drive_id.isnot(None),
                MaterialChunk.video_drive_id != '',
                MaterialChunk.video_youtube_id.is_(None),
            )

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
                print(f"  {i:3d}. [{mat.subject} Y{mat.year_group}] {chunk.title}")
                print(f"       DriveID: {chunk.video_drive_id}")
            print(f"\n合計 {len(chunks)} 件")
            return

        # サービス初期化
        print("YouTube API 初期化中...")
        yt_service = get_youtube_service()
        print("YouTube API 接続OK")

        print("Google Drive API 初期化中...")
        drive_service = get_drive_service()
        print("Google Drive API 接続OK\n")

        uploaded = 0
        errors = 0
        total_bytes = 0

        for i, chunk in enumerate(chunks, 1):
            mat = db.session.get(Material, chunk.material_id)
            prefix = f"[{i}/{len(chunks)}] {mat.subject} Y{mat.year_group} - {chunk.title}"
            print(f"{prefix}")

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Google Drive からダウンロード
                print(f"  Google Driveからダウンロード中...")
                size = download_from_drive(drive_service, chunk.video_drive_id, tmp_path)
                print(f"  サイズ: {format_size(size)}")

                # YouTube にアップロード
                yt_title = f"{mat.subject} Y{mat.year_group} - {chunk.title}"
                yt_desc = (f"KS3 {mat.subject} Year {mat.year_group}\n"
                           f"Unit: {mat.title}\n"
                           f"Lesson: {chunk.title}\n\n"
                           f"Source: Oak National Academy (OGL v3.0)")

                # タイトル100文字制限
                if len(yt_title) > 100:
                    yt_title = yt_title[:97] + '...'

                print(f"  YouTubeアップロード中...")
                video_id = upload_to_youtube(yt_service, tmp_path, yt_title, yt_desc)
                print(f"  完了! YouTube ID: {video_id}")
                print(f"  URL: https://youtu.be/{video_id}")

                # DB更新
                chunk.video_youtube_id = video_id
                db.session.commit()

                uploaded += 1
                total_bytes += size
                time.sleep(UPLOAD_INTERVAL)

            except Exception as e:
                print(f"  ERROR: {e}")
                errors += 1

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        print(f"\n{'='*50}")
        print(f"完了: {uploaded} 件アップロード, {errors} 件エラー")
        print(f"合計サイズ: {format_size(total_bytes)}")


if __name__ == '__main__':
    main()
