import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchSalesReport } from "../features/sales/salesSlice";
import { approveOrder, fetchPendingOrders, rejectOrder } from "../features/orders/ordersSlice";
import { booksApi, clientApi, questionsApi, usersApi } from "../api/endpoints";
import { getRoleLabel } from "../utils/roleLabels";
import { formatRuPhoneForStore, isValidRuPhone, normalizePhoneDigits } from "../utils/validators";

const ROLE_OPTIONS = ["client", "cashier", "manager", "admin"];
const PROFILE_LIMITS = {
  first_name: 50,
  last_name: 50,
  middle_name: 50,
  phone: 11,
  email: 120
};

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
  const [isUsersVisible, setIsUsersVisible] = useState(false);
  const [usersStatus, setUsersStatus] = useState("idle");
  const [usersError, setUsersError] = useState("");
  const [usersList, setUsersList] = useState([]);
  const [clientsByUserId, setClientsByUserId] = useState({});
  const [selectedUserId, setSelectedUserId] = useState("");
  const [editRole, setEditRole] = useState("client");
  const [profileForm, setProfileForm] = useState({
    first_name: "",
    last_name: "",
    middle_name: "",
    phone: "",
    email: ""
  });
  const [userManageStatus, setUserManageStatus] = useState("idle");
  const [userManageMessage, setUserManageMessage] = useState("");
  const [isActivityVisible, setIsActivityVisible] = useState(false);
  const [activityStatus, setActivityStatus] = useState("idle");
  const [activityError, setActivityError] = useState("");
  const [activityLogs, setActivityLogs] = useState([]);
  const statusLabels = {
    completed: "Завершенных",
    returned: "Возвратов",
    cancelled: "Отменённых"
  };

  const canProcessOrders = ["cashier", "manager", "admin"].includes(profile?.role);
  const canViewReports = ["manager", "admin"].includes(profile?.role);
  const canManageBooks = ["manager", "admin"].includes(profile?.role);
  const isAdmin = profile?.role === "admin";
  const selectedUser = usersList.find((user) => String(user.id) === String(selectedUserId));
  const isSelectedSelf = Boolean(selectedUser && profile && selectedUser.id === profile.id);

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

    } finally {
      setProcessingOrderId(null);
    }
  };

  const onRejectOrder = async (orderId) => {
    setProcessingOrderId(orderId);
    try {
      await dispatch(rejectOrder({ orderId })).unwrap();
    } catch {

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

  const onToggleUsersRoles = async () => {
    if (!isAdmin) {
      return;
    }

    if (isUsersVisible) {
      setIsUsersVisible(false);
      return;
    }

    setIsUsersVisible(true);
    if (usersStatus === "succeeded") {
      return;
    }

    setUsersStatus("loading");
    setUsersError("");
    try {
      const [usersResponse, clientsResponse] = await Promise.all([usersApi.getAll(), clientApi.getAll()]);
      const users = usersResponse.data?.users || [];
      setUsersList(users);
      const clients = clientsResponse.data?.clients || [];
      const map = {};
      clients.forEach((client) => {
        if (client.user_id) {
          map[client.user_id] = client;
        }
      });
      setClientsByUserId(map);
      if (users.length && !selectedUserId) {
        setSelectedUserId(String(users[0].id));
      }
      setUsersStatus("succeeded");
    } catch (error) {
      setUsersStatus("failed");
      setUsersError(error.response?.data?.message || "Не удалось загрузить роли пользователей.");
    }
  };

  useEffect(() => {
    if (!selectedUserId) {
      return;
    }
    const user = usersList.find((item) => String(item.id) === String(selectedUserId));
    if (!user) {
      return;
    }
    const client = clientsByUserId[user.id];
    setEditRole(user.role || "client");
    setProfileForm({
      first_name: client?.first_name || user.first_name || "",
      last_name: client?.last_name || user.last_name || "",
      middle_name: client?.middle_name || "",
      phone: normalizePhoneDigits(client?.phone || "").slice(0, PROFILE_LIMITS.phone),
      email: client?.email || user.email || ""
    });
  }, [selectedUserId, usersList, clientsByUserId]);

  const onSaveUserRole = async () => {
    if (!selectedUserId) {
      return;
    }
    setUserManageStatus("loading");
    setUserManageMessage("");
    try {
      await usersApi.updateRole(selectedUserId, editRole);
      setUsersList((prev) =>
        prev.map((user) => (String(user.id) === String(selectedUserId) ? { ...user, role: editRole } : user))
      );
      setUserManageStatus("success");
      setUserManageMessage("Роль пользователя обновлена.");
    } catch (error) {
      setUserManageStatus("error");
      setUserManageMessage(error.response?.data?.message || "Не удалось обновить роль пользователя.");
    }
  };

  const onSaveUserProfile = async () => {
    if (!selectedUserId) {
      return;
    }
    const firstName = profileForm.first_name.trim();
    const lastName = profileForm.last_name.trim();
    const middleName = profileForm.middle_name.trim();
    const email = profileForm.email.trim();
    const phone = profileForm.phone.trim();

    if (!firstName || !lastName) {
      setUserManageStatus("error");
      setUserManageMessage("Имя и фамилия обязательны.");
      return;
    }
    if (!isValidRuPhone(phone)) {
      setUserManageStatus("error");
      setUserManageMessage("Введите корректный номер телефона (10–11 цифр).");
      return;
    }

    const payload = {
      first_name: firstName,
      last_name: lastName,
      middle_name: middleName || undefined,
      phone: formatRuPhoneForStore(phone),
      email: email || undefined
    };

    setUserManageStatus("loading");
    setUserManageMessage("");
    try {
      const userIdNumber = Number(selectedUserId);
      const existingClient = clientsByUserId[userIdNumber];
      let client;
      if (existingClient?.id) {
        const response = await clientApi.updateById(existingClient.id, payload);
        client = response.data?.client;
      } else {
        const response = await clientApi.create({ ...payload, user_id: userIdNumber });
        client = response.data?.client;
      }
      if (client?.user_id) {
        setClientsByUserId((prev) => ({ ...prev, [client.user_id]: client }));
      }
      setUserManageStatus("success");
      setUserManageMessage("Профиль пользователя сохранён.");
    } catch (error) {
      setUserManageStatus("error");
      setUserManageMessage(error.response?.data?.message || "Не удалось сохранить профиль пользователя.");
    }
  };

  const onDeactivateUser = async () => {
    if (!selectedUserId) {
      return;
    }
    setUserManageStatus("loading");
    setUserManageMessage("");
    try {
      await usersApi.deactivate(selectedUserId);
      setUsersList((prev) =>
        prev.map((user) => (String(user.id) === String(selectedUserId) ? { ...user, is_active: false } : user))
      );
      setUserManageStatus("success");
      setUserManageMessage("Аккаунт пользователя деактивирован.");
    } catch (error) {
      setUserManageStatus("error");
      setUserManageMessage(error.response?.data?.message || "Не удалось деактивировать аккаунт.");
    }
  };

  const onActivateUser = async () => {
    if (!selectedUserId) {
      return;
    }
    setUserManageStatus("loading");
    setUserManageMessage("");
    try {
      await usersApi.activate(selectedUserId);
      setUsersList((prev) =>
        prev.map((user) => (String(user.id) === String(selectedUserId) ? { ...user, is_active: true } : user))
      );
      setUserManageStatus("success");
      setUserManageMessage("Аккаунт пользователя активирован.");
    } catch (error) {
      setUserManageStatus("error");
      setUserManageMessage(error.response?.data?.message || "Не удалось активировать аккаунт.");
    }
  };

  const onDeleteUser = async () => {
    if (!selectedUserId) {
      return;
    }
    if (isSelectedSelf) {
      setUserManageStatus("error");
      setUserManageMessage("Нельзя удалить свой собственный аккаунт администратора.");
      return;
    }
    setUserManageStatus("loading");
    setUserManageMessage("");
    try {
      const deletingId = Number(selectedUserId);
      await usersApi.remove(selectedUserId);
      const nextUsers = usersList.filter((user) => user.id !== deletingId);
      setUsersList(nextUsers);
      setClientsByUserId((prev) => {
        const updated = { ...prev };
        delete updated[deletingId];
        return updated;
      });
      if (nextUsers.length) {
        setSelectedUserId(String(nextUsers[0].id));
      } else {
        setSelectedUserId("");
      }
      setUserManageStatus("success");
      setUserManageMessage("Аккаунт пользователя удалён.");
    } catch (error) {
      setUserManageStatus("error");
      setUserManageMessage(error.response?.data?.message || "Не удалось удалить аккаунт.");
    }
  };

  const onToggleActivityLogs = async () => {
    if (!isAdmin) {
      return;
    }

    if (isActivityVisible) {
      setIsActivityVisible(false);
      return;
    }

    setIsActivityVisible(true);
    setActivityStatus("loading");
    setActivityError("");

    try {
      const response = await usersApi.getActivityLogs(200);
      setActivityLogs(response.data?.logs || []);
      setActivityStatus("succeeded");
    } catch (error) {
      setActivityStatus("failed");
      setActivityError(error.response?.data?.message || "Не удалось загрузить журнал активности.");
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
        <p className="error-text">У роли {getRoleLabel(profile.role)} нет доступа к обработке заказов и отчётам.</p>
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
                <p className="status-card-inline">
                  {statusLabels[item.status] || item.status}: {item.count} ({formatCurrency(item.total)})
                </p>
              </article>
            ))}
          </div>

          {isAdmin ? (
            <div className="admin-users-block">
              <div className="admin-tools-row">
                <button className="button button-secondary" type="button" onClick={onToggleUsersRoles}>
                {isUsersVisible ? "Скрыть роли пользователей" : "Показать роли пользователей"}
                </button>
                <button className="button button-secondary" type="button" onClick={onToggleActivityLogs}>
                  {isActivityVisible ? "Скрыть журнал действий" : "Показать журнал действий"}
                </button>
              </div>
              {isUsersVisible ? (
                <div className="admin-users-panel">
                  {usersStatus === "loading" ? <p className="muted">Загружаем роли...</p> : null}
                  {usersError ? <p className="error-text">{usersError}</p> : null}
                  {usersStatus === "succeeded" ? (
                    <>
                      <div className="manual-book-form">
                        <label className="select-wrap">
                          Пользователь
                          <select
                            className="input"
                            value={selectedUserId}
                            onChange={(event) => setSelectedUserId(event.target.value)}
                          >
                            {usersList.map((user) => (
                              <option key={user.id} value={user.id}>
                                {user.username} ({user.email})
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="select-wrap">
                          Роль
                          <select
                            className="input"
                            value={editRole}
                            onChange={(event) => setEditRole(event.target.value)}
                          >
                            {ROLE_OPTIONS.map((role) => (
                              <option key={role} value={role}>
                                {getRoleLabel(role)}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button className="button button-secondary" type="button" onClick={onSaveUserRole}>
                          Сохранить роль
                        </button>
                        <button
                          className="button button-secondary"
                          type="button"
                          onClick={onDeactivateUser}
                          disabled={!selectedUser || selectedUser.is_active === false}
                        >
                          Деактивировать аккаунт
                        </button>
                        <button
                          className="button button-secondary"
                          type="button"
                          onClick={onActivateUser}
                          disabled={!selectedUser || selectedUser.is_active === true}
                        >
                          Активировать аккаунт
                        </button>
                        <button
                          className="button button-danger"
                          type="button"
                          onClick={onDeleteUser}
                          disabled={!selectedUser || isSelectedSelf}
                        >
                          Удалить аккаунт
                        </button>
                        <input
                          className="input"
                          type="text"
                          placeholder="Имя"
                          value={profileForm.first_name}
                          maxLength={PROFILE_LIMITS.first_name}
                          onChange={(event) => setProfileForm((prev) => ({ ...prev, first_name: event.target.value }))}
                        />
                        <input
                          className="input"
                          type="text"
                          placeholder="Фамилия"
                          value={profileForm.last_name}
                          maxLength={PROFILE_LIMITS.last_name}
                          onChange={(event) => setProfileForm((prev) => ({ ...prev, last_name: event.target.value }))}
                        />
                        <input
                          className="input"
                          type="text"
                          placeholder="Отчество"
                          value={profileForm.middle_name}
                          maxLength={PROFILE_LIMITS.middle_name}
                          onChange={(event) =>
                            setProfileForm((prev) => ({ ...prev, middle_name: event.target.value }))
                          }
                        />
                        <input
                          className="input"
                          type="text"
                          placeholder="Телефон"
                          value={profileForm.phone}
                          maxLength={PROFILE_LIMITS.phone}
                          inputMode="numeric"
                          pattern="[0-9]*"
                          onChange={(event) =>
                            setProfileForm((prev) => ({
                              ...prev,
                              phone: normalizePhoneDigits(event.target.value).slice(0, PROFILE_LIMITS.phone)
                            }))
                          }
                        />
                        <input
                          className="input"
                          type="email"
                          placeholder="Email"
                          value={profileForm.email}
                          maxLength={PROFILE_LIMITS.email}
                          onChange={(event) => setProfileForm((prev) => ({ ...prev, email: event.target.value }))}
                        />
                        <button className="button" type="button" onClick={onSaveUserProfile}>
                          Сохранить профиль пользователя
                        </button>
                      </div>
                      {userManageMessage ? (
                        <p className={userManageStatus === "success" ? "success-text" : "error-text"}>
                          {userManageMessage}
                        </p>
                      ) : null}
                      <div className="admin-users-list">
                        {usersList.map((user) => (
                          <article className="admin-user-card" key={user.id}>
                            <strong>{user.username}</strong>
                            <span>{user.email}</span>
                            <span>Роль: {getRoleLabel(user.role)}</span>
                            <span>Статус: {user.is_active ? "Активен" : "Деактивирован"}</span>
                          </article>
                        ))}
                      </div>
                    </>
                  ) : null}
                </div>
              ) : null}
              {isActivityVisible ? (
                <div className="admin-users-panel">
                  {activityStatus === "loading" ? <p className="muted">Загружаем журнал...</p> : null}
                  {activityError ? <p className="error-text">{activityError}</p> : null}
                  {activityStatus === "succeeded" ? (
                    <pre className="activity-log-view">{activityLogs.join("\n") || "Журнал пока пуст."}</pre>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}

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
