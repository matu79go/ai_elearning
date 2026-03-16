from flask import Blueprint, render_template, request, redirect, flash, session
from flask_login import login_user, logout_user, current_user
from models import db
from models.parent import Parent, ParentChild, generate_family_code
from models.child import Child
from routes import dual_route

auth_bp = Blueprint('auth', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


# ---- Parent Login ----
@dual_route(auth_bp, '/parent/login', methods=['GET', 'POST'])
def parent_login():
    if current_user.is_authenticated and isinstance(current_user, Parent):
        return redirect(_lang_url('/admin/dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        parent = Parent.query.filter_by(email=email).first()
        if parent and parent.check_password(password):
            login_user(parent)
            session['_parent_uid'] = parent.get_id()
            return redirect(_lang_url('/admin/dashboard'))
        flash('login_failed', 'error')
    return render_template('auth/parent_login.html')


# ---- Parent Register ----
@dual_route(auth_bp, '/parent/register', methods=['GET', 'POST'])
def parent_register():
    if current_user.is_authenticated and isinstance(current_user, Parent):
        return redirect(_lang_url('/admin/dashboard'))
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

        # Generate unique family code
        family_code = generate_family_code()
        while Parent.query.filter_by(family_code=family_code).first():
            family_code = generate_family_code()

        parent = Parent(email=email, display_name=display_name, family_code=family_code)
        parent.set_password(password)
        db.session.add(parent)
        db.session.commit()
        login_user(parent)
        session['_parent_uid'] = parent.get_id()
        return redirect(_lang_url('/admin/dashboard'))

    return render_template('auth/parent_register.html')


# ---- Parent Logout ----
@dual_route(auth_bp, '/parent/logout')
def parent_logout():
    session.pop('_parent_uid', None)
    logout_user()
    return redirect(_lang_url('/'))


# ---- Child Login ----
@dual_route(auth_bp, '/child/login', methods=['GET', 'POST'])
def child_login():
    if current_user.is_authenticated and isinstance(current_user, Child):
        return redirect(_lang_url('/child/dashboard'))
    step = request.form.get('step', 'code')
    family_code = request.form.get('family_code', '').strip().upper()
    children = []
    selected_child_id = None

    if request.method == 'POST':
        if step == 'code':
            # Step 1: Validate family code
            parent = Parent.query.filter_by(family_code=family_code).first()
            if parent:
                links = ParentChild.query.filter_by(parent_id=parent.parent_id).all()
                child_ids = [link.child_id for link in links]
                children = Child.query.filter(Child.child_id.in_(child_ids)).all() if child_ids else []
                if children:
                    return render_template('auth/child_login.html',
                                           step='select', children=children, family_code=family_code)
                flash('no_children_for_code', 'error')
            else:
                flash('invalid_family_code', 'error')

        elif step == 'pin':
            # Step 2: Validate PIN
            child_id = request.form.get('child_id')
            pin = request.form.get('pin', '')
            if child_id:
                child = db.session.get(Child, int(child_id))
                if child and child.check_pin(pin):
                    login_user(child)
                    session['_child_uid'] = child.get_id()
                    return redirect(_lang_url('/child/dashboard'))
                flash('pin_incorrect', 'error')
                selected_child_id = int(child_id)

            # Reload children for the family
            parent = Parent.query.filter_by(family_code=family_code).first()
            if parent:
                links = ParentChild.query.filter_by(parent_id=parent.parent_id).all()
                child_ids = [link.child_id for link in links]
                children = Child.query.filter(Child.child_id.in_(child_ids)).all() if child_ids else []
            return render_template('auth/child_login.html',
                                   step='select', children=children, family_code=family_code,
                                   selected_child_id=selected_child_id)

    return render_template('auth/child_login.html', step='code')


# ---- Child Logout ----
@dual_route(auth_bp, '/child/logout')
def child_logout():
    session.pop('_child_uid', None)
    logout_user()
    return redirect(_lang_url('/'))
