

from typing import List, Dict, Any, Optional

from sqlalchemy import func, desc

from ai_module import BookRecommender
from app.extensions import db
from app.models import Book, BookStatus, Sale, SaleItem, SaleStatus, Client


class RecommendationService:


    _recommender = BookRecommender()

    @classmethod
    def _get_active_books(cls) -> List[Book]:

        return Book.query.filter(Book.status == BookStatus.ACTIVE).all()

    @classmethod
    def _load_completed_interactions(cls) -> List[Dict[str, Any]]:

        rows = (
            db.session.query(Sale.client_id, SaleItem.book_id, SaleItem.quantity)
            .join(SaleItem, SaleItem.sale_id == Sale.id)
            .filter(
                Sale.status == SaleStatus.COMPLETED,
                Sale.client_id.isnot(None)
            )
            .all()
        )

        interactions: List[Dict[str, Any]] = []
        for row in rows:
            interactions.append({
                'client_id': row.client_id,
                'book_id': row.book_id,
                'quantity': row.quantity or 1,
            })
        return interactions

    @classmethod
    def _train_ranking_model(cls, all_books: List[Dict[str, Any]]) -> bool:

        interactions = cls._load_completed_interactions()
        return cls._recommender.fit_ranking_model(
            interactions=interactions,
            all_books=all_books
        )

    @classmethod
    def get_client_id_by_user_id(cls, user_id: int) -> Optional[int]:

        client = Client.query.filter(Client.user_id == user_id).first()
        return client.id if client else None

    @classmethod
    def get_cart_recommendations(
        cls,
        cart_book_ids: List[int],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not cart_book_ids:
            return []

        cart_books = []
        for book_id in cart_book_ids:
            book = Book.query.get(book_id)
            if book and book.status == BookStatus.ACTIVE:
                cart_books.append(cls._book_to_dict(book))

        if not cart_books:
            return []

        all_books = [cls._book_to_dict(b) for b in cls._get_active_books()]
        if not all_books:
            return []

        recommendations = cls._recommender.recommend_by_cart(
            cart_books=cart_books,
            all_books=all_books,
            limit=limit
        )

        if recommendations:
            return recommendations[:limit]

        return cls.get_popular_books(limit=limit, exclude_book_ids=cart_book_ids)

    @classmethod
    def get_history_recommendations(
        cls,
        client_id: Optional[int],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not client_id:
            return cls.get_popular_books(limit)

        sales = Sale.query.filter_by(
            client_id=client_id,
            status=SaleStatus.COMPLETED
        ).all()

        if not sales:
            return cls.get_popular_books(limit)

        purchase_history = []
        purchased_book_ids = set()
        for sale in sales:
            items = []
            for item in sale.items:
                if item.book and item.book.status == BookStatus.ACTIVE:
                    items.append({'book': cls._book_to_dict(item.book)})
                    purchased_book_ids.add(item.book.id)
            if items:
                purchase_history.append({'items': items})

        if not purchase_history:
            return cls.get_popular_books(limit)

        all_books = [cls._book_to_dict(b) for b in cls._get_active_books()]
        if not all_books:
            return []


        cls._train_ranking_model(all_books)
        ranking_recommendations = cls._recommender.recommend_by_client_ranking(
            client_id=client_id,
            all_books=all_books,
            limit=limit,
            exclude_book_ids=list(purchased_book_ids)
        )
        if ranking_recommendations:
            return ranking_recommendations


        recommendations = cls._recommender.recommend_by_history(
            purchase_history=purchase_history,
            all_books=all_books,
            limit=limit
        )

        return recommendations or cls.get_popular_books(limit)

    @classmethod
    def get_set_recommendations(
        cls,
        cart_book_ids: List[int]
    ) -> List[Dict[str, Any]]:
        if not cart_book_ids:
            return []

        cart_books = []
        for book_id in cart_book_ids:
            book = Book.query.get(book_id)
            if book and book.status == BookStatus.ACTIVE:
                cart_books.append(cls._book_to_dict(book))

        if not cart_books:
            return []

        all_books = [cls._book_to_dict(b) for b in cls._get_active_books()]
        if not all_books:
            return []

        return cls._recommender.recommend_complete_set(
            cart_books=cart_books,
            all_books=all_books
        )

    @classmethod
    def get_popular_books(
        cls,
        limit: int = 5,
        exclude_book_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        exclude_ids = set(exclude_book_ids or [])

        top_books = db.session.query(
            SaleItem.book_id,
            func.sum(SaleItem.quantity).label('total_quantity')
        ).join(Sale).filter(
            Sale.status == SaleStatus.COMPLETED
        ).group_by(SaleItem.book_id).order_by(
            desc('total_quantity')
        ).limit(limit * 3).all()

        result = []
        for book_stat in top_books:
            book = Book.query.get(book_stat.book_id)
            if (
                book
                and book.status == BookStatus.ACTIVE
                and book.id not in exclude_ids
            ):
                result.append({
                    'book': cls._book_to_dict(book),
                    'reason': 'Популярная книга (по истории продаж)',
                    'score': float(book_stat.total_quantity)
                })
            if len(result) >= limit:
                break

        if result:
            return result[:limit]

        books = (
            Book.query
            .filter(Book.status == BookStatus.ACTIVE)
            .order_by(Book.created_at.desc())
            .limit(limit * 3)
            .all()
        )
        fallback = []
        for book in books:
            if book.id not in exclude_ids:
                fallback.append({
                    'book': cls._book_to_dict(book),
                    'reason': 'Новая или доступная книга',
                    'score': 0.0
                })
            if len(fallback) >= limit:
                break

        return fallback

    @classmethod
    def get_personal_recommendations(
        cls,
        client_id: Optional[int],
        cart_book_ids: Optional[List[int]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []
        seen_book_ids = set()

        if cart_book_ids:
            seen_book_ids.update(cart_book_ids)

        if client_id:
            history_recs = cls.get_history_recommendations(client_id=client_id, limit=limit)
            for rec in history_recs:
                book_id = rec['book'].get('id')
                if book_id and book_id not in seen_book_ids:
                    recommendations.append(rec)
                    seen_book_ids.add(book_id)
                if len(recommendations) >= limit:
                    return recommendations[:limit]

        if len(recommendations) < limit and cart_book_ids:
            cart_recs = cls.get_cart_recommendations(
                cart_book_ids=cart_book_ids,
                limit=limit - len(recommendations)
            )
            for rec in cart_recs:
                book_id = rec['book'].get('id')
                if book_id and book_id not in seen_book_ids:
                    recommendations.append(rec)
                    seen_book_ids.add(book_id)
                if len(recommendations) >= limit:
                    return recommendations[:limit]

        if len(recommendations) < limit:
            popular = cls.get_popular_books(
                limit=limit - len(recommendations),
                exclude_book_ids=list(seen_book_ids)
            )
            for rec in popular:
                book_id = rec['book'].get('id')
                if book_id and book_id not in seen_book_ids:
                    recommendations.append(rec)
                    seen_book_ids.add(book_id)
                if len(recommendations) >= limit:
                    break

        return recommendations[:limit]

    @staticmethod
    def _book_to_dict(book: Book) -> Dict[str, Any]:
        return {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'price': float(book.price) if book.price else 0.0,
            'publisher': book.publisher,
            'year': book.year,
            'description': book.description,
            'cover_url': book.cover_url,
            'status': book.status.value if hasattr(book.status, 'value') else book.status,
        }
