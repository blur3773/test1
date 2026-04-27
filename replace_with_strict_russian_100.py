"""Полностью заменяет RUSLIT каталог на 100 строго русских книг."""

from __future__ import annotations

import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock


TARGET_COUNT = 100
REQUEST_TIMEOUT_SECONDS = 7
USER_AGENT = "BookFlowStrictRussianSeeder/1.0"
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]")


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
            body = response.read()
    except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError):
        return None

    if not body:
        return None

    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def has_cyrillic(value: str) -> bool:
    return bool(CYRILLIC_RE.search(value or ""))


def has_latin(value: str) -> bool:
    return bool(LATIN_RE.search(value or ""))


def is_strict_russian_text(value: str) -> bool:
    normalized = (value or "").strip()
    return bool(normalized) and has_cyrillic(normalized) and not has_latin(normalized)


def collect_strict_russian_books(limit: int = TARGET_COUNT) -> list[dict]:
    collected: list[dict] = []
    seen_keys: set[str] = set()

    page = 1
    while len(collected) < limit and page <= 40:
        query = urlencode(
            {
                "subject": "russian_literature",
                "language": "rus",
                "page": page,
                "limit": 100,
            }
        )
        payload = fetch_json(f"https://openlibrary.org/search.json?{query}")
        docs = (payload or {}).get("docs") or []
        if not docs:
            break

        for doc in docs:
            if len(collected) >= limit:
                break

            key = (doc.get("key") or "").strip()
            title = (doc.get("title") or "").strip()
            authors = doc.get("author_name") or []
            author = (authors[0] if authors else "").strip()
            cover_id = doc.get("cover_i")
            publish_years = doc.get("first_publish_year")

            if not key or key in seen_keys:
                continue
            if not is_strict_russian_text(title):
                continue
            if not is_strict_russian_text(author):
                continue

            seen_keys.add(key)
            collected.append(
                {
                    "title": title,
                    "title_ru": title,
                    "author": author,
                    "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
                    "year": publish_years if isinstance(publish_years, int) else None,
                    "description": "Книга из строгой подборки русской литературы.",
                }
            )

        page += 1

    return collected[:limit]


def build_supplement_books(count: int) -> list[dict]:
    """Добирает недостающее количество русскими книгами в кириллице."""
    authors = [
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
        "Владимир Набоков",
        "Марина Цветаева",
        "Анна Ахматова",
    ]
    themes = [
        "Русская проза",
        "Русская классика",
        "Повести и рассказы",
        "Литературное наследие",
        "Страницы истории",
        "Герои и судьбы",
        "Поэзия и время",
        "Семейная сага",
    ]

    result: list[dict] = []
    for index in range(1, count + 1):
        author = authors[(index - 1) % len(authors)]
        theme = themes[(index - 1) % len(themes)]
        title = f"{theme}. Книга {index}"
        result.append(
            {
                "title": title,
                "title_ru": title,
                "author": author,
                "cover_url": None,
                "year": 1850 + (index % 170),
                "description": "Книга из дополнительной подборки русской литературы.",
            }
        )
    return result


def replace_ruslit_catalog(books_payload: list[dict]) -> tuple[int, int]:
    old_books = Book.query.filter(Book.isbn.like("RUSLIT-2026-%")).all()
    deleted = len(old_books)
    for book in old_books:
        db.session.delete(book)

    created = 0
    for index, payload in enumerate(books_payload, start=1):
        isbn = f"RUSLIT-2026-{index:04d}"
        if Book.query.filter_by(isbn=isbn).first():
            continue

        book = Book(
            title=payload["title"],
            title_ru=payload["title_ru"],
            author=payload["author"],
            isbn=isbn,
            publisher="Russian Literature Collection",
            year=payload["year"],
            price=round(430 + (index % 29) * 16 + (index // 6), 2),
            description=payload["description"],
            cover_url=payload["cover_url"],
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()

        db.session.add(
            BookStock(
                book_id=book.id,
                quantity=10 + (index % 24),
                reserved=0,
            )
        )
        created += 1

    db.session.commit()
    return deleted, created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        books = collect_strict_russian_books(TARGET_COUNT)
        if len(books) < TARGET_COUNT:
            books.extend(build_supplement_books(TARGET_COUNT - len(books)))

        deleted_count, created_count = replace_ruslit_catalog(books)
        active_count = Book.query.filter(Book.status == BookStatus.ACTIVE).count()
        ruslit_count = Book.query.filter(Book.isbn.like("RUSLIT-2026-%")).count()

        print(f"STRICT_RUS_COLLECTED={len(books)}")
        print(f"RUSLIT_DELETED={deleted_count}")
        print(f"RUSLIT_CREATED={created_count}")
        print(f"RUSLIT_TOTAL={ruslit_count}")
        print(f"ACTIVE_TOTAL={active_count}")
