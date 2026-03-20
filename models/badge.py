from models import db


class Badge(db.Model):
    __tablename__ = 'badges'
    badge_id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_ja = db.Column(db.String(100), nullable=False)
    description_en = db.Column(db.Text)
    description_ja = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fa-award')
    color = db.Column(db.String(20), default='#6366f1')
    condition_type = db.Column(db.String(50), nullable=False)
    condition_value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class ChildBadge(db.Model):
    __tablename__ = 'child_badges'
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.badge_id'), nullable=False)
    earned_at = db.Column(db.DateTime, server_default=db.func.now())
