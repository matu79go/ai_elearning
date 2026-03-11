from flask import Blueprint, render_template
from routes import dual_route

child_study_bp = Blueprint('child_study', __name__)


@dual_route(child_study_bp, '/child/study')
def child_study():
    return render_template('child/study.html')
