from flask import Blueprint, render_template
from routes import dual_route

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)


@dual_route(admin_dashboard_bp, '/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')
