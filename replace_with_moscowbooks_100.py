"""Заменяет активный каталог на 100 книг из https://www.moscowbooks.ru/books/fiction/."""

from __future__ import annotations

import json
import re
import socket
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app import create_app
from app.extensions import db
from app.models.store import Book, BookStatus, BookStock


BASE_URL = "https://www.moscowbooks.ru"
CATEGORY_URL = f"{BASE_URL}/books/fiction/"
TARGET_COUNT = 100
REQUEST_TIMEOUT_SECONDS = 12
USER_AGENT = "BookFlowMoscowBooksImporter/1.0"


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return ""
            data = response.read()
    except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError):
        return ""
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def clean_text(value: str) -> str:
    normalized = unescape(value or "")
    normalized = normalized.replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def parse_page_payload(html: str) -> tuple[list[dict], int, int]:
    page_info_match = re.search(r"window\.MbPageInfo\s*=\s*(\{.*?\});</script>", html, re.DOTALL)
    if not page_info_match:
        return [], 1, 1

    raw_json = page_info_match.group(1)
    try:
        page_info = json.loads(raw_json)
    except json.JSONDecodeError:
        return [], 1, 1

    products = page_info.get("Products") or []
    page = int(page_info.get("Page") or 1)
    total_pages = int(page_info.get("TotalPagesCount") or 1)
    return products, page, total_pages


def parse_authors(html: str) -> list[str]:
    authors = re.findall(
        r'<div class="book-preview__author">\s*<a[^>]*class="author-name"[^>]*>(.*?)</a>',
        html,
        flags=re.DOTALL,
    )
    return [clean_text(author) for author in authors]


def collect_books(limit: int = TARGET_COUNT) -> list[dict]:
    books: list[dict] = []
    seen_ids: set[str] = set()
    page = 1
    total_pages = 1

    while len(books) < limit and page <= total_pages:
        url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}?page={page}"
        html = fetch_html(url)
        if not html:
            break

        products, current_page, found_total_pages = parse_page_payload(html)
        authors = parse_authors(html)
        total_pages = found_total_pages or total_pages

        for index, product in enumerate(products):
            product_id = str(product.get("Id") or "").strip()
            if not product_id or product_id in seen_ids:
                continue
            seen_ids.add(product_id)

            title = clean_text(str(product.get("Name") or ""))
            if not title:
                continue

            unit_price = product.get("UnitPrice")
            try:
                price = float(unit_price)
            except (TypeError, ValueError):
                continue

            image_url = clean_text(str(product.get("ImageUrl") or ""))
            cover_url = f"{BASE_URL}{image_url}" if image_url.startswith("/") else (image_url or None)
            author = authors[index] if index < len(authors) and authors[index] else "Не указан"

            books.append(
                {
                    "source_id": product_id,
                    "title": title,
                    "title_ru": title,
                    "author": author,
                    "price": round(price, 2),
                    "cover_url": cover_url,
                    "description": f"Импортировано с {CATEGORY_URL} (страница {current_page}).",
                }
            )

            if len(books) >= limit:
                break

        page += 1

    return books[:limit]


def replace_catalog(items: list[dict]) -> tuple[int, int]:
    archived = 0
    created = 0

    active_books = Book.query.filter(Book.status == BookStatus.ACTIVE).all()
    for old_book in active_books:
        old_book.status = BookStatus.ARCHIVED
        archived += 1

    db.session.flush()

    for item in items:
        isbn = f"MBOOK-{item['source_id']}"
        exists = Book.query.filter(Book.isbn == isbn).first()
        if exists:
            exists.title = item["title"]
            exists.title_ru = item["title_ru"]
            exists.author = item["author"]
            exists.price = item["price"]
            exists.cover_url = item["cover_url"]
            exists.description = item["description"]
            exists.status = BookStatus.ACTIVE
            if not exists.stock:
                db.session.add(BookStock(book_id=exists.id, quantity=25, reserved=0))
            else:
                exists.stock.quantity = max(exists.stock.quantity, 25)
                exists.stock.reserved = 0
            created += 1
            continue

        book = Book(
            title=item["title"],
            title_ru=item["title_ru"],
            author=item["author"],
            isbn=isbn,
            publisher="Московский Дом Книги",
            year=None,
            price=item["price"],
            description=item["description"],
            cover_url=item["cover_url"],
            status=BookStatus.ACTIVE,
        )
        db.session.add(book)
        db.session.flush()
        db.session.add(BookStock(book_id=book.id, quantity=25, reserved=0))
        created += 1

    db.session.commit()
    return archived, created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        collected = collect_books(TARGET_COUNT)
        if len(collected) < TARGET_COUNT:
            raise RuntimeError(
                f"Не удалось собрать {TARGET_COUNT} книг с {CATEGORY_URL}. Собрано: {len(collected)}"
            )

        archived_count, created_count = replace_catalog(collected)
        active_total = Book.query.filter(Book.status == BookStatus.ACTIVE).count()
        mbook_total = Book.query.filter(Book.isbn.like("MBOOK-%")).count()

        print(f"MBOOK_COLLECTED={len(collected)}")
        print(f"BOOKS_ARCHIVED={archived_count}")
        print(f"MBOOK_CREATED_OR_UPDATED={created_count}")
        print(f"MBOOK_TOTAL={mbook_total}")
        print(f"ACTIVE_TOTAL={active_total}")
