from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@web_bp.route('/archive')
def archive():
    """문구 아카이브 페이지"""
    return render_template('archive.html')
