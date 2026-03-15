"""子供用学習画面 — 教科選択 → 単元一覧 → セクション要約 → クイズ → 結果"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db
from models.material import Material, MaterialChunk, Question, QuestionMastery
from routes import dual_route
from datetime import datetime

child_learn_bp = Blueprint('child_learn', __name__)

YEAR_GROUP = 7  # 当面 Year 7 固定


def _is_child():
    """子供ユーザーかチェック"""
    return hasattr(current_user, 'child_id')


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
        year_group=YEAR_GROUP,
    ).group_by(Material.subject).order_by(Material.subject).all()

    return render_template('child/subjects.html', subjects=subjects)


# ---- 単元一覧 ----
@dual_route(child_learn_bp, '/child/subjects/<subject>', methods=['GET'])
@login_required
def child_units(subject):
    if not _is_child():
        abort(403)
    materials = Material.query.filter_by(
        subject=subject, year_group=YEAR_GROUP,
    ).order_by(Material.title).all()

    # 各単元のマスタリー進捗を計算
    units_data = []
    for m in materials:
        total_q = m.questions.count()
        mastered_q = QuestionMastery.query.join(Question).filter(
            Question.material_id == m.material_id,
            QuestionMastery.child_id == current_user.child_id,
            QuestionMastery.mastered == True,
        ).count() if total_q > 0 else 0
        units_data.append({
            'material': m,
            'total': total_q,
            'mastered': mastered_q,
        })

    # サイドバー用: 全教科一覧
    from sqlalchemy import func
    all_subjects = db.session.query(
        Material.subject,
        func.count(Material.material_id).label('unit_count'),
    ).filter_by(
        year_group=YEAR_GROUP,
    ).group_by(Material.subject).order_by(Material.subject).all()

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

    # サイドバー用: 同じマテリアルの全セクション
    all_chunks = MaterialChunk.query.filter_by(
        material_id=chunk.material_id
    ).order_by(MaterialChunk.sort_order).all()

    return render_template('child/section.html',
                           chunk=chunk, material=material, parsed=parsed,
                           total_questions=len(questions), mastered_count=mastered_count,
                           all_chunks=all_chunks)


# ---- クイズ画面 ----
@dual_route(child_learn_bp, '/child/quiz/<int:chunk_id>', methods=['GET'])
@login_required
def child_quiz(chunk_id):
    if not _is_child():
        abort(403)
    chunk = MaterialChunk.query.get_or_404(chunk_id)
    material = Material.query.get(chunk.material_id)
    questions = Question.query.filter_by(chunk_id=chunk_id).all()

    # 各問題のマスタリー状態を取得
    mastery_map = {}
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

    results = []
    total_correct = 0
    total_points = 0

    for ans in answer_list:
        question = Question.query.get(ans.get('question_id'))
        if not question or question.chunk_id != chunk_id:
            continue

        user_answer = str(ans.get('answer', '')).strip()

        # 採点
        is_correct = False
        if question.question_type == 'multiple_choice':
            is_correct = (user_answer.upper() == question.correct_answer.upper())
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

        # 表示用の正解: correct_answer が空なら reference_answer を使う
        display_answer = (question.correct_answer or '').strip()
        if not display_answer:
            display_answer = (question.reference_answer or '').strip()

        results.append({
            'question_id': question.question_id,
            'correct': is_correct,
            'correct_answer': display_answer,
            'explanation': question.explanation or '',
            'points_earned': points_earned,
        })

    db.session.commit()

    return jsonify({
        'results': results,
        'total_correct': total_correct,
        'total_questions': len(results),
        'total_points': total_points,
    })


# ---- ヒント (Ajax) ----
@dual_route(child_learn_bp, '/child/hint/<int:question_id>', methods=['POST'])
@login_required
def child_hint(question_id):
    if not _is_child():
        return jsonify({'error': 'forbidden'}), 403

    question = Question.query.get_or_404(question_id)
    data = request.get_json() or {}
    user_message = data.get('message', '')

    # レベル1: 固定ヒント
    if not user_message:
        if not question.hint:
            return jsonify({'hint': 'Think carefully about what you learned in this section!', 'type': 'fixed'})
        return jsonify({'hint': question.hint, 'type': 'fixed'})

    # レベル2: AIチャット
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

    return render_template('child/quiz_result.html',
                           chunk=chunk, material=material,
                           questions=questions, mastery_map=mastery_map,
                           total=total, mastered=mastered)


# ---- ヘルパー関数 ----

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

    # 2) reference_answer にカンマ区切りの代替回答がある場合、各候補と一致チェック
    if ref and ',' in ref and len(ref) < 200:
        alternatives = [alt.strip().lower() for alt in ref.split(',')]
        if user in alternatives:
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
