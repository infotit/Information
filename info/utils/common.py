from flask import session, current_app, g
import functools
from info.models import User


def do_to_index(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)
    return wrapper

