function RecommendationList({ title, items, emptyText }) {
  return (
    <section className="recommendation-block">
      <h3>{title}</h3>
      {items.length ? (
        <ul className="recommendation-list">
          {items.map((item, index) => {
            const book = item.book || item;
            return (
              <li key={`${book.id || book.title}-${index}`}>
                <strong>{book.title}</strong>
                <span>{book.author}</span>
                {item.reason ? <em>{item.reason}</em> : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="muted">{emptyText}</p>
      )}
    </section>
  );
}

function RecommendationsPanel({ popularBooks, cartRecommendations, personalRecommendations }) {
  return (
    <aside className="recommendations-panel">
      <RecommendationList
        title="Популярные книги"
        items={popularBooks}
        emptyText="Пока нет данных о популярных книгах."
      />
      <RecommendationList
        title="Для вашей корзины"
        items={cartRecommendations}
        emptyText="Добавьте книги в корзину, чтобы увидеть рекомендации."
      />
      <RecommendationList
        title="Персонально для вас"
        items={personalRecommendations}
        emptyText="Войдите, чтобы получить персональные рекомендации."
      />
    </aside>
  );
}

export default RecommendationsPanel;
