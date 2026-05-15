

from datetime import datetime
from enum import Enum
from app.extensions import db


class BookStatus(Enum):

    ACTIVE = 'active'
    ARCHIVED = 'archived'


class Book(db.Model):


    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    title_ru = db.Column(db.String(200), nullable=True, index=True)
    author = db.Column(db.String(100), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    publisher = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    publication_place = db.Column(db.String(120), nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    weight_grams = db.Column(db.Integer, nullable=True)
    print_run = db.Column(db.Integer, nullable=True)
    genre = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum(BookStatus), default=BookStatus.ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    stock = db.relationship('BookStock', back_populates='book', uselist=False, cascade='all, delete-orphan')
    sale_items = db.relationship('SaleItem', back_populates='book', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='book', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class BookStock(db.Model):


    __tablename__ = 'book_stocks'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reserved = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    book = db.relationship('Book', back_populates='stock')

    @property
    def available(self) -> int:

        return self.quantity - self.reserved

    def __repr__(self):
        return f'<BookStock book_id={self.book_id} quantity={self.quantity}>'


class SaleStatus(Enum):

    COMPLETED = 'completed'
    RETURNED = 'returned'
    CANCELLED = 'cancelled'


class OrderStatus(Enum):

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class QuestionStatus(Enum):

    NEW = 'new'
    RESOLVED = 'resolved'


class Sale(db.Model):


    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(SaleStatus), default=SaleStatus.COMPLETED, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    items = db.relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')
    cashier = db.relationship('User', foreign_keys=[cashier_id])
    client = db.relationship('Client', back_populates='sales')

    def __repr__(self):
        return f'<Sale #{self.id} total={self.total_amount}>'


class SaleItem(db.Model):


    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)


    sale = db.relationship('Sale', back_populates='items')
    book = db.relationship('Book', back_populates='sale_items')

    def __repr__(self):
        return f'<SaleItem sale_id={self.sale_id} book_id={self.book_id} qty={self.quantity}>'


class Client(db.Model):


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


    user = db.relationship('User', backref='client_profile')
    sales = db.relationship('Sale', back_populates='client')
    orders = db.relationship('Order', back_populates='client')

    def __repr__(self):
        return f'<Client {self.last_name} {self.first_name}>'


class Order(db.Model):


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


    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys=[user_id])
    manager = db.relationship('User', foreign_keys=[manager_id])
    client = db.relationship('Client', back_populates='orders')
    sale = db.relationship('Sale', foreign_keys=[sale_id])

    def __repr__(self):
        return f'<Order #{self.id} status={self.status}>'


class OrderItem(db.Model):


    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)


    order = db.relationship('Order', back_populates='items')
    book = db.relationship('Book', back_populates='order_items')

    def __repr__(self):
        return f'<OrderItem order_id={self.order_id} book_id={self.book_id} qty={self.quantity}>'


class ManagerQuestion(db.Model):


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
