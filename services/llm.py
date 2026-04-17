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


GENERATE_PROMPT = """You are a {subject} teacher. Create {count} questions for Year {year_group} students that match the style of the reference questions below.

LESSON SUMMARY:
{summary}

REFERENCE QUESTIONS (existing questions from this lesson — follow this style and difficulty level, but do NOT duplicate them):
{oak_examples}

Requirements:
- {mc_count} multiple choice (4 options A-D, one correct)
- {fr_count} free response (with reference_answer and scoring_rubric, max_score=10)
- Difficulty: {difficulty}
- Base questions on the lesson summary. Mirror the reference style (phrasing, level, typical pitfalls).
- Return ONLY a JSON array. No markdown, no explanation outside JSON.

JSON format:
[{{"question_type":"multiple_choice","question_text":"...","options":[{{"label":"A","text":"..."}},{{"label":"B","text":"..."}},{{"label":"C","text":"..."}},{{"label":"D","text":"..."}}],"correct_answer":"A","explanation":"...","difficulty":"{difficulty}"}},{{"question_type":"free_response","question_text":"...","reference_answer":"...","scoring_rubric":"criterion1(2), criterion2(2), ...","max_score":10,"explanation":"...","difficulty":"{difficulty}"}}]"""


def _format_oak_examples(examples):
    """Format a list of existing-question dicts for the prompt's REFERENCE section."""
    if not examples:
        return "(none available — use lesson summary as the sole basis)"
    lines = []
    for i, q in enumerate(examples, 1):
        qtype = "MC" if q.get("question_type") == "multiple_choice" else "FR"
        lines.append(f"{i}. [{qtype}] {q.get('question_text', '').strip()}")
        if q.get("question_type") == "multiple_choice" and q.get("options"):
            for opt in q["options"]:
                mark = " *" if opt.get("label") == q.get("correct_answer") else "  "
                lines.append(f"   {mark}{opt.get('label')}) {opt.get('text', '')}")
        elif q.get("reference_answer"):
            lines.append(f"   ans: {q['reference_answer']}")
    return "\n".join(lines)


def generate_questions(
    summary,
    subject="science",
    year_group=7,
    oak_examples=None,
    count=6,
    mc_count=4,
    fr_count=2,
    difficulty="normal",
):
    """Generate questions from a lesson summary, optionally mirroring existing Oak questions.

    Args:
        summary: LLM-ready lesson summary (short, concept-focused).
        subject: Maths / Science / English / etc. — drives teacher persona.
        year_group: 4-11. Drives difficulty framing.
        oak_examples: list of existing-question dicts (question_text, options, etc.)
            used as style references. If None/empty, LLM works from summary alone.
        count, mc_count, fr_count, difficulty: generation controls.

    Returns:
        list[dict]: validated question dicts.
    """
    if not summary or not summary.strip():
        summary = "(no summary available)"

    # Cap summary length to keep prompt small
    max_summary_chars = 6000
    if len(summary) > max_summary_chars:
        summary = summary[:max_summary_chars]

    prompt = GENERATE_PROMPT.format(
        subject=subject or "science",
        year_group=year_group or 7,
        summary=summary,
        oak_examples=_format_oak_examples(oak_examples or []),
        count=count,
        mc_count=mc_count,
        fr_count=fr_count,
        difficulty=difficulty,
    )

    logger.info(
        f"Generating {count} questions ({mc_count} MC + {fr_count} FR), "
        f"subject={subject}, year={year_group}, refs={len(oak_examples or [])}, "
        f"difficulty={difficulty}"
    )

    raw = _call_llm(prompt)
    questions = _extract_json(raw)

    valid = []
    for q in questions:
        if q.get("question_type") == "multiple_choice":
            if q.get("options") and q.get("correct_answer") and q.get("question_text"):
                valid.append(q)
        elif q.get("question_type") == "free_response":
            if q.get("question_text") and q.get("reference_answer"):
                valid.append(q)

    logger.info(f"Generated {len(valid)} valid questions out of {len(questions)}")
    return valid
