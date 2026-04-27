"""Восстанавливает оригинальные названия у POP-2026 книг по данным OpenLibrary."""

from app import create_app
from app.extensions import db
from app.models.store import Book
from replace_with_popular_100_books import TARGET_BOOKS, collect_popular_books


def restore_titles() -> tuple[int, int]:
    popular_books = collect_popular_books(TARGET_BOOKS)
    if len(popular_books) < TARGET_BOOKS:
        raise RuntimeError(
            f"Не удалось загрузить {TARGET_BOOKS} популярных книг для восстановления. Получено: {len(popular_books)}"
        )

    updated = 0
    matched = 0

    for index, payload in enumerate(popular_books, start=1):
        isbn = f"POP-2026-{index:04d}"
        book = Book.query.filter_by(isbn=isbn).first()
        if not book:
            continue

        matched += 1
        new_title = payload["title"].strip()
        new_cover = payload["cover_url"]
        new_year = payload.get("year")

        changed = False
        if book.title != new_title:
            book.title = new_title
            changed = True
        if book.cover_url != new_cover:
            book.cover_url = new_cover
            changed = True
        if book.year != new_year:
            book.year = new_year
            changed = True
        if book.title_ru:
            book.title_ru = None
            changed = True

        if changed:
            updated += 1

    db.session.commit()
    return matched, updated


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        matched_count, updated_count = restore_titles()
        print(f"MATCHED={matched_count}")
        print(f"UPDATED={updated_count}")
