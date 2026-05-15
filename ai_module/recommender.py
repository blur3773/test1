

from __future__ import annotations

from collections import Counter, defaultdict
import math
import re
from typing import Any, Dict, List, Optional

try:
    from sklearn.ensemble import GradientBoostingClassifier
except Exception:
    GradientBoostingClassifier = None


class BookRecommender:


    GENRE_KEYWORDS = {
        'фантастика': ['фантастика', 'фэнтези', 'магия', 'волшебник', 'космос', 'будущее'],
        'классика': ['классика', 'классический', 'роман о', 'эпопея'],
        'детектив': ['детектив', 'расследование', 'преступление', 'убийство'],
        'романтика': ['любовь', 'роман о любви', 'чувства', 'страсть'],
        'антиутопия': ['антиутопия', 'тоталитарный', 'общество', '1984'],
        'приключения': ['приключения', 'путешествие', 'экспедиция'],
        'исторический': ['исторический', 'война', 'история'],
        'психология': ['психология', 'совесть', 'мораль', 'философский'],
        'подростковый': ['подросток', 'юный', 'школа'],
    }

    BOOK_SETS = {
        'Властелин колец': ['Властелин колец', 'Братство кольца', 'Две крепости', 'Возвращение короля', 'Хоббит'],
        'Гарри Поттер': ['Гарри Поттер'],
        'Преступление и наказание': ['Преступление и наказание', 'Братья Карамазовы', 'Идиот'],
        '1984': ['1984', 'Скотный двор'],
    }

    def __init__(self):

        self._idf: Dict[str, float] = {}
        self._book_vectors: Dict[int, Dict[str, float]] = {}
        self._dataset_signature = None


        self._ranking_model = None
        self._ranking_signature = None
        self._ranking_ready = False
        self._client_book_counter: Dict[int, Counter[int]] = {}
        self._book_popularity: Dict[int, float] = {}
        self._books_by_id: Dict[int, Dict[str, Any]] = {}





    def _normalize_text(self, text: str) -> str:
        return (text or '').lower().replace('ё', 'е')

    def _tokenize(self, text: str) -> List[str]:
        normalized = self._normalize_text(text)
        return re.findall(r'[a-zа-я0-9]+', normalized, flags=re.IGNORECASE)

    def extract_genres(self, text: str) -> List[str]:
        if not text:
            return []

        text_lower = self._normalize_text(text)
        genres = []

        for genre, keywords in self.GENRE_KEYWORDS.items():
            for keyword in keywords:
                if self._normalize_text(keyword) in text_lower:
                    genres.append(genre)
                    break

        return genres

    def _get_price_category(self, price: float) -> str:
        if price < 400:
            return 'low'
        if price < 600:
            return 'medium'
        return 'high'

    def get_book_features(self, book: Dict[str, Any]) -> Dict[str, Any]:
        text = self._book_text(book)
        return {
            'book_id': book.get('id'),
            'title': book.get('title'),
            'author': book.get('author'),
            'price': self._to_float(book.get('price')),
            'genres': self.extract_genres(text),
            'price_category': self._get_price_category(self._to_float(book.get('price'))),
            'tokens': self._tokenize(text),
        }

    def _book_text(self, book: Dict[str, Any]) -> str:
        def safe(value: Any) -> str:
            return '' if value is None else str(value)

        base_text = ' '.join([
            safe(book.get('title', '')),
            safe(book.get('author', '')),
            safe(book.get('description', '')),
            safe(book.get('publisher', '')),
            safe(book.get('year', '')),
        ]).strip()
        genres = self.extract_genres(base_text)
        return f"{base_text} {' '.join(genres)}".strip()

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default





    def _vectorize_tokens(self, tokens: List[str]) -> Dict[str, float]:
        if not tokens:
            return {}

        counts = Counter(tokens)
        total = sum(counts.values())
        if total == 0:
            return {}

        vector = {}
        for token, count in counts.items():
            idf = self._idf.get(token)
            if idf is None:
                continue
            tf = count / total
            vector[token] = tf * idf

        return self._normalize_vector(vector)

    def _normalize_vector(self, vector: Dict[str, float]) -> Dict[str, float]:
        if not vector:
            return {}
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm == 0:
            return {}
        return {token: value / norm for token, value in vector.items()}

    def _fit(self, all_books: List[Dict[str, Any]]) -> None:
        signature = tuple(sorted(
            (
                int(book.get('id', 0)),
                str(book.get('title', '')),
                str(book.get('author', '')),
                str(book.get('description', '')),
                str(book.get('publisher', '')),
                str(book.get('year', '')),
            )
            for book in all_books
        ))
        if signature == self._dataset_signature:
            return

        self._dataset_signature = signature
        self._book_vectors = {}
        self._idf = {}

        documents = {}
        df_counter = Counter()

        for book in all_books:
            book_id = book.get('id')
            if book_id is None:
                continue
            text = self._book_text(book)
            tokens = self._tokenize(text)
            documents[book_id] = tokens
            df_counter.update(set(tokens))

        num_docs = max(len(documents), 1)
        self._idf = {
            token: math.log((1 + num_docs) / (1 + doc_freq)) + 1.0
            for token, doc_freq in df_counter.items()
        }

        for book_id, tokens in documents.items():
            self._book_vectors[book_id] = self._vectorize_tokens(tokens)

    def _mean_vector(self, vectors: List[Dict[str, float]]) -> Dict[str, float]:
        if not vectors:
            return {}
        acc = defaultdict(float)
        for vector in vectors:
            for token, value in vector.items():
                acc[token] += value
        count = len(vectors)
        mean = {token: value / count for token, value in acc.items()}
        return self._normalize_vector(mean)

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        return sum(value * vec_b.get(token, 0.0) for token, value in vec_a.items())

    def _build_profile_vector(self, source_books: List[Dict[str, Any]]) -> Dict[str, float]:
        vectors = []
        for book in source_books:
            book_id = book.get('id')
            vector = self._book_vectors.get(book_id)
            if not vector:
                vector = self._vectorize_tokens(self._tokenize(self._book_text(book)))
            if vector:
                vectors.append(vector)
        return self._mean_vector(vectors)

    def _top_shared_terms(
        self,
        profile_vector: Dict[str, float],
        candidate_vector: Dict[str, float],
        top_n: int = 3
    ) -> List[str]:
        shared = []
        for token, profile_weight in profile_vector.items():
            candidate_weight = candidate_vector.get(token)
            if candidate_weight:
                shared.append((token, profile_weight * candidate_weight))
        shared.sort(key=lambda x: x[1], reverse=True)
        return [token for token, _ in shared[:top_n]]

    def _tfidf_recommend_by_cart(
        self,
        cart_books: List[Dict[str, Any]],
        all_books: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not cart_books or not all_books:
            return []

        self._fit(all_books)
        profile_vector = self._build_profile_vector(cart_books)
        if not profile_vector:
            return []

        cart_book_ids = {book.get('id') for book in cart_books}
        recommendations = []

        for book in all_books:
            book_id = book.get('id')
            if book_id in cart_book_ids:
                continue

            candidate_vector = self._book_vectors.get(book_id, {})
            similarity = self._cosine_similarity(profile_vector, candidate_vector)
            if similarity <= 0:
                continue

            shared_terms = self._top_shared_terms(profile_vector, candidate_vector, top_n=3)
            reason = (
                f"ML-рекомендация по текстовой близости (TF-IDF): {', '.join(shared_terms)}"
                if shared_terms
                else "ML-рекомендация по текстовой близости (TF-IDF)"
            )

            recommendations.append({
                'book': book,
                'score': round(similarity * 100, 2),
                'reason': reason,
            })

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]





    def fit_ranking_model(
        self,
        interactions: List[Dict[str, Any]],
        all_books: List[Dict[str, Any]]
    ) -> bool:

        if GradientBoostingClassifier is None:
            self._ranking_ready = False
            return False

        if not interactions or len(all_books) < 3:
            self._ranking_ready = False
            return False

        books_by_id = {
            int(book['id']): book
            for book in all_books
            if book.get('id') is not None
        }
        if len(books_by_id) < 3:
            self._ranking_ready = False
            return False

        client_book_counter: Dict[int, Counter[int]] = defaultdict(Counter)
        book_popularity_raw: Counter[int] = Counter()

        for row in interactions:
            client_id = row.get('client_id')
            book_id = row.get('book_id')
            if client_id is None or book_id is None:
                continue

            try:
                client_id_int = int(client_id)
                book_id_int = int(book_id)
            except (TypeError, ValueError):
                continue

            if book_id_int not in books_by_id:
                continue

            quantity = max(1, int(self._to_float(row.get('quantity'), default=1.0)))
            client_book_counter[client_id_int][book_id_int] += quantity
            book_popularity_raw[book_id_int] += quantity

        if len(client_book_counter) < 2:
            self._ranking_ready = False
            return False

        signature = (
            len(books_by_id),
            tuple(
                (client_id, tuple(sorted(counter.items())))
                for client_id, counter in sorted(client_book_counter.items(), key=lambda x: x[0])
            ),
        )
        if signature == self._ranking_signature and self._ranking_ready and self._ranking_model is not None:
            return True


        self._fit(list(books_by_id.values()))

        max_popularity = max(book_popularity_raw.values()) if book_popularity_raw else 1
        book_popularity = {
            book_id: qty / max_popularity
            for book_id, qty in book_popularity_raw.items()
        }

        all_book_ids = sorted(books_by_id.keys())
        X: List[List[float]] = []
        y: List[int] = []

        for client_id, purchased_counter in client_book_counter.items():
            purchased_ids = set(purchased_counter.keys())
            if not purchased_ids:
                continue

            purchased_books = [books_by_id[book_id] for book_id in purchased_ids if book_id in books_by_id]
            profile_vector = self._build_profile_vector(purchased_books)

            for book_id in purchased_ids:
                book = books_by_id.get(book_id)
                if not book:
                    continue
                X.append(
                    self._build_pair_features(
                        purchased_counter=purchased_counter,
                        candidate_book=book,
                        profile_vector=profile_vector,
                        popularity_score=book_popularity.get(book_id, 0.0),
                        books_by_id=books_by_id,
                    )
                )
                y.append(1)

            negative_ids = [book_id for book_id in all_book_ids if book_id not in purchased_ids]

            negative_ids.sort(key=lambda b_id: book_popularity.get(b_id, 0.0), reverse=True)
            negative_ids = negative_ids[: max(1, min(len(negative_ids), len(purchased_ids) * 2))]

            for book_id in negative_ids:
                book = books_by_id.get(book_id)
                if not book:
                    continue
                X.append(
                    self._build_pair_features(
                        purchased_counter=purchased_counter,
                        candidate_book=book,
                        profile_vector=profile_vector,
                        popularity_score=book_popularity.get(book_id, 0.0),
                        books_by_id=books_by_id,
                    )
                )
                y.append(0)


        if len(X) < 6 or len(set(y)) < 2:
            self._ranking_ready = False
            return False

        model = GradientBoostingClassifier(
            n_estimators=140,
            learning_rate=0.06,
            max_depth=3,
            subsample=0.9,
            random_state=42,
        )
        model.fit(X, y)

        self._ranking_model = model
        self._ranking_signature = signature
        self._ranking_ready = True
        self._client_book_counter = dict(client_book_counter)
        self._book_popularity = book_popularity
        self._books_by_id = books_by_id
        return True

    def _build_pair_features(
        self,
        purchased_counter: Counter[int],
        candidate_book: Dict[str, Any],
        profile_vector: Dict[str, float],
        popularity_score: float,
        books_by_id: Dict[int, Dict[str, Any]],
    ) -> List[float]:
        candidate_id = int(candidate_book.get('id', 0) or 0)
        candidate_price = self._to_float(candidate_book.get('price'))
        candidate_year = self._to_float(candidate_book.get('year'))
        candidate_author = self._normalize_text(str(candidate_book.get('author', '')))
        candidate_publisher = self._normalize_text(str(candidate_book.get('publisher', '')))
        candidate_genres = set(self.extract_genres(self._book_text(candidate_book)))

        total_purchases = max(1, sum(purchased_counter.values()))
        purchased_book_ids = list(purchased_counter.keys())
        purchased_books = [books_by_id[book_id] for book_id in purchased_book_ids if book_id in books_by_id]

        author_counter = Counter(self._normalize_text(str(book.get('author', ''))) for book in purchased_books)
        publisher_counter = Counter(self._normalize_text(str(book.get('publisher', ''))) for book in purchased_books)
        user_genres = []
        user_prices = []
        for book in purchased_books:
            user_genres.extend(self.extract_genres(self._book_text(book)))
            user_prices.append(self._to_float(book.get('price')))

        user_genres_counter = Counter(user_genres)
        user_avg_price = (sum(user_prices) / len(user_prices)) if user_prices else candidate_price
        price_distance = abs(candidate_price - user_avg_price)
        normalized_price_distance = min(1.0, price_distance / max(user_avg_price, 1.0))

        author_match_ratio = author_counter.get(candidate_author, 0) / max(1, len(purchased_books))
        publisher_match_ratio = publisher_counter.get(candidate_publisher, 0) / max(1, len(purchased_books))

        if candidate_genres:
            matched_genre_score = sum(user_genres_counter.get(genre, 0) for genre in candidate_genres)
            genre_match_ratio = matched_genre_score / max(1, sum(user_genres_counter.values()))
        else:
            genre_match_ratio = 0.0

        candidate_vector = self._book_vectors.get(candidate_id, {})
        semantic_similarity = self._cosine_similarity(profile_vector, candidate_vector)


        return [
            candidate_price / 1000.0,
            min(1.0, candidate_year / 2100.0),
            popularity_score,
            min(1.0, len(purchased_books) / 25.0),
            user_avg_price / 1000.0,
            1.0 - normalized_price_distance,
            author_match_ratio,
            publisher_match_ratio,
            genre_match_ratio,
            semantic_similarity,
            1.0 if candidate_id in purchased_counter else 0.0,
            purchased_counter.get(candidate_id, 0) / total_purchases,
        ]

    def recommend_by_client_ranking(
        self,
        client_id: int,
        all_books: List[Dict[str, Any]],
        limit: int = 5,
        exclude_book_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:

        if not self._ranking_ready or self._ranking_model is None:
            return []

        purchased_counter = self._client_book_counter.get(client_id)
        if not purchased_counter:
            return []

        purchased_books = [
            self._books_by_id[book_id]
            for book_id in purchased_counter.keys()
            if book_id in self._books_by_id
        ]
        profile_vector = self._build_profile_vector(purchased_books)
        if not profile_vector:
            return []

        exclude_ids = set(exclude_book_ids or [])
        recommendations = []

        for book in all_books:
            book_id = book.get('id')
            if book_id is None:
                continue
            book_id = int(book_id)
            if book_id in exclude_ids:
                continue

            features = self._build_pair_features(
                purchased_counter=purchased_counter,
                candidate_book=book,
                profile_vector=profile_vector,
                popularity_score=self._book_popularity.get(book_id, 0.0),
                books_by_id=self._books_by_id,
            )

            try:
                probability = float(self._ranking_model.predict_proba([features])[0][1])
            except Exception:
                probability = 0.0

            if probability <= 0:
                continue

            recommendations.append({
                'book': book,
                'score': round(probability * 100, 2),
                'reason': f'ML ranking (Gradient Boosting): вероятность покупки {round(probability * 100, 2)}%',
            })

        recommendations.sort(key=lambda item: item['score'], reverse=True)
        return recommendations[:limit]





    def recommend_by_cart(
        self,
        cart_books: List[Dict[str, Any]],
        all_books: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:

        return self._tfidf_recommend_by_cart(cart_books=cart_books, all_books=all_books, limit=limit)

    def recommend_by_history(
        self,
        purchase_history: List[Dict[str, Any]],
        all_books: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        purchased_books = []
        for purchase in purchase_history:
            for item in purchase.get('items', []):
                book = item.get('book')
                if book:
                    purchased_books.append(book)
        return self._tfidf_recommend_by_cart(
            cart_books=purchased_books,
            all_books=all_books,
            limit=limit
        )

    def recommend_complete_set(
        self,
        cart_books: List[Dict[str, Any]],
        all_books: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        recommendations = []

        for set_name, set_books in self.BOOK_SETS.items():
            cart_has_set_book = False
            cart_set_titles = []

            for cart_book in cart_books:
                title = cart_book.get('title', '')
                author = cart_book.get('author', '')
                for set_keyword in set_books:
                    if set_keyword in title or set_keyword in author:
                        cart_has_set_book = True
                        cart_set_titles.append(title)
                        break

            if cart_has_set_book:
                for book in all_books:
                    title = book.get('title', '')
                    author = book.get('author', '')
                    belongs_to_set = any(
                        set_keyword in title or set_keyword in author
                        for set_keyword in set_books
                    )
                    if belongs_to_set and book.get('id') not in {cb.get('id') for cb in cart_books}:
                        recommendations.append({
                            'book': book,
                            'reason': f'Дополнит комплект: {", ".join(cart_set_titles)}',
                            'set_name': set_name
                        })

        return recommendations
