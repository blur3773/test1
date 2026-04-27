"""Заполнение БД тестовыми пользователями и книгами."""

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from app.models.store import Book
from app.services.store_service import BookService


TEST_USERS = [
    {
        "email": "client@example.com",
        "username": "client_user",
        "password": "Client123!",
        "role": UserRole.CLIENT,
    },
    {
        "email": "cashier@bookstore.com",
        "username": "cashier",
        "password": "Cashier123!",
        "role": UserRole.CASHIER,
    },
    {
        "email": "manager@bookstore.com",
        "username": "manager",
        "password": "Manager123!",
        "role": UserRole.MANAGER,
    },
    {
        "email": "admin@bookstore.com",
        "username": "admin",
        "password": "Admin123!",
        "role": UserRole.ADMIN,
    },
]

BOOKS = [
    {
        "title": "Мастер и Маргарита",
        "author": "Михаил Булгаков",
        "isbn": "9785171491758",
        "price": 799.00,
        "publisher": "АСТ",
        "year": 2023,
        "description": "Классический роман о добре и зле в Москве 30-х годов.",
        "stock_quantity": 25,
    },
    {
        "title": "Преступление и наказание",
        "author": "Федор Достоевский",
        "isbn": "9785170906307",
        "price": 699.00,
        "publisher": "Эксмо",
        "year": 2022,
        "description": "Психологический роман о вине, совести и искуплении.",
        "stock_quantity": 18,
    },
    {
        "title": "1984",
        "author": "Джордж Оруэлл",
        "isbn": "9785171183660",
        "price": 649.00,
        "publisher": "АСТ",
        "year": 2021,
        "description": "Антиутопия о тотальном контроле и свободе личности.",
        "stock_quantity": 30,
    },
    {
        "title": "Гарри Поттер и философский камень",
        "author": "Дж. К. Роулинг",
        "isbn": "9785389074354",
        "price": 899.00,
        "publisher": "Махаон",
        "year": 2020,
        "description": "Первая книга о юном волшебнике Гарри Поттере.",
        "stock_quantity": 40,
    },
    {
        "title": "Три товарища",
        "author": "Эрих Мария Ремарк",
        "isbn": "9785170878840",
        "price": 739.00,
        "publisher": "АСТ",
        "year": 2023,
        "description": "История дружбы, любви и надежды в послевоенной Германии.",
        "stock_quantity": 22,
    },
    {
        "title": "Атомные привычки",
        "author": "Джеймс Клир",
        "isbn": "9785446111299",
        "price": 990.00,
        "publisher": "Питер",
        "year": 2024,
        "description": "Практическая система формирования полезных привычек.",
        "stock_quantity": 15,
    },
]


def seed_users() -> tuple[int, int]:
    created = 0
    existed = 0
    for data in TEST_USERS:
        user = User.query.filter((User.email == data["email"]) | (User.username == data["username"])).first()
        if user:
            existed += 1
            continue
        user = User(email=data["email"], username=data["username"], role=data["role"])
        user.set_password(data["password"])
        db.session.add(user)
        created += 1
    db.session.commit()
    return created, existed


def seed_books() -> tuple[int, int]:
    created = 0
    existed = 0
    for data in BOOKS:
        if Book.query.filter_by(isbn=data["isbn"]).first():
            existed += 1
            continue
        _, error = BookService.create_book(**data)
        if error:
            raise RuntimeError(error.get("message", "Ошибка при создании книги"))
        created += 1
    return created, existed


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        users_created, users_existed = seed_users()
        books_created, books_existed = seed_books()
        print(f"USERS created={users_created} existed={users_existed}")
        print(f"BOOKS created={books_created} existed={books_existed}")
