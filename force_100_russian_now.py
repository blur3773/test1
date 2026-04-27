"""Быстро создаёт 100 книг русской литературы в кириллице без внешних запросов."""

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock


AUTHORS = [
    "Александр Пушкин",
    "Михаил Лермонтов",
    "Николай Гоголь",
    "Иван Тургенев",
    "Лев Толстой",
    "Фёдор Достоевский",
    "Антон Чехов",
    "Александр Куприн",
    "Максим Горький",
    "Иван Бунин",
    "Михаил Булгаков",
    "Борис Пастернак",
    "Александр Солженицын",
    "Марина Цветаева",
    "Анна Ахматова",
    "Иосиф Бродский",
]

SERIES = [
    "Русская классика",
    "Русская проза",
    "Литературное наследие",
    "Повести и рассказы",
    "Романы эпохи",
    "Страницы истории",
    "Поэзия и время",
    "Герои и судьбы",
]


def replace_catalog(total: int = 100) -> tuple[int, int, int]:
    old_books = Book.query.filter(Book.isbn.like("RUSLIT-2026-%")).all()
    deleted = len(old_books)
    for book in old_books:
        db.session.delete(book)

    created = 0
    for index in range(1, total + 1):
        title = f"{SERIES[(index - 1) % len(SERIES)]}. Книга {index}"
        author = AUTHORS[(index - 1) % len(AUTHORS)]
        isbn = f"RUSLIT-2026-{index:04d}"

        book = Book(
            title=title,
            title_ru=title,
            author=author,
            isbn=isbn,
            publisher="Русская библиотека",
            year=1850 + (index % 171),
            price=round(410 + (index % 27) * 15 + (index // 7), 2),
            description="Книга из русской литературной коллекции.",
            cover_url=None,
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()

        db.session.add(
            BookStock(
                book_id=book.id,
                quantity=9 + (index % 25),
                reserved=0,
            )
        )
        created += 1

    db.session.commit()
    active_count = Book.query.filter(Book.status == BookStatus.ACTIVE).count()
    return deleted, created, active_count


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        deleted_count, created_count, active_total = replace_catalog(100)
        print(f"RUSLIT_DELETED={deleted_count}")
        print(f"RUSLIT_CREATED={created_count}")
        print(f"ACTIVE_TOTAL={active_total}")
