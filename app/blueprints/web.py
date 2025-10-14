from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@web_bp.route('/archive')
def archive():
    """문구 아카이브 페이지 (기존 호환성을 위해 유지)"""
    return render_template('archive.html')

@web_bp.route('/archive/phrases')
def phrases_archive():
    """문구 아카이브 페이지"""
    return render_template('phrases_archive.html')

@web_bp.route('/archive/trends')
def trends_archive():
    """트렌드 아카이브 페이지"""
    return render_template('trends_archive.html')

@web_bp.route('/upload')
def upload():
    """CSV 업로드 페이지"""
    return render_template('upload.html')
