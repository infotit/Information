import time
from datetime import datetime, timedelta

from flask import render_template, request, jsonify, current_app, session, redirect, url_for, g

from info.models import User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import admin_blu


@admin_blu.route('/user_count')
def user_count():
    total_count = 0
    mon_count = 0
    day_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    t = time.localtime()
    begin_mon = datetime.strptime(("%d-%02d-01" % (t.tm_year, t.tm_mon)), "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon).count()
    except Exception as e:
        current_app.logger.error(e)

    begin_day = datetime.strptime(("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day).count()
    except Exception as e:
        current_app.logger.error(e)

    active_time = []
    active_count = []

    # 今天0点0分0秒
    # 今天24点
    # 查询 今天0点0分0秒 <= User.last_login < 今天24点
    today = datetime.strptime(("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    for i in range(0, 31):
        today_begin = today - timedelta(days=i)
        today_end = today - timedelta(days=(i - 1))
        today_count = User.query.filter(User.is_admin == False, User.last_login >= today_begin,
                                        User.last_login < today_end).count()
        active_time.append(today_begin.strftime("%Y-%m-%d"))
        active_count.append(today_count)

    active_time.reverse()
    active_count.reverse()
    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template('admin/user_count.html', data=data)




@admin_blu.route('/')
@user_login_data
def index():
    user = g.user
    data = {"user": user.to_dict() if user else None}
    return render_template('admin/index.html', data=data)


@admin_blu.route('/login', methods=["POST", "GET"])
def admin_login():
    if request.method == "GET":
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
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
