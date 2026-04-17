"""子供用 小テスト (Drill) モード — 1問ずつ即時判定、N連続正解で完了。"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db
from models.material import MaterialChunk, Material, PointHistory
from models.drill import DrillQuestion, DrillSession, DrillAnswerHistory
from models.child import Child
from routes import dual_route
from config import DRILL_STREAK_TO_MASTER, DRILL_COMPLETION_POINTS

child_drill_bp = Blueprint('child_drill', __name__)


def _is_child():
    return hasattr(current_user, 'child_id')


@dual_route(child_drill_bp, '/child/drill/<int:chunk_id>', methods=['GET'])
@login_required
def child_drill(chunk_id):
    """小テスト画面 — pool を全部渡して JS で1問ずつ進行"""
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    drill_questions = DrillQuestion.query.filter_by(
        chunk_id=chunk_id, status='published',
    ).all()

    return render_template(
        'child/drill.html',
        chunk=chunk, material=material,
        drill_questions=drill_questions,
        streak_target=DRILL_STREAK_TO_MASTER,
        completion_points=DRILL_COMPLETION_POINTS,
    )


@dual_route(child_drill_bp, '/child/drill/<int:chunk_id>/start', methods=['POST'])
@login_required
def child_drill_start(chunk_id):
    """新規 DrillSession を作成して session_id を返す"""
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    sess = DrillSession(child_id=current_user.child_id, chunk_id=chunk.chunk_id)
    db.session.add(sess)
    db.session.commit()
    return jsonify({'drill_session_id': sess.drill_session_id})


@dual_route(child_drill_bp, '/child/drill/<int:chunk_id>/answer', methods=['POST'])
@login_required
def child_drill_answer(chunk_id):
    """1問の回答を記録、正誤を返す"""
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json() or {}
    drill_session_id = data.get('drill_session_id')
    drill_question_id = data.get('drill_question_id')
    user_answer = str(data.get('user_answer', '')).strip().upper()
    time_spent = int(data.get('time_spent_seconds', 0))

    sess = DrillSession.query.get_or_404(drill_session_id)
    if sess.child_id != current_user.child_id or sess.chunk_id != chunk_id:
        abort(403)

    q = DrillQuestion.query.get_or_404(drill_question_id)
    if q.chunk_id != chunk_id:
        abort(400)

    is_correct = (user_answer == (q.correct_answer or '').upper())

    hist = DrillAnswerHistory(
        drill_session_id=drill_session_id,
        drill_question_id=drill_question_id,
        child_id=current_user.child_id,
        user_answer=user_answer,
        is_correct=is_correct,
        time_spent_seconds=time_spent,
    )
    db.session.add(hist)

    sess.total_questions = (sess.total_questions or 0) + 1
    if is_correct:
        sess.correct_answers = (sess.correct_answers or 0) + 1

    db.session.commit()

    # UI表示用: 正解ラベル+テキスト
    correct_text = ''
    if q.options:
        for opt in q.options:
            if opt.get('label') == q.correct_answer:
                correct_text = opt.get('text', '')
                break

    return jsonify({
        'is_correct': is_correct,
        'correct_answer': q.correct_answer,
        'correct_text': correct_text,
        'explanation': q.explanation or '',
    })


@dual_route(child_drill_bp, '/child/drill/<int:chunk_id>/complete', methods=['POST'])
@login_required
def child_drill_complete(chunk_id):
    """マスタリー達成 → セッション完了 + ポイント付与"""
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json() or {}
    drill_session_id = data.get('drill_session_id')
    max_streak = int(data.get('max_streak', 0))

    sess = DrillSession.query.get_or_404(drill_session_id)
    if sess.child_id != current_user.child_id or sess.chunk_id != chunk_id:
        abort(403)

    # 二重付与防止
    if sess.mastered:
        return jsonify({
            'already_mastered': True,
            'points_earned': sess.points_earned,
            'total_points': current_user.total_points,
        })

    sess.mastered = True
    sess.completed_at = datetime.now()
    sess.max_streak = max(sess.max_streak or 0, max_streak)
    sess.points_earned = DRILL_COMPLETION_POINTS

    # ポイント付与
    child = Child.query.get(current_user.child_id)
    child.total_points = (child.total_points or 0) + DRILL_COMPLETION_POINTS
    ph = PointHistory(
        child_id=child.child_id,
        points=DRILL_COMPLETION_POINTS,
        reason=f'Mini-test mastered (chunk {chunk_id})',
        reason_type='drill_complete',
    )
    db.session.add(ph)
    db.session.commit()

    return jsonify({
        'mastered': True,
        'points_earned': DRILL_COMPLETION_POINTS,
        'total_points': child.total_points,
        'max_streak': sess.max_streak,
        'total_questions': sess.total_questions,
        'correct_answers': sess.correct_answers,
    })
