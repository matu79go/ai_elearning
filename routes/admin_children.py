from functools import wraps
from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case
from models import db
from models.child import Child
from models.parent import Parent, ParentChild, ChildInvite
from models.material import (Material, MaterialChunk, Question, QuestionMastery,
                             LearningSession, AnswerHistory, PointHistory)
from routes import dual_route

admin_children_bp = Blueprint('admin_children', __name__)


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


def _build_child_stats(child_id):
    """子供の教科別進捗データを構築 — その子の学年の教材のみ"""
    child = db.session.get(Child, child_id)
    year_group = (child.grade if child else None) or 7

    # その学年の公開問題の教科別件数
    subject_totals = db.session.query(
        Material.subject,
        func.count(Question.question_id).label('total'),
    ).join(Question, Question.material_id == Material.material_id
    ).filter(
        Material.status == 'published',
        Material.year_group == year_group,
    ).group_by(Material.subject).all()

    subject_total_map = {s.subject: s.total for s in subject_totals}
    all_total = sum(s.total for s in subject_totals)

    # この子供の教科別mastered数 (同じ学年の教材に限る)
    subject_mastered = db.session.query(
        Material.subject,
        func.count(QuestionMastery.id).label('mastered'),
    ).join(Question, QuestionMastery.question_id == Question.question_id
    ).join(Material, Question.material_id == Material.material_id
    ).filter(
        QuestionMastery.child_id == child_id,
        QuestionMastery.mastered == True,
        Material.year_group == year_group,
    ).group_by(Material.subject).all()

    subject_mastered_map = {s.subject: s.mastered for s in subject_mastered}
    all_mastered = sum(s.mastered for s in subject_mastered)

    # 教科別リスト
    subjects = []
    for subj, total in sorted(subject_total_map.items()):
        mastered = subject_mastered_map.get(subj, 0)
        subjects.append({
            'name': subj,
            'total': total,
            'mastered': mastered,
            'pct': round(mastered / total * 100) if total > 0 else 0,
        })

    return {
        'subjects': subjects,
        'total': all_total,
        'mastered': all_mastered,
        'pct': round(all_mastered / all_total * 100) if all_total > 0 else 0,
    }


def _verify_parent_owns_child(child_id):
    """親がこの子供を所有しているか確認。Childオブジェクトを返す。"""
    link = ParentChild.query.filter_by(
        parent_id=current_user.parent_id, child_id=child_id
    ).first()
    if not link:
        return None
    return db.session.get(Child, child_id)


@dual_route(admin_children_bp, '/admin/children', methods=['GET'])
@login_required
@parent_required
def admin_children():
    links = ParentChild.query.filter_by(parent_id=current_user.parent_id).all()
    child_ids = [link.child_id for link in links]
    children = Child.query.filter(Child.child_id.in_(child_ids)).all() if child_ids else []

    children_data = []
    for child in children:
        stats = _build_child_stats(child.child_id)
        children_data.append({
            'child': child,
            'stats': stats,
        })

    return render_template('admin/children.html', children_data=children_data)


@dual_route(admin_children_bp, '/admin/children/add', methods=['POST'])
@login_required
@parent_required
def admin_children_add():
    display_name = request.form.get('display_name', '').strip()
    grade = request.form.get('grade', '')
    pin = request.form.get('pin', '')
    pin_confirm = request.form.get('pin_confirm', '')

    errors = []
    if not display_name or not pin or not grade:
        errors.append('required_fields')
    if pin != pin_confirm:
        errors.append('pin_mismatch')
    if len(pin) != 4 or not pin.isdigit():
        errors.append('pin_must_be_4')

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(_lang_url('/admin/children'))

    child = Child(
        display_name=display_name,
        grade=int(grade) if grade else None,
        created_by=current_user.parent_id
    )
    child.set_pin(pin)
    db.session.add(child)
    db.session.flush()

    link = ParentChild(
        parent_id=current_user.parent_id,
        child_id=child.child_id,
        role='owner'
    )
    db.session.add(link)
    db.session.commit()

    flash('child_added', 'success')
    return redirect(_lang_url('/admin/children'))


@dual_route(admin_children_bp, '/admin/family-code', methods=['POST'])
@login_required
@parent_required
def admin_family_code_update():
    """Family Code を更新（重複チェック付き）"""
    data = request.get_json() or {}
    new_code = data.get('family_code', '').strip().upper()

    if not new_code.isalnum():
        return jsonify({'success': False, 'error': 'Letters and numbers only'}), 400

    if len(new_code) < 5 or len(new_code) > 10:
        return jsonify({'success': False, 'error': 'Code must be 5-10 characters'}), 400

    if new_code == current_user.family_code:
        return jsonify({'success': True, 'family_code': new_code})

    existing = Parent.query.filter_by(family_code=new_code).first()
    if existing:
        return jsonify({'success': False, 'error': 'This code is already taken'}), 409

    current_user.family_code = new_code
    db.session.commit()
    return jsonify({'success': True, 'family_code': new_code})


@dual_route(admin_children_bp, '/admin/children/<int:child_id>/edit', methods=['POST'])
@login_required
@parent_required
def admin_children_edit(child_id):
    """子供情報を更新（JSON API）"""
    child = _verify_parent_owns_child(child_id)
    if not child:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    data = request.get_json() or {}
    display_name = data.get('display_name', '').strip()
    grade = data.get('grade', '')
    pin = data.get('pin', '').strip()
    pin_confirm = data.get('pin_confirm', '').strip()

    if not display_name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    if not grade:
        return jsonify({'success': False, 'error': 'Year is required'}), 400

    if pin:
        if len(pin) != 4 or not pin.isdigit():
            return jsonify({'success': False, 'error': 'PIN must be 4 digits'}), 400
        if pin != pin_confirm:
            return jsonify({'success': False, 'error': 'PIN does not match'}), 400
        child.set_pin(pin)

    child.display_name = display_name
    child.grade = int(grade)
    db.session.commit()
    return jsonify({'success': True})


@dual_route(admin_children_bp, '/admin/children/<int:child_id>/delete', methods=['POST'])
@login_required
@parent_required
def admin_children_delete(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    ParentChild.query.filter_by(child_id=child_id).delete()
    db.session.delete(child)
    db.session.commit()
    flash('child_deleted', 'success')

    return redirect(_lang_url('/admin/children'))


# ---- 子供詳細ページ ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>', methods=['GET'])
@login_required
@parent_required
def admin_children_detail(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    # 階層データ構築: Subject > Material > Chunk > Questions
    # この子の学年の公開教材のみ
    year_group = (child.grade or 7)
    rows = db.session.query(
        Material.subject,
        Material.material_id,
        Material.title.label('material_title'),
        MaterialChunk.chunk_id,
        MaterialChunk.title.label('chunk_title'),
        MaterialChunk.sort_order,
        Question.question_id,
        Question.question_text,
        Question.question_type,
        QuestionMastery.mastered,
        QuestionMastery.attempts,
    ).join(MaterialChunk, MaterialChunk.material_id == Material.material_id
    ).join(Question, Question.chunk_id == MaterialChunk.chunk_id
    ).outerjoin(QuestionMastery, db.and_(
        QuestionMastery.question_id == Question.question_id,
        QuestionMastery.child_id == child_id,
    )).filter(
        Material.status == 'published',
        Material.year_group == year_group,
    ).order_by(
        Material.subject, Material.title,
        MaterialChunk.sort_order, Question.question_id,
    ).all()

    # 階層構造に組み立て
    from collections import OrderedDict
    subjects = OrderedDict()
    total_questions = 0
    total_mastered = 0

    for r in rows:
        total_questions += 1
        is_mastered = bool(r.mastered)
        if is_mastered:
            total_mastered += 1

        if r.subject not in subjects:
            subjects[r.subject] = {'materials': OrderedDict(), 'total': 0, 'mastered': 0}
        subj = subjects[r.subject]
        subj['total'] += 1
        if is_mastered:
            subj['mastered'] += 1

        if r.material_id not in subj['materials']:
            subj['materials'][r.material_id] = {
                'title': r.material_title, 'chunks': OrderedDict(),
                'total': 0, 'mastered': 0,
            }
        mat = subj['materials'][r.material_id]
        mat['total'] += 1
        if is_mastered:
            mat['mastered'] += 1

        if r.chunk_id not in mat['chunks']:
            mat['chunks'][r.chunk_id] = {
                'title': r.chunk_title, 'questions': [],
                'total': 0, 'mastered': 0,
            }
        chunk = mat['chunks'][r.chunk_id]
        chunk['total'] += 1
        if is_mastered:
            chunk['mastered'] += 1
        chunk['questions'].append({
            'id': r.question_id,
            'text': r.question_text,
            'type': r.question_type,
            'mastered': is_mastered,
            'attempts': r.attempts or 0,
        })

    # 紐づいている保護者一覧
    parent_links = db.session.query(ParentChild, Parent).join(
        Parent, Parent.parent_id == ParentChild.parent_id,
    ).filter(ParentChild.child_id == child_id).all()

    # 有効な招待コード
    from datetime import datetime as dt
    active_invite = ChildInvite.query.filter_by(
        child_id=child_id, used_by=None,
    ).filter(ChildInvite.expires_at > dt.utcnow()).first()

    # バッジ情報
    from models.badge import Badge, ChildBadge
    child_badges = ChildBadge.query.filter_by(child_id=child_id).all()
    earned_ids = {cb.badge_id for cb in child_badges}
    earned_map = {cb.badge_id: cb.earned_at for cb in child_badges}
    all_badges = Badge.query.order_by(Badge.condition_type, Badge.condition_value).all()

    # 週間進捗
    from routes.child_dashboard import _get_weekly_progress, _get_monthly_progress
    week_offset = request.args.get('week', 0, type=int)
    weekly = _get_weekly_progress(child_id, week_offset)

    # 月間進捗
    from datetime import date as date_type
    view_year = request.args.get('year', date_type.today().year, type=int)
    view_month = request.args.get('month', date_type.today().month, type=int)
    monthly = _get_monthly_progress(child_id, view_year, view_month)

    # 教科の和集合
    all_activity_subjects = sorted(set(weekly['subjects'] + monthly['subjects']))

    # スケジュールプレビュー (今月 + 来月)
    from routes.admin_schedule import build_month_preview
    today = date_type.today()
    next_m_year = today.year if today.month < 12 else today.year + 1
    next_m_month = today.month + 1 if today.month < 12 else 1
    schedule_this = build_month_preview(child_id, today.year, today.month)
    schedule_next = build_month_preview(child_id, next_m_year, next_m_month)

    return render_template('admin/child_detail.html',
                           child=child, subjects=subjects,
                           total_questions=total_questions,
                           total_mastered=total_mastered,
                           parent_links=parent_links,
                           active_invite=active_invite,
                           all_badges=all_badges, earned_ids=earned_ids,
                           earned_map=earned_map,
                           weekly=weekly, monthly=monthly,
                           all_activity_subjects=all_activity_subjects,
                           schedule_this=schedule_this,
                           schedule_next=schedule_next,
                           schedule_today=today)


# ---- セクション別問題管理ページ ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/section/<int:chunk_id>', methods=['GET'])
@login_required
@parent_required
def admin_children_section(child_id, chunk_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    # このチャンクの問題 + マスタリー状態
    questions = db.session.query(
        Question.question_id,
        Question.question_text,
        Question.question_type,
        QuestionMastery.mastered,
        QuestionMastery.attempts,
    ).outerjoin(QuestionMastery, db.and_(
        QuestionMastery.question_id == Question.question_id,
        QuestionMastery.child_id == child_id,
    )).filter(
        Question.chunk_id == chunk_id,
    ).order_by(Question.question_id).all()

    q_list = []
    mastered_count = 0
    for q in questions:
        is_mastered = bool(q.mastered)
        if is_mastered:
            mastered_count += 1
        q_list.append({
            'id': q.question_id,
            'text': q.question_text,
            'type': q.question_type,
            'mastered': is_mastered,
            'attempts': q.attempts or 0,
        })

    # Q&Aタブ用: 全問題の詳細データ
    full_questions = Question.query.filter_by(chunk_id=chunk_id)\
        .order_by(Question.question_id).all()

    # 全体集計（共通ヘッダー用）
    total_questions = Question.query.join(Material).filter(
        Material.status == 'published').count()
    total_mastered = QuestionMastery.query.filter_by(
        child_id=child_id, mastered=True).count()

    video_url = None
    video_type = None
    if chunk.video_youtube_id:
        video_url = f'https://www.youtube-nocookie.com/embed/{chunk.video_youtube_id}'
        video_type = 'youtube'
    elif chunk.video_drive_id:
        video_url = f'/child/drive-video/{chunk_id}'
        video_type = 'gdrive'

    # Drill + YouTube (material_chunk_detail と同じデータを流用)
    from models.drill import DrillQuestion
    from models.youtube_video import ChunkYoutubeVideo
    from config import DRILL_STREAK_TO_MASTER, DRILL_COMPLETION_POINTS
    from services.math_generator import templates_for_chunk
    rule_templates = [
        {'id': t.id, 'topic': t.topic, 'difficulty': t.difficulty}
        for t in templates_for_chunk(chunk_id)
    ]
    drill_questions = DrillQuestion.query.filter_by(chunk_id=chunk_id)\
        .order_by(DrillQuestion.drill_question_id).all()
    youtube_videos = ChunkYoutubeVideo.query.filter_by(chunk_id=chunk_id)\
        .order_by(ChunkYoutubeVideo.is_primary.desc(), ChunkYoutubeVideo.rank_position).all()

    return render_template('admin/child_section.html',
                           child=child, chunk=chunk, material=material,
                           questions=q_list, full_questions=full_questions,
                           mastered_count=mastered_count,
                           total_questions=total_questions,
                           total_mastered=total_mastered,
                           video_url=video_url, video_type=video_type,
                           rule_templates=rule_templates,
                           drill_questions=drill_questions,
                           drill_streak=DRILL_STREAK_TO_MASTER,
                           drill_points=DRILL_COMPLETION_POINTS,
                           youtube_videos=youtube_videos)


# ---- ポイント編集 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/points', methods=['POST'])
@login_required
@parent_required
def admin_children_points(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    try:
        new_points = int(request.form.get('points', 0))
    except (ValueError, TypeError):
        new_points = 0

    if new_points < 0:
        new_points = 0

    # ポイント差分を記録
    diff = new_points - child.total_points
    if diff != 0:
        history = PointHistory(
            child_id=child_id,
            points=diff,
            reason=request.form.get('reason', 'Manual adjustment').strip() or 'Manual adjustment',
            reason_type='manual_adjust',
        )
        db.session.add(history)

    child.total_points = new_points
    child.level = new_points // 100 + 1  # レベル自動連動
    db.session.commit()
    flash('points_adjusted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- レベル編集 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/level', methods=['POST'])
@login_required
@parent_required
def admin_children_level(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    try:
        new_level = int(request.form.get('level', 1))
    except (ValueError, TypeError):
        new_level = 1
    if new_level < 1:
        new_level = 1

    child.level = new_level
    db.session.commit()
    flash('level_adjusted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- ストリーク編集 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/streak', methods=['POST'])
@login_required
@parent_required
def admin_children_streak(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    try:
        new_streak = int(request.form.get('streak', 0))
    except (ValueError, TypeError):
        new_streak = 0
    if new_streak < 0:
        new_streak = 0

    child.streak_count = new_streak
    db.session.commit()
    flash('streak_adjusted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- 1日の目標設定 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/daily-goal', methods=['POST'])
@login_required
@parent_required
def admin_children_daily_goal(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    try:
        new_goal = int(request.form.get('daily_goal', 10))
    except (ValueError, TypeError):
        new_goal = 10
    if new_goal < 1:
        new_goal = 1
    if new_goal > 100:
        new_goal = 100

    child.daily_goal = new_goal
    db.session.commit()
    flash('daily_goal_adjusted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- バッジ取り消し ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/badges/<int:badge_id>/revoke', methods=['POST'])
@login_required
@parent_required
def admin_children_badge_revoke(child_id, badge_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    from models.badge import ChildBadge
    ChildBadge.query.filter_by(child_id=child_id, badge_id=badge_id).delete()
    db.session.commit()
    flash('badge_revoked', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- バッジ手動付与 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/badges/<int:badge_id>/grant', methods=['POST'])
@login_required
@parent_required
def admin_children_badge_grant(child_id, badge_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    from models.badge import Badge, ChildBadge
    badge = Badge.query.get(badge_id)
    if not badge:
        return redirect(_lang_url(f'/admin/children/{child_id}'))

    existing = ChildBadge.query.filter_by(child_id=child_id, badge_id=badge_id).first()
    if not existing:
        db.session.add(ChildBadge(child_id=child_id, badge_id=badge_id))
        db.session.commit()
    flash('badge_granted', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- バッジ全リセット ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/badges/reset-all', methods=['POST'])
@login_required
@parent_required
def admin_children_badge_reset_all(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    from models.badge import ChildBadge
    count = ChildBadge.query.filter_by(child_id=child_id).delete()
    db.session.commit()
    flash(f'badges_reset:{count}', 'success')
    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- 選択した問題のマスタリーをリセット ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/reset', methods=['POST'])
@login_required
@parent_required
def admin_children_reset(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    question_ids = request.form.getlist('question_ids')
    chunk_id = request.form.get('chunk_id', '')

    if not question_ids:
        flash('no_questions_selected', 'error')
        redirect_url = f'/admin/children/{child_id}/section/{chunk_id}' if chunk_id else f'/admin/children/{child_id}'
        return redirect(_lang_url(redirect_url))

    question_ids = [int(qid) for qid in question_ids]
    deduct_points = request.form.get('deduct_points') == '1'

    # 減算する場合は mastered=True の数だけ減算
    if deduct_points:
        mastered_count = QuestionMastery.query.filter(
            QuestionMastery.child_id == child_id,
            QuestionMastery.question_id.in_(question_ids),
            QuestionMastery.mastered == True,
        ).count()
        child.total_points = max(0, child.total_points - mastered_count)

    # 選択した問題のマスタリーを削除
    reset_count = QuestionMastery.query.filter(
        QuestionMastery.child_id == child_id,
        QuestionMastery.question_id.in_(question_ids),
    ).delete(synchronize_session=False)

    db.session.commit()

    flash(f'questions_reset:{reset_count}', 'success')
    redirect_url = f'/admin/children/{child_id}/section/{chunk_id}' if chunk_id else f'/admin/children/{child_id}'
    return redirect(_lang_url(redirect_url))


# ---- 招待コード生成 ----
@dual_route(admin_children_bp, '/admin/children/<int:child_id>/invite', methods=['POST'])
@login_required
@parent_required
def admin_children_invite(child_id):
    child = _verify_parent_owns_child(child_id)
    if not child:
        return redirect(_lang_url('/admin/children'))

    import secrets
    from datetime import datetime, timedelta

    # 既存の未使用コードがあれば再利用
    existing = ChildInvite.query.filter_by(
        child_id=child_id, used_by=None,
    ).filter(ChildInvite.expires_at > datetime.utcnow()).first()

    if existing:
        flash(f'invite_code:{existing.invite_code}', 'success')
    else:
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        code = ''.join(secrets.choice(alphabet) for _ in range(6))
        invite = ChildInvite(
            invite_code=code,
            child_id=child_id,
            created_by=current_user.parent_id,
            expires_at=datetime.utcnow() + timedelta(hours=48),
        )
        db.session.add(invite)
        db.session.commit()
        flash(f'invite_code:{code}', 'success')

    return redirect(_lang_url(f'/admin/children/{child_id}'))


# ---- 招待コード受理 ----
@dual_route(admin_children_bp, '/admin/accept-invite', methods=['POST'])
@login_required
@parent_required
def admin_accept_invite():
    from datetime import datetime

    code = request.form.get('invite_code', '').strip().upper()
    if not code:
        flash('invite_invalid', 'error')
        return redirect(_lang_url('/admin/dashboard'))

    invite = ChildInvite.query.filter_by(
        invite_code=code, used_by=None,
    ).filter(ChildInvite.expires_at > datetime.utcnow()).first()

    if not invite:
        flash('invite_invalid', 'error')
        return redirect(_lang_url('/admin/dashboard'))

    # 既にリンク済みかチェック
    existing_link = ParentChild.query.filter_by(
        parent_id=current_user.parent_id,
        child_id=invite.child_id,
    ).first()

    if existing_link:
        flash('invite_already_linked', 'error')
        return redirect(_lang_url('/admin/dashboard'))

    # リンク作成
    link = ParentChild(
        parent_id=current_user.parent_id,
        child_id=invite.child_id,
        role='caretaker',
    )
    db.session.add(link)

    # 招待を使用済みに
    invite.used_by = current_user.parent_id
    invite.used_at = datetime.utcnow()
    db.session.commit()

    child = Child.query.get(invite.child_id)
    flash(f'invite_accepted:{child.display_name}', 'success')
    return redirect(_lang_url('/admin/dashboard'))
