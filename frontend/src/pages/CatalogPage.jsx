import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import BookCard from "../components/BookCard";
import { fetchBooks, setSearchQuery, setStatusFilter } from "../features/books/booksSlice";
import { addToCart } from "../features/cart/cartSlice";
import { fetchPopularBooks } from "../features/recommendations/recommendationsSlice";
import { isNewBook, isSpringBestBook } from "../utils/bookPromos";

const CATALOG_SEARCH_MAX_LENGTH = 90;

function CatalogPage() {
  const dispatch = useAppDispatch();
  const { items, status, error, filters } = useAppSelector((state) => state.books);
  const { profile } = useAppSelector((state) => state.user);
  const { popularBooks } = useAppSelector((state) => state.recommendations);
  const [searchInput, setSearchInput] = useState(filters.query);
  const [promoFilter, setPromoFilter] = useState("all");

  const statusOptions = useMemo(() => {
    const role = profile?.role;
    const options = [{ value: "active", label: "В продаже" }];

    if (["manager", "admin"].includes(role)) {
      options.push({ value: "archived", label: "Архив" });
    }
    if (["manager", "admin"].includes(role)) {
      options.push({ value: "all", label: "Все книги" });
    }
    return options;
  }, [profile?.role]);

  const filteredItems = useMemo(() => {
    if (promoFilter === "new") {
      return items.filter((book) => isNewBook(book));
    }
    if (promoFilter === "spring") {
      return items.filter((book) => isSpringBestBook(book));
    }
    return items;
  }, [items, promoFilter]);

  useEffect(() => {
    dispatch(fetchBooks({ status: filters.status, query: filters.query }));
  }, [dispatch, filters.query, filters.status]);

  useEffect(() => {
    dispatch(fetchPopularBooks(3));
  }, [dispatch]);

  const onSearchSubmit = (event) => {
    event.preventDefault();
    dispatch(setSearchQuery(searchInput));
  };

  const openCatalogSection = () => {
    const target = document.getElementById("catalog");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <section className="catalog-page">
      <section id="hero" className="hero-yellow">
        <div className="hero-content">
          <h2>Книжная вселенная</h2>
          <p>Откройте для себя лучшие книги, добавляйте в корзину и оформляйте заказы онлайн.</p>
          <div className="hero-actions">
            <button type="button" className="button hero-button" onClick={openCatalogSection}>
              Посмотреть каталог
            </button>
            <Link to="/contacts" className="hero-secondary-link">
              Задать вопрос
            </Link>
          </div>
          <div className="hero-metrics">
            <div>
              <strong>24/7</strong>
              <span>онлайн-оформление заказов</span>
            </div>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-orb" />
          <article className="hero-book hero-book--main">
            <span>Книжная вселенная</span>
            <strong>Весенние бестселлеры</strong>
            <p>Подборка недели для уютных вечеров и поездок</p>
          </article>
          <article className="hero-book hero-book--accent">
            <span>Новинка</span>
            <strong>Лимитированная серия</strong>
          </article>
        </div>
      </section>

      <section className="benefits-section">
        <h3>Почему выбирают именно нас</h3>
        <div className="benefits-grid">
          <article>
            <div className="benefit-icon">🧠</div>
            <h4>Их много</h4>
            <p>Большой выбор книг разных жанров и направлений.</p>
          </article>
          <article>
            <div className="benefit-icon">📚</div>
            <h4>Они интересны</h4>
            <p>От классики до бестселлеров, каждый найдёт любимое.</p>
          </article>
          <article>
            <div className="benefit-icon">🚚</div>
            <h4>Доступны цены</h4>
            <p>Хорошие цены и быстрое оформление заказов.</p>
          </article>
        </div>
      </section>

      <section id="catalog" className="catalog-section">
        <div className="section-title-row">
          <h3>Каталог книг</h3>
          <form className="catalog-search" onSubmit={onSearchSubmit}>
            <input
              className="input"
              type="search"
              placeholder="Поиск по каталогу"
              value={searchInput}
              maxLength={CATALOG_SEARCH_MAX_LENGTH}
              onChange={(event) => setSearchInput(event.target.value.slice(0, CATALOG_SEARCH_MAX_LENGTH))}
            />
            <button className="button mini-submit" type="submit">
              Найти
            </button>
          </form>
        </div>

        <div className="tab-chips">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={filters.status === option.value ? "tab-chip active" : "tab-chip"}
              onClick={() => dispatch(setStatusFilter(option.value))}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="catalog-promo-filters">
          <button
            type="button"
            className={promoFilter === "all" ? "tab-chip active" : "tab-chip"}
            onClick={() => setPromoFilter("all")}
          >
            Все
          </button>
          <button
            type="button"
            className={promoFilter === "new" ? "tab-chip active" : "tab-chip"}
            onClick={() => setPromoFilter("new")}
          >
            Новинки
          </button>
          <button
            type="button"
            className={promoFilter === "spring" ? "tab-chip tab-chip--spring active" : "tab-chip tab-chip--spring"}
            onClick={() => setPromoFilter("spring")}
          >
            Весенние бестселлеры
          </button>
        </div>

        {status === "loading" ? <p className="muted">Загружаем каталог...</p> : null}
        {error ? <p className="error-text">{String(error)}</p> : null}

        <div className="books-grid">
          {filteredItems.map((book) => (
            <BookCard key={book.id} book={book} onAddToCart={(item) => dispatch(addToCart(item))} />
          ))}
        </div>

        {popularBooks?.length ? (
          <div className="popular-strip">
            <span>Популярно сейчас:</span>
            {popularBooks.map((item, index) => (
              <strong key={`${item.book?.id || index}-${index}`}>{item.book?.title || item.title}</strong>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}

export default CatalogPage;
