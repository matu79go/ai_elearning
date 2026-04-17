"""Drill (小テスト) models — 通常 questions/answer_history とは分離。"""

from models import db


class DrillQuestion(db.Model):
    __tablename__ = 'drill_questions'
    drill_question_id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    explanation = db.Column(db.Text)
    chart_svg = db.Column(db.Text)  # 任意: 図付き問題の SVG (pie/bar/line/function 等)
    source = db.Column(db.String(20), nullable=False)  # llm_generated | rule_based
    template_id = db.Column(db.String(100))
    generated_payload = db.Column(db.JSON)
    difficulty = db.Column(db.String(10), nullable=False, default='normal')
    status = db.Column(db.String(10), nullable=False, default='published')
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DrillSession(db.Model):
    __tablename__ = 'drill_sessions'
    drill_session_id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'), nullable=False)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)
    mastered = db.Column(db.Boolean, nullable=False, default=False)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    max_streak = db.Column(db.Integer, nullable=False, default=0)
    points_earned = db.Column(db.Integer, nullable=False, default=0)


class DrillAnswerHistory(db.Model):
    __tablename__ = 'drill_answer_history'
    drill_answer_id = db.Column(db.Integer, primary_key=True)
    drill_session_id = db.Column(db.Integer, db.ForeignKey('drill_sessions.drill_session_id'), nullable=False)
    drill_question_id = db.Column(db.Integer, db.ForeignKey('drill_questions.drill_question_id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    user_answer = db.Column(db.String(10), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    time_spent_seconds = db.Column(db.Integer, nullable=False, default=0)
    answered_at = db.Column(db.DateTime, server_default=db.func.now())
