function ProjectsPage() {
  return (
    <section className="projects-page">
      <article className="page-card">
        <h2>О проекте «Книжная вселенная»</h2>
        <p className="muted">
          «Книжная вселенная» — онлайн-площадка, где пользователи выбирают книги, добавляют их в корзину и
          оформляют заказы, а сотрудники подтверждают и обрабатывают покупки.
        </p>
      </article>

      <div className="project-grid">
        <article className="project-tile">
          <h3>Каталог</h3>
          <p>Подборки, поиск, карточки книг и рекомендации на основе истории покупок.</p>
        </article>
        <article className="project-tile">
          <h3>Оформление заказа</h3>
          <p>Клиент отправляет заказ, менеджер подтверждает его и переводит в продажу.</p>
        </article>
        <article className="project-tile">
          <h3>Склад и продажи</h3>
          <p>Система резервирует остатки, учитывает продажи, отмены и возвраты.</p>
        </article>
      </div>
    </section>
  );
}

export default ProjectsPage;
