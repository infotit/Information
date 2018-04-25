from flask import render_template, current_app, session, g, abort, request, jsonify

from info import constants, db
from info.models import News, User, Comment, CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blu


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = g.user
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    news = None

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        abort(404)

    news.clicks += 1
    # 判断是否是收藏
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    # 需求：查询当前用户在当前新闻里面都点赞了哪些评论
    # 1. 查询出当前新闻的所有评论 ([COMMENT]) 取到所有的评论id  [1, 2, 3, 4, 5]
    # 2. 再查询当前评论中哪些评论被当前用户所点赞 （[CommentLike]）查询comment_id 在第1步的评论id列表内的所有数据 & CommentList.user_id = g.user.id
    # 3. 取到所有被点赞的评论id 第2步查询出来是一个 [CommentLike] --> [3, 5]

    comment_like_ids = []
    try:
        comment_ids = [comment.id for comment in comments]
        comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                 CommentLike.user_id == g.user.id)
        comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
    except Exception as e:
        current_app.logger.error(e)

    comment_dict_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict['is_like'] = False
        if comment.id in comment_like_ids:
            comment_dict['is_like'] = True
        comment_dict_list.append(comment_dict)

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_list": news_dict_list,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comment_dict_list
    }

    return render_template('news/detail.html', data=data)


@news_blu.route('/news_collect', methods=["POST"])
@user_login_data
def collect_news():
    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误1")

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误2")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误3")
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg="数据查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")
    if action == "cancel_collect":
        if news in user.collection_news:
            user.collection_news.remove(news)
    else:
        if news not in user.collection_news:
            user.collection_news.append(news)

    return jsonify(errno=RET.OK, errmsg="保存成功", )


@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def comment_news():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误11")
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误22")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误33")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻未找到")

        # 初始化评论模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误1")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误2")

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误3")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        if not comment_like_model:
            # 点赞评论
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment.id
            db.session.add(comment_like_model)
            comment.like_count += 1
    else:
        # 取消点赞评论
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")
    return jsonify(errno=RET.OK, errmsg="OK")
