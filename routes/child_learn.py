"""子供用学習画面 — 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果"""

from flask import Blueprint, render_template, request, jsonify, abort, Response
from flask_login import login_required, current_user
from models import db
from models.material import (Material, MaterialChunk, Question, QuestionMastery,
                             LearningSession, AnswerHistory)
from models.badge import Badge, ChildBadge
from routes import dual_route
from datetime import datetime, timedelta
import json
import os
import random
import urllib.request
import urllib.error

from config import QUIZ_QUESTIONS_PER_SESSION

child_learn_bp = Blueprint('child_learn', __name__)

def _is_child():
    """子供ユーザーかチェック"""
    return hasattr(current_user, 'child_id')


def _year_group():
    """ログイン中の子供の学年を返す（未設定なら7）"""
    return getattr(current_user, 'grade', None) or 7


# 教科の表示順
SUBJECT_ORDER = [
    'Science', 'Maths', 'English', 'History', 'Geography',
    'Computing', 'Spanish', 'French', 'German',
]
_SUBJ_ORDER_MAP = {s: i for i, s in enumerate(SUBJECT_ORDER)}


# ---- 教科選択 ----
@dual_route(child_learn_bp, '/child/subjects', methods=['GET'])
@login_required
def child_subjects():
    if not _is_child():
        abort(403)
    from sqlalchemy import func
    subjects = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('unit_count'),
    ).filter_by(
        year_group=_year_group(),
        status='published',
    ).group_by(Material.subject).all()

    subjects = sorted(subjects, key=lambda s: _SUBJ_ORDER_MAP.get(s[0], 999))
    return render_template('child/subjects.html', subjects=subjects)


# ---- 単元一覧 ----
@dual_route(child_learn_bp, '/child/subjects/<subject>', methods=['GET'])
@login_required
def child_units(subject):
    if not _is_child():
        abort(403)
    materials = Material.query.filter_by(
        subject=subject, year_group=_year_group(), status='published',
    ).order_by(Material.sort_order, Material.title).all()

    # 各単元のマスタリー進捗を計算（チャンク別も含む）
    from sqlalchemy import func as sqlfunc
    units_data = []
    for m in materials:
        total_q = m.questions.count()
        mastered_q = QuestionMastery.query.join(Question).filter(
            Question.material_id == m.material_id,
            QuestionMastery.child_id == current_user.child_id,
            QuestionMastery.mastered == True,
        ).count() if total_q > 0 else 0

        # チャンク別進捗
        chunk_progress = {}
        chunk_stats = db.session.query(
            Question.chunk_id,
            sqlfunc.count(Question.question_id).label('total'),
            sqlfunc.sum(db.case(
                (db.and_(QuestionMastery.mastered == True,
                         QuestionMastery.child_id == current_user.child_id), 1),
                else_=0,
            )).label('mastered'),
        ).outerjoin(QuestionMastery, db.and_(
            QuestionMastery.question_id == Question.question_id,
            QuestionMastery.child_id == current_user.child_id,
        )).filter(
            Question.material_id == m.material_id,
        ).group_by(Question.chunk_id).all()

        for cs in chunk_stats:
            chunk_progress[cs.chunk_id] = {
                'total': cs.total, 'mastered': int(cs.mastered or 0),
            }

        units_data.append({
            'material': m,
            'total': total_q,
            'mastered': mastered_q,
            'chunk_progress': chunk_progress,
        })

    # サイドバー用: 全教科一覧
    from sqlalchemy import func
    all_subjects = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('unit_count'),
    ).filter_by(
        year_group=_year_group(),
        status='published',
    ).group_by(Material.subject).all()
    all_subjects = sorted(all_subjects, key=lambda s: _SUBJ_ORDER_MAP.get(s[0], 999))

    return render_template('child/units.html',
                           subject=subject, units_data=units_data,
                           all_subjects=all_subjects)


# ---- セクション要約 ----
@dual_route(child_learn_bp, '/child/section/<int:chunk_id>', methods=['GET'])
@login_required
def child_section(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    # summary が未生成なら LLM で生成してキャッシュ
    if not chunk.summary and chunk.content:
        chunk.summary = _generate_summary(chunk.content)
        db.session.commit()

    # このセクションの問題のマスタリー進捗
    questions = Question.query.filter_by(chunk_id=chunk_id).all()
    mastered_count = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
        QuestionMastery.mastered == True,
    ).count() if questions else 0

    # content からkey points等を抽出（パース）
    parsed = _parse_chunk_content(chunk.content)

    # サイドバー用: 同じマテリアルの全セクション + 進捗
    all_chunks = MaterialChunk.query.filter_by(
        material_id=chunk.material_id
    ).order_by(MaterialChunk.sort_order).all()

    from sqlalchemy import func as sqlfunc
    chunk_progress = {}
    chunk_stats = db.session.query(
        Question.chunk_id,
        sqlfunc.count(Question.question_id).label('total'),
        sqlfunc.sum(db.case(
            (db.and_(QuestionMastery.mastered == True,
                     QuestionMastery.child_id == current_user.child_id), 1),
            else_=0,
        )).label('mastered'),
    ).outerjoin(QuestionMastery, db.and_(
        QuestionMastery.question_id == Question.question_id,
        QuestionMastery.child_id == current_user.child_id,
    )).filter(
        Question.material_id == chunk.material_id,
    ).group_by(Question.chunk_id).all()

    for cs in chunk_stats:
        chunk_progress[cs.chunk_id] = {
            'total': cs.total, 'mastered': int(cs.mastered or 0),
        }

    # サイドバー用: 同じ教科の全ユニット（material）リスト
    sibling_units = Material.query.filter_by(
        subject=material.subject, year_group=material.year_group, status='published',
    ).order_by(Material.sort_order, Material.material_id).all()

    # 動画: chunk_youtube_videos 優先 (複数候補あり)、fallback で Oak Drive
    from models.youtube_video import ChunkYoutubeVideo
    youtube_videos = ChunkYoutubeVideo.query.filter_by(
        chunk_id=chunk_id,
    ).order_by(
        ChunkYoutubeVideo.is_primary.desc(),
        ChunkYoutubeVideo.rank_position,
    ).all()

    video_url = None
    video_type = None
    if youtube_videos:
        primary = next((v for v in youtube_videos if v.is_primary), youtube_videos[0])
        video_url = f'https://www.youtube-nocookie.com/embed/{primary.video_id}'
        video_type = 'youtube'
    elif chunk.video_youtube_id:  # legacy single-id fallback
        video_url = f'https://www.youtube-nocookie.com/embed/{chunk.video_youtube_id}'
        video_type = 'youtube'
    elif chunk.video_drive_id:
        video_url = f'/child/drive-video/{chunk.chunk_id}'
        video_type = 'gdrive'

    # Drill (小テスト) — プール数 + この子が既にマスタリー達成しているか
    from models.drill import DrillQuestion, DrillSession
    from config import DRILL_STREAK_TO_MASTER
    drill_count = DrillQuestion.query.filter_by(
        chunk_id=chunk_id, status='published',
    ).count()
    drill_mastered = DrillSession.query.filter_by(
        child_id=current_user.child_id,
        chunk_id=chunk_id,
        mastered=True,
    ).first() is not None
    # 小テストが用意されていないchunkはゲート対象外 (旧来と同じくquiz即開放)
    quiz_unlocked = (drill_count == 0) or drill_mastered

    return render_template('child/section.html',
                           chunk=chunk, material=material, parsed=parsed,
                           total_questions=len(questions), mastered_count=mastered_count,
                           all_chunks=all_chunks, chunk_progress=chunk_progress,
                           sibling_units=sibling_units,
                           video_url=video_url, video_type=video_type,
                           drill_count=drill_count,
                           drill_mastered=drill_mastered,
                           quiz_unlocked=quiz_unlocked,
                           drill_streak_target=DRILL_STREAK_TO_MASTER,
                           youtube_videos=youtube_videos)


# ---- クイズ画面 ----
def _answered_today_qids(child_id, chunk_id):
    """今日(ローカル0時以降)にこの子が答えた、このchunk内のquestion_idセット"""
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    rows = db.session.query(AnswerHistory.question_id).join(
        Question, AnswerHistory.question_id == Question.question_id,
    ).filter(
        AnswerHistory.child_id == child_id,
        AnswerHistory.answered_at >= today_start,
        Question.chunk_id == chunk_id,
    ).distinct().all()
    return {r[0] for r in rows}


def _recent_wrong_templates(child_id, chunk_id, days=3):
    """直近N日で誤答した rule_based の template_id セット"""
    since = datetime.now() - timedelta(days=days)
    rows = db.session.query(Question.template_id).join(
        AnswerHistory, AnswerHistory.question_id == Question.question_id,
    ).filter(
        AnswerHistory.child_id == child_id,
        AnswerHistory.answered_at >= since,
        AnswerHistory.is_correct == False,  # noqa: E712
        Question.chunk_id == chunk_id,
        Question.template_id.isnot(None),
    ).distinct().all()
    return {r[0] for r in rows if r[0]}


def _generate_rotation_priority(chunk_id, material_id, template_ids, max_n):
    """3日ローテ対象 template_id ごとに、新インスタンスを1問ずつ生成。
    生成したQuestionを返す（セッションにはcommit済み）。
    """
    if not template_ids or max_n <= 0:
        return []
    from services.math_generator import get_templates, materialize_question

    templates = get_templates()
    tids = list(template_ids)[:max_n]
    out = []
    for tid in tids:
        if tid not in templates:
            continue
        try:
            row = materialize_question(
                template_id=tid, material_id=material_id, chunk_id=chunk_id,
            )
            out.append(row)
        except Exception:
            continue
    if out:
        db.session.commit()
    return out


def _refill_rule_based_if_short(chunk_id, needed):
    """ルールベーステンプレがあり、出題可能な新鮮プールが不足なら自動補充"""
    if needed <= 0:
        return []
    from services.math_generator import materialize_chunk_pool, templates_for_chunk
    if not templates_for_chunk(chunk_id):
        return []
    try:
        rows = materialize_chunk_pool(chunk_id=chunk_id, count=needed)
        db.session.commit()
        return rows
    except Exception:
        db.session.rollback()
        return []


def _pick_quiz_questions_for_child(child_id, chunk_id, material_id, limit):
    """1セッション分のクイズ問題を返す。
    A. 今日答えた問題はプールから除外
    B. 直近3日で誤答したrule_based templateは、新インスタンスを生成して優先枠に入れる
    不足時: rule_basedテンプレがあれば自動補充
    """
    excluded = _answered_today_qids(child_id, chunk_id)

    # B: 3日以内の誤答テンプレに対して新インスタンスを先に作る
    wrong_templates = _recent_wrong_templates(child_id, chunk_id)
    max_priority = min(len(wrong_templates), limit // 2)
    priority_rows = _generate_rotation_priority(
        chunk_id, material_id, wrong_templates, max_priority,
    )
    priority_ids = {r.question_id for r in priority_rows}

    remaining = limit - len(priority_rows)

    # 残りをプールから
    def _pool():
        q = Question.query.filter(Question.chunk_id == chunk_id)
        exclude_ids = excluded | priority_ids
        if exclude_ids:
            q = q.filter(~Question.question_id.in_(exclude_ids))
        return q.all()

    pool = _pool()

    # 不足なら rule_based を自動補充
    if len(pool) < remaining:
        shortage = remaining - len(pool) + 5
        _refill_rule_based_if_short(chunk_id, shortage)
        pool = _pool()

    # ミックス (rule_based と other 半々狙い)
    rule = [q for q in pool if q.source == 'rule_based']
    other = [q for q in pool if q.source != 'rule_based']
    picks = list(priority_rows)
    if remaining > 0:
        if rule and other:
            n_rule = min(remaining // 2, len(rule))
            n_other = min(remaining - n_rule, len(other))
            picks += random.sample(rule, n_rule) + random.sample(other, n_other)
        elif rule:
            picks += random.sample(rule, min(remaining, len(rule)))
        else:
            picks += random.sample(other, min(remaining, len(other)))

    # まだ不足なら残り全部（優先とpicksを除外）
    if len(picks) < limit:
        taken = {q.question_id for q in picks}
        leftover = [q for q in pool if q.question_id not in taken]
        picks += random.sample(leftover, min(limit - len(picks), len(leftover)))

    random.shuffle(picks)
    return picks[:limit]


@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>', methods=['GET'])
@login_required
def child_quiz(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    # ドリルが用意されているchunkは、ドリルマスタリー達成までquiz禁止
    from models.drill import DrillQuestion, DrillSession
    from flask import redirect
    from app import lang_url
    has_drill = DrillQuestion.query.filter_by(
        chunk_id=chunk_id, status='published',
    ).first() is not None
    if has_drill:
        drill_mastered = DrillSession.query.filter_by(
            child_id=current_user.child_id, chunk_id=chunk_id, mastered=True,
        ).first() is not None
        if not drill_mastered:
            return redirect(lang_url(f'/child/drill/{chunk_id}'))

    questions = _pick_quiz_questions_for_child(
        current_user.child_id, chunk_id, chunk.material_id, QUIZ_QUESTIONS_PER_SESSION,
    )

    # 各問題のマスタリー状態を取得（出題される問題だけ）
    mastery_map = {}
    if questions:
        masteries = QuestionMastery.query.filter(
            QuestionMastery.question_id.in_([q.question_id for q in questions]),
            QuestionMastery.child_id == current_user.child_id,
        ).all()
        for m in masteries:
            mastery_map[m.question_id] = m

    return render_template('child/quiz.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map)


# ---- 一括採点 (Check Answers) ----
@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>/check', methods=['POST'])
@login_required
def child_quiz_check(chunk_id):
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    chunk = MaterialChunk.query.get_or_404(chunk_id)
    data = request.get_json()
    answer_list = data.get('answers', [])
    skipped_ids = data.get('skipped_ids', [])

    results = []
    total_correct = 0
    total_points = 0

    # 学習セッション作成
    session = LearningSession(
        child_id=current_user.child_id,
        material_id=chunk.material_id,
    )
    db.session.add(session)
    db.session.flush()  # session_id を確定

    # skipped問題の正解情報・解説も返す
    for qid in skipped_ids:
        question = Question.query.get(qid)
        if not question or question.chunk_id != chunk_id:
            continue
        if question.question_type == 'multiple_choice' and question.options:
            correct_labels = [l.strip() for l in (question.correct_answer or '').split(',')]
            parts = []
            for cl in correct_labels:
                ct = next((opt['text'] for opt in question.options if opt['label'] == cl), '')
                parts.append(f"{cl}) {ct}" if ct else cl)
            display_answer = ', '.join(parts)
        else:
            display_answer = (question.correct_answer or '').strip()
            if not display_answer:
                display_answer = (question.reference_answer or '').strip()
        results.append({
            'question_id': question.question_id,
            'correct': True,
            'correct_answer': display_answer,
            'explanation': question.explanation or '',
            'points_earned': 0,
        })

    for ans in answer_list:
        question = Question.query.get(ans.get('question_id'))
        if not question or question.chunk_id != chunk_id:
            continue

        user_answer = str(ans.get('answer', '')).strip()

        # 採点
        is_correct = False
        if question.question_type == 'multiple_choice':
            # 複数正解対応: ソートして比較
            user_labels = sorted(user_answer.upper().split(','))
            correct_labels = sorted(question.correct_answer.upper().split(','))
            is_correct = (user_labels == correct_labels)
        elif question.question_type == 'free_response':
            is_correct = _grade_free_response(
                user_answer, question.correct_answer, question.reference_answer)

        # マスタリー更新
        mastery = QuestionMastery.query.filter_by(
            child_id=current_user.child_id,
            question_id=question.question_id,
        ).first()
        if not mastery:
            mastery = QuestionMastery(
                child_id=current_user.child_id,
                question_id=question.question_id,
            )
            db.session.add(mastery)

        mastery.attempts = (mastery.attempts or 0) + 1
        points_earned = 0

        if is_correct:
            total_correct += 1
            if not mastery.mastered:
                mastery.mastered = True
                mastery.mastered_at = datetime.utcnow()
                points_earned = 1
                total_points += 1
                current_user.total_points += 1

        # 表示用の正解: MCは正解ラベル+テキスト、FRはreference_answer
        if question.question_type == 'multiple_choice' and question.options:
            correct_labels = [l.strip() for l in (question.correct_answer or '').split(',')]
            parts = []
            for cl in correct_labels:
                ct = next((opt['text'] for opt in question.options if opt['label'] == cl), '')
                parts.append(f"{cl}) {ct}" if ct else cl)
            display_answer = ', '.join(parts)
        else:
            display_answer = (question.correct_answer or '').strip()
            if not display_answer:
                display_answer = (question.reference_answer or '').strip()

        # 回答履歴を記録
        db.session.add(AnswerHistory(
            session_id=session.session_id,
            question_id=question.question_id,
            child_id=current_user.child_id,
            user_answer=user_answer[:10],  # VARCHAR(10)制限
            is_correct=is_correct,
            points_earned=points_earned,
        ))

        results.append({
            'question_id': question.question_id,
            'correct': is_correct,
            'correct_answer': display_answer,
            'explanation': question.explanation or '',
            'points_earned': points_earned,
        })

    # セッション完了情報を更新
    session.completed_at = datetime.utcnow()
    session.total_questions = len(answer_list)
    session.correct_answers = total_correct
    session.total_points_earned = total_points

    # レベル自動更新（100ptごとにレベルアップ）
    current_user.level = current_user.total_points // 100 + 1

    # ストリーク自動更新
    today = datetime.utcnow().date()
    if current_user.last_study_date != today:
        if current_user.last_study_date == today - timedelta(days=1):
            current_user.streak_count = (current_user.streak_count or 0) + 1
        elif current_user.last_study_date != today:
            current_user.streak_count = 1
        current_user.last_study_date = today

    db.session.commit()

    # バッジ獲得チェック
    new_badges = _check_badges(current_user, total_correct, len(answer_list))

    # 解説が未生成の問題にLLMで解説を生成してDB保存
    _generate_explanations(results, chunk_id)

    return jsonify({
        'results': results,
        'total_correct': total_correct,
        'total_questions': len(results),
        'total_points': total_points,
        'new_badges': new_badges,
    })


def _check_badges(child, correct_count, answer_count):
    """バッジ獲得条件をチェックし、新規獲得バッジを返す"""
    # 既に持っているバッジID
    owned_ids = {cb.badge_id for cb in ChildBadge.query.filter_by(child_id=child.child_id).all()}

    # 全バッジ取得
    all_badges = Badge.query.order_by(Badge.condition_type, Badge.condition_value).all()

    # 累計回答数（今回分含む）
    total_answers = QuestionMastery.query.filter(
        QuestionMastery.child_id == child.child_id,
        QuestionMastery.attempts > 0,
    ).count()

    new_badges = []
    for badge in all_badges:
        if badge.badge_id in owned_ids:
            continue

        earned = False
        if badge.condition_type == 'first_correct' and correct_count >= 1:
            earned = True
        elif badge.condition_type == 'streak' and (child.streak_count or 0) >= badge.condition_value:
            earned = True
        elif badge.condition_type == 'total_answers' and total_answers >= badge.condition_value:
            earned = True
        elif badge.condition_type == 'total_points' and (child.total_points or 0) >= badge.condition_value:
            earned = True

        if earned:
            db.session.add(ChildBadge(child_id=child.child_id, badge_id=badge.badge_id))
            new_badges.append({
                'badge_id': badge.badge_id,
                'name_en': badge.name_en,
                'name_ja': badge.name_ja,
                'description_en': badge.description_en,
                'description_ja': badge.description_ja,
                'icon': badge.icon,
                'color': badge.color,
            })

    if new_badges:
        db.session.commit()

    return new_badges


def _generate_explanations(results, chunk_id):
    """採点結果に解説がない問題にLLMで一括生成"""
    needs_explain = []
    for r in results:
        if not r.get('explanation'):
            q = Question.query.get(r['question_id'])
            if q:
                needs_explain.append((r, q))

    if not needs_explain:
        return

    # バッチプロンプト: 全問まとめて1回のAPI呼び出し
    lines = []
    for i, (r, q) in enumerate(needs_explain):
        correct_label = r['correct_answer']
        if q.question_type == 'multiple_choice' and q.options:
            # 正解の選択肢テキストを取得
            correct_text = next(
                (opt['text'] for opt in q.options if opt['label'] == q.correct_answer),
                correct_label)
            lines.append(
                f"Q{i+1}: {q.question_text}\n"
                f"Correct answer: {q.correct_answer}) {correct_text}")
        else:
            lines.append(
                f"Q{i+1}: {q.question_text}\n"
                f"Correct answer: {correct_label}")

    questions_block = "\n\n".join(lines)

    prompt = f"""Explain each answer to a Year 7 student in 1 short sentence (max 20 words). Simple language only.

{questions_block}

Format:
Q1: [explanation]
Q2: [explanation]"""

    try:
        from services.rate_limiter import llm_limiter
        limit_check = llm_limiter.check_and_record(
            getattr(current_user, 'child_id', 0))
        if limit_check is not True:
            return  # レート超過 → 解説スキップ

        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        response = client.responses.create(
            model=os.environ.get('LLM_MODEL_EXPLAIN', 'gpt-5-mini'),
            input=prompt,
        )

        text = response.output_text.strip()
        import re
        # Q1: ..., Q2: ... のパターンをパース
        explanations = {}
        for match in re.finditer(r'Q(\d+):\s*(.+?)(?=\nQ\d+:|\Z)', text, re.DOTALL):
            idx = int(match.group(1)) - 1
            explanations[idx] = match.group(2).strip()

        # DB保存 & results更新
        for i, (r, q) in enumerate(needs_explain):
            if i in explanations:
                q.explanation = explanations[i]
                r['explanation'] = explanations[i]

        db.session.commit()

    except Exception as e:
        import traceback
        traceback.print_exc()


# ---- ヒント (Ajax) ----
@dual_route(child_learn_bp, '/child/hint/<int:question_id>', methods=['POST'])
@login_required
def child_hint(question_id):
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    from services.rate_limiter import llm_limiter

    question = Question.query.get_or_404(question_id)
    data = request.get_json() or {}
    user_message = data.get('message', '')

    # レベル1: 固定ヒント（未生成ならLLMで自動生成してDB保存）
    if not user_message:
        if not question.hint:
            # レートリミットチェック（LLM呼び出しが必要な場合のみ）
            limit_check = llm_limiter.check_and_record(current_user.child_id)
            if limit_check is not True:
                return jsonify({'hint': limit_check, 'type': 'rate_limited'})
            try:
                from services.llm import _call_llm
                import os
                model = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')

                hint_prompt = f"""You are a friendly tutor for a primary/secondary school student.
Generate a helpful hint for this question. Do NOT reveal the answer.
Give a nudge that helps the student think in the right direction.
Keep it to 1-2 sentences, simple English.

Question: {question.question_text}
Correct answer: {question.correct_answer}

Hint:"""
                generated_hint = _call_llm(hint_prompt, model=model)
                if generated_hint:
                    generated_hint = generated_hint.strip()
                    question.hint = generated_hint
                    db.session.commit()
                    return jsonify({'hint': generated_hint, 'type': 'fixed'})
            except Exception:
                pass
            return jsonify({'hint': 'Think carefully about what you learned in this section!', 'type': 'fixed'})
        return jsonify({'hint': question.hint, 'type': 'fixed'})

    # レベル2: AIチャット — レートリミット + チャット回数制限
    chat_check = llm_limiter.check_hint_chat(current_user.child_id, question_id)
    if chat_check is not True:
        return jsonify({'hint': chat_check, 'type': 'rate_limited'})

    limit_check = llm_limiter.check_and_record(current_user.child_id)
    if limit_check is not True:
        return jsonify({'hint': limit_check, 'type': 'rate_limited'})

    try:
        from services.llm import _call_llm
        import os
        model = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')

        prompt = f"""You are a friendly tutor helping a Year 7 student (age 11-12).
The student is working on this question and needs help.

RULES:
- NEVER reveal the answer directly
- Give progressive hints, guiding them to think
- Use simple English appropriate for age 11-12
- Be encouraging and supportive
- Keep your response to 2-3 sentences

Question: {question.question_text}
Student's message: {user_message}"""

        response = _call_llm(prompt, model=model)
        return jsonify({'hint': response, 'type': 'ai'})
    except Exception as e:
        return jsonify({'hint': 'Sorry, I couldn\'t think of a hint right now. Try re-reading the section!', 'type': 'error'})


# ---- 結果画面 ----
@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>/result', methods=['GET'])
@login_required
def child_quiz_result(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)

    # 直近セッションで「このchunk」に出題された問題だけを表示
    latest_session = db.session.query(LearningSession).join(
        AnswerHistory, AnswerHistory.session_id == LearningSession.session_id,
    ).join(
        Question, AnswerHistory.question_id == Question.question_id,
    ).filter(
        LearningSession.child_id == current_user.child_id,
        Question.chunk_id == chunk_id,
    ).order_by(LearningSession.session_id.desc()).first()

    session_qids = []
    if latest_session:
        session_qids = [
            r.question_id for r in db.session.query(AnswerHistory)
                .join(Question, AnswerHistory.question_id == Question.question_id)
                .filter(
                    AnswerHistory.session_id == latest_session.session_id,
                    Question.chunk_id == chunk_id,
                )
                .order_by(AnswerHistory.answer_id).all()
        ]

    if session_qids:
        # 重複除去、順序保持
        seen = set()
        ordered_ids = [q for q in session_qids if not (q in seen or seen.add(q))]
        questions = Question.query.filter(Question.question_id.in_(ordered_ids)).all()
        # 表示順を answer_history の順に揃える
        q_by_id = {q.question_id: q for q in questions}
        questions = [q_by_id[qid] for qid in ordered_ids if qid in q_by_id]
    else:
        # フォールバック: セッションが見つからない時のみchunk全問
        questions = Question.query.filter_by(chunk_id=chunk_id).all()

    mastery_map = {}
    masteries = QuestionMastery.query.filter(
        QuestionMastery.question_id.in_([q.question_id for q in questions]),
        QuestionMastery.child_id == current_user.child_id,
    ).all()
    for m in masteries:
        mastery_map[m.question_id] = m

    total = len(questions)
    mastered = sum(1 for m in mastery_map.values() if m.mastered)

    # Prev/Next chunk navigation
    all_chunks = MaterialChunk.query.filter_by(material_id=chunk.material_id)\
        .order_by(MaterialChunk.sort_order).all()
    prev_chunk = None
    next_chunk = None
    for i, c in enumerate(all_chunks):
        if c.chunk_id == chunk_id:
            if i > 0:
                prev_chunk = all_chunks[i - 1]
            if i < len(all_chunks) - 1:
                next_chunk = all_chunks[i + 1]
            break

    # Incorrect question IDs for retry
    incorrect_ids = [q.question_id for q in questions
                     if not (mastery_map.get(q.question_id) and mastery_map[q.question_id].mastered)]

    return render_template('child/quiz_result.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map,
                           total=total, mastered=mastered,
                           prev_chunk=prev_chunk, next_chunk=next_chunk,
                           incorrect_ids=incorrect_ids)


# ---- ヘルパー関数 ----

def _normalize_number(s):
    """数値表記を正規化: スペース・カンマ除去、末尾.0除去など。"""
    import re
    t = re.sub(r'[\s,\u00a0\u2009]', '', s.strip())  # spaces, commas, nbsp, thin space
    # Try to parse as number for canonical form
    try:
        n = float(t)
        if n == int(n):
            return str(int(n))
        return str(n)
    except ValueError:
        return t

def _grade_free_response(user_answer, correct_answer, reference_answer):
    """自由回答の採点。LLM → spaCyフォールバック。"""
    user = user_answer.lower().strip()
    if not user:
        return False

    correct = (correct_answer or '').strip()
    ref = (reference_answer or '').strip()

    # 1) correct_answer との完全一致
    if correct and user == correct.lower():
        return True

    # 1b) 数値の正規化比較 (スペース・カンマ等の表記揺れ対応)
    if correct and _normalize_number(user) == _normalize_number(correct.lower()):
        return True

    # 2) reference_answer にカンマ区切りの代替回答がある場合、各候補と一致チェック
    if ref and ',' in ref and len(ref) < 200:
        alternatives = [alt.strip().lower() for alt in ref.split(',')]
        if user in alternatives:
            return True
        # 数値正規化で再チェック
        user_norm = _normalize_number(user)
        if any(_normalize_number(alt) == user_norm for alt in alternatives):
            return True

    # 3) LLM で模範解答との一致率を判定
    match_target = ref if ref else correct
    if match_target and len(user) >= 10:
        score = _llm_grade(user_answer, match_target)
        if score is not None:
            return score >= 30  # 30%以上で mastered（主要概念に触れていればOK）
        # LLM失敗時 → spaCy フォールバック
        return _fuzzy_match(user, match_target.lower())

    return False


def _llm_grade(user_answer, reference_answer):
    """GPT-5 Nano で模範解答との一致率を 0-100 で返す。失敗時は None。"""
    try:
        from services.rate_limiter import llm_limiter
        limit_check = llm_limiter.check_and_record(
            getattr(current_user, 'child_id', 0))
        if limit_check is not True:
            return None  # レート超過 → fuzzyフォールバック

        import os
        from openai import OpenAI

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return None

        client = OpenAI(api_key=api_key)

        prompt = f"""You are grading a Year 7 student's answer. Compare it with the reference answer.
Return ONLY a number 0-100.

Scoring guide:
- 100: Covers all key concepts with explanation
- 70: Covers the main idea AND gives specific reasons/details
- 40: States the main idea AND at least one supporting reason
- 20: Only states the conclusion without any reasoning or detail
- 0: Completely wrong or irrelevant

IMPORTANT: Just stating a fact (e.g. "A car is not living") without explaining WHY scores only 20. The student must show reasoning.

Reference: {reference_answer}
Student: {user_answer}

Score:"""

        response = client.responses.create(
            model='gpt-5-nano',
            input=prompt,
        )

        # レスポンスから数値を抽出
        text = response.output_text.strip()
        # 数字だけ取り出す
        import re
        match = re.search(r'\d+', text)
        if match:
            return min(int(match.group()), 100)
        return None

    except Exception:
        return None


def _fuzzy_match(user_text, ref_text):
    """spaCy NLP で自由回答を採点。レンマ化+ストップワード除去+キーワードマッチ"""
    try:
        nlp = _get_nlp()

        ref_doc = nlp(ref_text)
        user_doc = nlp(user_text)

        # spaCy はmove, do, canなどを stopword扱いするが、
        # 科学の文脈では重要語なので、短すぎる語（2文字以下）だけ除外
        ALWAYS_STOP = {'a', 'an', 'the', 'is', 'am', 'are', 'was', 'were',
                       'be', 'been', 'being', 'it', 'its', 'do', 'does',
                       'did', 'has', 'have', 'had', 'to', 'of', 'in', 'on',
                       'at', 'by', 'for', 'and', 'or', 'but', 'so', 'if',
                       'as', 'that', 'this', 'with', 'from', 'not', 'no',
                       'they', 'them', 'their', 'he', 'she', 'we', 'you',
                       'my', 'his', 'her', 'our', 'your'}

        def extract_tokens(doc):
            """各トークンの全形態（レンマ+原形）をセットのリストで返す"""
            tokens = []
            for token in doc:
                if token.is_punct or len(token.text) <= 1:
                    continue
                if token.text.lower() in ALWAYS_STOP:
                    continue
                forms = {token.lemma_.lower(), token.text.lower()}
                tokens.append(forms)
            return tokens

        ref_tokens = extract_tokens(ref_doc)
        user_tokens = extract_tokens(user_doc)

        if not ref_tokens or not user_tokens:
            return False

        # ユーザーの各トークンが模範解答のいずれかのトークンと一致するか
        matched = 0
        for u_forms in user_tokens:
            for r_forms in ref_tokens:
                if u_forms & r_forms:
                    matched += 1
                    break

        precision = matched / len(user_tokens)

        # 判定: 的外れでない (precision >= 0.5) かつ
        #   3つ以上一致、または 2つ以上 & 5語以上
        if precision < 0.5:
            return False
        if matched >= 3:
            return True
        if matched >= 2 and len(user_text.split()) >= 5:
            return True
        return False

    except Exception:
        # spaCy が使えない場合はフォールバック
        ref_words = set(w.lower() for w in ref_text.split() if len(w) > 3)
        if not ref_words:
            return False
        matched = sum(1 for w in ref_words if w in user_text.lower())
        return matched >= len(ref_words) * 0.3


# spaCy モデルのキャッシュ（毎回ロードしない）
_nlp_model = None

def _get_nlp():
    global _nlp_model
    if _nlp_model is None:
        import spacy
        _nlp_model = spacy.load('en_core_web_sm')
    return _nlp_model


def _generate_summary(content):
    """Transcriptを要約"""
    try:
        from services.llm import _call_llm
        import os
        model = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')

        # Transcript部分を抽出
        marker = '--- Lesson Transcript ---'
        if marker in content:
            transcript = content[content.index(marker) + len(marker):]
        else:
            transcript = content

        # 長すぎる場合は切り詰め
        if len(transcript) > 15000:
            transcript = transcript[:15000]

        prompt = f"""Summarise this lesson content in 3-5 short paragraphs for a Year 7 student (age 11-12).
Use simple, clear English. Focus on the most important concepts.
Do NOT use bullet points. Write in flowing prose.

{transcript}"""

        return _call_llm(prompt, model=model)
    except Exception:
        return None


# ---- Oak API 動画プロキシ ----

OAK_API_BASE = 'https://open-api.thenational.academy/api/v0'


def _oak_api_get(path):
    """Oak API への GET リクエスト（JSON）"""
    api_key = os.environ.get('OAK_API_KEY', '')
    url = f'{OAK_API_BASE}{path}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'OakAPIClient/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None


def _get_lesson_slug(chunk):
    """MaterialChunk の title から Oak API の lesson slug を推定"""
    # title を slug 化: "Animal cell structures and their functions"
    # → "animal-cell-structures-and-their-functions"
    slug = chunk.title.lower()
    slug = slug.replace("'", "").replace(",", "").replace(".", "")
    slug = slug.replace("(", "").replace(")", "").replace(":", "")
    slug = '-'.join(slug.split())
    return slug


def _get_drive_creds():
    """Google Drive OAuth認証情報を取得（キャッシュ付き）"""
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google.auth.transport.requests import Request as GRequest

    creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'credentials', 'gdrive_token.json')
    if not os.path.exists(creds_path):
        return None

    creds = OAuthCredentials.from_authorized_user_file(
        creds_path, ['https://www.googleapis.com/auth/drive.file'])
    if creds.expired and creds.refresh_token:
        creds.refresh(GRequest())
        with open(creds_path, 'w') as f:
            f.write(creds.to_json())
    return creds


@dual_route(child_learn_bp, '/child/drive-video/<int:chunk_id>')
@login_required
def child_drive_video(chunk_id):
    """Google Drive動画をRange Request対応でプロキシ配信（HTTP直接）"""
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    if not chunk.video_drive_id:
        abort(404)

    creds = _get_drive_creds()
    if not creds:
        abort(500)

    file_id = chunk.video_drive_id
    api_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'

    # まずファイルサイズ取得（HEADリクエスト相当）
    import urllib.request as urlreq
    size_req = urlreq.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=size',
        headers={'Authorization': f'Bearer {creds.token}'},
    )
    with urlreq.urlopen(size_req, timeout=10) as resp:
        file_size = int(json.loads(resp.read()).get('size', 0))

    if file_size == 0:
        abort(404)

    # Range Request パース
    range_header = request.headers.get('Range')
    CHUNK_SIZE = 2 * 1024 * 1024  # 2MB

    if range_header:
        range_match = range_header.replace('bytes=', '').split('-')
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else min(start + CHUNK_SIZE - 1, file_size - 1)
    else:
        start = 0
        end = min(CHUNK_SIZE - 1, file_size - 1)

    end = min(end, file_size - 1)

    # Google Drive APIから該当バイト範囲を取得
    dl_req = urlreq.Request(api_url, headers={
        'Authorization': f'Bearer {creds.token}',
        'Range': f'bytes={start}-{end}',
    })

    with urlreq.urlopen(dl_req, timeout=30) as resp:
        data = resp.read()

    return Response(
        data,
        status=206,
        headers={
            'Content-Type': 'video/mp4',
            'Content-Range': f'bytes {start}-{start + len(data) - 1}/{file_size}',
            'Content-Length': str(len(data)),
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=86400',
        },
    )


@dual_route(child_learn_bp, '/child/oak-video/<int:chunk_id>')
@login_required
def child_oak_video(chunk_id):
    """Oak 動画配信 — Google Driveプロキシ優先、フォールバックでOak APIプロキシ"""
    chunk = MaterialChunk.query.get_or_404(chunk_id)

    # Google Drive にキャッシュ済みならDriveプロキシへリダイレクト
    if chunk.video_drive_id:
        from flask import redirect
        return redirect(request.url.replace('/oak-video/', '/drive-video/'))

    # フォールバック: Oak API からストリーミングプロキシ
    lesson_slug = _get_lesson_slug(chunk)
    api_key = os.environ.get('OAK_API_KEY', '')
    url = f'{OAK_API_BASE}/lessons/{lesson_slug}/assets/video'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'OakAPIClient/1.0',
    })

    try:
        resp = urllib.request.urlopen(req, timeout=60)

        def generate():
            while True:
                data = resp.read(8192)
                if not data:
                    break
                yield data
            resp.close()

        return Response(
            generate(),
            content_type='video/mp4',
            headers={'Accept-Ranges': 'bytes'},
        )
    except Exception:
        abort(404)


@dual_route(child_learn_bp, '/child/oak-video-check/<int:chunk_id>')
@login_required
def child_oak_video_check(chunk_id):
    """Oak 動画が利用可能かチェック — parent/childどちらもアクセス可"""
    chunk = MaterialChunk.query.get_or_404(chunk_id)

    # Google Drive にキャッシュ済みなら即座に available
    if chunk.video_drive_id:
        return jsonify({'available': True, 'source': 'google_drive'})

    # Oak API で確認
    lesson_slug = _get_lesson_slug(chunk)
    assets = _oak_api_get(f'/lessons/{lesson_slug}/assets')
    if assets:
        has_video = any(a.get('type') == 'video' for a in assets.get('assets', []))
        return jsonify({'available': has_video, 'source': 'oak_proxy', 'lesson_slug': lesson_slug})
    return jsonify({'available': False})


def _parse_chunk_content(content):
    """チャンク本文からKey Points等を構造化して抽出"""
    result = {
        'learning_outcome': '',
        'key_points': [],
        'keywords': [],
        'misconceptions': [],
    }

    lines = content.split('\n')
    section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('Learning Outcome:'):
            result['learning_outcome'] = line.replace('Learning Outcome:', '').strip()
        elif line == 'Key Learning Points:':
            section = 'kp'
        elif line == 'Key Words:':
            section = 'kw'
        elif line == 'Common Misconceptions:':
            section = 'mc'
        elif line.startswith('--- Lesson Transcript ---'):
            break
        elif section == 'kp' and line.startswith('- '):
            result['key_points'].append(line[2:])
        elif section == 'kw' and line.startswith('- '):
            parts = line[2:].split(': ', 1)
            if len(parts) == 2:
                result['keywords'].append({'word': parts[0], 'definition': parts[1]})
            else:
                result['keywords'].append({'word': parts[0], 'definition': ''})
        elif section == 'mc' and line.startswith('- Misconception:'):
            result['misconceptions'].append({
                'misconception': line.replace('- Misconception:', '').strip(),
                'correction': '',
            })
        elif section == 'mc' and line.startswith('Correction:') and result['misconceptions']:
            result['misconceptions'][-1]['correction'] = line.replace('Correction:', '').strip()

    return result
