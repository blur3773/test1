"""Расширения Flask."""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()


def init_extensions(app):
    """Инициализация расширений приложения."""
    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
