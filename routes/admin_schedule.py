"""親用スケジュール画面 — 子供ごとの月カレンダー + 学習割当/締切の管理。"""

import calendar
from datetime import date, datetime
from functools import wraps

from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user

from models import db
from models.child import Child
from models.parent import Parent, ParentChild
from models.material import Material, MaterialChunk
from models.schedule import StudyPlan, StudyDeadline
from routes import dual_route

admin_schedule_bp = Blueprint('admin_schedule', __name__)


SUBJECT_COLORS = {
    'Maths': '#6366f1',
    'Science': '#10b981',
    'English': '#f59e0b',
    'Spanish': '#ef4444',
    'History': '#8b5cf6',
    'Geography': '#06b6d4',
    'Computing': '#ec4899',
}


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


def _verify_parent_owns_child(child_id):
    link = ParentChild.query.filter_by(
        parent_id=current_user.parent_id, child_id=child_id
    ).first()
    if not link:
        return None
    return db.session.get(Child, child_id)


def build_month_preview(child_id, year, month):
    """child_detail 用の月サマリ — 教科別集計 + 締切リスト。

    Returns:
        {
            'year': int, 'month': int,
            'plan_total': int, 'plan_done': int,
            'by_subject': [{'subject', 'color', 'total', 'done',
                            'plan_items': [{'title', 'status'}, ...]}],
            'deadlines': [{'id', 'due_date', 'kind', 'title', 'subject', 'done'}],
        }
    """
    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    plans = StudyPlan.query.filter(
        StudyPlan.child_id == child_id,
        StudyPlan.planned_date >= month_start,
        StudyPlan.planned_date <= month_end,
    ).order_by(StudyPlan.planned_date, StudyPlan.id).all()
    deadlines = StudyDeadline.query.filter(
        StudyDeadline.child_id == child_id,
        StudyDeadline.due_date >= month_start,
        StudyDeadline.due_date <= month_end,
    ).order_by(StudyDeadline.due_date, StudyDeadline.id).all()

    # Material titles を一括取得
    mat_ids = {p.material_id for p in plans if p.material_id}
    mat_map = {m.material_id: m.title for m in Material.query.filter(
        Material.material_id.in_(mat_ids)
    ).all()} if mat_ids else {}

    by_subj = {}
    plan_done = 0
    for p in plans:
        key = p.subject or '—'
        slot = by_subj.setdefault(key, {
            'subject': key,
            'color': SUBJECT_COLORS.get(key, '#64748b'),
            'total': 0, 'done': 0, 'plan_items': [],
        })
        slot['total'] += 1
        if p.status == 'done':
            slot['done'] += 1
            plan_done += 1
        title = p.title or mat_map.get(p.material_id) or ''
        slot['plan_items'].append({
            'title': title,
            'status': p.status,
            'material_id': p.material_id,
            'chunk_id': p.chunk_id,
        })

    by_subject = sorted(by_subj.values(), key=lambda x: -x['total'])

    deadline_list = [{
        'id': d.id, 'due_date': d.due_date, 'kind': d.kind,
        'title': d.title, 'subject': d.subject, 'done': d.done,
    } for d in deadlines]

    return {
        'year': year, 'month': month,
        'plan_total': len(plans), 'plan_done': plan_done,
        'by_subject': by_subject,
        'deadlines': deadline_list,
    }


def _build_month_grid(year, month):
    """その月の 7x6 グリッド(日付 or None)を返す。月曜始まり。"""
    cal = calendar.Calendar(firstweekday=0)  # 0=月曜
    weeks = cal.monthdatescalendar(year, month)
    # 必ず 6 週分になるよう埋める
    while len(weeks) < 6:
        last = weeks[-1][-1]
        extra = [last.fromordinal(last.toordinal() + i + 1) for i in range(7)]
        weeks.append(extra)
    return weeks


def _parse_date(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule', methods=['GET'])
@login_required
@parent_required
def admin_schedule(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))

    today = date.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    month_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    month_end = date(year, month, last_day)

    # 前後月のセルも含め 6 週分取得する
    weeks = _build_month_grid(year, month)
    grid_start = weeks[0][0]
    grid_end = weeks[-1][-1]

    plans = StudyPlan.query.filter(
        StudyPlan.child_id == child_id,
        StudyPlan.planned_date >= grid_start,
        StudyPlan.planned_date <= grid_end,
    ).order_by(StudyPlan.planned_date, StudyPlan.id).all()

    deadlines = StudyDeadline.query.filter(
        StudyDeadline.child_id == child_id,
        StudyDeadline.due_date >= grid_start,
        StudyDeadline.due_date <= grid_end,
    ).order_by(StudyDeadline.due_date, StudyDeadline.id).all()

    # Material 情報を一括取得してマップ化
    mat_ids = {p.material_id for p in plans if p.material_id}
    chunk_ids = {p.chunk_id for p in plans if p.chunk_id}
    mat_map = {m.material_id: m for m in Material.query.filter(
        Material.material_id.in_(mat_ids)
    ).all()} if mat_ids else {}
    chunk_map = {c.chunk_id: c for c in MaterialChunk.query.filter(
        MaterialChunk.chunk_id.in_(chunk_ids)
    ).all()} if chunk_ids else {}

    # 日付 -> {plans, deadlines} に整理
    by_date = {}
    for p in plans:
        by_date.setdefault(p.planned_date, {'plans': [], 'deadlines': []})['plans'].append({
            'id': p.id,
            'subject': p.subject,
            'title': p.title or (mat_map.get(p.material_id).title if p.material_id in mat_map else ''),
            'material_id': p.material_id,
            'chunk_id': p.chunk_id,
            'chunk_title': chunk_map.get(p.chunk_id).title if p.chunk_id in chunk_map else None,
            'status': p.status,
            'color': p.color or SUBJECT_COLORS.get(p.subject, '#64748b'),
            'note': p.note,
        })
    for d in deadlines:
        by_date.setdefault(d.due_date, {'plans': [], 'deadlines': []})['deadlines'].append({
            'id': d.id,
            'kind': d.kind,
            'title': d.title,
            'subject': d.subject,
            'material_id': d.material_id,
            'chunk_id': d.chunk_id,
            'done': d.done,
            'color': d.color or ('#dc2626' if d.kind == 'test' else '#f97316'),
            'note': d.note,
        })

    # 月サマリ (教科別割当数)
    summary_by_subject = {}
    plan_count = 0
    for p in plans:
        if month_start <= p.planned_date <= month_end:
            plan_count += 1
            subj = p.subject or '—'
            summary_by_subject.setdefault(subj, {'total': 0, 'done': 0})
            summary_by_subject[subj]['total'] += 1
            if p.status == 'done':
                summary_by_subject[subj]['done'] += 1
    summary_list = sorted(
        [{'subject': s, 'total': v['total'], 'done': v['done'],
          'color': SUBJECT_COLORS.get(s, '#64748b')}
         for s, v in summary_by_subject.items()],
        key=lambda x: -x['total']
    )

    # 未完了 deadline (月内)
    month_deadlines = [d for d in deadlines if month_start <= d.due_date <= month_end]

    # Material 選択用データ (subject -> list of {id, title, chunks: [...]})
    # この子の学年の教材に限定
    year_group = (child.grade or 7)
    materials_all = Material.query.filter_by(
        status='published', year_group=year_group
    ).order_by(
        Material.subject, Material.sort_order, Material.title
    ).all()
    chunks_all = MaterialChunk.query.order_by(
        MaterialChunk.material_id, MaterialChunk.sort_order
    ).all()
    chunks_by_mat = {}
    for c in chunks_all:
        chunks_by_mat.setdefault(c.material_id, []).append({
            'chunk_id': c.chunk_id, 'title': c.title,
        })
    materials_by_subject = {}
    for m in materials_all:
        materials_by_subject.setdefault(m.subject, []).append({
            'material_id': m.material_id,
            'title': m.title,
            'chunks': chunks_by_mat.get(m.material_id, []),
        })

    # ナビ
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    weekday_labels_key = ['day_mon', 'day_tue', 'day_wed', 'day_thu', 'day_fri', 'day_sat', 'day_sun']

    return render_template(
        'admin/child_schedule.html',
        child=child,
        year=year,
        month=month,
        today=today,
        weeks=weeks,
        month_start=month_start,
        month_end=month_end,
        by_date=by_date,
        summary=summary_list,
        plan_count=plan_count,
        month_deadlines=month_deadlines,
        materials_by_subject=materials_by_subject,
        subject_colors=SUBJECT_COLORS,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
        weekday_labels_key=weekday_labels_key,
    )


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/plans/add', methods=['POST'])
@login_required
@parent_required
def admin_schedule_plan_add(child_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))

    planned_date = _parse_date(request.form.get('planned_date'))
    if not planned_date:
        flash('invalid_date', 'error')
        return redirect(_lang_url(f'/admin/children/{child_id}/schedule'))

    subject = request.form.get('subject') or None
    material_id = request.form.get('material_id') or None
    chunk_id = request.form.get('chunk_id') or None
    title = (request.form.get('title') or '').strip() or None
    note = (request.form.get('note') or '').strip() or None

    plan = StudyPlan(
        child_id=child_id,
        planned_date=planned_date,
        subject=subject,
        material_id=int(material_id) if material_id else None,
        chunk_id=int(chunk_id) if chunk_id else None,
        title=title,
        note=note,
        created_by=current_user.parent_id,
    )
    db.session.add(plan)
    db.session.commit()
    flash('schedule_plan_added', 'success')
    return redirect(_lang_url(
        f'/admin/children/{child_id}/schedule?year={planned_date.year}&month={planned_date.month}'
    ))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/plans/<int:plan_id>/edit',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_plan_edit(child_id, plan_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    plan = StudyPlan.query.filter_by(id=plan_id, child_id=child_id).first_or_404()

    new_date = _parse_date(request.form.get('planned_date'))
    if not new_date:
        flash('invalid_date', 'error')
        y, m = plan.planned_date.year, plan.planned_date.month
        return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))

    plan.planned_date = new_date
    plan.subject = request.form.get('subject') or None
    material_id = request.form.get('material_id') or None
    chunk_id = request.form.get('chunk_id') or None
    plan.material_id = int(material_id) if material_id else None
    plan.chunk_id = int(chunk_id) if chunk_id else None
    plan.title = (request.form.get('title') or '').strip() or None
    plan.note = (request.form.get('note') or '').strip() or None

    db.session.commit()
    flash('schedule_plan_updated', 'success')
    return redirect(_lang_url(
        f'/admin/children/{child_id}/schedule?year={new_date.year}&month={new_date.month}'
    ))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/plans/<int:plan_id>/delete',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_plan_delete(child_id, plan_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    plan = StudyPlan.query.filter_by(id=plan_id, child_id=child_id).first_or_404()
    y, m = plan.planned_date.year, plan.planned_date.month
    db.session.delete(plan)
    db.session.commit()
    flash('schedule_plan_deleted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/plans/<int:plan_id>/status',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_plan_status(child_id, plan_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    plan = StudyPlan.query.filter_by(id=plan_id, child_id=child_id).first_or_404()
    new_status = request.form.get('status', 'planned')
    if new_status in ('planned', 'done', 'skipped'):
        plan.status = new_status
        db.session.commit()
    y, m = plan.planned_date.year, plan.planned_date.month
    return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/deadlines/add',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_deadline_add(child_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))

    due_date = _parse_date(request.form.get('due_date'))
    title = (request.form.get('title') or '').strip()
    if not due_date or not title:
        flash('invalid_input', 'error')
        return redirect(_lang_url(f'/admin/children/{child_id}/schedule'))

    kind = request.form.get('kind', 'other')
    if kind not in ('test', 'homework', 'other'):
        kind = 'other'
    subject = request.form.get('subject') or None
    note = (request.form.get('note') or '').strip() or None

    # homework kind では material_id / chunk_id を受け取り、assignment play にリンク
    material_id = request.form.get('material_id') or None
    chunk_id = request.form.get('chunk_id') or None
    if kind != 'homework':
        material_id = None
        chunk_id = None

    dl = StudyDeadline(
        child_id=child_id,
        due_date=due_date,
        kind=kind,
        title=title,
        subject=subject,
        material_id=int(material_id) if material_id else None,
        chunk_id=int(chunk_id) if chunk_id else None,
        note=note,
        created_by=current_user.parent_id,
    )
    db.session.add(dl)
    db.session.commit()
    flash('schedule_deadline_added', 'success')
    return redirect(_lang_url(
        f'/admin/children/{child_id}/schedule?year={due_date.year}&month={due_date.month}'
    ))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/deadlines/<int:dl_id>/edit',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_deadline_edit(child_id, dl_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    dl = StudyDeadline.query.filter_by(id=dl_id, child_id=child_id).first_or_404()

    new_date = _parse_date(request.form.get('due_date'))
    title = (request.form.get('title') or '').strip()
    if not new_date or not title:
        flash('invalid_input', 'error')
        y, m = dl.due_date.year, dl.due_date.month
        return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))

    kind = request.form.get('kind', 'other')
    if kind not in ('test', 'homework', 'other'):
        kind = 'other'
    dl.due_date = new_date
    dl.kind = kind
    dl.title = title
    dl.subject = request.form.get('subject') or None
    dl.note = (request.form.get('note') or '').strip() or None

    db.session.commit()
    flash('schedule_deadline_updated', 'success')
    return redirect(_lang_url(
        f'/admin/children/{child_id}/schedule?year={new_date.year}&month={new_date.month}'
    ))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/deadlines/<int:dl_id>/delete',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_deadline_delete(child_id, dl_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    dl = StudyDeadline.query.filter_by(id=dl_id, child_id=child_id).first_or_404()
    y, m = dl.due_date.year, dl.due_date.month
    db.session.delete(dl)
    db.session.commit()
    flash('schedule_deadline_deleted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))


@dual_route(admin_schedule_bp, '/admin/children/<int:child_id>/schedule/deadlines/<int:dl_id>/toggle',
            methods=['POST'])
@login_required
@parent_required
def admin_schedule_deadline_toggle(child_id, dl_id):
    if not _verify_parent_owns_child(child_id):
        flash('forbidden', 'error')
        return redirect(_lang_url('/admin/children'))
    dl = StudyDeadline.query.filter_by(id=dl_id, child_id=child_id).first_or_404()
    dl.done = not dl.done
    db.session.commit()
    y, m = dl.due_date.year, dl.due_date.month
    return redirect(_lang_url(f'/admin/children/{child_id}/schedule?year={y}&month={m}'))
