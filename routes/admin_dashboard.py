from functools import wraps
from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db
from models.parent import Parent, ParentChild
from models.child import Child
from models.material import Question, QuestionMastery
from routes import dual_route

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


def parent_required(f):
    """親ユーザー必須デコレータ — 子供は子供ダッシュボードへリダイレクト"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, Parent):
            return redirect(_lang_url('/child/dashboard'))
        return f(*args, **kwargs)
    return decorated


@dual_route(admin_dashboard_bp, '/admin/dashboard')
@login_required
@parent_required
def admin_dashboard():
    # 子供一覧
    links = ParentChild.query.filter_by(parent_id=current_user.parent_id).all()
    child_ids = [link.child_id for link in links]
    children = Child.query.filter(Child.child_id.in_(child_ids)).all() if child_ids else []

    from routes.admin_children import _build_child_stats

    children_data = []
    total_points = 0
    total_mastered = 0
    for child in children:
        child_stats = _build_child_stats(child.child_id)
        children_data.append({
            'child': child,
            'stats': child_stats,
        })
        total_points += child.total_points
        total_mastered += child_stats['mastered']

    # 集計
    stats = {
        'children_count': len(children),
        'questions_count': Question.query.count(),
        'total_mastered': total_mastered,
        'total_points': total_points,
    }

    return render_template('admin/dashboard.html',
                           children_data=children_data, stats=stats)
