"""Добавляет 100 книг в БД для демо-каталога."""

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock


AUTHORS = [
    "Алексей Воронов",
    "Мария Березина",
    "Илья Кравцов",
    "Софья Нестерова",
    "Дмитрий Орлов",
    "Екатерина Лескова",
    "Никита Сергеев",
    "Алина Рожкова",
]

SERIES = [
    "Городские хроники",
    "Школа магии",
    "Тайны старой библиотеки",
    "Научная фантастика",
    "Классика для всех",
    "Путешествия и открытия",
    "Современная проза",
    "Истории вдохновения",
]


def build_rows(total: int = 100) -> list[dict]:
    rows = []
    for index in range(1, total + 1):
        series = SERIES[(index - 1) % len(SERIES)]
        author = AUTHORS[(index - 1) % len(AUTHORS)]
        rows.append(
            {
                "title": f"{series}. Книга {index}",
                "author": author,
                "isbn": f"BFM-2026-{index:04d}",
                "publisher": "BookFlow Press",
                "year": 2008 + (index % 18),
                "price": round(290 + (index % 25) * 21 + (index // 5), 2),
                "description": f"Демо-издание #{index} для наполнения каталога.",
                "stock_quantity": 8 + (index % 27),
            }
        )
    return rows


def seed_books(total: int = 100) -> tuple[int, int]:
    created = 0
    existed = 0

    for row in build_rows(total):
        if Book.query.filter_by(isbn=row["isbn"]).first():
            existed += 1
            continue

        book = Book(
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            publisher=row["publisher"],
            year=row["year"],
            price=row["price"],
            description=row["description"],
            cover_url=None,
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()

        db.session.add(
            BookStock(
                book_id=book.id,
                quantity=row["stock_quantity"],
                reserved=0,
            )
        )
        created += 1

    db.session.commit()
    return created, existed


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        created_count, existed_count = seed_books(100)
        print(f"BOOKS_100 created={created_count} existed={existed_count}")
