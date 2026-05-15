from __future__ import annotations

import html
import re
from difflib import SequenceMatcher
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


class BookMetadataService:
    BASE_URL = "https://www.moscowbooks.ru"
    SEARCH_URL = "https://www.moscowbooks.ru/search/?text={query}"
    TIMEOUT = 20
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )

    @classmethod
    def enrich_from_moscowbooks(cls, book) -> bool:
        book_url = cls._resolve_book_url(book)
        if not book_url:
            return False

        page_html = cls._fetch_html(book_url)
        if not page_html:
            return False

        details_map = cls._extract_details_map(page_html)
        annotation = cls._extract_annotation(page_html)
        genre = cls._extract_genre(page_html)

        updated = False

        publisher = details_map.get("Издательство") or book.publisher
        year = cls._parse_int(details_map.get("Год издания")) if details_map.get("Год издания") else book.year
        publication_place = details_map.get("Место издания") or book.publication_place
        page_count = cls._parse_int(details_map.get("Страниц")) if details_map.get("Страниц") else book.page_count
        weight_grams = cls._parse_int(details_map.get("Вес")) if details_map.get("Вес") else book.weight_grams
        print_run = cls._parse_int(details_map.get("Тираж")) if details_map.get("Тираж") else book.print_run

        if publisher and publisher != book.publisher:
            book.publisher = publisher
            updated = True
        if year is not None and year != book.year:
            book.year = year
            updated = True
        if publication_place and publication_place != book.publication_place:
            book.publication_place = publication_place
            updated = True
        if page_count is not None and page_count != book.page_count:
            book.page_count = page_count
            updated = True
        if weight_grams is not None and weight_grams != book.weight_grams:
            book.weight_grams = weight_grams
            updated = True
        if print_run is not None and print_run != book.print_run:
            book.print_run = print_run
            updated = True
        if genre and genre != book.genre:
            book.genre = genre
            updated = True
        if annotation and annotation != book.description:
            book.description = annotation
            updated = True
        if book_url != getattr(book, "source_url", None):
            book.source_url = book_url
            updated = True

        return updated

    @classmethod
    def _resolve_book_url(cls, book) -> Optional[str]:
        moscowbook_id = cls._extract_moscowbook_id(book.isbn)
        if moscowbook_id:
            direct_url = f"{cls.BASE_URL}/book/{moscowbook_id}/"
            if cls._book_page_has_details(cls._fetch_html(direct_url)):
                return direct_url

        for query in filter(None, [book.title_ru, book.title]):
            found_url = cls._search_best_book_url(query, book.author)
            if found_url:
                return found_url

        return None

    @classmethod
    def _extract_moscowbook_id(cls, isbn: Optional[str]) -> Optional[str]:
        if not isbn:
            return None
        match = re.search(r"MBOOK-(\d+)", str(isbn).upper())
        if match:
            return match.group(1)
        return None

    @classmethod
    def _search_best_book_url(cls, title: str, author: Optional[str]) -> Optional[str]:
        query = quote_plus(title)
        search_html = cls._fetch_html(cls.SEARCH_URL.format(query=query))
        if not search_html:
            return None

        items = re.findall(
            r'<a href="(/book/\d+/)"[^>]*title="([^"]+)"[^>]*>',
            search_html,
            flags=re.S,
        )
        if not items:
            items = re.findall(
                r'<a href="(/book/\d+/)" class="book-preview__title-link"[^>]*>(.*?)</a>',
                search_html,
                flags=re.S,
            )

        if not items:
            return None

        normalized_title = cls._normalize_compare(title)
        normalized_author = cls._normalize_compare(author or "")
        best_score = 0.0
        best_url = None

        for href, title_candidate in items:
            candidate_text = cls._strip_html(title_candidate)
            normalized_candidate = cls._normalize_compare(candidate_text)

            similarity = SequenceMatcher(None, normalized_title, normalized_candidate).ratio()
            if normalized_title and normalized_candidate:
                if normalized_title == normalized_candidate:
                    similarity += 1.0
                if normalized_title in normalized_candidate or normalized_candidate in normalized_title:
                    similarity += 0.4

            if normalized_author and normalized_author in cls._normalize_compare(candidate_text):
                similarity += 0.2

            if similarity > best_score:
                best_score = similarity
                best_url = f"{cls.BASE_URL}{href}"

        if best_score < 0.35:
            return None
        return best_url

    @classmethod
    def _book_page_has_details(cls, page_html: Optional[str]) -> bool:
        if not page_html:
            return False
        return "book__details-item" in page_html and "book__description" in page_html

    @classmethod
    def _extract_details_map(cls, page_html: str) -> dict[str, str]:
        details = {}
        rows = re.findall(
            r'<dl class="book__details-item">.*?<dt class="book__details-name">\s*(.*?)\s*</dt>.*?<dt class="book__details-value">\s*(.*?)\s*</dt>.*?</dl>',
            page_html,
            flags=re.S,
        )
        for key_raw, value_raw in rows:
            key = cls._strip_html(key_raw).rstrip(":").strip()
            value = cls._strip_html(value_raw)
            if key and value:
                details[key] = value
        return details

    @classmethod
    def _extract_annotation(cls, page_html: str) -> Optional[str]:
        match = re.search(
            r'<div class="book__description[^>]*>(.*?)<a href="#" class="book__description-link',
            page_html,
            flags=re.S,
        )
        if not match:
            match = re.search(
                r'<div class="book__description[^>]*>(.*?)</div>',
                page_html,
                flags=re.S,
            )
        if not match:
            return None

        text = cls._strip_html(match.group(1))
        text = re.sub(r"^Аннотация к книге[^:]*:\s*", "", text, flags=re.I)
        return text.strip() or None

    @classmethod
    def _extract_genre(cls, page_html: str) -> Optional[str]:
        genre_matches = re.findall(
            r'<a class="genre_link"[^>]*>(.*?)</a>',
            page_html,
            flags=re.S,
        )
        genres = [cls._strip_html(match) for match in genre_matches if cls._strip_html(match)]
        if not genres:
            return None
        unique = []
        for item in genres:
            if item not in unique:
                unique.append(item)
        return ", ".join(unique)

    @classmethod
    def _parse_int(cls, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        match = re.search(r"(\d+)", value.replace(" ", ""))
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    @classmethod
    def _fetch_html(cls, url: str) -> Optional[str]:
        try:
            request = Request(url, headers={"User-Agent": cls.USER_AGENT})
            with urlopen(request, timeout=cls.TIMEOUT) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            return None

    @staticmethod
    def _normalize_compare(value: str) -> str:
        normalized = (value or "").lower().replace("ё", "е")
        normalized = re.sub(r"[^a-zа-я0-9]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    @staticmethod
    def _strip_html(value: str) -> str:
        text = value or ""
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
