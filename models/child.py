import bcrypt
from models import db


class Child(db.Model):
    __tablename__ = 'children'
    child_id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.SmallInteger)
    avatar = db.Column(db.String(50), default='default')
    pin_code = db.Column(db.String(255), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak_count = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date)
    daily_goal = db.Column(db.Integer, default=10, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Flask-Login interface
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return f'child:{self.child_id}'

    def set_pin(self, pin):
        self.pin_code = bcrypt.hashpw(
            pin.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_pin(self, pin):
        return bcrypt.checkpw(
            pin.encode('utf-8'), self.pin_code.encode('utf-8')
        )
