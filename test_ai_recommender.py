"""
Тестирование AI-модуля рекомендаций.
"""

from ai_module.recommender import BookRecommender


def main():
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ AI-МОДУЛЯ РЕКОМЕНДАЦИЙ")
    print("=" * 70)

    # Создаём рекомендатель
    recommender = BookRecommender()

    # Тестовые данные - книги в корзине пользователя
    cart_books = [
        {
            'id': 1,
            'title': 'Преступление и наказание',
            'author': 'Фёдор Достоевский',
            'description': 'Классический роман о Раскольникове, преступлении и совести',
            'price': 449.99
        },
        {
            'id': 2,
            'title': '1984',
            'author': 'Джордж Оруэлл',
            'description': 'Антиутопия о тоталитарном обществе',
            'price': 399.99
        }
    ]

    # Все доступные книги в магазине
    all_books = [
        {
            'id': 1,
            'title': 'Преступление и наказание',
            'author': 'Фёдор Достоевский',
            'description': 'Классический роман о Раскольникове',
            'price': 449.99
        },
        {
            'id': 2,
            'title': '1984',
            'author': 'Джордж Оруэлл',
            'description': 'Антиутопия о тоталитарном обществе',
            'price': 399.99
        },
        {
            'id': 3,
            'title': 'Братья Карамазовы',
            'author': 'Фёдор Достоевский',
            'description': 'Философский роман о вере и безверии',
            'price': 549.99
        },
        {
            'id': 4,
            'title': 'Идиот',
            'author': 'Фёдор Достоевский',
            'description': 'Роман о князе Мышкине',
            'price': 499.99
        },
        {
            'id': 5,
            'title': 'Скотный двор',
            'author': 'Джордж Оруэлл',
            'description': 'Сатирическая антиутопия',
            'price': 299.99
        },
        {
            'id': 6,
            'title': 'Мастер и Маргарита',
            'author': 'Михаил Булгаков',
            'description': 'Роман о дьяволе в Москве, классика',
            'price': 599.99
        },
        {
            'id': 7,
            'title': 'Гарри Поттер и философский камень',
            'author': 'Дж. К. Роулинг',
            'description': 'Фэнтези о юном волшебнике, магия и приключения',
            'price': 699.99
        },
        {
            'id': 8,
            'title': 'Война и мир',
            'author': 'Лев Толстой',
            'description': 'Классическая эпопея о войне и мире',
            'price': 899.99
        },
        {
            'id': 9,
            'title': 'Великий Гэтсби',
            'author': 'Фрэнсис Скотт Фицджеральд',
            'description': 'Роман о американской мечте',
            'price': 349.99
        }
    ]

    # ========================================================================
    # ТЕСТ 1: Рекомендации по корзине
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТ 1: Рекомендации по корзине")
    print("=" * 70)
    print(f"\nКорзина пользователя:")
    for book in cart_books:
        print(f"  - {book['title']} ({book['author']})")

    print(f"\n📚 Рекомендации:")
    recommendations = recommender.recommend_by_cart(cart_books, all_books, limit=5)

    if not recommendations:
        print("  Нет рекомендаций 😞")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. {rec['book']['title']} ({rec['book']['author']})")
            print(f"     Score: {rec['score']}")
            print(f"     Причина: {rec['reason']}")

    # ========================================================================
    # ТЕСТ 2: Рекомендации по истории покупок
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТ 2: Рекомендации по истории покупок")
    print("=" * 70)

    # Формируем историю покупок
    purchase_history = [
        {
            'id': 1,
            'items': [
                {'book': cart_books[0]}  # Преступление и наказание
            ]
        },
        {
            'id': 2,
            'items': [
                {'book': {
                    'id': 10,
                    'title': 'Война и мир',
                    'author': 'Лев Толстой',
                    'description': 'Классическая эпопея',
                    'price': 899.99
                }}
            ]
        }
    ]

    print(f"\nИстория покупок:")
    for purchase in purchase_history:
        for item in purchase.get('items', []):
            if 'book' in item:
                print(f"  - {item['book']['title']} ({item['book']['author']})")

    print(f"\n📚 Рекомендации:")
    recommendations = recommender.recommend_by_history(purchase_history, all_books, limit=5)

    if not recommendations:
        print("  Нет рекомендаций 😞")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. {rec['book']['title']} ({rec['book']['author']})")
            print(f"     Score: {rec['score']}")
            print(f"     Причина: {rec['reason']}")

    # ========================================================================
    # ТЕСТ 3: Дополнение комплекта (серии книг)
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТ 3: Дополнение комплекта (серии книг)")
    print("=" * 70)

    # Корзина с книгой из серии
    cart_books_for_set = [
        {
            'id': 7,
            'title': 'Гарри Поттер и философский камень',
            'author': 'Дж. К. Роулинг',
            'description': 'Фэнтези о юном волшебнике',
            'price': 699.99
        }
    ]

    print(f"\nКорзина пользователя:")
    for book in cart_books_for_set:
        print(f"  - {book['title']}")

    print(f"\n📚 Рекомендации для дополнения комплекта:")
    set_recommendations = recommender.recommend_complete_set(cart_books_for_set, all_books)

    if not set_recommendations:
        print("  Нет книг для дополнения комплекта 😞")
    else:
        for i, rec in enumerate(set_recommendations, 1):
            print(f"\n  {i}. {rec['book']['title']} ({rec['book']['author']})")
            print(f"     Причина: {rec['reason']}")
            print(f"     Серия: {rec.get('set_name', 'N/A')}")

    # ========================================================================
    # ТЕСТ 4: Извлечение жанров
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТ 4: Извлечение жанров")
    print("=" * 70)

    test_texts = [
        "Преступление и наказание - классический роман о Раскольникове",
        "Гарри Поттер - фэнтези о магии и волшебнике",
        "1984 - антиутопия о тоталитарном обществе",
        "Война и мир - историческая эпопея о войне",
    ]

    for text in test_texts:
        genres = recommender.extract_genres(text)
        print(f"\n  Текст: {text[:50]}...")
        print(f"  Жанры: {', '.join(genres) if genres else 'не определены'}")

    # ========================================================================
    # ТЕСТ 5: Признаки книги
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТ 5: Признаки книги")
    print("=" * 70)

    test_book = {
        'id': 3,
        'title': 'Братья Карамазовы',
        'author': 'Фёдор Достоевский',
        'description': 'Философский роман о вере и безверии',
        'price': 549.99
    }

    features = recommender.get_book_features(test_book)
    print(f"\n  Книга: {features['title']}")
    print(f"  Автор: {features['author']}")
    print(f"  Цена: {features['price']} руб.")
    print(f"  Жанры: {', '.join(features['genres']) if features['genres'] else 'не определены'}")
    print(f"  Ценовая категория: {features['price_category']}")

    # ========================================================================
    # ИТОГ
    # ========================================================================
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ✅")
    print("=" * 70)


if __name__ == '__main__':
    main()
