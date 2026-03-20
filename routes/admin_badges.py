"""Admin バッジ管理"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.parent import Parent
from models.badge import Badge, ChildBadge
from routes import dual_route

admin_badges_bp = Blueprint('admin_badges', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


def parent_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, Parent):
            return redirect(_lang_url('/child/dashboard'))
        return f(*args, **kwargs)
    return decorated


@dual_route(admin_badges_bp, '/admin/badges')
@login_required
@parent_required
def admin_badges():
    badges = Badge.query.order_by(Badge.condition_type, Badge.condition_value).all()

    # condition_type ごとにグループ化
    groups = {}
    for b in badges:
        ct = b.condition_type
        if ct not in groups:
            groups[ct] = []
        groups[ct].append(b)

    return render_template('admin/badges.html', badges=badges, groups=groups)


@dual_route(admin_badges_bp, '/admin/badges/add', methods=['POST'])
@login_required
@parent_required
def admin_badges_add():
    ct = request.form.get('condition_type', '').strip()
    cv = int(request.form.get('condition_value', 0))
    name_en = request.form.get('name_en', '').strip()
    name_ja = request.form.get('name_ja', '').strip()
    desc_en = request.form.get('description_en', '').strip()
    desc_ja = request.form.get('description_ja', '').strip()
    icon = request.form.get('icon', 'fa-award').strip()
    color = request.form.get('color', '#6366f1').strip()

    if not ct or cv <= 0 or not name_en:
        flash('badge_invalid', 'error')
        return redirect(_lang_url('/admin/badges'))

    badge = Badge(
        name_en=name_en, name_ja=name_ja or name_en,
        description_en=desc_en, description_ja=desc_ja or desc_en,
        icon=icon, color=color,
        condition_type=ct, condition_value=cv,
    )
    db.session.add(badge)
    db.session.commit()
    flash('badge_added', 'success')
    return redirect(_lang_url('/admin/badges'))


@dual_route(admin_badges_bp, '/admin/badges/<int:badge_id>/delete', methods=['POST'])
@login_required
@parent_required
def admin_badges_delete(badge_id):
    badge = Badge.query.get_or_404(badge_id)
    # 関連する獲得記録も削除
    ChildBadge.query.filter_by(badge_id=badge_id).delete()
    db.session.delete(badge)
    db.session.commit()
    flash('badge_deleted', 'success')
    return redirect(_lang_url('/admin/badges'))
