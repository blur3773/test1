import { useEffect, useRef, useState } from "react";
import { isNewBook, isSpringBestBook } from "../utils/bookPromos";

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2
  }).format(Number(value || 0));

const COVER_THEMES = [
  "cover-theme-red",
  "cover-theme-dark",
  "cover-theme-gray",
  "cover-theme-blue",
  "cover-theme-gold"
];

const buildAbbr = (title) => title.split(" ").slice(0, 2).map((word) => word[0]).join("").toUpperCase();

function BookCard({ book, onAddToCart }) {
  const [imageFailed, setImageFailed] = useState(false);
  const [isAdded, setIsAdded] = useState(false);
  const timerRef = useRef(null);
  const themeClass = COVER_THEMES[book.id % COVER_THEMES.length];
  const showCoverImage = Boolean(book.cover_url) && !imageFailed;
  const hasNewBadge = isNewBook(book);
  const hasSpringBadge = isSpringBestBook(book);

  useEffect(
    () => () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    },
    []
  );

  const onBuyClick = () => {
    onAddToCart(book);
    setIsAdded(true);

    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }

    timerRef.current = window.setTimeout(() => {
      setIsAdded(false);
    }, 550);
  };

  return (
    <article className="book-card">
      <div className={`book-cover ${showCoverImage ? "book-cover--image" : themeClass}`}>
        {hasNewBadge || hasSpringBadge ? (
          <div className="book-promo-badges">
            {hasNewBadge ? <span className="book-promo-badge book-promo-badge--new">Новинка</span> : null}
            {hasSpringBadge ? (
              <span className="book-promo-badge book-promo-badge--spring">Весенний бестселлер</span>
            ) : null}
          </div>
        ) : null}
        {showCoverImage ? (
          <img
            src={book.cover_url}
            alt={`Обложка книги ${book.title}`}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <>
            <span className="book-cover-abbr">{buildAbbr(book.title)}</span>
            <span className="book-cover-name">{book.title}</span>
          </>
        )}
      </div>

      <div className="book-card__head">
        <h3>{book.title_ru || book.title}</h3>
        {book.title_ru ? <p className="book-title-original">{book.title}</p> : null}
        <span>{book.author}</span>
      </div>

      <div className="book-meta">
        <span>ISBN: {book.isbn}</span>
        <span>В наличии: {book.available_quantity ?? book.stock_quantity ?? 0}</span>
      </div>

      <div className="book-footer">
        <strong>{formatCurrency(book.price)}</strong>
        <button
          className={`button card-buy-button ${isAdded ? "is-added" : ""}`}
          type="button"
          onClick={onBuyClick}
        >
          Купить
        </button>
      </div>
    </article>
  );
}

export default BookCard;
