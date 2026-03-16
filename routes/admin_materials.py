from functools import wraps
from flask import Blueprint, render_template, request, redirect, flash, abort
from flask_login import login_required, current_user
from models import db
from models.material import Material, MaterialChunk, Question
from routes import dual_route

admin_materials_bp = Blueprint('admin_materials', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


def admin_required(f):
    """admin ロール必須デコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


@dual_route(admin_materials_bp, '/admin/materials', methods=['GET'])
@login_required
@admin_required
def admin_materials():
    """Year選択画面 — Year別の教科数・マテリアル数を表示"""
    from sqlalchemy import func
    years_data = db.session.query(
        Material.year_group,
        func.count(func.distinct(Material.subject)).label('subject_count'),
        func.count(Material.material_id).label('material_count'),
    ).group_by(Material.year_group).order_by(Material.year_group).all()
    return render_template('admin/materials_years.html', years_data=years_data)


@dual_route(admin_materials_bp, '/admin/materials/year/<int:year>', methods=['GET'])
@login_required
@admin_required
def admin_materials_by_year(year):
    """Subject選択画面 — 指定Yearの教科別マテリアル数を表示"""
    from sqlalchemy import func
    subjects_data = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('material_count'),
    ).filter_by(year_group=year).group_by(Material.subject).order_by(Material.subject).all()
    return render_template('admin/materials_subjects.html',
                           year=year, subjects_data=subjects_data)


@dual_route(admin_materials_bp, '/admin/materials/year/<int:year>/<subject>', methods=['GET'])
@login_required
@admin_required
def admin_materials_list(year, subject):
    """マテリアル一覧 — 指定Year・教科のマテリアル"""
    materials = Material.query.filter_by(
        year_group=year, subject=subject
    ).order_by(Material.updated_at.desc()).all()
    return render_template('admin/materials.html',
                           materials=materials, year=year, subject=subject)


@dual_route(admin_materials_bp, '/admin/materials/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_materials_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        language = request.form.get('language', 'en')
        difficulty = request.form.get('difficulty', 'normal')
        description = request.form.get('description', '').strip()
        source_type = request.form.get('source_type', 'text')
        source_content = request.form.get('source_content', '').strip()

        if not title or not source_content:
            flash('required_fields', 'error')
            return redirect(_lang_url('/admin/materials/new'))

        material = Material(
            title=title,
            subject=subject,
            language=language,
            difficulty=difficulty,
            description=description,
            source_type=source_type,
            source_content=source_content,
            created_by=current_user.parent_id
        )
        db.session.add(material)
        db.session.commit()

        flash('material_added', 'success')
        return redirect(_lang_url(f'/admin/materials/{material.material_id}'))

    return render_template('admin/material_form.html')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>', methods=['GET'])
@login_required
@admin_required
def admin_materials_detail(material_id):
    material = Material.query.get_or_404(material_id)
    chunks = MaterialChunk.query.filter_by(
        material_id=material_id
    ).order_by(MaterialChunk.sort_order).all()

    # チャンク別に問題をグループ化
    all_questions = material.questions.all()
    questions_by_chunk = {}
    unlinked_questions = []
    for q in all_questions:
        if q.chunk_id:
            questions_by_chunk.setdefault(q.chunk_id, []).append(q)
        else:
            unlinked_questions.append(q)

    return render_template('admin/material_detail.html',
                           material=material, chunks=chunks,
                           questions_by_chunk=questions_by_chunk,
                           unlinked_questions=unlinked_questions,
                           total_questions=len(all_questions))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_materials_edit(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        material.title = request.form.get('title', '').strip()
        material.subject = request.form.get('subject', '').strip()
        material.language = request.form.get('language', 'en')
        material.difficulty = request.form.get('difficulty', 'normal')
        material.description = request.form.get('description', '').strip()
        material.source_type = request.form.get('source_type', 'text')
        material.source_content = request.form.get('source_content', '').strip()
        db.session.commit()

        flash('material_updated', 'success')
        return redirect(_lang_url(f'/admin/materials/{material_id}'))

    return render_template('admin/material_form.html', material=material)


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_materials_delete(material_id):
    material = Material.query.get(material_id)
    if material:
        db.session.delete(material)
        db.session.commit()
        flash('material_deleted', 'success')
    return redirect(_lang_url('/admin/materials'))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks', methods=['POST'])
@login_required
@admin_required
def admin_materials_add_chunk(material_id):
    Material.query.get_or_404(material_id)

    title = request.form.get('chunk_title', '').strip()
    content = request.form.get('chunk_content', '').strip()

    if not title or not content:
        flash('required_fields', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}'))

    max_order = db.session.query(db.func.max(MaterialChunk.sort_order)).filter_by(
        material_id=material_id
    ).scalar() or 0

    chunk = MaterialChunk(
        material_id=material_id,
        title=title,
        content=content,
        sort_order=max_order + 1
    )
    db.session.add(chunk)
    db.session.commit()

    flash('chunk_added', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}'))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_materials_delete_chunk(material_id, chunk_id):
    Material.query.get_or_404(material_id)

    chunk = MaterialChunk.query.filter_by(
        chunk_id=chunk_id, material_id=material_id
    ).first()
    if chunk:
        db.session.delete(chunk)
        db.session.commit()
        flash('chunk_deleted', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}'))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/publish', methods=['POST'])
@login_required
@admin_required
def admin_materials_publish(material_id):
    """マテリアルの公開/非公開を切り替え"""
    material = Material.query.get_or_404(material_id)
    action = request.form.get('action', 'publish')

    if action == 'publish' and material.status in ('ready', 'draft'):
        material.status = 'published'
        flash('material_published', 'success')
    elif action == 'unpublish' and material.status == 'published':
        material.status = 'ready'
        flash('material_unpublished', 'success')

    db.session.commit()
    return redirect(_lang_url(f'/admin/materials/{material_id}'))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/generate', methods=['POST'])
@login_required
@admin_required
def admin_materials_generate(material_id):
    material = Material.query.get_or_404(material_id)

    # フォームからオプション取得
    mc_count = int(request.form.get('mc_count', 4))
    fr_count = int(request.form.get('fr_count', 2))
    difficulty = request.form.get('difficulty', material.difficulty)
    chunk_ids = request.form.getlist('chunk_ids')

    # 対象チャンクを取得
    if chunk_ids:
        chunks = MaterialChunk.query.filter(
            MaterialChunk.chunk_id.in_(chunk_ids),
            MaterialChunk.material_id == material_id
        ).all()
    else:
        chunks = MaterialChunk.query.filter_by(
            material_id=material_id
        ).order_by(MaterialChunk.sort_order).all()

    if not chunks:
        flash('no_chunks_yet', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}'))

    from services.llm import generate_questions
    total_generated = 0

    for chunk in chunks:
        try:
            questions = generate_questions(
                chunk_text=chunk.content,
                count=mc_count + fr_count,
                mc_count=mc_count,
                fr_count=fr_count,
                difficulty=difficulty,
            )

            for q in questions:
                question = Question(
                    material_id=material_id,
                    chunk_id=chunk.chunk_id,
                    question_type=q['question_type'],
                    question_text=q['question_text'],
                    options=q.get('options'),
                    correct_answer=q.get('correct_answer', ''),
                    explanation=q.get('explanation'),
                    reference_answer=q.get('reference_answer'),
                    max_score=q.get('max_score', 10),
                    scoring_rubric=q.get('scoring_rubric'),
                    difficulty=q.get('difficulty', difficulty),
                    source='llm_generated',
                )
                db.session.add(question)

            total_generated += len(questions)
        except Exception as e:
            flash(f'Error generating for "{chunk.title}": {str(e)}', 'error')

    db.session.commit()

    if material.status == 'draft':
        material.status = 'ready'
        db.session.commit()

    flash(f'questions_generated:{total_generated}', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}'))
