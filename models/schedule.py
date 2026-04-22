"""学習スケジュール用モデル — 日別割当 (StudyPlan) と締切 (StudyDeadline)。"""

from models import db


class StudyPlan(db.Model):
    __tablename__ = 'study_plans'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    planned_date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(50))
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'))
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'))
    title = db.Column(db.String(255))
    note = db.Column(db.Text)
    status = db.Column(db.Enum('planned', 'done', 'skipped'), nullable=False, default='planned')
    color = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class StudyDeadline(db.Model):
    __tablename__ = 'study_deadlines'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    kind = db.Column(db.Enum('test', 'homework', 'other'), nullable=False, default='other')
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(50))
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'))
    chunk_id = db.Column(db.Integer, db.ForeignKey('material_chunks.chunk_id'))
    note = db.Column(db.Text)
    done = db.Column(db.Boolean, nullable=False, default=False)
    color = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
