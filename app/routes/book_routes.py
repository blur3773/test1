"""Роуты для управления книгами."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt
from app.models import Book, BookStatus
from app.schemas import BookSchema
from app.services import BookService, StockService
from app.decorators import role_required, UserRole, manager_or_admin_required, admin_required

book_bp = Blueprint('books', __name__, url_prefix='/api/books')


@book_bp.route('', methods=['GET'])
def get_all_books():
    """
    Список книг (все)

    ---
    tags:
      - Books
    summary: Список книг
    description: Возвращает список активных книг (публично). Архив/all доступны только авторизованным ролям.
    parameters:
      - in: query
        name: status
        required: false
        schema:
          type: string
          enum: [active, archived, all]
        description: active - только активные (по умолчанию), archived - только архивированные, all - все (только менеджер/админ)
    responses:
      200:
        description: Список книг
        content:
          application/json:
            schema:
              type: object
              properties:
                books:
                  type: array
                  items:
                    $ref: '#/components/schemas/Book'
      403:
        description: Недостаточно прав для просмотра архивированных книг
    """
    status_param = request.args.get('status', 'active')  # По умолчанию только активные
    verify_jwt_in_request(optional=True)
    current_user_role = get_jwt().get('role')

    # По умолчанию показываем только активные книги
    if status_param == 'active' or status_param is None:
        books = BookService.get_all_books(BookStatus.ACTIVE)

    # Архивированные книги — кассир, менеджер и админ
    elif status_param == 'archived':
        if current_user_role not in ['cashier', 'manager', 'admin']:
            return jsonify({'message': 'Недостаточно прав для просмотра архивированных книг'}), 403
        books = BookService.get_all_books(BookStatus.ARCHIVED)

    # Все книги — только менеджер и админ
    elif status_param == 'all':
        if current_user_role not in ['manager', 'admin']:
            return jsonify({'message': 'Недостаточно прав для просмотра всех книг'}), 403
        books = BookService.get_all_books(None)  # Без фильтра

    else:
        return jsonify({'message': 'Неверный параметр status (active, archived, all)'}), 400

    return jsonify({
        'books': BookSchema(many=True).dump(books)
    }), 200


@book_bp.route('/search', methods=['GET'])
def search_books():
    """
    Поиск книг (все)

    ---
    tags:
      - Books
    summary: Поиск книг
    description: Ищет книги по названию, автору или ISBN
    parameters:
      - in: query
        name: q
        required: true
        schema:
          type: string
        description: Поисковый запрос
    responses:
      200:
        description: Результаты поиска
        content:
          application/json:
            schema:
              type: object
              properties:
                books:
                  type: array
                  items:
                    $ref: '#/components/schemas/Book'
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({'message': 'Введите поисковый запрос'}), 400

    books = BookService.search_books(query)
    return jsonify({
        'books': BookSchema(many=True).dump(books)
    }), 200


@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id: int):
    """
    Получение книги по ID (все)

    ---
    tags:
      - Books
    summary: Данные книги
    description: Возвращает информацию о книге по её ID
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    responses:
      200:
        description: Данные книги
        content:
          application/json:
            schema:
              type: object
              properties:
                book:
                  $ref: '#/components/schemas/Book'
      404:
        description: Книга не найдена
    """
    book = BookService.get_book_by_id(book_id)
    if not book:
        return jsonify({'message': 'Книга не найдена'}), 404

    return jsonify({
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('', methods=['POST'])
@jwt_required()
@manager_or_admin_required
def create_book():
    """
    Создание новой книги (менеджер, администратор)

    ---
    tags:
      - Books
    summary: Создать книгу
    description: Создаёт новую книгу
    security:
      - BearerAuth: 0
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - title
              - author
              - isbn
              - price
            properties:
              title:
                type: string
                example: "Мастер и Маргарита"
              author:
                type: string
                example: "Михаил Булгаков"
              isbn:
                type: string
                example: "978-5-17-123456-7"
              price:
                type: number
                format: float
                example: 599.99
              publisher:
                type: string
                example: "АСТ"
              year:
                type: integer
                example: 2023
              description:
                type: string
                example: "Роман о дьяволе в Москве"
              stock_quantity:
                type: integer
                default: 0
                example: 50
    responses:
      201:
        description: Книга успешно создана
      400:
        description: Ошибка валидации данных
      403:
        description: Недостаточно прав
    """
    data = request.get_json()

    required_fields = ['title', 'author', 'isbn', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Поле {field} обязательно'}), 400

    book, error = BookService.create_book(
        title=data['title'],
        title_ru=data.get('title_ru'),
        author=data['author'],
        isbn=data['isbn'],
        price=data['price'],
        publisher=data.get('publisher'),
        year=data.get('year'),
        description=data.get('description'),
        stock_quantity=data.get('stock_quantity', 0)
    )

    if error:
        return jsonify(error), 400

    return jsonify({
        'message': 'Книга успешно создана',
        'book': BookSchema().dump(book)
    }), 201


@book_bp.route('/<int:book_id>', methods=['PUT'])
@jwt_required()
@manager_or_admin_required
def update_book(book_id: int):
    """
    Обновление книги (менеджер, администратор)

    ---
    tags:
      - Books
    summary: Обновить книгу
    description: Обновляет данные книги
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
              author:
                type: string
              isbn:
                type: string
              price:
                type: number
                format: float
              publisher:
                type: string
              year:
                type: integer
              description:
                type: string
    responses:
      200:
        description: Книга успешно обновлена
      404:
        description: Книга не найдена
      403:
        description: Недостаточно прав
    """
    data = request.get_json()

    book, error = BookService.update_book(
        book_id=book_id,
        title=data.get('title'),
        title_ru=data.get('title_ru'),
        author=data.get('author'),
        isbn=data.get('isbn'),
        price=data.get('price'),
        publisher=data.get('publisher'),
        year=data.get('year'),
        description=data.get('description')
    )

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Книга успешно обновлена',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/archive', methods=['POST'])
@jwt_required()
@admin_required
def archive_book(book_id: int):
    """
    Архивация книги (администратор)

    ---
    tags:
      - Books
    summary: Архивировать книгу
    description: Архивирует книгу
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    responses:
      200:
        description: Книга заархивирована
      404:
        description: Книга не найдена
      403:
        description: Недостаточно прав
    """
    book, error = BookService.archive_book(book_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Книга заархивирована',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/restore', methods=['POST'])
@jwt_required()
@admin_required
def restore_book(book_id: int):
    """
    Восстановление книги (администратор)

    ---
    tags:
      - Books
    summary: Восстановить книгу
    description: Восстанавливает книгу из архива
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    responses:
      200:
        description: Книга восстановлена
      404:
        description: Книга не найдена
      403:
        description: Недостаточно прав
    """
    book, error = BookService.restore_book(book_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Книга восстановлена',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/stock', methods=['GET'])
def get_book_stock(book_id: int):
    """
    Получение остатков книги (все)

    ---
    tags:
      - Stock
    summary: Остатки книги
    description: Возвращает информацию об остатках книги
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    responses:
      200:
        description: Данные об остатках
        content:
          application/json:
            schema:
              type: object
              properties:
                stock:
                  $ref: '#/components/schemas/BookStock'
      404:
        description: Книга не найдена
    """
    book = BookService.get_book_by_id(book_id)
    if not book:
        return jsonify({'message': 'Книга не найдена'}), 404

    stock = StockService.get_stock(book_id)
    if not stock:
        return jsonify({'message': 'Остатки не найдены'}), 404

    from app.schemas import BookStockSchema
    return jsonify({
        'stock': BookStockSchema().dump(stock)
    }), 200


@book_bp.route('/<int:book_id>/stock', methods=['PUT'])
@jwt_required()
@manager_or_admin_required
def update_book_stock(book_id: int):
    """
    Обновление остатков книги (менеджер, администратор)

    ---
    tags:
      - Stock
    summary: Обновить остатки
    description: Устанавливает новое количество книг на складе
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - quantity
            properties:
              quantity:
                type: integer
                example: 100
    responses:
      200:
        description: Остатки обновлены
      404:
        description: Книга не найдена
      403:
        description: Недостаточно прав
    """
    data = request.get_json()
    quantity = data.get('quantity')

    if quantity is None:
        return jsonify({'message': 'Поле quantity обязательно'}), 400

    stock, error = StockService.update_stock(book_id, quantity)

    if error:
        return jsonify(error), 404

    from app.schemas import BookStockSchema
    return jsonify({
        'message': 'Остатки обновлены',
        'stock': BookStockSchema().dump(stock)
    }), 200


@book_bp.route('/<int:book_id>/stock/adjust', methods=['POST'])
@jwt_required()
@manager_or_admin_required
def adjust_book_stock(book_id: int):
    """
    Корректировка остатков (менеджер, администратор)

    ---
    tags:
      - Stock
    summary: Корректировка остатков
    description: Корректирует количество книг на складе
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: ID книги
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - quantity_change
            properties:
              quantity_change:
                type: integer
                example: 50
                description: Положительное число для добавления, отрицательное для вычитания
    responses:
      200:
        description: Остатки скорректированы
      404:
        description: Книга не найдена
      403:
        description: Недостаточно прав
    """
    data = request.get_json()
    quantity_change = data.get('quantity_change')

    if quantity_change is None:
        return jsonify({'message': 'Поле quantity_change обязательно'}), 400

    stock, error = StockService.adjust_stock(book_id, quantity_change)

    if error:
        return jsonify(error), 404

    from app.schemas import BookStockSchema
    return jsonify({
        'message': 'Остатки скорректированы',
        'stock': BookStockSchema().dump(stock)
    }), 200
