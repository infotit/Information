import random
import re
from datetime import datetime

from flask import request, abort, make_response, current_app, jsonify, session

from info import redis_store, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu
from info.utils.captcha.captcha import captcha
from info import constants


@passport_blu.route('/register', methods=["POST"])
def regitster():
    """
    1. 获取参数 mobile， smscode， password
    2. 校验参数
    3. 若校验不通过，返回错误
    4. 若校验通过，从数据库中取出短信验证码，进行比较
    5. 比较不通过，返回错误。
    6. 比较通过，创建User的模型user
    7. 将user模型存到数据库
    8. 返回响应
    :return:
    """
    params_dict = request.json
    mobile = params_dict.get("mobile")
    smscode = params_dict.get("smscode")
    password = params_dict.get("password")

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not re.match("1[3456789]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码不正确")

    try:
        real_sms_code = redis_store.get("SMS_CODE_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已过期")

    if smscode != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码输入错误")
    user = User()

    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    user.last_login = datetime.now()
    try:
        db.session.add(user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库保存错误")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, errmsg="注册成功")



@passport_blu.route('/sms_code', methods=["POST"])
def send_sms_code():
    """
    1. 获取参数：手机号， 图片验证码文字， 图片验证码随机值
    2. 校验参数是否正确
    3. 从redis中取出保存的真实图片验证码， 与用户输入的验证码比较
    4. 若不一致， 返回错误
    5. 若一致，利用第三方工具发送短信验证码
    6. 保存短信验证码
    7. 返回发送验证码结果
    :return:
    """
    params_dict = request.json
    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not re.match('1[3456789]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    try:
        real_image_code = redis_store.get("imageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码失效")

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码输入错误")

    sms_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("短信验证码是：%s" % sms_code_str)

    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 60], "1")
    #
    # print(result)
    # if not result == 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg="短信验证码发送失败")

    try:
        redis_store.set("SMS_CODE_" + mobile, sms_code_str)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库存储错误")

    return jsonify(errno=RET.OK, errmsg="验证短信发送成功")


@passport_blu.route('/image_code')
def get_image_code():
    """
    1. 获取图片随机参数
    2. 校验参数
    3. 若符合要求，生成图片验证码
    4. 将图片随机值id'存入redis
    5. 返回图片验证码
    :return:
    """
    image_code_id = request.args.get("imageCodeId", None)

    if not image_code_id:
        return abort(403)

    name, text, image = captcha.generate_captcha()

    try:
        redis_store.set("imageCodeId_" + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)

    except Exception as e:
        current_app.logger.error(e)
        return abort(500)
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response
