"""AI e-Learning System - Flask Application"""
import json
import os
from flask import Flask, g, request, session, redirect
from flask_login import LoginManager
from config import DATABASE_URL, SECRET_KEY
from models import db

# ---- i18n ----
TRANSLATIONS = {}
SUPPORTED_LANGS = ['en', 'ja']
DEFAULT_LANG = 'en'


def load_translations():
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    for lang in SUPPORTED_LANGS:
        filepath = os.path.join(translations_dir, f'{lang}.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            TRANSLATIONS[lang] = json.load(f)


def lang_url(path):
    """現在の言語に応じたURLを生成"""
    lang = g.get('lang', DEFAULT_LANG)
    if lang == 'ja':
        return '/ja' + path
    return path


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY

    # Initialize extensions
    db.init_app(app)

    # ---- Dual session: parent + child can coexist in same browser ----
    @app.before_request
    def _dual_session_swap():
        """URL pathに応じて _user_id を親/子供のセッションから切り替え"""
        path = request.path
        # /ja プレフィックスを除去
        clean = path[3:] if path.startswith('/ja/') or path == '/ja' else path
        clean = clean.lstrip('/')

        if clean.startswith('admin') or clean.startswith('parent'):
            uid = session.get('_parent_uid')
            if uid:
                session['_user_id'] = uid
            else:
                session.pop('_user_id', None)
        elif clean.startswith('child'):
            uid = session.get('_child_uid')
            if uid:
                session['_user_id'] = uid
            else:
                session.pop('_user_id', None)
        # else: top page, static等はそのまま

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.parent_login'

    @login_manager.unauthorized_handler
    def unauthorized():
        """未認証時: child系URLなら子供ログインへ、それ以外は親ログインへ"""
        path = request.path
        clean = path[3:] if path.startswith('/ja/') or path == '/ja' else path
        if clean.lstrip('/').startswith('child'):
            return redirect(lang_url('/child/login'))
        return redirect(lang_url('/parent/login'))

    # Load translations
    load_translations()

    # ---- i18n middleware ----
    @app.before_request
    def set_lang():
        path = request.path
        if path.startswith('/ja/') or path == '/ja':
            g.lang = 'ja'
        else:
            g.lang = 'en'
        g.t = TRANSLATIONS.get(g.lang, TRANSLATIONS[DEFAULT_LANG])

    @app.context_processor
    def inject_i18n():
        lang = g.get('lang', DEFAULT_LANG)
        t = g.get('t', TRANSLATIONS[DEFAULT_LANG])

        path = request.path
        if lang == 'ja':
            switch_path = path[3:] if path.startswith('/ja/') else path.replace('/ja', '/', 1)
            if not switch_path:
                switch_path = '/'
        else:
            switch_path = '/ja' + path

        # 子供画面用: サイドバー教科リスト（child/ページでのみクエリ実行）
        nav_subjects = []
        if '/child/' in request.path:
            from sqlalchemy import func as sqlfunc
            from models.material import Material
            nav_subjects = db.session.query(
                Material.subject,
                sqlfunc.count(Material.material_id).label('cnt'),
            ).filter_by(status='published').group_by(
                Material.subject
            ).order_by(Material.subject).all()

        return dict(t=t, lang=lang, switch_lang_url=switch_path,
                    lang_url=lang_url, nav_subjects=nav_subjects)

    # ---- User loader ----
    from models.parent import Parent
    from models.child import Child

    @login_manager.user_loader
    def load_user(user_id):
        """user_id format: 'parent:1' or 'child:2'"""
        if ':' not in user_id:
            return None
        user_type, uid = user_id.split(':', 1)
        if user_type == 'parent':
            return db.session.get(Parent, int(uid))
        elif user_type == 'child':
            return db.session.get(Child, int(uid))
        return None

    # ---- Register Blueprints ----
    from routes.top import top_bp
    from routes.auth import auth_bp
    from routes.child_dashboard import child_dashboard_bp
    from routes.child_study import child_study_bp
    from routes.admin_dashboard import admin_dashboard_bp
    from routes.admin_children import admin_children_bp
    from routes.admin_materials import admin_materials_bp
    from routes.child_learn import child_learn_bp

    for bp in [top_bp, auth_bp, child_dashboard_bp, child_study_bp, admin_dashboard_bp, admin_children_bp, admin_materials_bp, child_learn_bp]:
        app.register_blueprint(bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
