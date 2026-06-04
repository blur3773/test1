from __future__ import annotations

from datetime import timedelta

import pytest
from flask import Flask

from app.extensions import db, init_extensions
from app.models import Book, BookStatus, BookStock, User, UserRole


@pytest.fixture()
def app():
    test_app = Flask(__name__)
    test_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=1),
    )
    init_extensions(test_app)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def make_user(app):
    def factory(
        email: str = "user@example.com",
        username: str = "user",
        password: str = "StrongPass123!",
        role: UserRole = UserRole.CLIENT,
    ) -> User:
        user = User(email=email, username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return factory


@pytest.fixture()
def make_book(app):
    def factory(
        title: str = "Тестовая книга",
        author: str = "Автор",
        isbn: str = "ISBN-UNIT-1",
        price: float = 500.0,
        quantity: int = 5,
        reserved: int = 0,
    ) -> Book:
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            price=price,
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()
        db.session.add(BookStock(book_id=book.id, quantity=quantity, reserved=reserved))
        db.session.commit()
        return book

    return factory
