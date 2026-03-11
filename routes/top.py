from flask import Blueprint, render_template
from routes import dual_route

top_bp = Blueprint('top', __name__)


@dual_route(top_bp, '/')
def index():
    return render_template('index.html')
