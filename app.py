"""AI e-Learning System - Flask Application"""
import json
import os
import bcrypt
from flask import Flask, render_template, redirect, url_for, g, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import DATABASE_URL, SECRET_KEY

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# ---- i18n ----
TRANSLATIONS = {}
SUPPORTED_LANGS = ['en', 'ja']
DEFAULT_LANG = 'en'

translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
for _lang in SUPPORTED_LANGS:
    filepath = os.path.join(translations_dir, f'{_lang}.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        TRANSLATIONS[_lang] = json.load(f)


def get_lang_from_path():
    """URLパスから言語を判定"""
    path = request.path
    if path.startswith('/ja/') or path == '/ja':
        return 'ja'
    return 'en'


def lang_url(path):
    """現在の言語に応じたURLを生成"""
    lang = g.get('lang', DEFAULT_LANG)
    if lang == 'ja':
        return '/ja' + path
    return path


@app.before_request
def set_lang():
    """リクエストごとに言語を設定"""
    g.lang = get_lang_from_path()
    g.t = TRANSLATIONS.get(g.lang, TRANSLATIONS[DEFAULT_LANG])


@app.context_processor
def inject_i18n():
    """テンプレートに翻訳データと言語切替URLを注入"""
    lang = g.get('lang', DEFAULT_LANG)
    t = g.get('t', TRANSLATIONS[DEFAULT_LANG])

    # 言語切替URL生成
    path = request.path
    if lang == 'ja':
        switch_path = path[3:] if path.startswith('/ja/') else path.replace('/ja', '/', 1)
        if not switch_path:
            switch_path = '/'
    else:
        switch_path = '/ja' + path

    return dict(t=t, lang=lang, switch_lang_url=switch_path, lang_url=lang_url)


# ---- Models ----
class Parent(db.Model):
    __tablename__ = 'parents'
    parent_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
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
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


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
        self.pin_code = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_pin(self, pin):
        return bcrypt.checkpw(pin.encode('utf-8'), self.pin_code.encode('utf-8'))


class ParentChild(db.Model):
    __tablename__ = 'parent_children'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    child_id = db.Column(db.Integer, db.ForeignKey('children.child_id'))
    role = db.Column(db.String(20), default='owner')
    linked_at = db.Column(db.DateTime, server_default=db.func.now())


@login_manager.user_loader
def load_user(user_id):
    """user_id format: 'parent:1' or 'child:2'"""
    if ':' not in user_id:
        return None
    user_type, uid = user_id.split(':', 1)
    if user_type == 'parent':
        return Parent.query.get(int(uid))
    elif user_type == 'child':
        return Child.query.get(int(uid))
    return None


# ---- Helper ----
def dual_route(rule, **kwargs):
    """Register both /path and /ja/path routes"""
    def decorator(f):
        app.add_url_rule(rule, f.__name__, f, **kwargs)
        app.add_url_rule('/ja' + rule, f.__name__ + '_ja', f, **kwargs)
        return f
    return decorator


# ---- Routes ----
@dual_route('/')
def index():
    return render_template('index.html')


# -- Parent Auth --
@dual_route('/parent/login', methods=['GET', 'POST'])
def parent_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        parent = Parent.query.filter_by(email=email).first()
        if parent and parent.check_password(password):
            login_user(parent)
            return redirect(lang_url('/admin/dashboard'))
        flash('login_failed', 'error')
    return render_template('auth/parent_login.html')


@dual_route('/parent/register', methods=['GET', 'POST'])
def parent_register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        errors = []
        if not email or not display_name or not password:
            errors.append('required_fields')
        if password != password_confirm:
            errors.append('password_mismatch')
        if len(password) < 8:
            errors.append('password_too_short')
        if Parent.query.filter_by(email=email).first():
            errors.append('email_taken')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/parent_register.html')

        parent = Parent(email=email, display_name=display_name)
        parent.set_password(password)
        db.session.add(parent)
        db.session.commit()
        login_user(parent)
        return redirect(lang_url('/admin/dashboard'))

    return render_template('auth/parent_register.html')


@dual_route('/parent/logout')
def parent_logout():
    logout_user()
    return redirect(lang_url('/'))


# -- Child Auth --
@dual_route('/child/login', methods=['GET', 'POST'])
def child_login():
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        pin = request.form.get('pin', '')
        if child_id:
            child = Child.query.get(int(child_id))
            if child and child.check_pin(pin):
                login_user(child)
                return redirect(lang_url('/child/dashboard'))
            flash('pin_incorrect', 'error')
            return render_template('auth/child_login.html', children=Child.query.all(),
                                   selected_child_id=int(child_id))

    children = Child.query.all()
    return render_template('auth/child_login.html', children=children)


@dual_route('/child/logout')
def child_logout():
    logout_user()
    return redirect(lang_url('/'))


# -- Child Pages --
@dual_route('/child/dashboard')
def child_dashboard():
    return render_template('child/dashboard.html')


@dual_route('/child/study')
def child_study():
    return render_template('child/study.html')


# -- Admin Pages --
@dual_route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
