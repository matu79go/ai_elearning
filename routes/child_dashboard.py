from flask import Blueprint, render_template, abort, redirect
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

        subjects_data.append({
            'name': subj,
            'unit_count': unit_count,
            'total': total_q,
            'mastered': mastered_q,
            'pct': pct,
            'next_section': next_section,
        })

    return render_template('child/dashboard.html', subjects_data=subjects_data)


def _find_next_section(subject, child_id):
    """教科内で最初の未完了セクションを返す"""
    materials = Material.query.filter_by(
        subject=subject, year_group=YEAR_GROUP, status='published'
    ).order_by(Material.title).all()

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
