from flask import jsonify
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from info.models import User
from info.utils.response_code import RET

app = create_app("development")

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def createSuperUser(name, password):

    if not all([name, password]):
        print("参数不足")

    user = User()
    user.nick_name = name
    user.password = password
    user.is_admin = True
    user.mobile = name

    try:
        db.session.add(user)
        db.session.commit()
        print("添加成功！")
    except Exception as e:
        db.session.rollback()
        print(e)


if __name__ == '__main__':
    print(app.url_map)
    manager.run()
