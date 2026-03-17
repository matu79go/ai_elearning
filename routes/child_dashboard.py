from flask import Blueprint, render_template, abort, redirect, request, jsonify
from flask_login import login_required, current_user
from routes import dual_route
from models import db
from models.material import Material, MaterialChunk, Question, QuestionMastery

child_dashboard_bp = Blueprint('child_dashboard', __name__)

YEAR_GROUP = 7


@dual_route(child_dashboard_bp, '/child/dashboard')
@login_required
def child_dashboard():
    if not hasattr(current_user, 'child_id'):
        abort(403)

    from sqlalchemy import func

    # 教科一覧（published に限定しない — 全教科を表示）
    subjects_raw = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('unit_count'),
    ).filter_by(
        year_group=YEAR_GROUP,
    ).group_by(Material.subject).order_by(Material.subject).all()

    subjects_data = []
    for subj, unit_count in subjects_raw:
        # この教科の全問題数とマスタリー数
        total_q = db.session.query(func.count(Question.question_id)).join(
            Material, Question.material_id == Material.material_id
        ).filter(
            Material.subject == subj,
            Material.year_group == YEAR_GROUP,
            Material.status == 'published',
        ).scalar() or 0

        mastered_q = 0
        if total_q > 0:
            mastered_q = db.session.query(func.count(QuestionMastery.id)).join(
                Question, QuestionMastery.question_id == Question.question_id
            ).join(
                Material, Question.material_id == Material.material_id
            ).filter(
                Material.subject == subj,
                Material.year_group == YEAR_GROUP,
                Material.status == 'published',
                QuestionMastery.child_id == current_user.child_id,
                QuestionMastery.mastered == True,
            ).scalar() or 0

        pct = int(mastered_q / total_q * 100) if total_q > 0 else 0

        # 次にやるべきセクション（最初の未完了チャンク）
        next_section = _find_next_section(subj, current_user.child_id)

        # 最終学習日時（この教科の最新mastery更新）
        last_activity = None
        if mastered_q > 0:
            last_activity = db.session.query(func.max(QuestionMastery.updated_at)).join(
                Question, QuestionMastery.question_id == Question.question_id
            ).join(
                Material, Question.material_id == Material.material_id
            ).filter(
                Material.subject == subj,
                Material.year_group == YEAR_GROUP,
                QuestionMastery.child_id == current_user.child_id,
            ).scalar()

        subjects_data.append({
            'name': subj,
            'unit_count': unit_count,
            'total': total_q,
            'mastered': mastered_q,
            'pct': pct,
            'next_section': next_section,
            'last_activity': last_activity,
        })

    # ソート: 進行中（0<pct<100）を最終学習日時降順で上に、次に未着手、最後に完了
    from datetime import datetime
    def sort_key(sd):
        in_progress = 0 < sd['pct'] < 100
        has_started = sd['mastered'] > 0
        last = sd['last_activity'] or datetime.min
        # 優先: 進行中(最新順) → 未着手 → 完了(最新順)
        if in_progress:
            return (0, -last.timestamp())
        elif not has_started and sd['total'] > 0:
            return (1, sd['name'])
        elif sd['pct'] == 100:
            return (3, -last.timestamp())
        else:
            return (2, sd['name'])

    subjects_data.sort(key=sort_key)

    return render_template('child/dashboard.html', subjects_data=subjects_data)


@dual_route(child_dashboard_bp, '/child/profile')
@login_required
def child_profile():
    if not hasattr(current_user, 'child_id'):
        abort(403)

    from sqlalchemy import func
    from collections import OrderedDict

    # 全問題 + マスタリー状態を一括取得
    rows = db.session.query(
        Material.subject,
        Material.material_id,
        Material.title.label('material_title'),
        MaterialChunk.chunk_id,
        MaterialChunk.title.label('chunk_title'),
        MaterialChunk.sort_order,
        func.count(Question.question_id).label('total'),
        func.sum(db.case(
            (db.and_(QuestionMastery.mastered == True,
                     QuestionMastery.child_id == current_user.child_id), 1),
            else_=0,
        )).label('mastered'),
    ).join(MaterialChunk, MaterialChunk.material_id == Material.material_id
    ).join(Question, Question.chunk_id == MaterialChunk.chunk_id
    ).outerjoin(QuestionMastery, db.and_(
        QuestionMastery.question_id == Question.question_id,
        QuestionMastery.child_id == current_user.child_id,
    )).filter(
        Material.status == 'published',
        Material.year_group == YEAR_GROUP,
    ).group_by(
        Material.subject, Material.material_id, MaterialChunk.chunk_id,
    ).order_by(
        Material.subject, Material.title, MaterialChunk.sort_order,
    ).all()

    # 階層構造に組み立て
    subjects = OrderedDict()
    total_all = 0
    mastered_all = 0

    for r in rows:
        t = r.total
        m = int(r.mastered or 0)
        total_all += t
        mastered_all += m

        if r.subject not in subjects:
            subjects[r.subject] = {'materials': OrderedDict(), 'total': 0, 'mastered': 0}
        subj = subjects[r.subject]
        subj['total'] += t
        subj['mastered'] += m

        if r.material_id not in subj['materials']:
            subj['materials'][r.material_id] = {
                'title': r.material_title, 'chunks': [],
                'total': 0, 'mastered': 0,
            }
        mat = subj['materials'][r.material_id]
        mat['total'] += t
        mat['mastered'] += m
        mat['chunks'].append({
            'chunk_id': r.chunk_id,
            'title': r.chunk_title,
            'total': t,
            'mastered': m,
            'pct': round(m / t * 100) if t > 0 else 0,
        })

    return render_template('child/profile.html',
                           subjects=subjects,
                           total_all=total_all,
                           mastered_all=mastered_all)


AVATAR_MAP = {
    'boy1': '👦', 'boy2': '🧑', 'girl1': '👧', 'girl2': '👩',
    'cat': '🐱', 'dog': '🐶', 'fox': '🦊', 'panda': '🐼',
}


@dual_route(child_dashboard_bp, '/child/profile/avatar', methods=['POST'])
@login_required
def child_profile_avatar():
    if not hasattr(current_user, 'child_id'):
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json()
    avatar_key = data.get('avatar', '')

    if avatar_key not in AVATAR_MAP:
        return jsonify({'error': 'invalid'}), 400

    current_user.avatar = avatar_key
    db.session.commit()

    return jsonify({'ok': True, 'emoji': AVATAR_MAP[avatar_key]})


def _find_next_section(subject, child_id):
    """教科内で最初の未完了セクションを返す"""
    materials = Material.query.filter_by(
        subject=subject, year_group=YEAR_GROUP, status='published'
    ).order_by(Material.sort_order, Material.title).all()

    for m in materials:
        chunks = MaterialChunk.query.filter_by(
            material_id=m.material_id
        ).order_by(MaterialChunk.sort_order).all()

        for chunk in chunks:
            total = Question.query.filter_by(chunk_id=chunk.chunk_id).count()
            if total == 0:
                continue
            mastered = QuestionMastery.query.join(Question).filter(
                Question.chunk_id == chunk.chunk_id,
                QuestionMastery.child_id == child_id,
                QuestionMastery.mastered == True,
            ).count()
            if mastered < total:
                return {
                    'chunk_id': chunk.chunk_id,
                    'title': chunk.title,
                    'unit_title': m.title.replace(f'KS3 {subject} - ', ''),
                    'mastered': mastered,
                    'total': total,
                }

    return None  # 全完了
