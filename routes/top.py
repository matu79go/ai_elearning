import os
from flask import Blueprint, render_template, send_from_directory, make_response, current_app
from routes import dual_route

top_bp = Blueprint('top', __name__)


@dual_route(top_bp, '/')
def index():
    return render_template('index.html')


@top_bp.route('/sw.js')
def service_worker():
    resp = make_response(
        send_from_directory(
            os.path.join(current_app.root_path, 'static'), 'sw.js'
        )
    )
    resp.headers['Content-Type'] = 'application/javascript'
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp
