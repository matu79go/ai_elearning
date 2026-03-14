"""
LLMサービス — Gemini / OpenAI 切り替え対応

.env の LLM_PROVIDER で切り替え:
  - gemini: Google Gemini API (google-genai SDK)
  - openai: OpenAI API (openai SDK)
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')
LLM_MODEL_GENERATE = os.environ.get('LLM_MODEL_GENERATE', 'gemini-2.0-flash')
LLM_MODEL_SCORING = os.environ.get('LLM_MODEL_SCORING', 'gemini-2.0-flash')


def _call_gemini(prompt, model=None):
    """Gemini API呼び出し"""
    from google import genai
    client = genai.Client(api_key=os.environ.get('GOOGLE_API_KEY'))
    resp = client.models.generate_content(
        model=model or LLM_MODEL_GENERATE,
        contents=prompt,
    )
    return resp.text


def _call_openai(prompt, model=None):
    """OpenAI API呼び出し"""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    resp = client.chat.completions.create(
        model=model or LLM_MODEL_GENERATE,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content


def _call_llm(prompt, model=None):
    """プロバイダーに応じてLLMを呼び出す"""
    if LLM_PROVIDER == 'openai':
        return _call_openai(prompt, model)
    else:
        return _call_gemini(prompt, model)


def _extract_json(text):
    """LLMレスポンスからJSONを抽出（複数のパターンに対応）"""
    import re

    # ```json ... ``` ブロックを探す
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # [ で始まる配列を探す
    start = text.find('[')
    if start == -1:
        raise ValueError(f'No JSON array found in response: {text[:200]}')

    # 対応する ] を見つける
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                text = text[start:i + 1]
                break

    return json.loads(text)


GENERATE_PROMPT = """You are a KS3 science teacher. Create {count} questions for Year 7 students based on the lesson content below.

Requirements:
- {mc_count} multiple choice (4 options A-D, one correct)
- {fr_count} free response (with reference_answer and scoring_rubric, max_score=10)
- Difficulty: {difficulty}
- Return ONLY a JSON array. No markdown, no explanation outside JSON.

JSON format:
[{{"question_type":"multiple_choice","question_text":"...","options":[{{"label":"A","text":"..."}},{{"label":"B","text":"..."}},{{"label":"C","text":"..."}},{{"label":"D","text":"..."}}],"correct_answer":"A","explanation":"...","difficulty":"{difficulty}"}},{{"question_type":"free_response","question_text":"...","reference_answer":"...","scoring_rubric":"criterion1(2), criterion2(2), ...","max_score":10,"explanation":"...","difficulty":"{difficulty}"}}]

LESSON CONTENT:
{content}"""


def generate_questions(chunk_text, count=6, mc_count=4, fr_count=2, difficulty='normal'):
    """チャンクテキストから問題を生成

    Args:
        chunk_text: レッスン内容テキスト
        count: 生成する問題数
        mc_count: 4択問題の数
        fr_count: 自由回答の数
        difficulty: easy/normal/hard

    Returns:
        list[dict]: 問題のリスト
    """
    # テキストが長すぎる場合、transcript部分を切り詰め
    # key points等の構造化部分は残し、transcriptを制限
    max_chars = 15000
    if len(chunk_text) > max_chars:
        # "--- Lesson Transcript ---" の前後で分割
        marker = '--- Lesson Transcript ---'
        if marker in chunk_text:
            header = chunk_text[:chunk_text.index(marker)]
            transcript = chunk_text[chunk_text.index(marker) + len(marker):]
            remaining = max_chars - len(header) - len(marker) - 100
            chunk_text = header + marker + '\n' + transcript[:max(remaining, 3000)]
        else:
            chunk_text = chunk_text[:max_chars]

    prompt = GENERATE_PROMPT.format(
        count=count,
        mc_count=mc_count,
        fr_count=fr_count,
        difficulty=difficulty,
        content=chunk_text,
    )

    logger.info(f'Generating {count} questions ({mc_count} MC + {fr_count} FR), difficulty={difficulty}')

    raw = _call_llm(prompt)
    questions = _extract_json(raw)

    # バリデーション
    valid = []
    for q in questions:
        if q.get('question_type') == 'multiple_choice':
            if q.get('options') and q.get('correct_answer') and q.get('question_text'):
                valid.append(q)
        elif q.get('question_type') == 'free_response':
            if q.get('question_text') and q.get('reference_answer'):
                valid.append(q)

    logger.info(f'Generated {len(valid)} valid questions out of {len(questions)}')
    return valid
