from flask import render_template, request, jsonify, current_app, session, redirect, url_for

from info.models import User
from info.utils.response_code import RET
from . import admin_blu


@admin_blu.route('/')
def index():
    return render_template('admin/index.html')


@admin_blu.route('/login', methods=["POST", "GET"])
def admin_login():
    if request.method == "GET":
        return render_template('admin/login.html')

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        return render_template('admin/login.html', errmsg='参数错误')

    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据库错误')

    if not user:
        return render_template('admin/login.html', errmsg='用户不存在')

    if not user.check_password(password):
        return render_template('admin/login.html', errmsg='密码输入错误')

    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['is_admin'] = user.is_admin

    return redirect(url_for('admin.index'))
