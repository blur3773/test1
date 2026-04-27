"""Заменяет демо-книги на 100 популярных книг с обложками OpenLibrary."""

from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock


SUBJECTS = [
    "fantasy",
    "science_fiction",
    "mystery",
    "thriller",
    "romance",
    "horror",
    "classics",
    "historical_fiction",
    "adventure",
    "young_adult",
    "biography",
    "history",
]

REQUEST_TIMEOUT_SECONDS = 5
USER_AGENT = "BookFlowSeeder/1.0"
TARGET_BOOKS = 100


def fetch_json(url: str) -> dict | None:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            raw_data = response.read()
    except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError):
        return None

    if not raw_data:
        return None

    try:
        return json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def collect_popular_books(limit: int = TARGET_BOOKS) -> list[dict]:
    collected: list[dict] = []
    seen_keys: set[str] = set()

    for subject in SUBJECTS:
        if len(collected) >= limit:
            break

        payload = fetch_json(f"https://openlibrary.org/subjects/{quote_plus(subject)}.json?limit=90")
        works = (payload or {}).get("works") or []

        for work in works:
            if len(collected) >= limit:
                break

            cover_id = work.get("cover_id")
            title = (work.get("title") or "").strip()
            key = (work.get("key") or "").strip()
            authors = work.get("authors") or []
            author_name = (authors[0].get("name") if authors else "") or "Неизвестный автор"
            first_publish_year = work.get("first_publish_year")

            if not cover_id or not title or not key:
                continue

            unique_key = f"{key}:{cover_id}"
            if unique_key in seen_keys:
                continue
            seen_keys.add(unique_key)

            collected.append(
                {
                    "title": title,
                    "author": author_name.strip(),
                    "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg",
                    "year": first_publish_year if isinstance(first_publish_year, int) else None,
                    "description": f"Популярная книга в категории {subject.replace('_', ' ')}.",
                }
            )

    return collected[:limit]


def reset_catalog_and_insert_popular(books_payload: list[dict]) -> tuple[int, int, int]:
    """
    Выполняет замену каталога:
    1) удаляет старые 100 демо-книг (BFM-2026-*)
    2) архивирует остальные активные книги
    3) добавляет 100 новых популярных книг
    """
    demo_books = Book.query.filter(Book.isbn.like("BFM-2026-%")).all()
    deleted_demo = len(demo_books)
    for book in demo_books:
        db.session.delete(book)

    for book in Book.query.filter(Book.status == BookStatus.ACTIVE).all():
        book.status = BookStatus.ARCHIVED

    created = 0
    for index, payload in enumerate(books_payload, start=1):
        isbn = f"POP-2026-{index:04d}"
        if Book.query.filter_by(isbn=isbn).first():
            continue

        price = round(420 + (index % 28) * 19 + (index // 7), 2)
        stock_quantity = 9 + (index % 31)

        book = Book(
            title=payload["title"],
            author=payload["author"],
            isbn=isbn,
            publisher="OpenLibrary Collection",
            year=payload["year"],
            price=price,
            description=payload["description"],
            cover_url=payload["cover_url"],
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()

        db.session.add(
            BookStock(
                book_id=book.id,
                quantity=stock_quantity,
                reserved=0,
            )
        )
        created += 1

    db.session.commit()
    active_count = Book.query.filter(Book.status == BookStatus.ACTIVE).count()
    return deleted_demo, created, active_count


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        popular_books = collect_popular_books(TARGET_BOOKS)
        if len(popular_books) < TARGET_BOOKS:
            raise RuntimeError(
                f"Не удалось собрать {TARGET_BOOKS} популярных книг с обложками. Собрано: {len(popular_books)}"
            )

        deleted_count, created_count, active_total = reset_catalog_and_insert_popular(popular_books)
        print(f"DELETED_DEMO={deleted_count}")
        print(f"CREATED_POPULAR={created_count}")
        print(f"ACTIVE_BOOKS_TOTAL={active_total}")
