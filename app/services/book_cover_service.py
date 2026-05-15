

from __future__ import annotations

import json
import socket
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


class BookCoverService:


    REQUEST_TIMEOUT_SECONDS = 1.8
    USER_AGENT = 'BookFlowStore/1.0 (+https://bookflow.local)'

    @classmethod
    def find_cover_url(
        cls,
        title: Optional[str],
        author: Optional[str],
        isbn: Optional[str] = None
    ) -> Optional[str]:

        normalized_isbn = cls._normalize_isbn(isbn)

        if normalized_isbn:
            open_library_cover = cls._query_open_library_by_isbn(normalized_isbn)
            if open_library_cover:
                return open_library_cover

            google_isbn_cover = cls._query_google_books(f'isbn:{normalized_isbn}')
            if google_isbn_cover:
                return google_isbn_cover

        search_query_parts = [part for part in [title, author] if part]
        if search_query_parts:
            query = ' '.join(search_query_parts)

            google_cover = cls._query_google_books(query)
            if google_cover:
                return google_cover

            open_library_cover = cls._query_open_library_by_title_author(title, author)
            if open_library_cover:
                return open_library_cover

        return None

    @staticmethod
    def _normalize_isbn(isbn: Optional[str]) -> Optional[str]:

        if not isbn:
            return None

        cleaned = ''.join(char for char in isbn.upper() if char.isdigit() or char == 'X')
        if len(cleaned) not in (10, 13):
            return None
        return cleaned

    @classmethod
    def _query_open_library_by_isbn(cls, isbn: str) -> Optional[str]:
        url = (
            'https://openlibrary.org/api/books?'
            f'bibkeys=ISBN:{isbn}&format=json&jscmd=data'
        )
        payload = cls._fetch_json(url)
        if not payload:
            return None

        book_data = payload.get(f'ISBN:{isbn}', {})
        cover = book_data.get('cover', {})
        return cover.get('large') or cover.get('medium') or cover.get('small')

    @classmethod
    def _query_open_library_by_title_author(
        cls,
        title: Optional[str],
        author: Optional[str]
    ) -> Optional[str]:
        query_parts = []
        if title:
            query_parts.append(f'title={quote_plus(title)}')
        if author:
            query_parts.append(f'author={quote_plus(author)}')
        if not query_parts:
            return None

        url = f"https://openlibrary.org/search.json?{'&'.join(query_parts)}&limit=1"
        payload = cls._fetch_json(url)
        if not payload:
            return None

        docs = payload.get('docs') or []
        if not docs:
            return None

        first_doc = docs[0]
        cover_id = first_doc.get('cover_i')
        if cover_id:
            return f'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg'

        doc_isbn_values = first_doc.get('isbn') or []
        for doc_isbn in doc_isbn_values[:3]:
            normalized_isbn = cls._normalize_isbn(doc_isbn)
            if not normalized_isbn:
                continue
            url_from_isbn = cls._query_open_library_by_isbn(normalized_isbn)
            if url_from_isbn:
                return url_from_isbn

        return None

    @classmethod
    def _query_google_books(cls, query: str) -> Optional[str]:
        url = f'https://www.googleapis.com/books/v1/volumes?q={quote_plus(query)}&maxResults=1'
        payload = cls._fetch_json(url)
        if not payload:
            return None

        items = payload.get('items') or []
        if not items:
            return None

        for item in items:
            image_links = item.get('volumeInfo', {}).get('imageLinks', {})
            cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail')
            if cover_url:
                return cover_url.replace('http://', 'https://')

        return None

    @classmethod
    def _fetch_json(cls, url: str) -> Optional[dict]:
        request = Request(
            url,
            headers={
                'User-Agent': cls.USER_AGENT,
                'Accept': 'application/json',
            }
        )

        try:
            with urlopen(request, timeout=cls.REQUEST_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    return None
                raw_body = response.read()
        except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError):
            return None

        if not raw_body:
            return None

        try:
            return json.loads(raw_body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
