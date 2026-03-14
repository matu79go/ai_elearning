import bcrypt
import secrets
import string
from models import db


def generate_family_code():
    """6文字の英数字の家族コードを生成（紛らわしい文字を除外）"""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(6))


class Parent(db.Model):
    __tablename__ = 'parents'
    parent_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    family_code = db.Column(db.String(10), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False, default='parent')
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
        return f'parent:{self.parent_id}'

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'), self.password_hash.encode('utf-8')
        )


class ParentChild(db.Model):
    __tablename__ = 'parent_children'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'))
    role = db.Column(db.String(20), default='owner')
    linked_at = db.Column(db.DateTime, server_default=db.func.now())
