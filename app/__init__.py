

from flask import Flask
from sqlalchemy import inspect, text
from logging.handlers import RotatingFileHandler
import logging
import os
from config import config
from app.extensions import init_extensions
from app.routes import register_blueprints
from app.models import User
from flasgger import Swagger
from app.utils import log_user_activity, mark_request_start


def _ensure_books_cover_column(app: Flask) -> None:

    from app.extensions import db

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if 'books' not in table_names:
        return

    columns = {column['name'] for column in inspector.get_columns('books')}
    if 'cover_url' in columns:
        return

    try:
        db.session.execute(text('ALTER TABLE books ADD COLUMN cover_url VARCHAR(500)'))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        app.logger.warning('Не удалось добавить колонку cover_url: %s', exc)


def _ensure_books_title_ru_column(app: Flask) -> None:

    from app.extensions import db

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if 'books' not in table_names:
        return

    columns = {column['name'] for column in inspector.get_columns('books')}
    if 'title_ru' in columns:
        return

    try:
        db.session.execute(text('ALTER TABLE books ADD COLUMN title_ru VARCHAR(200)'))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        app.logger.warning('Не удалось добавить колонку title_ru: %s', exc)


def _ensure_books_extended_columns(app: Flask) -> None:

    from app.extensions import db

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if 'books' not in table_names:
        return

    columns = {column['name'] for column in inspector.get_columns('books')}
    columns_to_add = [
        ('publication_place', 'VARCHAR(120)'),
        ('page_count', 'INTEGER'),
        ('weight_grams', 'INTEGER'),
        ('print_run', 'INTEGER'),
        ('genre', 'VARCHAR(255)'),
        ('source_url', 'VARCHAR(500)'),
    ]

    for column_name, column_type in columns_to_add:
        if column_name in columns:
            continue
        try:
            db.session.execute(text(f'ALTER TABLE books ADD COLUMN {column_name} {column_type}'))
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning('Не удалось добавить колонку %s: %s', column_name, exc)


def create_app(config_name='development'):

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    _configure_audit_loggers(app)


    app.config['SWAGGER'] = {
        'title': 'Flask Auth API',
        'uiversion': 3,
        'version': '1.0.0',
        'openapi': '3.0.0',
    }
    app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
    app.config['SWAGGER_UI_OPERATION_ID'] = True
    app.config['SWAGGER_UI_REQUEST_DURATION'] = True


    init_extensions(app)


    swagger_config = {
        'headers': [],
        'specs': [
            {
                'endpoint': 'apispec_1',
                'route': '/apispec_1.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            }
        ],
        'static_url_path': '/flasgger_static',
        'swagger_ui': True,
        'specs_route': '/swagger/',
    }

    swagger = Swagger(app, template={
        'info': {
            'title': 'Книжный магазин API',
            'description': 'API для управления книжным магазином: авторизация, книги, продажи, клиенты',
            'version': '1.0.0',
        },
        'basePath': '/',
        'tags': [
            {'name': 'Authentication', 'description': 'Аутентификация и регистрация'},
            {'name': 'Users', 'description': 'Управление пользователями (только администратор)'},
            {'name': 'Books', 'description': 'Управление книгами'},
            {'name': 'Stock', 'description': 'Управление остатками'},
            {'name': 'Sales', 'description': 'Продажи и возвраты'},
            {'name': 'Orders', 'description': 'Клиентские заказы и их обработка менеджером'},
            {'name': 'Clients', 'description': 'Управление клиентами'},
            {'name': 'Reports', 'description': 'Отчёты'},
            {'name': 'Recommendations', 'description': 'AI рекомендации книг (на основе корзины и истории покупок)'},
        ],
        'components': {
            'securitySchemes': {
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                    'description': 'Введите JWT токен (без префикса Bearer)'
                }
            },
            'schemas': {
                'User': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
                        'username': {'type': 'string', 'example': 'john_doe'},
                        'role': {'type': 'string', 'example': 'client'},
                        'is_active': {'type': 'boolean', 'example': True},
                        'is_verified': {'type': 'boolean', 'example': False},
                        'created_at': {'type': 'string', 'format': 'date-time'},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'Book': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'title': {'type': 'string', 'example': 'Мастер и Маргарита'},
                        'title_ru': {'type': 'string', 'example': 'Мастер и Маргарита'},
                        'author': {'type': 'string', 'example': 'Михаил Булгаков'},
                        'isbn': {'type': 'string', 'example': '978-5-17-123456-7'},
                        'publisher': {'type': 'string', 'example': 'АСТ'},
                        'year': {'type': 'integer', 'example': 2023},
                        'price': {'type': 'number', 'format': 'float', 'example': 599.99},
                        'description': {'type': 'string', 'example': 'Роман о дьяволе в Москве'},
                        'cover_url': {'type': 'string', 'example': 'https://covers.openlibrary.org/b/id/14603284-L.jpg'},
                        'status': {'type': 'string', 'example': 'active'},
                        'stock_quantity': {'type': 'integer', 'example': 50},
                        'available_quantity': {'type': 'integer', 'example': 45},
                        'created_at': {'type': 'string', 'format': 'date-time'},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'BookStock': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'book_id': {'type': 'integer', 'example': 1},
                        'quantity': {'type': 'integer', 'example': 50},
                        'reserved': {'type': 'integer', 'example': 5},
                        'available': {'type': 'integer', 'example': 45},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'Sale': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'cashier_id': {'type': 'integer', 'example': 2},
                        'cashier_name': {'type': 'string', 'example': 'Иван Петров'},
                        'client_id': {'type': 'integer', 'example': 1},
                        'client_name': {'type': 'string', 'example': 'Алексей Смирнов'},
                        'total_amount': {'type': 'number', 'format': 'float', 'example': 1199.98},
                        'status': {'type': 'string', 'example': 'completed'},
                        'items': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/SaleItem'}
                        },
                        'created_at': {'type': 'string', 'format': 'date-time'},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'OrderItem': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'book_id': {'type': 'integer', 'example': 2},
                        'book_title': {'type': 'string', 'example': '1984'},
                        'quantity': {'type': 'integer', 'example': 1},
                        'price': {'type': 'number', 'format': 'float', 'example': 649.00},
                        'subtotal': {'type': 'number', 'format': 'float', 'example': 649.00}
                    }
                },
                'Order': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 101},
                        'user_id': {'type': 'integer', 'example': 4},
                        'user_name': {'type': 'string', 'example': 'client_user'},
                        'client_id': {'type': 'integer', 'example': 1},
                        'manager_id': {'type': 'integer', 'example': 3},
                        'manager_name': {'type': 'string', 'example': 'manager'},
                        'sale_id': {'type': 'integer', 'example': 12},
                        'total_amount': {'type': 'number', 'format': 'float', 'example': 1898.00},
                        'status': {'type': 'string', 'example': 'pending'},
                        'customer_comment': {'type': 'string', 'example': 'Позвоните перед доставкой'},
                        'manager_comment': {'type': 'string', 'example': 'Подтверждён, готовим к выдаче'},
                        'items': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/OrderItem'}
                        },
                        'created_at': {'type': 'string', 'format': 'date-time'},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'SaleItem': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'book_id': {'type': 'integer', 'example': 1},
                        'book_title': {'type': 'string', 'example': 'Мастер и Маргарита'},
                        'quantity': {'type': 'integer', 'example': 2},
                        'price': {'type': 'number', 'format': 'float', 'example': 599.99},
                        'subtotal': {'type': 'number', 'format': 'float', 'example': 1199.98}
                    }
                },
                'Client': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'user_id': {'type': 'integer', 'example': 1},
                        'first_name': {'type': 'string', 'example': 'Алексей'},
                        'last_name': {'type': 'string', 'example': 'Смирнов'},
                        'middle_name': {'type': 'string', 'example': 'Иванович'},
                        'phone': {'type': 'string', 'example': '+7 (999) 123-45-67'},
                        'email': {'type': 'string', 'format': 'email', 'example': 'client@example.com'},
                        'created_at': {'type': 'string', 'format': 'date-time'},
                        'updated_at': {'type': 'string', 'format': 'date-time'}
                    }
                },
                'Recommendation': {
                    'type': 'object',
                    'properties': {
                        'book': {'$ref': '#/components/schemas/Book'},
                        'score': {'type': 'number', 'format': 'float', 'example': 10.5, 'description': 'Score релевантности'},
                        'reason': {'type': 'string', 'example': 'Рекомендуем по похожим жанрам (фантастика, приключения)', 'description': 'Причина рекомендации'}
                    }
                }
            }
        }
    }, config=swagger_config)


    register_blueprints(app)
    _register_user_activity_hooks(app)


    with app.app_context():
        from app.extensions import db


        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)

        db.create_all()
        _ensure_books_cover_column(app)
        _ensure_books_title_ru_column(app)
        _ensure_books_extended_columns(app)

    return app


def _configure_audit_loggers(app: Flask) -> None:
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    _ensure_rotating_handler(app, os.path.join(log_dir, "admin_audit.log"))
    _ensure_rotating_handler(app, os.path.join(log_dir, "user_activity.log"))
    app.logger.setLevel(logging.INFO)


def _ensure_rotating_handler(app: Flask, log_path: str) -> None:
    target_name = os.path.basename(log_path)

    has_handler = any(
        isinstance(handler, RotatingFileHandler) and getattr(handler, "baseFilename", "").endswith(target_name)
        for handler in app.logger.handlers
    )
    if has_handler:
        return

    audit_handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    app.logger.addHandler(audit_handler)


def _register_user_activity_hooks(app: Flask) -> None:
    @app.before_request
    def _before_request_log_marker():
        mark_request_start()

    @app.after_request
    def _after_request_user_activity(response):
        try:
            log_user_activity(response.status_code)
        except Exception:
            pass
        return response
