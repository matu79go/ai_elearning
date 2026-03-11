"""AI e-Learning System - Flask Application"""
import json
import os
from flask import Flask, render_template, redirect, url_for, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import DATABASE_URL, SECRET_KEY

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---- i18n ----
TRANSLATIONS = {}
SUPPORTED_LANGS = ['en', 'ja']
DEFAULT_LANG = 'en'

translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
for lang in SUPPORTED_LANGS:
    filepath = os.path.join(translations_dir, f'{lang}.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        TRANSLATIONS[lang] = json.load(f)


def get_lang_from_path():
    """URLパスから言語を判定"""
    path = request.path
    if path.startswith('/ja/') or path == '/ja':
        return 'ja'
    return 'en'


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
        # /ja/xxx → /xxx
        switch_path = path[3:] if path.startswith('/ja/') else path.replace('/ja', '/', 1)
        if not switch_path:
            switch_path = '/'
    else:
        # /xxx → /ja/xxx
        switch_path = '/ja' + path

    return dict(t=t, lang=lang, switch_lang_url=switch_path)


# ---- Models ----
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='child')
    parent_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    total_points = db.Column(db.Integer, default=0)

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
        return str(self.user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---- Routes (English: default) ----
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/child/dashboard')
def child_dashboard():
    return render_template('child/dashboard.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')


# ---- Routes (Japanese: /ja/ prefix) ----
@app.route('/ja/')
def index_ja():
    return render_template('index.html')


@app.route('/ja/child/dashboard')
def child_dashboard_ja():
    return render_template('child/dashboard.html')


@app.route('/ja/admin/dashboard')
def admin_dashboard_ja():
    return render_template('admin/dashboard.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
