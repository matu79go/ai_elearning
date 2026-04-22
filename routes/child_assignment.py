"""子供用の宿題（Assignment）プレイ画面。

chunk単位と material単位の両方に対応。既存の quiz.html を再利用する。
"""
from flask import Blueprint, render_template, abort, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.material import (
    Material, MaterialChunk, Question, QuestionMastery,
    LearningSession, AnswerHistory,
)
from routes import dual_route
from config import ASSIGNMENT_QUESTIONS_PER_SESSION
from datetime import datetime
import random

child_assignment_bp = Blueprint('child_assignment', __name__)


def _is_child():
    return hasattr(current_user, 'child_id')


def _pick_session(pool: list, child_id: int, limit: int) -> list:
    """プールから1セッション分(最大limit問)を選ぶ。
    未マスタリーを優先 → 足りなければマスタリー済みも補充。
    結果はランダム順。「もう一度」で別の組合せが出やすい。"""
    if not pool or len(pool) <= limit:
        random.shuffle(pool)
        return pool

    qids = [q.question_id for q in pool]
    mastered_ids = set(r.question_id for r in QuestionMastery.query.filter(
        QuestionMastery.child_id == child_id,
        QuestionMastery.question_id.in_(qids),
        QuestionMastery.mastered == True,
    ).all())

    unmastered = [q for q in pool if q.question_id not in mastered_ids]
    mastered = [q for q in pool if q.question_id in mastered_ids]

    picks = []
    if len(unmastered) >= limit:
        picks = random.sample(unmastered, limit)
    else:
        picks = list(unmastered)
        need = limit - len(picks)
        if mastered and need > 0:
            picks += random.sample(mastered, min(need, len(mastered)))
    random.shuffle(picks)
    return picks


def _assignment_questions_for_chunk(chunk_id: int):
    """特定chunkのassignment問題プール (全件)。"""
    return Question.query.filter_by(
        chunk_id=chunk_id, is_assignment=True,
    ).all()


def _assignment_questions_for_material(material_id: int):
    """materialに属する全chunkのassignment問題プール (全件)。"""
    chunks = MaterialChunk.query.filter_by(material_id=material_id)\
        .order_by(MaterialChunk.sort_order).all()
    all_questions = []
    for ch in chunks:
        qs = Question.query.filter_by(chunk_id=ch.chunk_id, is_assignment=True).all()
        all_questions.extend(qs)
    return all_questions


def _assignment_questions_for_subject(subject: str, year_group: int):
    """subject + year_group全体のassignment問題プール (全件)。"""
    materials = Material.query.filter_by(
        subject=subject, year_group=year_group, status='published',
    ).order_by(Material.sort_order, Material.title).all()
    all_questions = []
    for m in materials:
        all_questions.extend(_assignment_questions_for_material(m.material_id))
    return all_questions


# ---- chunk単位の宿題 ----
@dual_route(child_assignment_bp, '/child/chunks/<int:chunk_id>/assignment', methods=['GET'])
@login_required
def child_chunk_assignment(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    pool = _assignment_questions_for_chunk(chunk_id)
    questions = _pick_session(pool, current_user.child_id, ASSIGNMENT_QUESTIONS_PER_SESSION)

    # マスタリー (points 獲得履歴)
    mastery_map = {}
    if questions:
        masteries = QuestionMastery.query.filter(
            QuestionMastery.question_id.in_([q.question_id for q in questions]),
            QuestionMastery.child_id == current_user.child_id,
        ).all()
        for m in masteries:
            mastery_map[m.question_id] = m

    return render_template('child/quiz.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map,
                           is_assignment=True)


# ---- material単位の宿題（全chunk横断） ----
@dual_route(child_assignment_bp, '/child/materials/<int:material_id>/assignment', methods=['GET'])
@login_required
def child_material_assignment(material_id):
    if not _is_child():
        abort(403)
    material = Material.query.get_or_404(material_id)

    pool = _assignment_questions_for_material(material_id)
    questions = _pick_session(pool, current_user.child_id, ASSIGNMENT_QUESTIONS_PER_SESSION)
    if not questions:
        # 宿題問題がない場合は material の最初のchunkにリダイレクト
        from flask import redirect
        from app import lang_url
        return redirect(lang_url(f'/child/section/{material_id}'))

    mastery_map = {}
    if questions:
        masteries = QuestionMastery.query.filter(
            QuestionMastery.question_id.in_([q.question_id for q in questions]),
            QuestionMastery.child_id == current_user.child_id,
        ).all()
        for m in masteries:
            mastery_map[m.question_id] = m

    # template は material全体をあらわす「仮想chunk」として、最初のchunkをchunk引数に渡す
    # (submit先のチェック関数が chunk_id を使うため)
    first_chunk = MaterialChunk.query.filter_by(material_id=material_id)\
        .order_by(MaterialChunk.sort_order).first()

    return render_template('child/quiz.html',
                           chunk=first_chunk, material=material,
                           questions=questions, mastery_map=mastery_map,
                           is_assignment=True, assignment_scope='material')


# ---- subject単位の宿題（全material横断） ----
@dual_route(child_assignment_bp, '/child/subjects/<subject>/assignment', methods=['GET'])
@login_required
def child_subject_assignment(subject):
    if not _is_child():
        abort(403)
    year_group = getattr(current_user, 'grade', None) or 7

    pool = _assignment_questions_for_subject(subject, year_group)
    questions = _pick_session(pool, current_user.child_id, ASSIGNMENT_QUESTIONS_PER_SESSION)
    if not questions:
        from flask import redirect
        from app import lang_url
        return redirect(lang_url(f'/child/subjects/{subject}'))

    # 最初のquestionのchunk/materialを「代表」として渡す
    first_q = questions[0]
    first_chunk = MaterialChunk.query.get(first_q.chunk_id)
    first_material = Material.query.get(first_q.material_id)

    mastery_map = {}
    masteries = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
    ).all()
    for m in masteries:
        mastery_map[m.question_id] = m

    return render_template('child/quiz.html',
                           chunk=first_chunk, material=first_material,
                           questions=questions, mastery_map=mastery_map,
                           is_assignment=True, assignment_scope='material',
                           subject_label=subject)


# ---- 宿題の一括採点 (material横断対応) ----
@dual_route(child_assignment_bp, '/child/assignment/check', methods=['POST'])
@login_required
def child_assignment_check():
    """material横断の宿題をまとめて採点するAPI。
    既存の /child/quiz/<cid>/check は chunk_id 単一前提なのでこちらを使う。"""
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json()
    material_id = data.get('material_id')
    answer_list = data.get('answers', [])
    skipped_ids = data.get('skipped_ids', [])

    material = Material.query.get_or_404(material_id)

    session = LearningSession(
        child_id=current_user.child_id,
        material_id=material_id,
    )
    db.session.add(session)
    db.session.flush()

    results = []
    total_correct = 0
    total_points = 0

    # skipped の情報
    for qid in skipped_ids:
        q = Question.query.get(qid)
        if not q or not q.is_assignment:
            continue
        if q.question_type == 'multiple_choice' and q.options:
            correct_labels = [l.strip() for l in (q.correct_answer or '').split(',')]
            parts = []
            for cl in correct_labels:
                ct = next((opt['text'] for opt in q.options if opt['label'] == cl), '')
                parts.append(f"{cl}) {ct}" if ct else cl)
            display_answer = ', '.join(parts)
        else:
            display_answer = (q.correct_answer or '').strip() or (q.reference_answer or '').strip()
        results.append({
            'question_id': qid,
            'correct': True,
            'correct_answer': display_answer,
            'explanation': q.explanation or '',
            'points_earned': 0,
        })

    for ans in answer_list:
        q = Question.query.get(ans.get('question_id'))
        if not q or not q.is_assignment:
            continue

        user_answer = (ans.get('answer') or '').strip()
        is_correct = False
        display_answer = ''

        if q.question_type == 'multiple_choice':
            correct_labels = sorted([l.strip().upper() for l in (q.correct_answer or '').split(',') if l.strip()])
            user_labels = sorted([l.strip().upper() for l in user_answer.split(',') if l.strip()])
            is_correct = user_labels == correct_labels
            parts = []
            for cl in correct_labels:
                ct = next((opt['text'] for opt in (q.options or []) if opt['label'] == cl), '')
                parts.append(f"{cl}) {ct}" if ct else cl)
            display_answer = ', '.join(parts)
        else:
            is_correct = user_answer.lower() == (q.correct_answer or '').strip().lower()
            display_answer = (q.correct_answer or '').strip() or (q.reference_answer or '').strip()

        # マスタリー更新 (既存quizと共通: 初めて正解した時のみ +1pt)
        mastery = QuestionMastery.query.filter_by(
            child_id=current_user.child_id,
            question_id=q.question_id,
        ).first()
        if not mastery:
            mastery = QuestionMastery(
                child_id=current_user.child_id,
                question_id=q.question_id,
            )
            db.session.add(mastery)
        mastery.attempts = (mastery.attempts or 0) + 1

        points_earned = 0
        if is_correct:
            total_correct += 1
            if not mastery.mastered:
                mastery.mastered = True
                mastery.mastered_at = datetime.utcnow()
                points_earned = 1
                total_points += 1
                current_user.total_points += 1

        ah = AnswerHistory(
            session_id=session.session_id,
            question_id=q.question_id,
            child_id=current_user.child_id,
            user_answer=user_answer[:10],  # schema: varchar(10)
            is_correct=is_correct,
            points_earned=points_earned,
        )
        db.session.add(ah)

        results.append({
            'question_id': q.question_id,
            'correct': is_correct,
            'correct_answer': display_answer,
            'explanation': q.explanation or '',
            'points_earned': points_earned,
        })

    session.completed_at = datetime.utcnow()
    session.correct_answers = total_correct
    session.total_questions = len(answer_list)
    session.total_points_earned = total_points
    # レベル自動更新 (100pt毎)
    current_user.level = current_user.total_points // 100 + 1
    db.session.commit()

    return jsonify({
        'results': results,
        'total_correct': total_correct,
        'total_answered': len(answer_list),
        'total_skipped': len(skipped_ids),
        'total_points': total_points,
    })
