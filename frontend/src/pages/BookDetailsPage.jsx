import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { addToCart } from "../features/cart/cartSlice";
import { clearSelectedBook, fetchBookById } from "../features/books/booksSlice";

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2
  }).format(Number(value || 0));

const formatInt = (value, suffix = "") => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return String(value);
  }
  const formatted = new Intl.NumberFormat("ru-RU").format(Math.round(numericValue));
  return suffix ? `${formatted} ${suffix}` : formatted;
};

const normalizeAnnotation = (value) => {
  const raw = String(value || "").trim();
  if (!raw) {
    return "Описание для этой книги пока не добавлено.";
  }
  return raw.replace(/^Аннотация к книге[^:]*:\s*/i, "").trim() || raw;
};

function BookDetailsPage() {
  const dispatch = useAppDispatch();
  const { bookId } = useParams();
  const { selectedBook, selectedStatus, selectedError } = useAppSelector((state) => state.books);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (bookId) {
      dispatch(fetchBookById(bookId));
    }
    return () => {
      dispatch(clearSelectedBook());
    };
  }, [dispatch, bookId]);

  const onAddToCart = () => {
    if (!selectedBook) {
      return;
    }
    dispatch(addToCart(selectedBook));
    setNotice(`Книга «${selectedBook.title_ru || selectedBook.title}» добавлена в корзину.`);
    window.setTimeout(() => setNotice(""), 1800);
  };

  if (selectedStatus === "loading") {
    return (
      <section className="page-card">
        <p className="muted">Загружаем карточку книги...</p>
      </section>
    );
  }

  if (selectedStatus === "failed" || !selectedBook) {
    return (
      <section className="page-card">
        <h2>Карточка книги</h2>
        <p className="error-text">{String(selectedError || "Книга не найдена")}</p>
        <Link to="/" className="mini-link">
          Вернуться в каталог
        </Link>
      </section>
    );
  }

  return (
    <section className="page-card book-details-page">
      <div className="book-details-back">
        <Link to="/" className="mini-link">
          ← Назад в каталог
        </Link>
      </div>

      <div className="book-details-grid">
        <div className="book-details-cover">
          {selectedBook.cover_url ? (
            <img src={selectedBook.cover_url} alt={`Обложка книги ${selectedBook.title}`} />
          ) : (
            <div className="book-details-cover__fallback">
              <span>Нет обложки</span>
            </div>
          )}
        </div>

        <div className="book-details-info">
          <h2>{selectedBook.title_ru || selectedBook.title}</h2>
          {selectedBook.title_ru ? <p className="book-title-original">{selectedBook.title}</p> : null}
          <p className="muted">{selectedBook.author}</p>

          <div className="book-details-meta">
            <article>
              <p className="muted">ISBN</p>
              <strong>{selectedBook.isbn || "—"}</strong>
            </article>
            <article>
              <p className="muted">Издательство</p>
              <strong>{selectedBook.publisher || "—"}</strong>
            </article>
            <article>
              <p className="muted">Год</p>
              <strong>{selectedBook.year || "—"}</strong>
            </article>
            <article>
              <p className="muted">В наличии</p>
              <strong>{selectedBook.available_quantity ?? selectedBook.stock_quantity ?? 0}</strong>
            </article>
          </div>

          <div className="book-extended-grid">
            <div className="book-extended-column">
              <div className="book-extended-row">
                <span>Издательство:</span>
                <strong>{selectedBook.publisher || "—"}</strong>
              </div>
              <div className="book-extended-row">
                <span>Год издания:</span>
                <strong>{selectedBook.year || "—"}</strong>
              </div>
              <div className="book-extended-row">
                <span>Место издания:</span>
                <strong>{selectedBook.publication_place || "—"}</strong>
              </div>
            </div>
            <div className="book-extended-column">
              <div className="book-extended-row">
                <span>Вес:</span>
                <strong>{formatInt(selectedBook.weight_grams, "гр.")}</strong>
              </div>
              <div className="book-extended-row">
                <span>Страниц:</span>
                <strong>{formatInt(selectedBook.page_count)}</strong>
              </div>
              <div className="book-extended-row">
                <span>Тираж:</span>
                <strong>{formatInt(selectedBook.print_run, "экз.")}</strong>
              </div>
            </div>
          </div>

          <article className="book-details-description">
            <h3>Аннотация</h3>
            <p>{normalizeAnnotation(selectedBook.description)}</p>
            {selectedBook.genre ? (
              <p className="book-genre-line">
                <strong>Жанр/Категория:</strong> {selectedBook.genre}
              </p>
            ) : null}
            {selectedBook.source_url ? (
              <p className="book-source-line">
                <a href={selectedBook.source_url} target="_blank" rel="noreferrer">
                  Источник карточки
                </a>
              </p>
            ) : null}
          </article>

          <div className="book-details-footer">
            <strong>{formatCurrency(selectedBook.price)}</strong>
            <button className="button" type="button" onClick={onAddToCart}>
              Добавить в корзину
            </button>
          </div>

          {notice ? <p className="success-text">{notice}</p> : null}
        </div>
      </div>
    </section>
  );
}

export default BookDetailsPage;
