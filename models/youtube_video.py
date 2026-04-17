"""chunk_youtube_videos モデル — 1 chunk あたり複数のYouTube動画候補を保持。"""

from models import db


class ChunkYoutubeVideo(db.Model):
    __tablename__ = 'chunk_youtube_videos'

    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255))
    channel = db.Column(db.String(100))
    duration_seconds = db.Column(db.Integer)
    thumbnail_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    rank_position = db.Column(db.Integer, nullable=False, default=99)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    source = db.Column(db.String(20), nullable=False, default='api_search')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
