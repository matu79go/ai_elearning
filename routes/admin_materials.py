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
    ).order_by(Material.sort_order, Material.title).all()
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


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>', methods=['GET'])
@login_required
@admin_required
def admin_materials_chunk_detail(material_id, chunk_id):
    """チャンク詳細 — Contents / Questions タブ"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    questions = Question.query.filter_by(chunk_id=chunk_id)\
        .order_by(Question.question_id).all()

    # サイドバー用: 同じマテリアルの全チャンク
    all_chunks = MaterialChunk.query.filter_by(
        material_id=material_id
    ).order_by(MaterialChunk.sort_order).all()

    video_url = None
    if chunk.video_drive_id:
        video_url = f'https://drive.google.com/file/d/{chunk.video_drive_id}/preview'

    # ルールベース: このチャンクに紐付くテンプレがあれば UI で有効化
    from services.math_generator import templates_for_chunk
    rule_templates = [
        {'id': t.id, 'topic': t.topic, 'difficulty': t.difficulty}
        for t in templates_for_chunk(chunk_id)
    ]

    # Drill (小テスト) 問題プール
    from models.drill import DrillQuestion
    from config import DRILL_STREAK_TO_MASTER, DRILL_COMPLETION_POINTS
    drill_questions = DrillQuestion.query.filter_by(chunk_id=chunk_id)\
        .order_by(DrillQuestion.drill_question_id).all()

    # YouTube 動画候補
    from models.youtube_video import ChunkYoutubeVideo
    youtube_videos = ChunkYoutubeVideo.query.filter_by(chunk_id=chunk_id)\
        .order_by(ChunkYoutubeVideo.is_primary.desc(), ChunkYoutubeVideo.rank_position).all()

    return render_template('admin/material_chunk_detail.html',
                           material=material, chunk=chunk,
                           questions=questions, all_chunks=all_chunks,
                           video_url=video_url,
                           rule_templates=rule_templates,
                           drill_questions=drill_questions,
                           drill_streak=DRILL_STREAK_TO_MASTER,
                           drill_points=DRILL_COMPLETION_POINTS,
                           youtube_videos=youtube_videos)


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/drill/generate-rule', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_drill_generate_rule(material_id, chunk_id):
    """Drill向けルールベース問題を生成 → drill_questions に追加"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    count = int(request.form.get('count', 10))
    count = max(1, min(count, 50))

    from services.math_generator import templates_for_chunk
    from services.drill_generator import materialize_drill_rule_based
    if not templates_for_chunk(chunk_id):
        flash('no_rule_templates', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}'))

    try:
        rows = materialize_drill_rule_based(chunk_id=chunk_id, count=count, material_id=material_id)
        db.session.commit()
        flash(f'drill_questions_generated:{len(rows)}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#drill')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/drill/generate-llm', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_drill_generate_llm(material_id, chunk_id):
    """Drill向けLLM問題を生成 → drill_questions に追加"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    count = int(request.form.get('count', 5))
    count = max(1, min(count, 20))
    difficulty = request.form.get('difficulty', material.difficulty or 'normal')

    from services.drill_generator import materialize_drill_llm
    try:
        rows = materialize_drill_llm(
            chunk_id=chunk_id, count=count,
            material_id=material_id, difficulty=difficulty,
        )
        db.session.commit()
        flash(f'drill_questions_generated:{len(rows)}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#drill')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/youtube/search', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_youtube_search(material_id, chunk_id):
    """YouTube Data API で検索して chunk_youtube_videos に追加"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    from services.youtube_finder import find_and_save_videos
    try:
        rows = find_and_save_videos(
            chunk_id=chunk_id, title=chunk.title,
            subject=material.subject, year_group=material.year_group,
            max_results=5,
        )
        db.session.commit()
        flash(f'youtube_found:{len(rows)}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/youtube/<int:video_id>/primary', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_youtube_primary(material_id, chunk_id, video_id):
    """指定した動画を primary にする (他は primary=False)"""
    from models.youtube_video import ChunkYoutubeVideo
    target = ChunkYoutubeVideo.query.get_or_404(video_id)
    if target.chunk_id != chunk_id:
        abort(404)
    ChunkYoutubeVideo.query.filter_by(chunk_id=chunk_id).update({'is_primary': False})
    target.is_primary = True
    db.session.commit()
    flash('youtube_primary_updated', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/youtube/<int:video_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_youtube_delete(material_id, chunk_id, video_id):
    from models.youtube_video import ChunkYoutubeVideo
    target = ChunkYoutubeVideo.query.get_or_404(video_id)
    if target.chunk_id != chunk_id:
        abort(404)
    db.session.delete(target)
    db.session.commit()
    flash('youtube_deleted', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/youtube/add', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_youtube_add(material_id, chunk_id):
    """手動で YouTube URL を追加"""
    from models.youtube_video import ChunkYoutubeVideo
    import re as _re
    url = request.form.get('url', '').strip()
    m = _re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})', url)
    if not m:
        flash('youtube_invalid_url', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')
    vid = m.group(1)
    existing = ChunkYoutubeVideo.query.filter_by(chunk_id=chunk_id, video_id=vid).first()
    if existing:
        flash('youtube_already_exists', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')
    # 最大 rank_position + 1
    max_rank = db.session.query(db.func.max(ChunkYoutubeVideo.rank_position)).filter_by(
        chunk_id=chunk_id).scalar() or 0
    row = ChunkYoutubeVideo(
        chunk_id=chunk_id, video_id=vid,
        title=request.form.get('title', '').strip() or f'Manually added ({vid})',
        channel=request.form.get('channel', '').strip(),
        rank_position=max_rank + 1,
        is_primary=False,
        source='manual',
        thumbnail_url=f'https://i.ytimg.com/vi/{vid}/mqdefault.jpg',
    )
    db.session.add(row)
    db.session.commit()
    flash('youtube_added', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#youtube')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/drill/<int:drill_question_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_drill_delete(material_id, chunk_id, drill_question_id):
    """Drill問題を1件削除"""
    from models.drill import DrillQuestion
    q = DrillQuestion.query.get_or_404(drill_question_id)
    if q.chunk_id != chunk_id:
        abort(404)
    db.session.delete(q)
    db.session.commit()
    flash('drill_question_deleted', 'success')
    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}') + '#drill')


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/generate-rule', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_generate_rule(material_id, chunk_id):
    """ルールベース問題の一括生成 (YAMLテンプレから)"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    count = int(request.form.get('count', 10))
    count = max(1, min(count, 50))  # clamp 1-50

    from services.math_generator import materialize_chunk_pool, templates_for_chunk
    if not templates_for_chunk(chunk_id):
        flash('no_rule_templates', 'error')
        return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}'))

    try:
        rows = materialize_chunk_pool(chunk_id=chunk_id, count=count, material_id=material_id)
        db.session.commit()
        flash(f'questions_generated:{len(rows)}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}'))


@dual_route(admin_materials_bp, '/admin/materials/<int:material_id>/chunks/<int:chunk_id>/generate', methods=['POST'])
@login_required
@admin_required
def admin_materials_chunk_generate(material_id, chunk_id):
    """チャンク単位の問題生成"""
    material = Material.query.get_or_404(material_id)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if chunk.material_id != material_id:
        abort(404)

    mc_count = int(request.form.get('mc_count', 4))
    fr_count = int(request.form.get('fr_count', 2))
    difficulty = request.form.get('difficulty', material.difficulty)

    # Sample up to 5 existing Oak/LLM questions from this chunk as style reference
    ref_rows = Question.query.filter(
        Question.chunk_id == chunk_id,
        Question.source.in_(['oak', 'llm_generated']),
    ).limit(5).all()
    oak_examples = [
        {
            'question_type': r.question_type,
            'question_text': r.question_text,
            'options': r.options,
            'correct_answer': r.correct_answer,
            'reference_answer': r.reference_answer,
        }
        for r in ref_rows
    ]

    from services.llm import generate_questions
    try:
        questions = generate_questions(
            summary=chunk.summary or chunk.content,
            subject=material.subject,
            year_group=material.year_group,
            oak_examples=oak_examples,
            count=mc_count + fr_count,
            mc_count=mc_count,
            fr_count=fr_count,
            difficulty=difficulty,
        )
        for q in questions:
            question = Question(
                material_id=material_id,
                chunk_id=chunk_id,
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
        db.session.commit()
        flash(f'questions_generated:{len(questions)}', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(_lang_url(f'/admin/materials/{material_id}/chunks/{chunk_id}'))


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
            ref_rows = Question.query.filter(
                Question.chunk_id == chunk.chunk_id,
                Question.source.in_(['oak', 'llm_generated']),
            ).limit(5).all()
            oak_examples = [
                {
                    'question_type': r.question_type,
                    'question_text': r.question_text,
                    'options': r.options,
                    'correct_answer': r.correct_answer,
                    'reference_answer': r.reference_answer,
                }
                for r in ref_rows
            ]
            questions = generate_questions(
                summary=chunk.summary or chunk.content,
                subject=material.subject,
                year_group=material.year_group,
                oak_examples=oak_examples,
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
