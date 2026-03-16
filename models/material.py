from models import db


class Material(db.Model):
    __tablename__ = 'materials'
    material_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    source_type = db.Column(db.String(10), nullable=False)
    source_content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500))
    subject = db.Column(db.String(100))
    year_group = db.Column(db.Integer, nullable=False, default=7)
    difficulty = db.Column(db.String(10), nullable=False, default='normal')
    language = db.Column(db.String(2), nullable=False, default='en')
    status = db.Column(db.String(10), nullable=False, default='published')
    created_by = db.Column(db.Integer, db.ForeignKey('parents.parent_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    chunks = db.relationship('MaterialChunk', backref='material', lazy='dynamic',
                             order_by='MaterialChunk.sort_order')
    questions = db.relationship('Question', backref='material', lazy='dynamic')


class MaterialChunk(db.Model):
    __tablename__ = 'material_chunks'
    chunk_id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    page_start = db.Column(db.Integer)
    page_end = db.Column(db.Integer)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Question(db.Model):
    __tablename__ = 'questions'
    question_id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)
    correct_answer = db.Column(db.String(10), nullable=False)
    explanation = db.Column(db.Text)
    reference_answer = db.Column(db.Text)
    max_score = db.Column(db.Integer, nullable=False, default=10)
    scoring_rubric = db.Column(db.Text)
    hint = db.Column(db.Text)
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'))
    source = db.Column(db.String(20), nullable=False, default='manual')
    difficulty = db.Column(db.String(10), nullable=False, default='normal')
    points_value = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class QuestionMastery(db.Model):
    __tablename__ = 'question_mastery'
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    mastered = db.Column(db.Boolean, nullable=False, default=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    mastered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class LearningSession(db.Model):
    __tablename__ = 'learning_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=False)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    total_points_earned = db.Column(db.Integer, nullable=False, default=0)
    time_spent_seconds = db.Column(db.Integer, nullable=False, default=0)


class AnswerHistory(db.Model):
    __tablename__ = 'answer_history'
    answer_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.session_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    user_answer = db.Column(db.String(10), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    points_earned = db.Column(db.Integer, nullable=False, default=0)
    time_spent_seconds = db.Column(db.Integer, nullable=False, default=0)
    answered_at = db.Column(db.DateTime, server_default=db.func.now())


class PointHistory(db.Model):
    __tablename__ = 'point_history'
    point_id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reason_type = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.session_id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
