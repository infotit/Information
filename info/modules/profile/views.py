from flask import render_template, g, redirect, url_for, jsonify, request, current_app

from info import db, constants
from info.models import News, User, Category
from info.utils.common import user_login_data
from info.utils.image_storage import image_storage
from info.utils.response_code import RET
from . import profile_blu


@profile_blu.route('/news_list')
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    user_news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        user_news_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    user_news_dict_list = []
    for news in user_news_list:
        user_news_dict_list.append(news.to_review_dict())

    data = {
        "current_page":current_page,
        "total_page": total_page,
        "news_list": user_news_dict_list
    }

    return render_template('news/user_news_list.html', data=data)


@profile_blu.route('/news_release', methods=["POST", "GET"])
@user_login_data
def news_release():
    if request.method == "GET":
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        category_dict_list = []
        for category in categories:
            category_dict_list.append(category.to_dict())  # id, name

        category_dict_list.pop(0)

        return render_template('news/user_news_release.html', data={"categories": category_dict_list})

    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")

    if not all([title, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        index_image_data = index_image.read()
        if index_image_data:
            key = image_storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传错误")
    else:
        print("上传成功！！！！！")

    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    # 1：待审核， 0：审核通过，其他：审核中
    news.status = 1
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.source = source
    news.user_id = g.user.id

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库保存错误")

    return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route('/collection')
@user_login_data
def user_collection():
    page = request.args.get("page", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    user = g.user
    collections_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        collections_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    news_collection_dict_list = []

    for news_collection in collections_list:
        news_collection_dict_list.append(news_collection.to_basic_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "collections": news_collection_dict_list
    }

    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/pass_info', methods=["POST", "GET"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template('news/user_pass_info.html')

    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user

    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码输入错误")

    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route('/pic_info', methods=["POST", "GET"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        return render_template('news/user_pic_info.html', data={"user": user.to_dict()})

    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        key = image_storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传错误")

    user.avatar_url = key
    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + key})


@profile_blu.route('/base_info', methods=["POST", "GET"])
@user_login_data
def base_info():
    if request.method == "GET":
        return render_template('news/user_base_info.html', data={"user": g.user.to_dict()})

    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route('/info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return redirect('/')
    data = {
        "user": user.to_dict()
    }
    return render_template('news/user.html', data=data)
