

from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.book_routes import book_bp
from app.routes.sale_routes import sale_bp
from app.routes.order_routes import order_bp
from app.routes.client_routes import client_bp
from app.routes.report_routes import report_bp
from app.routes.recommendation_routes import recommendation_bp
from app.routes.question_routes import question_bp


def register_blueprints(app):

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(sale_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(question_bp)


__all__ = [
    'register_blueprints',
    'auth_bp',
    'user_bp',
    'book_bp',
    'sale_bp',
    'order_bp',
    'client_bp',
    'report_bp',
    'recommendation_bp',
    'question_bp'
]
