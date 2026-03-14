"""子供用学習画面 — 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db
from models.material import Material, MaterialChunk, Question, QuestionMastery
from routes import dual_route
from datetime import datetime

child_learn_bp = Blueprint('child_learn', __name__)

YEAR_GROUP = 7  # 当面 Year 7 固定


def _is_child():
    """子供ユーザーかチェック"""
    return hasattr(current_user, 'child_id')


# ---- 教科選択 ----
@dual_route(child_learn_bp, '/child/subjects', methods=['GET'])
@login_required
def child_subjects():
    if not _is_child():
        abort(403)
    from sqlalchemy import func
    subjects = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('unit_count'),
    ).filter_by(
        year_group=YEAR_GROUP, status='published'
    ).group_by(Material.subject).order_by(Material.subject).all()
    return render_template('child/subjects.html', subjects=subjects)


# ---- 単元一覧 ----
@dual_route(child_learn_bp, '/child/subjects/<subject>', methods=['GET'])
@login_required
def child_units(subject):
    if not _is_child():
        abort(403)
    materials = Material.query.filter_by(
        subject=subject, year_group=YEAR_GROUP, status='published'
    ).order_by(Material.title).all()

    # 各単元のマスタリー進捗を計算
    units_data = []
    for m in materials:
        total_q = m.questions.count()
        mastered_q = QuestionMastery.query.join(Question).filter(
            Question.material_id == m.material_id,
            QuestionMastery.child_id == current_user.child_id,
            QuestionMastery.mastered == True,
        ).count() if total_q > 0 else 0
        units_data.append({
            'material': m,
            'total': total_q,
            'mastered': mastered_q,
        })

    return render_template('child/units.html',
                           subject=subject, units_data=units_data)


# ---- セクション要約 ----
@dual_route(child_learn_bp, '/child/section/<int:chunk_id>', methods=['GET'])
@login_required
def child_section(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    # summary が未生成なら LLM で生成してキャッシュ
    if not chunk.summary and chunk.content:
        chunk.summary = _generate_summary(chunk.content)
        db.session.commit()

    # このセクションの問題のマスタリー進捗
    questions = Question.query.filter_by(chunk_id=chunk_id).all()
    mastered_count = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
        QuestionMastery.mastered == True,
    ).count() if questions else 0

    # content からkey points等を抽出（パース）
    parsed = _parse_chunk_content(chunk.content)

    return render_template('child/section.html',
                           chunk=chunk, material=material, parsed=parsed,
                           total_questions=len(questions), mastered_count=mastered_count)


# ---- クイズ画面 ----
@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>', methods=['GET'])
@login_required
def child_quiz(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)
    questions = Question.query.filter_by(chunk_id=chunk_id).all()

    # 各問題のマスタリー状態を取得
    mastery_map = {}
    masteries = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
    ).all()
    for m in masteries:
        mastery_map[m.question_id] = m

    return render_template('child/quiz.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map)


# ---- 回答送信 (Ajax) ----
@dual_route(child_learn_bp, '/child/quiz/answer', methods=['POST'])
@login_required
def child_quiz_answer():
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer', '').strip()

    question = Question.query.get_or_404(question_id)

    # マスタリーレコードを取得 or 作成
    mastery = QuestionMastery.query.filter_by(
        child_id=current_user.child_id,
        question_id=question_id,
    ).first()
    if not mastery:
        mastery = QuestionMastery(
            child_id=current_user.child_id,
            question_id=question_id,
        )
        db.session.add(mastery)

    mastery.attempts += 1

    # 採点
    is_correct = False
    points_earned = 0

    if question.question_type == 'multiple_choice':
        is_correct = (user_answer.upper() == question.correct_answer.upper())
    elif question.question_type == 'free_response':
        # 簡易マッチ（完全一致 or 部分一致）— 将来LLM採点に置き換え
        correct = question.correct_answer.lower().strip()
        is_correct = (user_answer.lower().strip() == correct)

    # マスタリー更新
    newly_mastered = False
    if is_correct and not mastery.mastered:
        mastery.mastered = True
        mastery.mastered_at = datetime.utcnow()
        points_earned = 1
        newly_mastered = True

        # ポイント加算
        current_user.total_points += points_earned

    db.session.commit()

    return jsonify({
        'correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation or '',
        'points_earned': points_earned,
        'newly_mastered': newly_mastered,
        'already_mastered': mastery.mastered and not newly_mastered,
    })


# ---- ヒント (Ajax) ----
@dual_route(child_learn_bp, '/child/hint/<int:question_id>', methods=['POST'])
@login_required
def child_hint(question_id):
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    question = Question.query.get_or_404(question_id)
    data = request.get_json() or {}
    user_message = data.get('message', '')

    # レベル1: 固定ヒント
    if not user_message:
        if not question.hint:
            return jsonify({'hint': 'Think carefully about what you learned in this section!', 'type': 'fixed'})
        return jsonify({'hint': question.hint, 'type': 'fixed'})

    # レベル2: AIチャット
    try:
        from services.llm import _call_llm
        import os
        model = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')

        prompt = f"""You are a friendly tutor helping a Year 7 student (age 11-12).
The student is working on this question and needs help.

RULES:
- NEVER reveal the answer directly
- Give progressive hints, guiding them to think
- Use simple English appropriate for age 11-12
- Be encouraging and supportive
- Keep your response to 2-3 sentences

Question: {question.question_text}
Student's message: {user_message}"""

        response = _call_llm(prompt, model=model)
        return jsonify({'hint': response, 'type': 'ai'})
    except Exception as e:
        return jsonify({'hint': 'Sorry, I couldn\'t think of a hint right now. Try re-reading the section!', 'type': 'error'})


# ---- 結果画面 ----
@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>/result', methods=['GET'])
@login_required
def child_quiz_result(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)
    questions = Question.query.filter_by(chunk_id=chunk_id).all()

    mastery_map = {}
    masteries = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
    ).all()
    for m in masteries:
        mastery_map[m.question_id] = m

    total = len(questions)
    mastered = sum(1 for m in mastery_map.values() if m.mastered)

    return render_template('child/quiz_result.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map,
                           total=total, mastered=mastered)


# ---- ヘルパー関数 ----

def _generate_summary(content):
    """Transcriptを要約"""
    try:
        from services.llm import _call_llm
        import os
        model = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')

        # Transcript部分を抽出
        marker = '--- Lesson Transcript ---'
        if marker in content:
            transcript = content[content.index(marker) + len(marker):]
        else:
            transcript = content

        # 長すぎる場合は切り詰め
        if len(transcript) > 15000:
            transcript = transcript[:15000]

        prompt = f"""Summarise this lesson content in 3-5 short paragraphs for a Year 7 student (age 11-12).
Use simple, clear English. Focus on the most important concepts.
Do NOT use bullet points. Write in flowing prose.

{transcript}"""

        return _call_llm(prompt, model=model)
    except Exception:
        return None


def _parse_chunk_content(content):
    """チャンク本文からKey Points等を構造化して抽出"""
    result = {
        'learning_outcome': '',
        'key_points': [],
        'keywords': [],
        'misconceptions': [],
    }

    lines = content.split('\n')
    section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('Learning Outcome:'):
            result['learning_outcome'] = line.replace('Learning Outcome:', '').strip()
        elif line == 'Key Learning Points:':
            section = 'kp'
        elif line == 'Key Words:':
            section = 'kw'
        elif line == 'Common Misconceptions:':
            section = 'mc'
        elif line.startswith('--- Lesson Transcript ---'):
            break
        elif section == 'kp' and line.startswith('- '):
            result['key_points'].append(line[2:])
        elif section == 'kw' and line.startswith('- '):
            parts = line[2:].split(': ', 1)
            if len(parts) == 2:
                result['keywords'].append({'word': parts[0], 'definition': parts[1]})
            else:
                result['keywords'].append({'word': parts[0], 'definition': ''})
        elif section == 'mc' and line.startswith('- Misconception:'):
            result['misconceptions'].append({
                'misconception': line.replace('- Misconception:', '').strip(),
                'correction': '',
            })
        elif section == 'mc' and line.startswith('Correction:') and result['misconceptions']:
            result['misconceptions'][-1]['correction'] = line.replace('Correction:', '').strip()

    return result
