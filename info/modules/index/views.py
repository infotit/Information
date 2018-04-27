from flask import current_app, render_template, session, request, jsonify

from info import constants
from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blu


@index_blu.route('/news_list')
def news_list():
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "10")

    try:
        page = int(page)
        per_page = int(per_page)
        cid = int(cid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 3. 查询数据并分页
    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    news_model_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_dict_list = []
    for news in news_model_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_list": news_dict_list
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@index_blu.route('/')
def index():
    """
    1. 判断用户是否登录
    2. 未登录，什么也不做
    3. 若登录，从数据库中查找用户信息
    4. 若未找到，什么也不做
    5. 若找到， 将用户信息从数据库取出，返回给模板
    :return:z
    """
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 新闻首页
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    category_dict_list = []
    for category in categories:
        category_dict_list.append(category.to_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_list": news_dict_list,
        "categories": category_dict_list
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")
