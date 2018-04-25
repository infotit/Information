from flask import render_template, g, redirect, url_for, jsonify, request, current_app

from info import db, constants
from info.models import News
from info.utils.common import user_login_data
from info.utils.image_storage import image_storage
from info.utils.response_code import RET
from . import profile_blu


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
