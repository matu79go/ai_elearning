"""
Oak National Academy KS3 全教科データ取り込みスクリプト

Usage:
    docker exec elearn_app python batch/import_oak_all.py

レート制限:
    - リクエスト間隔: 2秒
    - 単元間: 3秒の追加待機
    - 教科間: 5秒の追加待機
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, '/app')
from app import create_app
from models import db
from models.material import Material, MaterialChunk, Question

BASE_URL = 'https://www.thenational.academy'
REQUEST_INTERVAL = 2.0
UNIT_INTERVAL = 3.0
SUBJECT_INTERVAL = 5.0

# インポート対象の教科（プログラムslug → DB subject名）
# 全教科のslug一覧は docs/oak_import.md を参照
SUBJECTS = {
    # 'science-secondary-ks3': 'Science',  # 別スクリプト(import_oak.py)でインポート済み
    'maths-secondary-ks3': 'Maths',
    'english-secondary-ks3': 'English',
    'history-secondary-ks3': 'History',
    'geography-secondary-ks3': 'Geography',
    'computing-secondary-ks3': 'Computing',
    'spanish-secondary-ks3': 'Spanish',
}

# 未インポートの教科（後日追加時にコメントを外す）
# ADDITIONAL_SUBJECTS = {
#     'french-secondary-ks3': 'French',
#     'german-secondary-ks3': 'German',
#     'latin-secondary-ks3-l': 'Latin',
#     'art-secondary-ks3': 'Art',
#     'citizenship-secondary-ks3': 'Citizenship',
#     'cooking-nutrition-secondary-ks3': 'Cooking',
#     'design-technology-secondary-ks3': 'Design Technology',
#     'drama-secondary-ks3-l': 'Drama',
#     'financial-education-secondary-ks3': 'Financial Education',
#     'music-secondary-ks3': 'Music',
#     'physical-education-secondary-ks3': 'Physical Education',
#     'religious-education-secondary-ks3': 'Religious Education',
#     'rshe-pshe-secondary-ks3': 'RSHE',
# }

TARGET_YEAR = 7


def fetch_page(url):
    """URLからHTMLを取得（レート制限付き）"""
    time.sleep(REQUEST_INTERVAL)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'OakContentImporter/1.0 (personal education project)'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f'    ERROR: HTTP {e.code} for {url}')
        return None
    except Exception as e:
        print(f'    ERROR: {e}')
        return None


def extract_next_data(html):
    """HTMLから __NEXT_DATA__ JSONを抽出"""
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def get_units_for_programme(programme_slug):
    """プログラムページから Year 7 の単元slug一覧を取得"""
    url = f'{BASE_URL}/teachers/programmes/{programme_slug}/units'
    print(f'  Fetching units from {url}')
    html = fetch_page(url)
    if not html:
        return []

    data = extract_next_data(html)
    if not data:
        return []

    try:
        units = data['props']['pageProps']['curriculumData']['units']
        year7_units = []
        for unit_group in units:
            # 各unitGroupはyear情報を持つ場合がある
            if isinstance(unit_group, list):
                for u in unit_group:
                    if u.get('year', '') == f'{TARGET_YEAR}' or u.get('year') == TARGET_YEAR:
                        year7_units.append(u.get('slug') or u.get('unitSlug', ''))
            elif isinstance(unit_group, dict):
                year_val = str(unit_group.get('year', ''))
                if year_val == str(TARGET_YEAR):
                    year7_units.append(unit_group.get('slug') or unit_group.get('unitSlug', ''))
        return [u for u in year7_units if u]
    except (KeyError, TypeError) as e:
        print(f'    Could not parse units: {e}')
        # フォールバック: ページ内のunit slugを正規表現で探す
        return []


def get_units_from_lessons_page(programme_slug):
    """ユニットページのHTMLからYear 7ユニットを別方法で取得"""
    url = f'{BASE_URL}/teachers/programmes/{programme_slug}/units'
    html = fetch_page(url)
    if not html:
        return []

    data = extract_next_data(html)
    if not data:
        return []

    try:
        page_data = data['props']['pageProps']['curriculumData']
        units = page_data.get('units', [])

        year7_units = []
        for unit_group in units:
            # units は [[{unit1}, {unit2}], [{unit3}]] のようなネスト構造の場合がある
            if isinstance(unit_group, list):
                for u in unit_group:
                    year_str = str(u.get('year', ''))
                    if year_str == str(TARGET_YEAR):
                        slug = u.get('slug') or u.get('unitSlug', '')
                        title = u.get('title') or u.get('unitTitle', '')
                        if slug:
                            year7_units.append({'slug': slug, 'title': title})
            elif isinstance(unit_group, dict):
                year_str = str(unit_group.get('year', ''))
                if year_str == str(TARGET_YEAR):
                    slug = unit_group.get('slug') or unit_group.get('unitSlug', '')
                    title = unit_group.get('title') or unit_group.get('unitTitle', '')
                    if slug:
                        year7_units.append({'slug': slug, 'title': title})

        return year7_units
    except (KeyError, TypeError) as e:
        print(f'    Parse error: {e}')
        return []


def get_lesson_slugs(programme_slug, unit_slug):
    """単元ページからレッスンslug一覧を取得"""
    url = f'{BASE_URL}/teachers/programmes/{programme_slug}/units/{unit_slug}/lessons'
    html = fetch_page(url)
    if not html:
        return []

    data = extract_next_data(html)
    if not data:
        return []

    try:
        lessons = data['props']['pageProps']['curriculumData']['lessons']
        return [l['lessonSlug'] for l in lessons]
    except (KeyError, TypeError):
        return []


def get_lesson_data(programme_slug, unit_slug, lesson_slug):
    """レッスンページから教材データを取得"""
    url = f'{BASE_URL}/teachers/programmes/{programme_slug}/units/{unit_slug}/lessons/{lesson_slug}'
    html = fetch_page(url)
    if not html:
        return None

    data = extract_next_data(html)
    if not data:
        return None

    try:
        return data['props']['pageProps']['curriculumData']
    except (KeyError, TypeError):
        return None


def build_chunk_content(lesson_data):
    """レッスンデータからチャンク用テキストを組み立てる"""
    parts = []

    outcome = lesson_data.get('pupilLessonOutcome', '')
    if outcome:
        parts.append(f'Learning Outcome: {outcome}')

    klps = lesson_data.get('keyLearningPoints', [])
    if klps:
        parts.append('\nKey Learning Points:')
        for p in klps:
            parts.append(f'- {p["keyLearningPoint"]}')

    keywords = lesson_data.get('lessonKeywords', [])
    if keywords:
        parts.append('\nKey Words:')
        for k in keywords:
            parts.append(f'- {k["keyword"]}: {k["description"]}')

    misconceptions = lesson_data.get('misconceptionsAndCommonMistakes', [])
    if misconceptions:
        parts.append('\nCommon Misconceptions:')
        for m in misconceptions:
            parts.append(f'- Misconception: {m["misconception"]}')
            parts.append(f'  Correction: {m["response"]}')

    sentences = lesson_data.get('transcriptSentences', [])
    if sentences:
        parts.append('\n--- Lesson Transcript ---\n')
        if isinstance(sentences[0], str):
            parts.append(' '.join(sentences))
        else:
            parts.append(' '.join(str(s) for s in sentences))

    return '\n'.join(parts)


def extract_quiz_questions(quiz_data, chunk_id):
    """クイズデータからQuestion オブジェクトのリストを生成"""
    questions = []
    if not quiz_data:
        return questions

    for q in quiz_data:
        stem_parts = q.get('questionStem', [])
        question_text = ' '.join(
            p.get('text', '') for p in stem_parts if p.get('type') == 'text'
        ).strip()
        question_text = question_text.replace('{{}}', '[___]')

        if not question_text:
            continue

        answers = q.get('answers') or {}

        mc_answers = answers.get('multiple-choice', [])
        if mc_answers:
            options = []
            correct_label = None
            labels = ['A', 'B', 'C', 'D', 'E', 'F']

            for i, a in enumerate(mc_answers):
                if i >= len(labels):
                    break
                answer_text = ''
                if a.get('answer'):
                    answer_text = ' '.join(
                        p.get('text', '') for p in a['answer'] if p.get('type') == 'text'
                    ).strip()

                label = labels[i]
                options.append({'label': label, 'text': answer_text})

                if not a.get('answer_is_default', True):
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
            continue

        short_answers = answers.get('short-answer', [])
        if short_answers:
            answer_texts = []
            for a in short_answers:
                if a.get('answer'):
                    t = ' '.join(
                        p.get('text', '') for p in a['answer'] if p.get('type') == 'text'
                    ).strip()
                    if t:
                        answer_texts.append(t)

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

    return questions


def import_unit(programme_slug, unit_slug, unit_title, subject_name, parent_id):
    """1単元分をインポート"""
    material_title = f'KS3 {subject_name} - {unit_title}'

    # 既にインポート済みか確認
    existing = Material.query.filter_by(title=material_title).first()
    if existing:
        print(f'    SKIP: already imported')
        return

    # レッスン一覧を取得
    lesson_slugs = get_lesson_slugs(programme_slug, unit_slug)
    if not lesson_slugs:
        print(f'    WARN: No lessons found')
        return

    print(f'    {len(lesson_slugs)} lessons')

    # マテリアル作成
    material = Material(
        title=material_title,
        description=f'Oak National Academy KS3 {subject_name} Year {TARGET_YEAR}: {unit_title} ({len(lesson_slugs)} lessons)',
        source_type='url',
        source_content=f'{BASE_URL}/teachers/programmes/{programme_slug}/units/{unit_slug}/lessons',
        subject=subject_name,
        year_group=TARGET_YEAR,
        difficulty='normal',
        language='en',
        status='draft',
        created_by=parent_id,
    )
    db.session.add(material)
    db.session.flush()

    total_questions = 0

    for i, lesson_slug in enumerate(lesson_slugs):
        lesson_data = get_lesson_data(programme_slug, unit_slug, lesson_slug)
        if not lesson_data:
            continue

        lesson_title = lesson_data.get('lessonTitle', lesson_slug)
        chunk_content = build_chunk_content(lesson_data)

        chunk = MaterialChunk(
            material_id=material.material_id,
            title=lesson_title,
            content=chunk_content,
            sort_order=i + 1,
        )
        db.session.add(chunk)
        db.session.flush()

        starter_quiz = lesson_data.get('starterQuiz', [])
        exit_quiz = lesson_data.get('exitQuiz', [])

        questions = []
        questions.extend(extract_quiz_questions(starter_quiz, chunk.chunk_id))
        questions.extend(extract_quiz_questions(exit_quiz, chunk.chunk_id))

        for q in questions:
            q.material_id = material.material_id

        db.session.add_all(questions)
        total_questions += len(questions)

    db.session.commit()
    print(f'    -> {material.chunks.count()} chunks, {total_questions} questions')


def import_subject(programme_slug, subject_name, parent_id):
    """1教科分をインポート"""
    print(f'\n{"="*60}')
    print(f'{subject_name} ({programme_slug})')
    print(f'{"="*60}')

    # Year 7 の単元を取得
    units = get_units_from_lessons_page(programme_slug)
    if not units:
        print(f'  No Year {TARGET_YEAR} units found')
        return

    print(f'  Found {len(units)} Year {TARGET_YEAR} units')

    for i, unit_info in enumerate(units):
        if i > 0:
            time.sleep(UNIT_INTERVAL)
        unit_slug = unit_info['slug']
        unit_title = unit_info.get('title', unit_slug.replace('-', ' ').title())
        print(f'\n  [{i+1}/{len(units)}] {unit_title}')
        import_unit(programme_slug, unit_slug, unit_title, subject_name, parent_id)


def main():
    app = create_app()
    with app.app_context():
        from models.parent import Parent
        parent = Parent.query.filter_by(role='admin').first()
        if not parent:
            print('ERROR: No admin account found.')
            sys.exit(1)

        print(f'Importing as: {parent.display_name} (id={parent.parent_id})')
        print(f'Target: Year {TARGET_YEAR}, {len(SUBJECTS)} subjects')
        print(f'Rate limit: {REQUEST_INTERVAL}s/req, {UNIT_INTERVAL}s/unit, {SUBJECT_INTERVAL}s/subject')

        for i, (prog_slug, subj_name) in enumerate(SUBJECTS.items()):
            if i > 0:
                print(f'\n  Waiting {SUBJECT_INTERVAL}s before next subject...')
                time.sleep(SUBJECT_INTERVAL)
            import_subject(prog_slug, subj_name, parent.parent_id)

        # サマリー
        print(f'\n{"="*60}')
        print('IMPORT COMPLETE')
        print(f'{"="*60}')
        from sqlalchemy import func
        summary = db.session.query(
            Material.subject,
            func.count(Material.material_id)
        ).filter_by(year_group=TARGET_YEAR).group_by(Material.subject).all()
        for subj, cnt in sorted(summary):
            print(f'  {subj}: {cnt} units')


if __name__ == '__main__':
    main()
