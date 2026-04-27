"""Переводит названия всех книг на русский и сохраняет в title_ru."""

from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app import create_app
from app.extensions import db
from app.models.store import Book


TRANSLATE_URL = (
    "https://translate.googleapis.com/translate_a/single"
    "?client=gtx&sl=auto&tl=ru&dt=t&q="
)
USER_AGENT = "BookFlowTranslator/1.0"
REQUEST_TIMEOUT_SECONDS = 6


def translate_to_ru(text: str) -> str | None:
    """Переводит строку на русский через публичный Google endpoint."""
    if not text.strip():
        return None

    request = Request(
        TRANSLATE_URL + quote(text),
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
        payload = json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    chunks = payload[0] if isinstance(payload, list) and payload else []
    translated = "".join(
        part[0] for part in chunks if isinstance(part, list) and part and isinstance(part[0], str)
    ).strip()
    return translated or None


def translate_all_books() -> tuple[int, int]:
    books = Book.query.order_by(Book.id).all()
    updated = 0

    for book in books:
        translated = translate_to_ru(book.title)
        if not translated:
            continue
        if book.title_ru == translated:
            continue
        book.title_ru = translated
        updated += 1

    db.session.commit()
    return len(books), updated


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        total_count, updated_count = translate_all_books()
        print(f"TOTAL_BOOKS={total_count}")
        print(f"UPDATED_TITLE_RU={updated_count}")
