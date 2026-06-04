from app.extensions import db
from app.models import BookStatus, Client, OrderStatus, SaleStatus, UserRole
from app.services.book_cover_service import BookCoverService
from app.services.store_service import BookService, OrderService, StockService


def test_create_book_creates_stock_and_rejects_duplicate_isbn(app, monkeypatch):
    monkeypatch.setattr(
        BookCoverService,
        "find_cover_url",
        staticmethod(lambda title, author, isbn=None: None),
    )

    book, error = BookService.create_book(
        title="Мастер и Маргарита",
        author="Михаил Булгаков",
        isbn="978-UNIT-1",
        price=700,
        stock_quantity=12,
    )

    assert error is None
    assert book.id is not None
    assert book.status == BookStatus.ACTIVE
    assert book.stock.quantity == 12
    assert book.stock.available == 12

    duplicate, duplicate_error = BookService.create_book(
        title="Другая книга",
        author="Другой автор",
        isbn="978-UNIT-1",
        price=500,
    )

    assert duplicate is None
    assert duplicate_error["message"] == "Книга с таким ISBN уже существует"


def test_stock_reserve_adjust_and_release_flow(app, make_book):
    book = make_book(quantity=5, reserved=1)

    stock, reserve_error = StockService.reserve_stock(book.id, 3)
    assert reserve_error is None
    assert stock.quantity == 5
    assert stock.reserved == 4
    assert stock.available == 1

    missing_stock, missing_error = StockService.reserve_stock(book.id, 2)
    assert missing_stock is None
    assert missing_error["message"] == "Недостаточно книг на складе"

    released_stock, release_error = StockService.release_reservation(book.id, 10)
    assert release_error is None
    assert released_stock.reserved == 0

    adjusted_stock, adjust_error = StockService.adjust_stock(book.id, -99)
    assert adjust_error is None
    assert adjusted_stock.quantity == 0


def test_order_creation_reserves_stock_and_approval_creates_sale(app, make_user, make_book):
    client_user = make_user(email="buyer@example.com", username="buyer", role=UserRole.CLIENT)
    manager = make_user(email="manager@example.com", username="manager", role=UserRole.MANAGER)
    client = Client(first_name="Иван", last_name="Покупатель", user_id=client_user.id)
    db.session.add(client)
    db.session.commit()
    book = make_book(title="Заказная книга", isbn="ORDER-1", price=250, quantity=5)

    order, create_error = OrderService.create_order(
        user_id=client_user.id,
        items=[{"book_id": book.id, "quantity": 2}],
        customer_comment="Позвонить перед выдачей",
    )

    assert create_error is None
    assert order.status == OrderStatus.PENDING
    assert float(order.total_amount) == 500.0
    assert order.client_id == client.id
    assert book.stock.quantity == 5
    assert book.stock.reserved == 2

    approved_order, sale, approve_error = OrderService.approve_order(
        order_id=order.id,
        manager_id=manager.id,
        manager_comment="Подтверждено",
    )

    assert approve_error is None
    assert approved_order.status == OrderStatus.COMPLETED
    assert approved_order.manager_id == manager.id
    assert approved_order.sale_id == sale.id
    assert sale.status == SaleStatus.COMPLETED
    assert float(sale.total_amount) == 500.0
    assert len(sale.items) == 1
    assert book.stock.quantity == 3
    assert book.stock.reserved == 0


def test_client_can_cancel_pending_order_and_release_reservation(app, make_user, make_book):
    client_user = make_user(email="cancel@example.com", username="cancel_user", role=UserRole.CLIENT)
    book = make_book(title="Книга для отмены", isbn="ORDER-CANCEL-1", price=300, quantity=4)
    order, create_error = OrderService.create_order(
        user_id=client_user.id,
        items=[{"book_id": book.id, "quantity": 2}],
    )
    assert create_error is None
    assert book.stock.reserved == 2

    cancelled_order, cancel_error = OrderService.cancel_order(
        order_id=order.id,
        actor_user_id=client_user.id,
    )

    assert cancel_error is None
    assert cancelled_order.status == OrderStatus.CANCELLED
    assert book.stock.quantity == 4
    assert book.stock.reserved == 0
