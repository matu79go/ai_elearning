from flask import Blueprint, render_template
from routes import dual_route

child_dashboard_bp = Blueprint('child_dashboard', __name__)


@dual_route(child_dashboard_bp, '/child/dashboard')
def child_dashboard():
    return render_template('child/dashboard.html')
