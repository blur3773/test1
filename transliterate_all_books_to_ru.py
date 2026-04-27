"""Проставляет русские названия (кириллица) для всех книг через транслитерацию."""

from app import create_app
from app.extensions import db
from app.models.store import Book


DIGRAPH_MAP = {
    "shch": "щ",
    "sch": "щ",
    "yo": "ё",
    "zh": "ж",
    "kh": "х",
    "ts": "ц",
    "ch": "ч",
    "sh": "ш",
    "yu": "ю",
    "ya": "я",
    "ye": "е",
    "th": "т",
    "wh": "в",
    "qu": "кв",
    "ph": "ф",
    "ck": "к",
    "oo": "у",
    "ee": "и",
}

CHAR_MAP = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "дж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}


def transliterate_word(word: str) -> str:
    lower = word.lower()
    result = []
    index = 0

    while index < len(lower):
        matched = False
        for length in (4, 3, 2):
            if index + length > len(lower):
                continue
            part = lower[index : index + length]
            value = DIGRAPH_MAP.get(part)
            if value is not None:
                result.append(value)
                index += length
                matched = True
                break
        if matched:
            continue

        char = lower[index]
        result.append(CHAR_MAP.get(char, char))
        index += 1

    output = "".join(result)
    if word and word[0].isupper():
        return output[:1].upper() + output[1:]
    return output


def transliterate_text(text: str) -> str:
    token = []
    parts = []

    def flush_token() -> None:
        if token:
            parts.append(transliterate_word("".join(token)))
            token.clear()

    for char in text:
        if char.isalpha():
            token.append(char)
        else:
            flush_token()
            parts.append(char)
    flush_token()
    return "".join(parts)


def apply_transliteration() -> tuple[int, int]:
    books = Book.query.order_by(Book.id).all()
    updated = 0

    for book in books:
        title = (book.title or "").strip()
        if not title:
            continue
        ru_title = transliterate_text(title)
        if book.title_ru == ru_title:
            continue
        book.title_ru = ru_title
        updated += 1

    db.session.commit()
    return len(books), updated


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        total_count, updated_count = apply_transliteration()
        print(f"TOTAL_BOOKS={total_count}")
        print(f"UPDATED_TITLE_RU={updated_count}")
