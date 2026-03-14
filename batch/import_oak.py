"""
Oak National Academy KS3 Science データ取り込みスクリプト

Usage:
    docker exec elearn_app python batch/import_oak.py

レート制限:
    - リクエスト間隔: 2秒（サーバー負荷軽減）
    - 単元間: 5秒の追加待機
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error

# ---- DB接続 ----
sys.path.insert(0, '/app')
from app import create_app
from models import db
from models.material import Material, MaterialChunk, Question

BASE_URL = 'https://www.thenational.academy'
REQUEST_INTERVAL = 2.0    # リクエスト間隔（秒）
UNIT_INTERVAL = 5.0       # 単元間の追加待機（秒）

# KS3 Science Year 7 の全単元
UNITS = [
    'cells',
    'ecosystems',
    'solutions',
    'forces',
    'solid-liquid-gas-states-and-changes-of-state',
    'solar-system-and-beyond',
    'sound-light-and-vision',
]

PROGRAMME = 'science-secondary-ks3'


def fetch_page(url):
    """URLからHTMLを取得（レート制限付き）"""
    time.sleep(REQUEST_INTERVAL)
    print(f'  GET {url}')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'OakContentImporter/1.0 (personal education project)'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f'  ERROR: HTTP {e.code} for {url}')
        return None
    except Exception as e:
        print(f'  ERROR: {e}')
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


def get_lesson_slugs(unit_slug):
    """単元ページからレッスンslug一覧を取得"""
    url = f'{BASE_URL}/teachers/programmes/{PROGRAMME}/units/{unit_slug}/lessons'
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


def get_lesson_data(unit_slug, lesson_slug):
    """レッスンページから教材データを取得"""
    url = f'{BASE_URL}/teachers/programmes/{PROGRAMME}/units/{unit_slug}/lessons/{lesson_slug}'
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

    # 学習目標
    outcome = lesson_data.get('pupilLessonOutcome', '')
    if outcome:
        parts.append(f'Learning Outcome: {outcome}')

    # Key Learning Points
    klps = lesson_data.get('keyLearningPoints', [])
    if klps:
        parts.append('\nKey Learning Points:')
        for p in klps:
            parts.append(f'- {p["keyLearningPoint"]}')

    # Keywords
    keywords = lesson_data.get('lessonKeywords', [])
    if keywords:
        parts.append('\nKey Words:')
        for k in keywords:
            parts.append(f'- {k["keyword"]}: {k["description"]}')

    # Misconceptions
    misconceptions = lesson_data.get('misconceptionsAndCommonMistakes', [])
    if misconceptions:
        parts.append('\nCommon Misconceptions:')
        for m in misconceptions:
            parts.append(f'- Misconception: {m["misconception"]}')
            parts.append(f'  Correction: {m["response"]}')

    # Transcript（授業の書き起こし）
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

        # 穴埋め部分を [___] に置換
        question_text = question_text.replace('{{}}', '[___]')

        if not question_text:
            continue

        answers = q.get('answers', {})

        # multiple-choice
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

                # answer_is_default=False means it's the correct answer
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
                ))
            continue

        # short-answer (穴埋め)
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
                ))

    return questions


def import_unit(unit_slug, parent_id):
    """1単元分をインポート"""
    print(f'\n{"="*60}')
    print(f'Unit: {unit_slug}')
    print(f'{"="*60}')

    # 既にインポート済みか確認
    existing = Material.query.filter_by(
        title=f'KS3 Science - {unit_slug}',
        created_by=parent_id
    ).first()
    if existing:
        print(f'  SKIP: already imported (material_id={existing.material_id})')
        return

    # レッスン一覧を取得
    lesson_slugs = get_lesson_slugs(unit_slug)
    if not lesson_slugs:
        print(f'  ERROR: No lessons found for {unit_slug}')
        return

    print(f'  Found {len(lesson_slugs)} lessons')

    # マテリアル作成
    unit_title = unit_slug.replace('-', ' ').title()
    material = Material(
        title=f'KS3 Science - {unit_title}',
        description=f'Oak National Academy KS3 Science Year 7: {unit_title} ({len(lesson_slugs)} lessons)',
        source_type='url',
        source_content=f'{BASE_URL}/teachers/programmes/{PROGRAMME}/units/{unit_slug}/lessons',
        subject='Science',
        difficulty='normal',
        language='en',
        status='draft',
        created_by=parent_id,
    )
    db.session.add(material)
    db.session.flush()  # material_id を確定

    total_questions = 0

    # 各レッスンを取得してチャンク+問題を作成
    for i, lesson_slug in enumerate(lesson_slugs):
        print(f'\n  Lesson {i+1}/{len(lesson_slugs)}: {lesson_slug}')
        lesson_data = get_lesson_data(unit_slug, lesson_slug)
        if not lesson_data:
            print(f'    SKIP: could not fetch lesson data')
            continue

        lesson_title = lesson_data.get('lessonTitle', lesson_slug)
        chunk_content = build_chunk_content(lesson_data)

        # チャンク作成
        chunk = MaterialChunk(
            material_id=material.material_id,
            title=lesson_title,
            content=chunk_content,
            sort_order=i + 1,
        )
        db.session.add(chunk)
        db.session.flush()  # chunk_id を確定

        # クイズ問題を取得
        starter_quiz = lesson_data.get('starterQuiz', [])
        exit_quiz = lesson_data.get('exitQuiz', [])

        questions = []
        questions.extend(extract_quiz_questions(starter_quiz, chunk.chunk_id))
        questions.extend(extract_quiz_questions(exit_quiz, chunk.chunk_id))

        for q in questions:
            q.material_id = material.material_id

        db.session.add_all(questions)
        total_questions += len(questions)
        print(f'    -> {lesson_title}: {len(questions)} questions')

    db.session.commit()
    print(f'\n  DONE: material_id={material.material_id}, '
          f'{len(lesson_slugs)} chunks, {total_questions} questions')


def main():
    app = create_app()
    with app.app_context():
        # 管理者アカウントを取得
        from models.parent import Parent
        parent = Parent.query.filter_by(role='admin').first()
        if not parent:
            print('ERROR: No admin account found. Please set role=admin for a parent.')
            sys.exit(1)

        print(f'Importing as parent: {parent.display_name} (id={parent.parent_id})')
        print(f'Rate limit: {REQUEST_INTERVAL}s between requests, {UNIT_INTERVAL}s between units')
        print(f'Units to import: {len(UNITS)}')

        for i, unit_slug in enumerate(UNITS):
            if i > 0:
                print(f'\n  Waiting {UNIT_INTERVAL}s before next unit...')
                time.sleep(UNIT_INTERVAL)
            import_unit(unit_slug, parent.parent_id)

        # 結果サマリー
        print(f'\n{"="*60}')
        print('IMPORT COMPLETE')
        print(f'{"="*60}')
        materials = Material.query.filter_by(created_by=parent.parent_id, subject='Science').all()
        for m in materials:
            chunk_count = m.chunks.count()
            q_count = m.questions.count()
            print(f'  {m.title}: {chunk_count} sections, {q_count} questions [{m.status}]')


if __name__ == '__main__':
    main()
