from flask import Blueprint

admin_blu = Blueprint('admin', __name__)

from . import views