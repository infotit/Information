from flask import current_app, render_template, session

from info.models import User
from . import index_blu


@index_blu.route('/')
def index():
    """
    1. 判断用户是否登录
    2. 未登录，什么也不做
    3. 若登录，从数据库中查找用户信息
    4. 若未找到，什么也不做
    5. 若找到， 将用户信息从数据库取出，返回给模板
    :return:
    """
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    data = {
        "user": user.to_dict() if user else None
    }
    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")

