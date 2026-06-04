from ai_module.recommender import BookRecommender


def test_recommend_by_cart_returns_semantically_similar_book():
    recommender = BookRecommender()
    cart_books = [
        {
            "id": 1,
            "title": "Космическая фантастика",
            "author": "Автор A",
            "description": "космос будущее экспедиция фантастика",
            "publisher": "Demo",
            "price": 500,
        }
    ]
    all_books = [
        *cart_books,
        {
            "id": 2,
            "title": "Звездное путешествие",
            "author": "Автор B",
            "description": "космос будущее фантастика приключения",
            "publisher": "Demo",
            "price": 520,
        },
        {
            "id": 3,
            "title": "Домашняя кулинария",
            "author": "Автор C",
            "description": "рецепты кухня десерты",
            "publisher": "Demo",
            "price": 350,
        },
    ]

    recommendations = recommender.recommend_by_cart(cart_books, all_books, limit=2)

    assert recommendations
    assert recommendations[0]["book"]["id"] == 2
    assert recommendations[0]["score"] > 0
    assert "TF-IDF" in recommendations[0]["reason"]


def test_recommend_complete_set_finds_missing_book_from_series():
    recommender = BookRecommender()
    cart_books = [{"id": 1, "title": "Гарри Поттер и философский камень", "author": "Дж. К. Роулинг"}]
    all_books = [
        *cart_books,
        {"id": 2, "title": "Гарри Поттер и тайная комната", "author": "Дж. К. Роулинг"},
        {"id": 3, "title": "1984", "author": "Джордж Оруэлл"},
    ]

    recommendations = recommender.recommend_complete_set(cart_books, all_books)

    assert len(recommendations) == 1
    assert recommendations[0]["book"]["id"] == 2
    assert recommendations[0]["set_name"] == "Гарри Поттер"


def test_extract_genres_recognizes_keywords():
    recommender = BookRecommender()

    genres = recommender.extract_genres("детективное расследование преступления")

    assert "детектив" in genres
