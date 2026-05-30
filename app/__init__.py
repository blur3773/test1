

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


def _swagger_paths() -> dict:

    def response(description: str, schema_ref: str | None = None, array: bool = False) -> dict:
        content = {'description': description}
        if schema_ref:
            schema = {'$ref': schema_ref}
            if array:
                schema = {'type': 'array', 'items': schema}
            content['content'] = {'application/json': {'schema': schema}}
        return content

    def operation(
        tag: str,
        summary: str,
        *,
        security: bool = False,
        request_schema: dict | None = None,
        responses: dict | None = None,
        parameters: list[dict] | None = None,
    ) -> dict:
        item = {
            'tags': [tag],
            'summary': summary,
            'responses': responses or {
                '200': response('Успешный ответ'),
                '400': response('Ошибка запроса'),
            },
        }
        if security:
            item['security'] = [{'BearerAuth': []}]
        if request_schema:
            item['requestBody'] = {
                'required': True,
                'content': {'application/json': {'schema': request_schema}},
            }
        if parameters:
            item['parameters'] = parameters
        return item

    def path_param(name: str, description: str) -> dict:
        return {
            'name': name,
            'in': 'path',
            'required': True,
            'description': description,
            'schema': {'type': 'integer'},
        }

    def query_param(name: str, description: str, default: str | int | None = None) -> dict:
        schema = {'type': 'integer'} if isinstance(default, int) else {'type': 'string'}
        if default is not None:
            schema['default'] = default
        return {
            'name': name,
            'in': 'query',
            'required': False,
            'description': description,
            'schema': schema,
        }

    login_schema = {
        'type': 'object',
        'required': ['email', 'password'],
        'properties': {
            'email': {'type': 'string', 'format': 'email', 'example': 'admin@bookstore.com'},
            'password': {'type': 'string', 'example': 'Admin123!'},
        },
    }
    register_schema = {
        'type': 'object',
        'required': ['email', 'username', 'password'],
        'properties': {
            'email': {'type': 'string', 'format': 'email', 'example': 'client@example.com'},
            'username': {'type': 'string', 'example': 'client_user'},
            'password': {'type': 'string', 'example': 'Client123!'},
            'role': {'type': 'string', 'example': 'client'},
        },
    }
    sale_items_schema = {
        'type': 'object',
        'required': ['items'],
        'properties': {
            'items': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['book_id', 'quantity'],
                    'properties': {
                        'book_id': {'type': 'integer', 'example': 1},
                        'quantity': {'type': 'integer', 'example': 1},
                    },
                },
            },
            'client_id': {'type': 'integer', 'nullable': True, 'example': 1},
        },
    }
    order_checkout_schema = {
        **sale_items_schema,
        'properties': {
            **sale_items_schema['properties'],
            'customer_comment': {'type': 'string', 'nullable': True, 'example': 'Позвоните перед доставкой'},
        },
    }
    book_schema = {
        'type': 'object',
        'required': ['title', 'author', 'isbn', 'price'],
        'properties': {
            'title': {'type': 'string', 'example': 'Мастер и Маргарита'},
            'title_ru': {'type': 'string', 'example': 'Мастер и Маргарита'},
            'author': {'type': 'string', 'example': 'Михаил Булгаков'},
            'isbn': {'type': 'string', 'example': '978-5-17-123456-7'},
            'price': {'type': 'number', 'example': 599.99},
            'publisher': {'type': 'string', 'example': 'АСТ'},
            'year': {'type': 'integer', 'example': 2023},
            'description': {'type': 'string', 'example': 'Описание книги'},
            'stock_quantity': {'type': 'integer', 'example': 10},
        },
    }
    client_schema = {
        'type': 'object',
        'required': ['first_name', 'last_name'],
        'properties': {
            'first_name': {'type': 'string', 'example': 'Алексей'},
            'last_name': {'type': 'string', 'example': 'Смирнов'},
            'middle_name': {'type': 'string', 'nullable': True},
            'phone': {'type': 'string', 'example': '+7 (999) 123-45-67'},
            'email': {'type': 'string', 'format': 'email', 'example': 'client@example.com'},
            'user_id': {'type': 'integer', 'nullable': True, 'example': 4},
        },
    }

    return {
        '/api/auth/register': {
            'post': operation('Authentication', 'Регистрация пользователя', request_schema=register_schema, responses={'201': response('Пользователь создан'), '400': response('Ошибка регистрации')})
        },
        '/api/auth/login': {
            'post': operation('Authentication', 'Вход пользователя', request_schema=login_schema, responses={'200': response('Вход выполнен'), '401': response('Неверные данные')})
        },
        '/api/auth/me': {
            'get': operation('Authentication', 'Текущий пользователь', security=True, responses={'200': response('Профиль пользователя', '#/components/schemas/User'), '404': response('Пользователь не найден')})
        },
        '/api/auth/refresh': {
            'post': operation('Authentication', 'Обновить JWT токены', request_schema={'type': 'object', 'required': ['refresh_token'], 'properties': {'refresh_token': {'type': 'string'}}})
        },
        '/api/auth/logout': {
            'post': operation('Authentication', 'Выход пользователя', security=True)
        },
        '/api/books': {
            'get': operation('Books', 'Список книг', parameters=[query_param('status', 'active, archived или all', 'active')], responses={'200': response('Список книг')}),
            'post': operation('Books', 'Создать книгу', security=True, request_schema=book_schema, responses={'201': response('Книга создана'), '400': response('Ошибка данных')}),
        },
        '/api/books/search': {
            'get': operation('Books', 'Поиск книг', parameters=[query_param('q', 'Поисковая строка')], responses={'200': response('Результаты поиска')})
        },
        '/api/books/{book_id}': {
            'get': operation('Books', 'Данные книги', parameters=[path_param('book_id', 'ID книги')], responses={'200': response('Книга', '#/components/schemas/Book'), '404': response('Книга не найдена')}),
            'put': operation('Books', 'Обновить книгу', security=True, parameters=[path_param('book_id', 'ID книги')], request_schema=book_schema),
        },
        '/api/books/{book_id}/archive': {
            'post': operation('Books', 'Архивировать книгу', security=True, parameters=[path_param('book_id', 'ID книги')])
        },
        '/api/books/{book_id}/restore': {
            'post': operation('Books', 'Восстановить книгу', security=True, parameters=[path_param('book_id', 'ID книги')])
        },
        '/api/books/{book_id}/stock': {
            'get': operation('Stock', 'Остатки книги', parameters=[path_param('book_id', 'ID книги')], responses={'200': response('Остатки', '#/components/schemas/BookStock'), '404': response('Остатки не найдены')}),
            'put': operation('Stock', 'Обновить остаток', security=True, parameters=[path_param('book_id', 'ID книги')], request_schema={'type': 'object', 'required': ['quantity'], 'properties': {'quantity': {'type': 'integer', 'example': 25}}}),
        },
        '/api/books/{book_id}/stock/adjust': {
            'post': operation('Stock', 'Скорректировать остаток', security=True, parameters=[path_param('book_id', 'ID книги')], request_schema={'type': 'object', 'required': ['quantity_change'], 'properties': {'quantity_change': {'type': 'integer', 'example': -1}}})
        },
        '/api/sales': {
            'post': operation('Sales', 'Оформить продажу', security=True, request_schema=sale_items_schema, responses={'201': response('Продажа создана')}),
            'get': operation('Sales', 'Список продаж', security=True, responses={'200': response('Список продаж')}),
        },
        '/api/sales/{sale_id}': {
            'get': operation('Sales', 'Данные продажи', security=True, parameters=[path_param('sale_id', 'ID продажи')])
        },
        '/api/sales/{sale_id}/return': {
            'post': operation('Sales', 'Оформить возврат', security=True, parameters=[path_param('sale_id', 'ID продажи')])
        },
        '/api/sales/{sale_id}/cancel': {
            'post': operation('Sales', 'Отменить продажу', security=True, parameters=[path_param('sale_id', 'ID продажи')])
        },
        '/api/orders/checkout': {
            'post': operation('Orders', 'Клиентский заказ на подтверждение менеджеру', security=True, request_schema=order_checkout_schema, responses={'201': response('Заказ создан')})
        },
        '/api/orders/my': {
            'get': operation('Orders', 'Мои заказы', security=True, responses={'200': response('Список заказов')})
        },
        '/api/orders': {
            'get': operation('Orders', 'Заказы для менеджера', security=True, parameters=[query_param('status', 'pending, completed, rejected, cancelled или all', 'pending')])
        },
        '/api/orders/{order_id}/approve': {
            'post': operation('Orders', 'Подтвердить заказ', security=True, parameters=[path_param('order_id', 'ID заказа')])
        },
        '/api/orders/{order_id}/reject': {
            'post': operation('Orders', 'Отклонить заказ', security=True, parameters=[path_param('order_id', 'ID заказа')])
        },
        '/api/orders/{order_id}/cancel': {
            'post': operation('Orders', 'Отменить заказ', security=True, parameters=[path_param('order_id', 'ID заказа')])
        },
        '/api/clients': {
            'get': operation('Clients', 'Список клиентов', security=True),
            'post': operation('Clients', 'Создать клиента', security=True, request_schema=client_schema, responses={'201': response('Клиент создан')}),
        },
        '/api/clients/me': {
            'get': operation('Clients', 'Мой профиль клиента', security=True),
            'put': operation('Clients', 'Обновить мой профиль клиента', security=True, request_schema=client_schema),
        },
        '/api/clients/{client_id}': {
            'get': operation('Clients', 'Данные клиента', security=True, parameters=[path_param('client_id', 'ID клиента')]),
            'put': operation('Clients', 'Обновить клиента', security=True, parameters=[path_param('client_id', 'ID клиента')], request_schema=client_schema),
            'delete': operation('Clients', 'Удалить клиента', security=True, parameters=[path_param('client_id', 'ID клиента')]),
        },
        '/api/reports/sales': {
            'get': operation('Reports', 'Отчёт по продажам', security=True, parameters=[query_param('status', 'Фильтр статуса продажи')])
        },
        '/api/reports/sales/top-books': {
            'get': operation('Reports', 'Топ книг по продажам', security=True, parameters=[query_param('limit', 'Количество книг', 10)])
        },
        '/api/reports/stock': {
            'get': operation('Reports', 'Отчёт по остаткам', security=True)
        },
        '/api/reports/cashier/{cashier_id}': {
            'get': operation('Reports', 'Отчёт по кассиру', security=True, parameters=[path_param('cashier_id', 'ID кассира')])
        },
        '/api/recommendations/popular': {
            'get': operation('Recommendations', 'Популярные книги', parameters=[query_param('limit', 'Количество рекомендаций', 5)])
        },
        '/api/recommendations/cart': {
            'post': operation('Recommendations', 'Рекомендации по корзине', request_schema={'type': 'object', 'required': ['cart_book_ids'], 'properties': {'cart_book_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2]}, 'limit': {'type': 'integer', 'example': 5}}})
        },
        '/api/recommendations/history': {
            'get': operation('Recommendations', 'Рекомендации по истории покупок', security=True, parameters=[query_param('limit', 'Количество рекомендаций', 5)])
        },
        '/api/recommendations/personal': {
            'get': operation('Recommendations', 'Персональные рекомендации', security=True, parameters=[query_param('limit', 'Количество рекомендаций', 5), query_param('cart_book_ids', 'ID книг через запятую')])
        },
        '/api/recommendations/sets': {
            'post': operation('Recommendations', 'Дополнить книжный комплект', request_schema={'type': 'object', 'required': ['cart_book_ids'], 'properties': {'cart_book_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2]}}})
        },
        '/api/questions': {
            'post': operation('Questions', 'Отправить вопрос менеджеру', request_schema={'type': 'object', 'required': ['name', 'message'], 'properties': {'name': {'type': 'string', 'example': 'Иван'}, 'email': {'type': 'string', 'format': 'email'}, 'phone': {'type': 'string'}, 'topic': {'type': 'string'}, 'message': {'type': 'string', 'example': 'Нужна помощь с заказом'}}}, responses={'201': response('Вопрос создан')}),
            'get': operation('Questions', 'Список вопросов менеджеру', security=True, parameters=[query_param('status', 'new, resolved или all', 'new')]),
        },
    }


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
            {'name': 'Questions', 'description': 'Вопросы клиентов менеджеру'},
        ],
        'paths': _swagger_paths(),
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
