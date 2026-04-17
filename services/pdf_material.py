"""PDF → マテリアル 自動変換サービス。

1. PDF からテキスト抽出 (PyMuPDF)
2. LLM で論理的な章に分割 + 要約生成
3. Material + MaterialChunks を作成
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / 'static' / 'uploads' / 'materials'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# LLM が切り分ける最大文字数 (入力全体)
MAX_LLM_INPUT_CHARS = 20000


def save_pdf(file_storage, material_id: int) -> str:
    """Flask の FileStorage を保存し、static 配下の相対パスを返す。"""
    filename = f'material_{material_id}.pdf'
    path = UPLOAD_DIR / filename
    file_storage.save(str(path))
    return f'uploads/materials/{filename}'


def extract_text(pdf_path: str | Path) -> str:
    """PDF から全ページテキストを抽出。ページ境界は \\n--- page N ---\\n で示す。"""
    import fitz  # PyMuPDF
    doc = fitz.open(str(pdf_path))
    parts = []
    for i, page in enumerate(doc, 1):
        text = page.get_text().strip()
        if text:
            parts.append(f'--- page {i} ---\n{text}')
    doc.close()
    return '\n\n'.join(parts)


METADATA_PROMPT = """You are analyzing a learning material (PDF extracted text) to infer its metadata.

TEXT (first part of PDF):
{text}

TASK: Extract the following fields as JSON:
- "title": a short descriptive title (under 80 chars), plain English/Japanese, no quotes
- "subject": ONE of [Science, Maths, English, History, Geography, Computing, Spanish]
- "difficulty": ONE of [easy, normal, hard] — based on apparent complexity for KS3 students
- "description": one sentence describing what the material teaches (under 150 chars)
- "material_type": ONE of the following:
    * "lesson" — a teaching material with sequential topics/concepts (most common)
    * "glossary" — a list of terms and definitions (reference / word list)
    * "worksheet" — exercises, problems, or practice questions
    * "assessment" — a test, evaluation, or assessment criteria
    * "other" — doesn't fit the above

Respond ONLY with a JSON object. No prose.

{{"title": "...", "subject": "...", "difficulty": "...", "description": "...", "material_type": "..."}}
"""


def extract_metadata(pdf_text: str) -> dict:
    """PDF テキストから title/subject/difficulty/description/material_type を LLM で推定。"""
    from services.llm import _call_llm

    snippet = pdf_text[:4000]
    prompt = METADATA_PROMPT.format(text=snippet)
    raw = _call_llm(prompt)

    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        raise ValueError(f'no JSON object in LLM response: {raw[:300]!r}')
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f'invalid JSON: {e}') from e

    valid_subjects = {'Science', 'Maths', 'English', 'History', 'Geography', 'Computing', 'Spanish'}
    valid_difficulty = {'easy', 'normal', 'hard'}
    valid_types = {'lesson', 'glossary', 'worksheet', 'assessment', 'other'}
    out = {
        'title': (data.get('title') or '').strip()[:255],
        'subject': data.get('subject', 'Science') if data.get('subject') in valid_subjects else 'Science',
        'difficulty': data.get('difficulty', 'normal') if data.get('difficulty') in valid_difficulty else 'normal',
        'description': (data.get('description') or '').strip()[:255],
        'material_type': data.get('material_type', 'lesson') if data.get('material_type') in valid_types else 'lesson',
    }
    return out


CHUNKING_PROMPTS = {
    'lesson': """You are organizing a lesson into logical sections for a Year {year_group} student studying {subject}.

MATERIAL TEXT (extracted from PDF, page markers kept):
{text}

TASK:
Split this lesson into 3-8 logical sections. Each section should represent a distinct teaching topic or concept.

For each section:
- "title": short descriptive heading (under 60 chars, plain text, no quotes)
- "summary": 2-3 sentences describing what the section teaches
- "content": the relevant source text for this section. Copy verbatim text from the PDF. Trim page markers.

Respond ONLY with a JSON array. No prose before or after.

[{{"title": "...", "summary": "...", "content": "..."}}, ...]
""",
    'glossary': """You are organizing a glossary (term list) into thematic groups for Year {year_group} {subject} students.

MATERIAL TEXT (extracted from PDF):
{text}

TASK:
Group the terms into 2-5 thematic sections. Each section contains related terms.

For each section:
- "title": theme name (under 60 chars, e.g. "Definitions", "Measurement", "Common Substances")
- "summary": a comma-separated list of the key terms in this section, e.g. "Key terms: acid, alkali, base, pH, neutral."
- "content": the verbatim term+definition lines from the PDF that belong to this theme. Preserve the "term:\\ndefinition" format.

Respond ONLY with a JSON array. No prose before or after.

[{{"title": "...", "summary": "...", "content": "..."}}, ...]
""",
    'worksheet': """You are organizing a worksheet into sections for a Year {year_group} {subject} student.

MATERIAL TEXT (extracted from PDF):
{text}

TASK:
Identify 2-6 distinct sections (tasks, problems, exercises, or target lists).

For each section:
- "title": short descriptive heading (under 60 chars), e.g. "Task 1: Fill in the blanks", "Target: Identify acids"
- "summary": 1-2 sentences stating what the student is asked to do in this section
- "content": the verbatim instructions and problem text from the PDF for this section

Respond ONLY with a JSON array.

[{{"title": "...", "summary": "...", "content": "..."}}, ...]
""",
    'assessment': """You are organizing an assessment / test for a Year {year_group} {subject} student.

MATERIAL TEXT (extracted from PDF):
{text}

TASK:
Split the assessment into 1-6 sections (question groups or assessment areas).

For each section:
- "title": short descriptive heading (under 60 chars)
- "summary": 1-2 sentences describing what is being assessed in this section
- "content": the verbatim questions/criteria from the PDF

Respond ONLY with a JSON array.

[{{"title": "...", "summary": "...", "content": "..."}}, ...]
""",
    'other': """You are organizing a reference material for Year {year_group} {subject} student.

MATERIAL TEXT (extracted from PDF):
{text}

TASK:
Split into 1-6 logical sections (groupings that make sense for the content).

For each section:
- "title": short heading (under 60 chars)
- "summary": 1-2 sentences describing what this section contains
- "content": the verbatim source text for this section

Respond ONLY with a JSON array.

[{{"title": "...", "summary": "...", "content": "..."}}, ...]
""",
}


def chunk_with_llm(text: str, subject: str, year_group: int, material_type: str = 'lesson') -> list[dict]:
    """LLM に PDF テキストを渡し、種別に応じた章立て + summary を JSON で返させる。"""
    from services.llm import _call_llm

    if len(text) > MAX_LLM_INPUT_CHARS:
        logger.warning(f'PDF text {len(text)} chars truncated to {MAX_LLM_INPUT_CHARS}')
        text = text[:MAX_LLM_INPUT_CHARS] + '\n\n[...truncated...]'

    prompt_tpl = CHUNKING_PROMPTS.get(material_type, CHUNKING_PROMPTS['lesson'])
    prompt = prompt_tpl.format(
        year_group=year_group or 7,
        subject=subject or 'General',
        text=text,
    )
    logger.info(f'Chunking with material_type={material_type}')
    raw = _call_llm(prompt)

    # JSON 抽出
    m = re.search(r'\[[\s\S]*\]', raw)
    if not m:
        raise ValueError(f'no JSON array in LLM response: {raw[:300]!r}')
    try:
        chunks = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f'LLM returned invalid JSON: {e}: {raw[:300]!r}') from e

    # バリデーション
    valid = []
    for i, c in enumerate(chunks):
        if not isinstance(c, dict):
            continue
        title = (c.get('title') or '').strip()
        summary = (c.get('summary') or '').strip()
        content = (c.get('content') or '').strip()
        if not title or not content:
            continue
        valid.append({'title': title[:255], 'summary': summary, 'content': content})
    if not valid:
        raise ValueError('LLM produced no usable chunks')
    return valid


def create_material_from_pdf(
    file_storage, title: str, subject: str, year_group: int,
    description: str, language: str, difficulty: str, created_by: int,
    material_type: str = 'lesson',
) -> int:
    """FileStorage を保存 → テキスト抽出 → LLMチャンク化 → Material+Chunks INSERT。

    Returns: material_id
    """
    from models import db
    from models.material import Material, MaterialChunk

    # 1) Material を先に作って ID を確定
    material = Material(
        title=title, subject=subject, year_group=year_group,
        description=description, language=language, difficulty=difficulty,
        source_type='pdf', source_content='(extracted from PDF)',
        material_type=material_type,
        status='draft',
        created_by=created_by,
    )
    db.session.add(material)
    db.session.flush()

    # 2) PDF 保存
    file_path = save_pdf(file_storage, material.material_id)
    material.file_path = file_path
    abs_path = Path(__file__).resolve().parent.parent / 'static' / file_path.replace('uploads/materials/', 'uploads/materials/')

    # 3) テキスト抽出
    text = extract_text(abs_path)
    if not text.strip():
        raise ValueError('PDF is empty or text extraction failed')
    material.source_content = text[:50000]

    # 4) LLM チャンク化 (種別別プロンプト)
    chunks = chunk_with_llm(text, subject=subject, year_group=year_group, material_type=material_type)

    # 5) MaterialChunk INSERT
    for i, c in enumerate(chunks, 1):
        chunk = MaterialChunk(
            material_id=material.material_id,
            title=c['title'],
            content=c['content'],
            summary=c['summary'],
            sort_order=i,
        )
        db.session.add(chunk)

    material.status = 'published'
    db.session.commit()
    logger.info(f'Created material {material.material_id} with {len(chunks)} chunks from PDF')
    # YouTube動画は admin chunk detail の「自動検索」ボタンから手動実行
    return material.material_id
