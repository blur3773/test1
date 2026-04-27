"""Переименовывает 100 популярных книг в русские названия."""

from app import create_app
from app.extensions import db
from app.models.store import Book


PREFIXES = [
    "Золотой",
    "Скрытый",
    "Последний",
    "Тихий",
    "Далекий",
    "Лунный",
    "Стеклянный",
    "Северный",
    "Огненный",
    "Старинный",
]

NOUNS = [
    "сад",
    "город",
    "маяк",
    "архив",
    "лабиринт",
    "дневник",
    "портал",
    "остров",
    "ключ",
    "маршрут",
]


def rename_books() -> tuple[int, int]:
    books = Book.query.filter(Book.isbn.like("POP-2026-%")).order_by(Book.isbn).all()
    renamed = 0

    for index, book in enumerate(books):
        prefix = PREFIXES[index // len(NOUNS)]
        noun = NOUNS[index % len(NOUNS)]
        new_title = f"{prefix} {noun}"
        if book.title != new_title:
            book.title = new_title
            renamed += 1

    db.session.commit()
    return len(books), renamed


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        total, renamed_count = rename_books()
        print(f"TOTAL_POPULAR={total}")
        print(f"RENAMED={renamed_count}")
