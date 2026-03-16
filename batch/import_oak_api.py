"""
Oak National Academy データ取り込みスクリプト（公式API版）

公式 Open API (https://open-api.thenational.academy/api/v0) を使用。
スクレイピング版 (import_oak.py / import_oak_all.py) の後継。
全 Key Stage (KS1-KS4)、全学年 (Year 1-11) に対応。

Usage:
    # デフォルト（KS3, 7教科, 全学年）
    docker exec elearn_app python batch/import_oak_api.py

    # 特定教科・Key Stage・学年を指定
    docker exec elearn_app python batch/import_oak_api.py --subjects science --key-stages ks3 --years 7

    # 全Key Stage、全教科
    docker exec elearn_app python batch/import_oak_api.py --all-key-stages --all-subjects

    # dry-run（APIテストのみ、DB書き込みなし）
    docker exec elearn_app python batch/import_oak_api.py --dry-run

    # 利用可能な教科一覧
    docker exec elearn_app python batch/import_oak_api.py --list-subjects

認証:
    .env の OAK_API_KEY を Authorization: Bearer ヘッダーで送信

レート制限:
    Oak API: 1000 req/hour
    3.6秒/リクエスト の間隔を設定（3600/1000=3.6）
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, '/app')
from app import create_app
from models import db
from models.material import Material, MaterialChunk, Question

# ---- 設定 ----
API_BASE = 'https://open-api.thenational.academy/api/v0'
API_KEY = os.environ.get('OAK_API_KEY', '')
REQUEST_INTERVAL = 3.6  # 1000 req/hour 制限に合わせて 3600/1000=3.6秒

ALL_KEY_STAGES = ['ks1', 'ks2', 'ks3', 'ks4']

# Key Stage → 学年のマッピング
KS_YEARS = {
    'ks1': [1, 2],
    'ks2': [3, 4, 5, 6],
    'ks3': [7, 8, 9],
    'ks4': [10, 11],
}

# インポート対象教科（slug → DB subject名）
ALL_SUBJECTS = {
    'science': 'Science',
    'maths': 'Maths',
    'english': 'English',
    'history': 'History',
    'geography': 'Geography',
    'computing': 'Computing',
    'spanish': 'Spanish',
    'french': 'French',
    'german': 'German',
    'latin': 'Latin',
    'art': 'Art',
    'citizenship': 'Citizenship',
    'cooking-nutrition': 'Cooking',
    'design-technology': 'Design Technology',
    'drama': 'Drama',
    'financial-education': 'Financial Education',
    'music': 'Music',
    'physical-education': 'Physical Education',
    'religious-education': 'Religious Education',
    'rshe-pshe': 'RSHE',
}

# デフォルトでインポートする教科
DEFAULT_SUBJECTS = [
    'science', 'maths', 'english', 'history',
    'geography', 'computing', 'spanish',
]

DEFAULT_KEY_STAGES = ['ks3']

MAX_RETRIES = 3
RETRY_DELAY = 5  # Cloudflare 401 対策


def api_get(path, params=None):
    """Oak API への GET リクエスト（リトライ付き）"""
    url = f'{API_BASE}{path}'
    if params:
        query = '&'.join(f'{k}={v}' for k, v in params.items() if v is not None)
        if query:
            url += f'?{query}'

    for attempt in range(MAX_RETRIES):
        time.sleep(REQUEST_INTERVAL)
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {API_KEY}',
            'Accept': 'application/json',
            'User-Agent': 'OakContentImporter/2.0 (personal education project)',
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = ''
            try:
                body = e.read().decode('utf-8')
            except Exception:
                pass
            # 401 は Cloudflare の一時エラーの場合があるのでリトライ
            if e.code == 401 and attempt < MAX_RETRIES - 1:
                print(f'    RETRY ({attempt+1}/{MAX_RETRIES}): HTTP 401 for {path}')
                time.sleep(RETRY_DELAY)
                continue
            print(f'    ERROR: HTTP {e.code} for {url}')
            if body:
                print(f'    {body[:200]}')
            return None
        except Exception as e:
            print(f'    ERROR: {e}')
            return None
    return None


# ---- データ取得 ----

def get_units(key_stage, subject_slug, target_years=None):
    """教科の単元一覧を取得
    GET /key-stages/{ks}/subject/{subject}/units
    Response: [{yearSlug: "year-7", yearTitle: "Year 7",
                units: [{unitSlug, unitTitle}, ...]}, ...]

    target_years: フィルタする学年リスト（Noneなら全学年）
    Returns: [(year, slug, title), ...]
    """
    data = api_get(f'/key-stages/{key_stage}/subject/{subject_slug}/units')
    if not data or not isinstance(data, list):
        return []

    units = []
    for year_group in data:
        if not isinstance(year_group, dict):
            continue
        year_slug = year_group.get('yearSlug', '')  # "year-7"
        try:
            year_num = int(year_slug.replace('year-', ''))
        except (ValueError, AttributeError):
            continue

        if target_years and year_num not in target_years:
            continue

        for u in year_group.get('units', []):
            slug = u.get('unitSlug', '')
            if slug:
                units.append((year_num, slug, u.get('unitTitle', '')))

    return units


def get_lessons(key_stage, subject_slug, unit_slug=None):
    """レッスン一覧を取得
    GET /key-stages/{ks}/subject/{subject}/lessons?unit=xxx
    Response: [{unitSlug, unitTitle, lessons: [{lessonSlug, lessonTitle}]}, ...]
    """
    params = {}
    if unit_slug:
        params['unit'] = unit_slug
    data = api_get(f'/key-stages/{key_stage}/subject/{subject_slug}/lessons', params)
    if not data or not isinstance(data, list):
        return []

    lessons = []
    for unit_group in data:
        if not isinstance(unit_group, dict):
            continue
        for l in unit_group.get('lessons', []):
            lessons.append({
                'slug': l.get('lessonSlug', ''),
                'title': l.get('lessonTitle', ''),
            })

    return [l for l in lessons if l['slug']]


def get_lesson_summary(lesson_slug):
    """レッスン要約を取得
    GET /lessons/{lesson}/summary
    """
    return api_get(f'/lessons/{lesson_slug}/summary')


def get_lesson_transcript(lesson_slug):
    """レッスンのトランスクリプトを取得
    GET /lessons/{lesson}/transcript
    """
    return api_get(f'/lessons/{lesson_slug}/transcript')


def get_lesson_quiz(lesson_slug):
    """レッスンのクイズを取得
    GET /lessons/{lesson}/quiz
    """
    return api_get(f'/lessons/{lesson_slug}/quiz')


# ---- データ変換 ----

def build_chunk_content(summary_data, transcript_data):
    """API レスポンスからチャンク用テキストを組み立てる"""
    parts = []

    if summary_data:
        outcome = summary_data.get('pupilLessonOutcome', '')
        if outcome:
            parts.append(f'Learning Outcome: {outcome}')

        klps = summary_data.get('keyLearningPoints', [])
        if klps:
            parts.append('\nKey Learning Points:')
            for p in klps:
                parts.append(f'- {p.get("keyLearningPoint", "")}')

        keywords = summary_data.get('lessonKeywords', [])
        if keywords:
            parts.append('\nKey Words:')
            for k in keywords:
                parts.append(f'- {k.get("keyword", "")}: {k.get("description", "")}')

        misconceptions = summary_data.get('misconceptionsAndCommonMistakes', [])
        if misconceptions:
            parts.append('\nCommon Misconceptions:')
            for m in misconceptions:
                parts.append(f'- Misconception: {m.get("misconception", "")}')
                parts.append(f'  Correction: {m.get("response", "")}')

    if transcript_data:
        transcript_text = transcript_data.get('transcript', '')
        if transcript_text:
            parts.append('\n--- Lesson Transcript ---\n')
            parts.append(transcript_text)

    return '\n'.join(parts)


def extract_quiz_questions(quiz_data, chunk_id):
    """APIクイズデータからQuestion オブジェクトのリストを生成

    API レスポンス構造:
    - question: str（問題文）
    - questionType: "multiple-choice" | "short-answer" | "match" | "ordering"
    - answers: [{content: str, distractor: bool, type: "text"}, ...]
      - distractor=false → 正解、distractor=true → 不正解
    """
    questions = []
    if not quiz_data:
        return questions

    for q in quiz_data:
        question_text = q.get('question', '')
        if not question_text:
            continue

        question_text = question_text.replace('{{}}', '[___]')
        q_type = q.get('questionType', '')
        answers = q.get('answers', [])

        # --- multiple-choice ---
        if q_type == 'multiple-choice':
            options = []
            correct_label = None
            labels = ['A', 'B', 'C', 'D', 'E', 'F']

            for i, a in enumerate(answers):
                if i >= len(labels):
                    break
                label = labels[i]
                options.append({'label': label, 'text': a.get('content', '')})
                if not a.get('distractor', True):
                    correct_label = label

            if options and correct_label:
                questions.append(Question(
                    question_type='multiple_choice',
                    question_text=question_text,
                    options=options,
                    correct_answer=correct_label,
                    difficulty='normal',
                    chunk_id=chunk_id,
                    source='oak',
                ))

        # --- short-answer → free_response ---
        # short-answer では全 answers が許容される正解バリエーション
        elif q_type == 'short-answer':
            answer_texts = [
                a.get('content', '') for a in answers
                if a.get('content')
            ]
            if answer_texts:
                questions.append(Question(
                    question_type='free_response',
                    question_text=question_text,
                    correct_answer=answer_texts[0],
                    reference_answer=', '.join(answer_texts),
                    max_score=10,
                    difficulty='normal',
                    chunk_id=chunk_id,
                    source='oak',
                ))

        # --- match → multiple_choice として変換 ---
        # 各 matchOption について、全 correctChoice を選択肢にした多肢選択問題を生成
        elif q_type == 'match':
            # 有効なペアを収集
            match_pairs = []
            for a in answers:
                match_opt = a.get('matchOption')
                correct_choice = a.get('correctChoice')
                if match_opt and correct_choice:
                    match_text = match_opt.get('content', '')
                    correct_text = correct_choice.get('content', '')
                    if match_text and correct_text:
                        match_pairs.append((match_text, correct_text))

            if len(match_pairs) >= 2:
                labels = ['A', 'B', 'C', 'D', 'E', 'F']
                # 全 correctChoice を選択肢として使う（元の順序で固定ラベル付与）
                all_choices = [pair[1] for pair in match_pairs]
                options = []
                for idx, choice_text in enumerate(all_choices):
                    if idx >= len(labels):
                        break
                    options.append({'label': labels[idx], 'text': choice_text})

                for pair_idx, (match_text, correct_text) in enumerate(match_pairs):
                    if pair_idx >= len(labels):
                        break
                    # この matchOption の正解ラベルを特定
                    correct_label = labels[pair_idx]
                    questions.append(Question(
                        question_type='multiple_choice',
                        question_text=f'{question_text}\n\n{match_text} is...',
                        options=options,
                        correct_answer=correct_label,
                        difficulty='normal',
                        chunk_id=chunk_id,
                        source='oak',
                    ))

        # --- ordering → free_response として変換 ---
        elif q_type == 'ordering':
            ordered = sorted(
                [a for a in answers if a.get('order') is not None],
                key=lambda a: a['order']
            )
            if ordered:
                correct_order = ' → '.join(a.get('content', '') for a in ordered)
                questions.append(Question(
                    question_type='free_response',
                    question_text=f'{question_text}\n\nPut these in the correct order.',
                    correct_answer=correct_order,
                    reference_answer=correct_order,
                    max_score=10,
                    difficulty='normal',
                    chunk_id=chunk_id,
                    source='oak',
                ))

    return questions


# ---- インポートロジック ----

def ks_label(key_stage):
    """KS slug → 表示名"""
    return key_stage.upper().replace('KS', 'KS')


def import_unit(key_stage, subject_slug, subject_name, year, unit_slug, unit_title,
                parent_id, dry_run=False):
    """1単元分をインポート"""
    ks = ks_label(key_stage)
    material_title = f'{ks} {subject_name} - {unit_title}'

    # 既にインポート済みか確認
    if not dry_run:
        existing = Material.query.filter_by(title=material_title).first()
        if existing:
            print(f'    SKIP: already imported')
            return

    # レッスン一覧を取得
    lessons = get_lessons(key_stage, subject_slug, unit_slug)
    if not lessons:
        print(f'    WARN: No lessons found')
        return

    print(f'    {len(lessons)} lessons')

    if dry_run:
        if lessons:
            first = lessons[0]
            print(f'      Sample: {first["title"]} ({first["slug"]})')
            summary = get_lesson_summary(first['slug'])
            if summary:
                print(f'      Summary keys: {list(summary.keys())[:10]}')
            quiz = get_lesson_quiz(first['slug'])
            if quiz:
                starter_count = len(quiz.get('starterQuiz', []))
                exit_count = len(quiz.get('exitQuiz', []))
                print(f'      Quiz: {starter_count} starter + {exit_count} exit')
        return

    # マテリアル作成
    material = Material(
        title=material_title,
        description=f'Oak National Academy {ks} {subject_name} Year {year}: '
                    f'{unit_title} ({len(lessons)} lessons)',
        source_type='url',
        source_content=f'https://open-api.thenational.academy/api/v0'
                       f'/key-stages/{key_stage}/subject/{subject_slug}/lessons?unit={unit_slug}',
        subject=subject_name,
        year_group=year,
        difficulty='normal',
        language='en',
        status='draft',
        created_by=parent_id,
    )
    db.session.add(material)
    db.session.flush()

    total_questions = 0

    for i, lesson_info in enumerate(lessons):
        lesson_slug = lesson_info['slug']
        lesson_title = lesson_info.get('title', lesson_slug)

        summary = get_lesson_summary(lesson_slug)
        transcript = get_lesson_transcript(lesson_slug)
        quiz = get_lesson_quiz(lesson_slug)

        if not summary and not transcript:
            print(f'      [{i+1}] {lesson_title}: SKIP (no data)')
            continue

        chunk_content = build_chunk_content(summary, transcript)
        chunk = MaterialChunk(
            material_id=material.material_id,
            title=lesson_title,
            content=chunk_content,
            sort_order=i + 1,
        )
        db.session.add(chunk)
        db.session.flush()

        questions = []
        if quiz:
            questions.extend(extract_quiz_questions(
                quiz.get('starterQuiz', []), chunk.chunk_id))
            questions.extend(extract_quiz_questions(
                quiz.get('exitQuiz', []), chunk.chunk_id))

        for q in questions:
            q.material_id = material.material_id

        db.session.add_all(questions)
        total_questions += len(questions)

    db.session.commit()
    chunk_count = material.chunks.count()
    print(f'    -> {chunk_count} chunks, {total_questions} questions')


def import_subject(key_stage, subject_slug, subject_name, target_years,
                   parent_id, dry_run=False):
    """1教科分をインポート（指定学年のみ）"""
    ks = ks_label(key_stage)
    print(f'\n{"="*60}')
    print(f'{ks} {subject_name} ({subject_slug})')
    print(f'{"="*60}')

    units = get_units(key_stage, subject_slug, target_years)
    if not units:
        print(f'  No units found for Year {target_years}')
        return

    # 学年ごとにグループ表示
    years_found = sorted(set(y for y, _, _ in units))
    print(f'  Found {len(units)} units across Year {years_found}')

    for i, (year, unit_slug, unit_title) in enumerate(units):
        print(f'\n  [{i+1}/{len(units)}] Year {year}: {unit_title}')
        import_unit(key_stage, subject_slug, subject_name, year,
                    unit_slug, unit_title, parent_id, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(
        description='Import Oak data via official API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Year 7 Science only
  %(prog)s --subjects science --key-stages ks3 --years 7

  # All KS3 subjects, all years
  %(prog)s --key-stages ks3

  # All key stages, all subjects
  %(prog)s --all-key-stages --all-subjects

  # KS1+KS2 Maths and English
  %(prog)s --key-stages ks1 ks2 --subjects maths english
        """)
    parser.add_argument('--subjects', nargs='+', default=None,
                        help='Subject slugs to import')
    parser.add_argument('--all-subjects', action='store_true',
                        help='Import all available subjects')
    parser.add_argument('--key-stages', nargs='+', default=None,
                        help='Key stages to import (e.g. ks1 ks2 ks3 ks4)')
    parser.add_argument('--all-key-stages', action='store_true',
                        help='Import all key stages (KS1-KS4)')
    parser.add_argument('--years', nargs='+', type=int, default=None,
                        help='Specific years to import (e.g. 7 8 9)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Test API calls without writing to DB')
    parser.add_argument('--list-subjects', action='store_true',
                        help='List available subject slugs and exit')
    args = parser.parse_args()

    if args.list_subjects:
        print('Available subjects:')
        for slug, name in sorted(ALL_SUBJECTS.items()):
            default = ' (default)' if slug in DEFAULT_SUBJECTS else ''
            print(f'  {slug:25s} → {name}{default}')
        print(f'\nKey stages: {", ".join(ALL_KEY_STAGES)}')
        print('KS → Years:', {k: v for k, v in KS_YEARS.items()})
        return

    if not API_KEY:
        print('ERROR: OAK_API_KEY not set in environment')
        sys.exit(1)

    # インポート対象を決定
    if args.all_subjects:
        subjects = ALL_SUBJECTS
    elif args.subjects:
        subjects = {}
        for s in args.subjects:
            if s in ALL_SUBJECTS:
                subjects[s] = ALL_SUBJECTS[s]
            else:
                print(f'WARNING: Unknown subject "{s}", skipping')
        if not subjects:
            print('ERROR: No valid subjects specified')
            sys.exit(1)
    else:
        subjects = {s: ALL_SUBJECTS[s] for s in DEFAULT_SUBJECTS}

    if args.all_key_stages:
        key_stages = ALL_KEY_STAGES
    elif args.key_stages:
        key_stages = [ks for ks in args.key_stages if ks in ALL_KEY_STAGES]
        if not key_stages:
            print('ERROR: No valid key stages specified')
            sys.exit(1)
    else:
        key_stages = DEFAULT_KEY_STAGES

    # API接続テスト
    print('Testing API connection...')
    test = api_get('/key-stages')
    if test is None:
        print('ERROR: Cannot connect to Oak API. Check OAK_API_KEY.')
        sys.exit(1)
    print('API connection OK')

    app = create_app()
    with app.app_context():
        if args.dry_run:
            print('\n*** DRY RUN MODE — no DB writes ***\n')
            for ks in key_stages:
                target_years = args.years if args.years else KS_YEARS.get(ks, [])
                for slug, name in subjects.items():
                    import_subject(ks, slug, name, target_years,
                                   parent_id=1, dry_run=True)
            return

        from models.parent import Parent
        parent = Parent.query.filter_by(role='admin').first()
        if not parent:
            print('ERROR: No admin account found.')
            sys.exit(1)

        print(f'Importing as: {parent.display_name} (id={parent.parent_id})')
        print(f'Key stages: {key_stages}')
        print(f'Subjects: {list(subjects.keys())}')
        if args.years:
            print(f'Years: {args.years}')
        print(f'Rate limit: {REQUEST_INTERVAL}s/request (API: 1000 req/hour)')

        for ks in key_stages:
            target_years = args.years if args.years else KS_YEARS.get(ks, [])
            for slug, name in subjects.items():
                import_subject(ks, slug, name, target_years, parent.parent_id)

        # サマリー
        print(f'\n{"="*60}')
        print('IMPORT COMPLETE')
        print(f'{"="*60}')
        from sqlalchemy import func
        summary = db.session.query(
            Material.subject,
            Material.year_group,
            func.count(Material.material_id)
        ).group_by(Material.subject, Material.year_group).all()
        for subj, year, cnt in sorted(summary):
            print(f'  {subj} Year {year}: {cnt} units')


if __name__ == '__main__':
    main()
