from flask import render_template, g, redirect, url_for, jsonify, request, current_app

from info import db, constants
from info.models import News
from info.utils.common import user_login_data
from info.utils.image_storage import image_storage
from info.utils.response_code import RET
from . import profile_blu


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
        redirect('/')

    data = {
        "user": user.to_dict()
    }
    return render_template('news/user.html', data=data)
