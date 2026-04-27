"""Модели для книжного магазина."""

from datetime import datetime
from enum import Enum
from app.extensions import db


class BookStatus(Enum):
    """Статус книги."""
    ACTIVE = 'active'       # Книга доступна для продажи
    ARCHIVED = 'archived'   # Книга заархивирована (удалена)


class Book(db.Model):
    """Модель книги."""

    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    title_ru = db.Column(db.String(200), nullable=True, index=True)
    author = db.Column(db.String(100), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    publisher = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum(BookStatus), default=BookStatus.ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    stock = db.relationship('BookStock', back_populates='book', uselist=False, cascade='all, delete-orphan')
    sale_items = db.relationship('SaleItem', back_populates='book', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='book', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class BookStock(db.Model):
    """Модель остатков книг."""

    __tablename__ = 'book_stocks'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reserved = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    book = db.relationship('Book', back_populates='stock')

    @property
    def available(self) -> int:
        """Возвращает количество доступных книг."""
        return self.quantity - self.reserved

    def __repr__(self):
        return f'<BookStock book_id={self.book_id} quantity={self.quantity}>'


class SaleStatus(Enum):
    """Статус продажи."""
    COMPLETED = 'completed'   # Продажа завершена
    RETURNED = 'returned'     # Продажа возвращена
    CANCELLED = 'cancelled'   # Продажа отменена


class OrderStatus(Enum):
    """Статус заказа клиента."""
    PENDING = 'pending'       # Новый заказ, ожидает обработки менеджером
    APPROVED = 'approved'     # Заказ одобрен
    REJECTED = 'rejected'     # Заказ отклонён менеджером
    CANCELLED = 'cancelled'   # Заказ отменён клиентом/менеджером
    COMPLETED = 'completed'   # Заказ выполнен и оформлен как продажа


class QuestionStatus(Enum):
    """Статус вопроса клиента."""
    NEW = 'new'               # Новый вопрос, ожидает ответа менеджера
    RESOLVED = 'resolved'     # Вопрос обработан


class Sale(db.Model):
    """Модель продажи."""

    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(SaleStatus), default=SaleStatus.COMPLETED, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    items = db.relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')
    cashier = db.relationship('User', foreign_keys=[cashier_id])
    client = db.relationship('Client', back_populates='sales')

    def __repr__(self):
        return f'<Sale #{self.id} total={self.total_amount}>'


class SaleItem(db.Model):
    """Модель позиции в продаже."""

    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Связи
    sale = db.relationship('Sale', back_populates='items')
    book = db.relationship('Book', back_populates='sale_items')

    def __repr__(self):
        return f'<SaleItem sale_id={self.sale_id} book_id={self.book_id} qty={self.quantity}>'


class Client(db.Model):
    """Модель клиента."""

    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    user = db.relationship('User', backref='client_profile')
    sales = db.relationship('Sale', back_populates='client')
    orders = db.relationship('Order', back_populates='client')

    def __repr__(self):
        return f'<Client {self.last_name} {self.first_name}>'


class Order(db.Model):
    """Модель заказа клиента."""

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=True, unique=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    customer_comment = db.Column(db.Text, nullable=True)
    manager_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys=[user_id])
    manager = db.relationship('User', foreign_keys=[manager_id])
    client = db.relationship('Client', back_populates='orders')
    sale = db.relationship('Sale', foreign_keys=[sale_id])

    def __repr__(self):
        return f'<Order #{self.id} status={self.status}>'


class OrderItem(db.Model):
    """Модель позиции в заказе."""

    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Связи
    order = db.relationship('Order', back_populates='items')
    book = db.relationship('Book', back_populates='order_items')

    def __repr__(self):
        return f'<OrderItem order_id={self.order_id} book_id={self.book_id} qty={self.quantity}>'


class ManagerQuestion(db.Model):
    """Модель вопроса клиента менеджеру."""

    __tablename__ = 'manager_questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    topic = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(QuestionStatus), default=QuestionStatus.NEW, nullable=False, index=True)
    manager_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id])
    manager = db.relationship('User', foreign_keys=[manager_id])

    def __repr__(self):
        return f'<ManagerQuestion #{self.id} status={self.status}>'
