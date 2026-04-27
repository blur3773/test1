"""Добавляет 100 книг русской литературы в активный каталог."""

from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock
from transliterate_all_books_to_ru import transliterate_text


REQUEST_TIMEOUT_SECONDS = 6
USER_AGENT = "BookFlowRussianLiteratureSeeder/1.0"
TARGET_COUNT = 100


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
    return any("А" <= ch <= "я" or ch == "ё" or ch == "Ё" for ch in value)


def collect_russian_lit_works(limit: int = TARGET_COUNT) -> list[dict]:
    collected: list[dict] = []
    seen: set[str] = set()
    offset = 0
    batch = 80

    while len(collected) < limit and offset < 1200:
        url = (
            "https://openlibrary.org/subjects/russian_literature.json"
            f"?limit={batch}&offset={offset}"
        )
        payload = fetch_json(url)
        works = (payload or {}).get("works") or []
        if not works:
            break

        for work in works:
            if len(collected) >= limit:
                break

            key = (work.get("key") or "").strip()
            title = (work.get("title") or "").strip()
            authors = work.get("authors") or []
            author_name = (authors[0].get("name") if authors else "") or "Неизвестный автор"
            cover_id = work.get("cover_id")
            year = work.get("first_publish_year")

            if not key or not title:
                continue
            if key in seen:
                continue
            seen.add(key)

            title_ru = title if has_cyrillic(title) else transliterate_text(title)

            collected.append(
                {
                    "title": title,
                    "title_ru": title_ru,
                    "author": author_name.strip(),
                    "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
                    "year": year if isinstance(year, int) else None,
                    "description": "Книга из подборки русской литературы.",
                }
            )

        offset += batch

    return collected[:limit]


def insert_books(books_payload: list[dict]) -> tuple[int, int]:
    created = 0
    existed = 0

    for index, payload in enumerate(books_payload, start=1):
        isbn = f"RUSLIT-2026-{index:04d}"
        if Book.query.filter_by(isbn=isbn).first():
            existed += 1
            continue

        book = Book(
            title=payload["title"],
            title_ru=payload["title_ru"],
            author=payload["author"],
            isbn=isbn,
            publisher="Russian Literature Collection",
            year=payload["year"],
            price=round(390 + (index % 34) * 17 + (index // 8), 2),
            description=payload["description"],
            cover_url=payload["cover_url"],
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()

        db.session.add(
            BookStock(
                book_id=book.id,
                quantity=10 + (index % 25),
                reserved=0,
            )
        )
        created += 1

    db.session.commit()
    return created, existed


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        works = collect_russian_lit_works(TARGET_COUNT)
        if len(works) < TARGET_COUNT:
            raise RuntimeError(
                f"Не удалось собрать {TARGET_COUNT} книг русской литературы. Собрано: {len(works)}"
            )

        created_count, existed_count = insert_books(works)
        active_count = Book.query.filter(Book.status == BookStatus.ACTIVE).count()
        rus_count = Book.query.filter(Book.isbn.like("RUSLIT-2026-%")).count()

        print(f"RUSLIT_COLLECTED={len(works)}")
        print(f"RUSLIT_CREATED={created_count}")
        print(f"RUSLIT_EXISTED={existed_count}")
        print(f"RUSLIT_TOTAL={rus_count}")
        print(f"ACTIVE_TOTAL={active_count}")
