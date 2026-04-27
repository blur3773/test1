import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchSalesReport } from "../features/sales/salesSlice";
import { approveOrder, fetchPendingOrders, rejectOrder } from "../features/orders/ordersSlice";
import { booksApi, questionsApi } from "../api/endpoints";

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2
  }).format(Number(value || 0));

const formatDateTime = (value) => {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
};

function AdminPanelPage() {
  const dispatch = useAppDispatch();
  const { profile } = useAppSelector((state) => state.user);
  const { report, reportStatus, reportError } = useAppSelector((state) => state.sales);
  const { managerOrders, managerOrdersStatus, managerOrdersError, actionStatus, actionError } = useAppSelector(
    (state) => state.orders
  );
  const [statusFilter, setStatusFilter] = useState("");
  const [processingOrderId, setProcessingOrderId] = useState(null);
  const [managerQuestions, setManagerQuestions] = useState([]);
  const [questionsStatus, setQuestionsStatus] = useState("idle");
  const [questionsError, setQuestionsError] = useState(null);
  const [bookForm, setBookForm] = useState({
    title: "",
    title_ru: "",
    author: "",
    isbn: "",
    price: "",
    publisher: "",
    year: "",
    description: "",
    stock_quantity: "0"
  });
  const [bookCreateStatus, setBookCreateStatus] = useState("idle");
  const [bookCreateMessage, setBookCreateMessage] = useState("");

  const canProcessOrders = ["cashier", "manager", "admin"].includes(profile?.role);
  const canViewReports = ["manager", "admin"].includes(profile?.role);
  const canManageBooks = ["manager", "admin"].includes(profile?.role);

  useEffect(() => {
    if (canProcessOrders) {
      dispatch(fetchPendingOrders());
    }
  }, [dispatch, canProcessOrders]);

  useEffect(() => {
    if (canViewReports) {
      dispatch(fetchSalesReport({ status: statusFilter || undefined }));
    }
  }, [dispatch, canViewReports, statusFilter]);

  useEffect(() => {
    if (!canViewReports) {
      setManagerQuestions([]);
      setQuestionsStatus("idle");
      setQuestionsError(null);
      return;
    }

    let isMounted = true;
    setQuestionsStatus("loading");
    setQuestionsError(null);

    questionsApi
      .getAll("new")
      .then((response) => {
        if (!isMounted) {
          return;
        }
        setManagerQuestions(response.data?.questions || []);
        setQuestionsStatus("succeeded");
      })
      .catch((error) => {
        if (!isMounted) {
          return;
        }
        setQuestionsStatus("failed");
        setQuestionsError(error.response?.data?.message || "Не удалось загрузить вопросы клиентов");
      });

    return () => {
      isMounted = false;
    };
  }, [canViewReports]);

  const onApproveOrder = async (orderId) => {
    setProcessingOrderId(orderId);
    try {
      await dispatch(approveOrder({ orderId })).unwrap();
    } catch {
      // Ошибка уже в orders.actionError
    } finally {
      setProcessingOrderId(null);
    }
  };

  const onRejectOrder = async (orderId) => {
    setProcessingOrderId(orderId);
    try {
      await dispatch(rejectOrder({ orderId })).unwrap();
    } catch {
      // Ошибка уже в orders.actionError
    } finally {
      setProcessingOrderId(null);
    }
  };

  const onBookFieldChange = (field, value) => {
    setBookForm((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const onCreateBook = async (event) => {
    event.preventDefault();

    const normalizedPrice = Number(String(bookForm.price).replace(",", "."));
    const normalizedYear = bookForm.year ? Number(bookForm.year) : null;
    const normalizedStock = bookForm.stock_quantity ? Number(bookForm.stock_quantity) : 0;

    if (!bookForm.title.trim() || !bookForm.author.trim() || !bookForm.isbn.trim()) {
      setBookCreateStatus("error");
      setBookCreateMessage("Заполните обязательные поля: название, автор, ISBN.");
      return;
    }

    if (!Number.isFinite(normalizedPrice) || normalizedPrice <= 0) {
      setBookCreateStatus("error");
      setBookCreateMessage("Цена должна быть больше 0.");
      return;
    }

    if (!Number.isInteger(normalizedStock) || normalizedStock < 0) {
      setBookCreateStatus("error");
      setBookCreateMessage("Остаток должен быть целым числом 0 или больше.");
      return;
    }

    if (normalizedYear !== null && (!Number.isInteger(normalizedYear) || normalizedYear < 0)) {
      setBookCreateStatus("error");
      setBookCreateMessage("Год должен быть целым положительным числом.");
      return;
    }

    setBookCreateStatus("loading");
    setBookCreateMessage("");

    try {
      const response = await booksApi.create({
        title: bookForm.title.trim(),
        title_ru: bookForm.title_ru.trim() || undefined,
        author: bookForm.author.trim(),
        isbn: bookForm.isbn.trim(),
        price: normalizedPrice,
        publisher: bookForm.publisher.trim() || undefined,
        year: normalizedYear || undefined,
        description: bookForm.description.trim() || undefined,
        stock_quantity: normalizedStock
      });

      const createdBook = response.data?.book;
      setBookCreateStatus("success");
      setBookCreateMessage(
        createdBook?.title
          ? `Книга "${createdBook.title}" успешно добавлена.`
          : "Книга успешно добавлена."
      );
      setBookForm({
        title: "",
        title_ru: "",
        author: "",
        isbn: "",
        price: "",
        publisher: "",
        year: "",
        description: "",
        stock_quantity: "0"
      });
    } catch (error) {
      setBookCreateStatus("error");
      setBookCreateMessage(error.response?.data?.message || "Не удалось добавить книгу.");
    }
  };

  if (!profile) {
    return (
      <section className="page-card">
        <h2>Панель сотрудника</h2>
        <p className="muted">Войдите в аккаунт менеджера или администратора.</p>
      </section>
    );
  }

  if (!canProcessOrders) {
    return (
      <section className="page-card">
        <h2>Панель сотрудника</h2>
        <p className="error-text">У роли {profile.role} нет доступа к обработке заказов и отчётам.</p>
      </section>
    );
  }

  return (
    <section className="page-card">
      <div className="page-card__header">
        <h2>{canViewReports ? "Панель менеджера" : "Панель кассира"}</h2>
        {canViewReports ? (
          <label className="select-wrap">
            Статус
            <select
              className="input"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="">Все</option>
              <option value="completed">Завершённые</option>
              <option value="returned">Возвраты</option>
              <option value="cancelled">Отменённые</option>
            </select>
          </label>
        ) : null}
      </div>

      {canViewReports ? (
        <>
          {reportStatus === "loading" ? <p className="muted">Загружаем отчёт...</p> : null}
          {reportError ? <p className="error-text">{String(reportError)}</p> : null}
        </>
      ) : null}

      {canViewReports && report ? (
        <>
          <div className="stats-grid">
            <article className="stat-card">
              <p>Продаж</p>
              <strong>{report.total_sales}</strong>
            </article>
            <article className="stat-card">
              <p>Выручка</p>
              <strong>{formatCurrency(report.total_revenue)}</strong>
            </article>
            <article className="stat-card">
              <p>Продано позиций</p>
              <strong>{report.total_items_sold}</strong>
            </article>
          </div>

          <h3>Разбивка по статусам</h3>
          <div className="status-grid">
            {(report.sales_by_status || []).map((item) => (
              <article className="status-card" key={item.status}>
                <p>{item.status}</p>
                <strong>{item.count}</strong>
                <span>{formatCurrency(item.total)}</span>
              </article>
            ))}
          </div>

        </>
      ) : null}

      {canManageBooks ? (
        <>
          <h3>Добавление книги вручную</h3>
          <form className="manual-book-form" onSubmit={onCreateBook}>
            <input
              className="input"
              type="text"
              placeholder="Название книги *"
              value={bookForm.title}
              onChange={(event) => onBookFieldChange("title", event.target.value)}
            />
            <input
              className="input"
              type="text"
              placeholder="Русское название (опционально)"
              value={bookForm.title_ru}
              onChange={(event) => onBookFieldChange("title_ru", event.target.value)}
            />
            <input
              className="input"
              type="text"
              placeholder="Автор *"
              value={bookForm.author}
              onChange={(event) => onBookFieldChange("author", event.target.value)}
            />
            <input
              className="input"
              type="text"
              placeholder="ISBN *"
              value={bookForm.isbn}
              onChange={(event) => onBookFieldChange("isbn", event.target.value)}
            />
            <input
              className="input"
              type="text"
              placeholder="Цена *"
              value={bookForm.price}
              onChange={(event) => onBookFieldChange("price", event.target.value)}
            />
            <input
              className="input"
              type="text"
              placeholder="Издательство"
              value={bookForm.publisher}
              onChange={(event) => onBookFieldChange("publisher", event.target.value)}
            />
            <input
              className="input"
              type="number"
              min="0"
              placeholder="Год издания"
              value={bookForm.year}
              onChange={(event) => onBookFieldChange("year", event.target.value)}
            />
            <input
              className="input"
              type="number"
              min="0"
              placeholder="Остаток на складе"
              value={bookForm.stock_quantity}
              onChange={(event) => onBookFieldChange("stock_quantity", event.target.value)}
            />
            <textarea
              className="input manual-book-form__description"
              placeholder="Описание книги"
              value={bookForm.description}
              onChange={(event) => onBookFieldChange("description", event.target.value)}
            />
            <button className="button" type="submit" disabled={bookCreateStatus === "loading"}>
              {bookCreateStatus === "loading" ? "Добавляем..." : "Добавить книгу"}
            </button>
          </form>
          {bookCreateMessage ? (
            <p className={bookCreateStatus === "success" ? "success-text" : "error-text"}>{bookCreateMessage}</p>
          ) : null}
        </>
      ) : null}

      <h3>Новые заказы клиентов</h3>
      {managerOrdersStatus === "loading" ? <p className="muted">Загружаем заказы...</p> : null}
      {managerOrdersError ? <p className="error-text">{String(managerOrdersError)}</p> : null}
      {actionError ? <p className="error-text">{String(actionError)}</p> : null}

      {managerOrders?.length ? (
        <div className="orders-queue">
          {managerOrders.map((order) => {
            const isProcessing = actionStatus === "loading" && processingOrderId === order.id;

            return (
              <article key={order.id} className="order-card">
                <div className="order-card__head">
                  <div>
                    <strong>Заказ #{order.id}</strong>
                    <p>
                      Клиент: {order.user_name || `user_${order.user_id}`} · Сумма:{" "}
                      {formatCurrency(order.total_amount)}
                    </p>
                  </div>
                  <span>{formatDateTime(order.created_at)}</span>
                </div>

                <div className="order-items">
                  {(order.items || []).map((item) => (
                    <div key={`${order.id}-${item.id || item.book_id}`} className="order-item-row">
                      <span>
                        {item.book_title || `Книга #${item.book_id}`} × {item.quantity}
                      </span>
                      <strong>{formatCurrency(item.subtotal)}</strong>
                    </div>
                  ))}
                </div>

                {order.customer_comment ? (
                  <p className="muted">Комментарий клиента: {order.customer_comment}</p>
                ) : null}

                <div className="order-actions">
                  <button
                    type="button"
                    className="button"
                    onClick={() => onApproveOrder(order.id)}
                    disabled={isProcessing}
                  >
                    {isProcessing ? "Обрабатываем..." : "Подтвердить"}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => onRejectOrder(order.id)}
                    disabled={isProcessing}
                  >
                    Отклонить
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="muted">Новых заказов нет.</p>
      )}

      {canViewReports ? (
        <>
          <h3>Вопросы клиентов</h3>
          {questionsStatus === "loading" ? <p className="muted">Загружаем вопросы...</p> : null}
          {questionsError ? <p className="error-text">{String(questionsError)}</p> : null}

          {managerQuestions.length ? (
            <div className="orders-queue">
              {managerQuestions.map((question) => (
                <article key={question.id} className="question-card">
                  <div className="order-card__head">
                    <div>
                      <strong>{question.topic || "Вопрос клиента"}</strong>
                      <p>
                        От: {question.name}
                        {question.email ? ` · ${question.email}` : ""}
                        {question.phone ? ` · ${question.phone}` : ""}
                      </p>
                    </div>
                    <span>{formatDateTime(question.created_at)}</span>
                  </div>
                  <p className="question-message">{question.message}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="muted">Новых вопросов пока нет.</p>
          )}
        </>
      ) : null}
    </section>
  );
}

export default AdminPanelPage;
