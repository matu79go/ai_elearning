"""YouTube 動画検索サービス — YouTube Data API v3 + LLM でランキング。"""
from __future__ import annotations

import os
import re
import time
import urllib.parse
import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
API_BASE = 'https://www.googleapis.com/youtube/v3'

# 教科ごとの優先チャンネル (検索結果ランキングで優遇)
PREFERRED_CHANNELS = {
    'Science':   ['Free Science Lessons', 'Primrose Kitten', 'BBC Teach', 'FuseSchool',
                  'Fuse School', 'Crash Course', 'Cognito'],
    'Maths':     ['Corbett Maths', 'Maths Genie', 'BBC Teach', 'FuseSchool', 'Fuse School',
                  'TLMaths'],
    'English':   ['Mr Bruff', 'Mr Salles', 'BBC Teach', 'Crash Course'],
    'Spanish':   ['Dreaming Spanish', 'Butterfly Spanish', 'Easy Spanish', 'SpanishPod101'],
    'History':   ['OverSimplified', 'Simple History', 'Crash Course', 'BBC Teach'],
    'Geography': ['Geography Now', 'Crash Course', 'BBC Teach'],
    'Computing': ['Crash Course', 'BBC Teach'],
}


def _iso8601_duration_to_seconds(iso: str) -> int | None:
    """PT5M13S -> 313."""
    if not iso or not iso.startswith('PT'):
        return None
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso)
    if not m:
        return None
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mn * 60 + s


def _http_get_json(url: str, timeout: float = 15.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def youtube_search(query: str, max_results: int = 5) -> list[dict]:
    """YouTube Data API で検索し、動画情報を返す。"""
    if not YOUTUBE_API_KEY:
        raise RuntimeError('YOUTUBE_API_KEY not set')

    params = {
        'part': 'snippet',
        'type': 'video',
        'maxResults': max_results,
        'q': query,
        'relevanceLanguage': 'en',
        'safeSearch': 'strict',
        'videoEmbeddable': 'true',
        'key': YOUTUBE_API_KEY,
    }
    url = f'{API_BASE}/search?' + urllib.parse.urlencode(params)
    data = _http_get_json(url)

    items = []
    video_ids = []
    for item in data.get('items', []):
        vid = item.get('id', {}).get('videoId')
        if not vid:
            continue
        snip = item.get('snippet', {})
        items.append({
            'video_id': vid,
            'title': snip.get('title', ''),
            'channel': snip.get('channelTitle', ''),
            'description': snip.get('description', '')[:500],
            'thumbnail_url': (snip.get('thumbnails', {}).get('medium') or
                              snip.get('thumbnails', {}).get('default') or {}).get('url', ''),
        })
        video_ids.append(vid)

    # 2nd call: videos API で contentDetails (duration) を取得
    if video_ids:
        params2 = {
            'part': 'contentDetails',
            'id': ','.join(video_ids),
            'key': YOUTUBE_API_KEY,
        }
        url2 = f'{API_BASE}/videos?' + urllib.parse.urlencode(params2)
        try:
            ddata = _http_get_json(url2)
            dur_map = {}
            for v in ddata.get('items', []):
                dur_map[v['id']] = _iso8601_duration_to_seconds(
                    v.get('contentDetails', {}).get('duration', '')
                )
            for it in items:
                it['duration_seconds'] = dur_map.get(it['video_id'])
        except Exception as e:
            logger.warning(f'videos API failed: {e}')
            for it in items:
                it['duration_seconds'] = None
    return items


def rank_videos_with_llm(chunk_title: str, subject: str, year_group: int,
                        candidates: list[dict]) -> list[int]:
    """LLM に候補を順位付けさせる。候補の index を希望順に並べて返す。

    ranking order: best candidate first. len(return) <= len(candidates).
    On failure: returns list as-is (順序維持).
    """
    if not candidates:
        return []
    from services.llm import _call_llm

    preferred = PREFERRED_CHANNELS.get(subject, [])
    preferred_str = ', '.join(preferred) if preferred else '(none specified)'

    lines = []
    for i, c in enumerate(candidates):
        dur = c.get('duration_seconds')
        dur_str = f'{dur//60}:{dur%60:02d}' if dur else '??'
        lines.append(
            f'{i}: [{c["channel"]}] ({dur_str}) {c["title"]}\n'
            f'   desc: {c.get("description","")[:200]}'
        )
    catalog = '\n'.join(lines)

    prompt = f"""You are helping to pick the best YouTube video for a UK school lesson.

LESSON: {chunk_title}
SUBJECT: {subject}  YEAR: {year_group} (KS3)

PREFERRED CHANNELS (higher priority): {preferred_str}

CANDIDATES:
{catalog}

RULES:
- Prefer candidates from the preferred channels above.
- Prefer videos whose title/description matches the lesson topic.
- Prefer 3-15 minute videos, but longer is OK if highly relevant.
- Year {year_group} students are 11-14 years old; "for kids" videos are usually fine.
- Only completely exclude videos that are clearly off-topic or unsuitable (explicit, wrong subject, etc.)

Respond ONLY with a JSON array of candidate indices in best-to-worst order.
Example: [2, 0, 4, 1, 3]
Include ALL candidates unless they are truly unsuitable. Prefer to rank rather than exclude.
"""
    try:
        raw = _call_llm(prompt)
        logger.info(f'LLM rank raw response: {raw[:200]!r}')
    except Exception as e:
        logger.warning(f'LLM rank failed: {e}')
        return list(range(len(candidates)))

    m = re.search(r'\[[^\]]*\]', raw)
    if not m:
        logger.warning(f'no JSON array in LLM response: {raw[:200]!r}')
        return list(range(len(candidates)))
    try:
        order = json.loads(m.group(0))
        order = [int(i) for i in order if isinstance(i, int) and 0 <= i < len(candidates)]
        # deduplicate keeping first occurrence
        seen = set()
        clean = []
        for i in order:
            if i not in seen:
                seen.add(i)
                clean.append(i)
        return clean
    except Exception:
        return list(range(len(candidates)))


def _build_query(title: str, subject: str, year_group: int) -> str:
    """検索クエリ組み立て。長すぎる title は短縮、特殊文字除去。"""
    # 特殊文字を空白に
    clean = re.sub(r"[^\w\s]", ' ', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # コロン以降の細かい文法ラベル等を切り落とす (例: "...: 'estar' 1st and 3rd person singular")
    # 単語数多すぎたら最初の8単語だけ使う
    words = clean.split()
    if len(words) > 8:
        clean = ' '.join(words[:8])
    return f'{clean} {subject} KS3'


def find_and_save_videos(chunk_id: int, title: str, subject: str,
                        year_group: int, max_results: int = 5,
                        force: bool = False) -> list:
    """検索 → LLMランク付け → DB保存。保存済みを返す。

    既にこの chunk に動画が保存されている場合、API quota を節約するため何もしない
    (force=True で強制再検索可能)。
    """
    from models import db
    from models.youtube_video import ChunkYoutubeVideo

    if not force:
        existing_count = ChunkYoutubeVideo.query.filter_by(chunk_id=chunk_id).count()
        if existing_count > 0:
            logger.info(f'chunk {chunk_id} already has {existing_count} videos, skipping API call (force=False)')
            return []

    # 検索クエリ組み立て (クリーン + 短縮)
    query = _build_query(title, subject, year_group)
    logger.info(f'chunk {chunk_id} query: {query!r}')
    candidates = youtube_search(query, max_results=max_results)
    # fallback: タイトル短縮でも0件なら、さらに単語3つまで絞って再試行
    if not candidates:
        short_words = ' '.join(query.split()[:4])
        logger.info(f'chunk {chunk_id} retry with: {short_words!r}')
        candidates = youtube_search(short_words, max_results=max_results)
    if not candidates:
        return []

    # LLM でランキング
    order = rank_videos_with_llm(title, subject, year_group, candidates)
    logger.info(f'chunk {chunk_id} rank order: {order} from {len(candidates)} candidates')
    # LLM が全否定したら、API検索順をそのまま採用 (少なくとも検索上位は出題トピックに関連)
    if not order:
        logger.info(f'chunk {chunk_id} LLM returned empty, falling back to API search order')
        order = list(range(len(candidates)))

    # 既存 (重複防止)
    existing_vids = {v.video_id for v in ChunkYoutubeVideo.query.filter_by(
        chunk_id=chunk_id
    ).all()}

    rows = []
    for new_rank, orig_idx in enumerate(order):
        c = candidates[orig_idx]
        if c['video_id'] in existing_vids:
            continue
        row = ChunkYoutubeVideo(
            chunk_id=chunk_id,
            video_id=c['video_id'],
            title=c['title'],
            channel=c['channel'],
            duration_seconds=c.get('duration_seconds'),
            thumbnail_url=c.get('thumbnail_url'),
            description=c.get('description'),
            rank_position=new_rank + 1,
            is_primary=(new_rank == 0),
            source='llm_pick' if new_rank == 0 else 'api_search',
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows
