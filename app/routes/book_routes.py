

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt
from app.models import Book, BookStatus
from app.schemas import BookSchema
from app.services import BookService, StockService
from app.decorators import role_required, UserRole, manager_or_admin_required, admin_required
from app.utils import log_admin_action

book_bp = Blueprint('books', __name__, url_prefix='/api/books')


@book_bp.route('', methods=['GET'])
def get_all_books():

    status_param = request.args.get('status', 'active')
    verify_jwt_in_request(optional=True)
    current_user_role = get_jwt().get('role')


    if status_param == 'active' or status_param is None:
        books = BookService.get_all_books(BookStatus.ACTIVE)


    elif status_param == 'archived':
        if current_user_role not in ['manager', 'admin']:
            return jsonify({'message': 'Недостаточно прав для просмотра архивированных книг'}), 403
        books = BookService.get_all_books(BookStatus.ARCHIVED)


    elif status_param == 'all':
        if current_user_role not in ['manager', 'admin']:
            return jsonify({'message': 'Недостаточно прав для просмотра всех книг'}), 403
        books = BookService.get_all_books(None)

    else:
        return jsonify({'message': 'Неверный параметр status (active, archived, all)'}), 400

    return jsonify({
        'books': BookSchema(many=True).dump(books)
    }), 200


@book_bp.route('/search', methods=['GET'])
def search_books():

    query = request.args.get('q', '')
    if not query:
        return jsonify({'message': 'Введите поисковый запрос'}), 400

    books = BookService.search_books(query)
    return jsonify({
        'books': BookSchema(many=True).dump(books)
    }), 200


@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id: int):

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
        publication_place=data.get('publication_place'),
        page_count=data.get('page_count'),
        weight_grams=data.get('weight_grams'),
        print_run=data.get('print_run'),
        genre=data.get('genre'),
        description=data.get('description'),
        source_url=data.get('source_url'),
        stock_quantity=data.get('stock_quantity', 0)
    )

    if error:
        return jsonify(error), 400

    log_admin_action("book_create", f"book_id={book.id}, isbn={book.isbn}")
    return jsonify({
        'message': 'Книга успешно создана',
        'book': BookSchema().dump(book)
    }), 201


@book_bp.route('/<int:book_id>', methods=['PUT'])
@jwt_required()
@manager_or_admin_required
def update_book(book_id: int):

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
        publication_place=data.get('publication_place'),
        page_count=data.get('page_count'),
        weight_grams=data.get('weight_grams'),
        print_run=data.get('print_run'),
        genre=data.get('genre'),
        description=data.get('description'),
        source_url=data.get('source_url')
    )

    if error:
        return jsonify(error), 404

    log_admin_action("book_update", f"book_id={book_id}")
    return jsonify({
        'message': 'Книга успешно обновлена',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/archive', methods=['POST'])
@jwt_required()
@admin_required
def archive_book(book_id: int):

    book, error = BookService.archive_book(book_id)

    if error:
        return jsonify(error), 404

    log_admin_action("book_archive", f"book_id={book_id}")
    return jsonify({
        'message': 'Книга заархивирована',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/restore', methods=['POST'])
@jwt_required()
@admin_required
def restore_book(book_id: int):

    book, error = BookService.restore_book(book_id)

    if error:
        return jsonify(error), 404

    log_admin_action("book_restore", f"book_id={book_id}")
    return jsonify({
        'message': 'Книга восстановлена',
        'book': BookSchema().dump(book)
    }), 200


@book_bp.route('/<int:book_id>/stock', methods=['GET'])
def get_book_stock(book_id: int):

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

    data = request.get_json()
    quantity = data.get('quantity')

    if quantity is None:
        return jsonify({'message': 'Поле quantity обязательно'}), 400

    stock, error = StockService.update_stock(book_id, quantity)

    if error:
        return jsonify(error), 404

    log_admin_action("book_stock_update", f"book_id={book_id}, quantity={quantity}")
    from app.schemas import BookStockSchema
    return jsonify({
        'message': 'Остатки обновлены',
        'stock': BookStockSchema().dump(stock)
    }), 200


@book_bp.route('/<int:book_id>/stock/adjust', methods=['POST'])
@jwt_required()
@manager_or_admin_required
def adjust_book_stock(book_id: int):

    data = request.get_json()
    quantity_change = data.get('quantity_change')

    if quantity_change is None:
        return jsonify({'message': 'Поле quantity_change обязательно'}), 400

    stock, error = StockService.adjust_stock(book_id, quantity_change)

    if error:
        return jsonify(error), 404

    log_admin_action("book_stock_adjust", f"book_id={book_id}, quantity_change={quantity_change}")
    from app.schemas import BookStockSchema
    return jsonify({
        'message': 'Остатки скорректированы',
        'stock': BookStockSchema().dump(stock)
    }), 200
