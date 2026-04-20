"""子供用スケジュール画面 — 月カレンダー表示 (読み取り + ステータス切替)。"""

import calendar
from datetime import date
from functools import wraps

from flask import Blueprint, render_template, request, redirect, abort
from flask_login import login_required, current_user

from models import db
from models.child import Child
from models.material import Material, MaterialChunk
from models.schedule import StudyPlan, StudyDeadline
from routes import dual_route
from routes.admin_schedule import SUBJECT_COLORS, _build_month_grid

child_schedule_bp = Blueprint('child_schedule', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


def _is_child():
    return hasattr(current_user, 'child_id')


@dual_route(child_schedule_bp, '/child/schedule', methods=['GET'])
@login_required
def child_schedule():
    if not _is_child():
        abort(403)
    child_id = current_user.child_id

    today = date.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    month_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    month_end = date(year, month, last_day)

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

    mat_ids = {p.material_id for p in plans if p.material_id}
    mat_map = {m.material_id: m for m in Material.query.filter(
        Material.material_id.in_(mat_ids)
    ).all()} if mat_ids else {}
    chunk_ids = {p.chunk_id for p in plans if p.chunk_id}
    chunk_map = {c.chunk_id: c for c in MaterialChunk.query.filter(
        MaterialChunk.chunk_id.in_(chunk_ids)
    ).all()} if chunk_ids else {}

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
            'done': d.done,
            'color': d.color or ('#dc2626' if d.kind == 'test' else '#f97316'),
            'note': d.note,
        })

    # 月サマリ
    summary = {}
    plan_count = 0
    done_count = 0
    for p in plans:
        if month_start <= p.planned_date <= month_end:
            plan_count += 1
            if p.status == 'done':
                done_count += 1
            subj = p.subject or '—'
            summary.setdefault(subj, {'total': 0, 'done': 0,
                                      'color': SUBJECT_COLORS.get(subj, '#64748b')})
            summary[subj]['total'] += 1
            if p.status == 'done':
                summary[subj]['done'] += 1
    summary_list = sorted(
        [{'subject': s, **v} for s, v in summary.items()],
        key=lambda x: -x['total']
    )

    month_deadlines = [d for d in deadlines if month_start <= d.due_date <= month_end]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template(
        'child/schedule.html',
        year=year, month=month, today=today,
        weeks=weeks, by_date=by_date,
        summary=summary_list, plan_count=plan_count, done_count=done_count,
        month_deadlines=month_deadlines,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
    )


@dual_route(child_schedule_bp, '/child/schedule/plans/<int:plan_id>/done', methods=['POST'])
@login_required
def child_schedule_plan_done(plan_id):
    if not _is_child():
        abort(403)
    plan = StudyPlan.query.filter_by(
        id=plan_id, child_id=current_user.child_id
    ).first_or_404()
    new_status = request.form.get('status', 'done')
    if new_status in ('planned', 'done', 'skipped'):
        plan.status = new_status
        db.session.commit()
    y, m = plan.planned_date.year, plan.planned_date.month
    return redirect(_lang_url(f'/child/schedule?year={y}&month={m}'))


@dual_route(child_schedule_bp, '/child/schedule/deadlines/<int:dl_id>/toggle', methods=['POST'])
@login_required
def child_schedule_deadline_toggle(dl_id):
    if not _is_child():
        abort(403)
    dl = StudyDeadline.query.filter_by(
        id=dl_id, child_id=current_user.child_id
    ).first_or_404()
    dl.done = not dl.done
    db.session.commit()
    y, m = dl.due_date.year, dl.due_date.month
    return redirect(_lang_url(f'/child/schedule?year={y}&month={m}'))
