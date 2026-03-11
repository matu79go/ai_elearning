from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from models import db
from models.child import Child
from models.parent import ParentChild
from routes import dual_route

admin_children_bp = Blueprint('admin_children', __name__)


def _lang_url(path):
    from app import lang_url
    return lang_url(path)


@dual_route(admin_children_bp, '/admin/children', methods=['GET'])
@login_required
def admin_children():
    # Get children linked to this parent
    links = ParentChild.query.filter_by(parent_id=current_user.parent_id).all()
    child_ids = [link.child_id for link in links]
    children = Child.query.filter(Child.child_id.in_(child_ids)).all() if child_ids else []
    return render_template('admin/children.html', children=children)


@dual_route(admin_children_bp, '/admin/children/add', methods=['POST'])
@login_required
def admin_children_add():
    display_name = request.form.get('display_name', '').strip()
    grade = request.form.get('grade', '')
    pin = request.form.get('pin', '')
    pin_confirm = request.form.get('pin_confirm', '')

    errors = []
    if not display_name or not pin:
        errors.append('required_fields')
    if pin != pin_confirm:
        errors.append('pin_mismatch')
    if len(pin) != 4 or not pin.isdigit():
        errors.append('pin_must_be_4')

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(_lang_url('/admin/children'))

    child = Child(
        display_name=display_name,
        grade=int(grade) if grade else None,
        created_by=current_user.parent_id
    )
    child.set_pin(pin)
    db.session.add(child)
    db.session.flush()

    # Link parent to child
    link = ParentChild(
        parent_id=current_user.parent_id,
        child_id=child.child_id,
        role='owner'
    )
    db.session.add(link)
    db.session.commit()

    flash('child_added', 'success')
    return redirect(_lang_url('/admin/children'))


@dual_route(admin_children_bp, '/admin/children/<int:child_id>/delete', methods=['POST'])
@login_required
def admin_children_delete(child_id):
    # Verify parent owns this child
    link = ParentChild.query.filter_by(
        parent_id=current_user.parent_id, child_id=child_id
    ).first()
    if not link:
        return redirect(_lang_url('/admin/children'))

    # Delete link and child
    child = db.session.get(Child, child_id)
    if child:
        ParentChild.query.filter_by(child_id=child_id).delete()
        db.session.delete(child)
        db.session.commit()
        flash('child_deleted', 'success')

    return redirect(_lang_url('/admin/children'))
