from flask import Blueprint, session, redirect, request

admin_blu = Blueprint('admin', __name__)

from . import views


@admin_blu.before_request
def check_admin():
    is_admin = session.get('is_admin', False)
    if not is_admin and request.url.endswith('/admin/login'):
        return redirect('/')
