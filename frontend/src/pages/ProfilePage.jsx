import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchMyOrders } from "../features/orders/ordersSlice";
import { fetchMyClientProfile } from "../features/user/userSlice";
import { getRoleLabel } from "../utils/roleLabels";

const ORDER_STATUS_LABELS = {
  pending: "Ожидает менеджера",
  approved: "Подтверждён",
  completed: "Покупка завершена",
  rejected: "Отклонён",
  cancelled: "Отменён"
};

const ORDER_PROGRESS_META = {
  pending: {
    percent: 50,
    activeIndex: 1,
    tone: "active",
    finalLabel: "Решение"
  },
  approved: {
    percent: 100,
    activeIndex: 2,
    tone: "success",
    finalLabel: "Подтверждён"
  },
  completed: {
    percent: 100,
    activeIndex: 2,
    tone: "success",
    finalLabel: "Подтверждён"
  },
  rejected: {
    percent: 100,
    activeIndex: 2,
    tone: "danger",
    finalLabel: "Отклонён"
  },
  cancelled: {
    percent: 100,
    activeIndex: 2,
    tone: "muted",
    finalLabel: "Отменён"
  }
};

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2
  }).format(Number(value || 0));

const formatDateTime = (value) => {
  if (!value) {
    return "Дата не указана";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
};

function OrderProgress({ status }) {
  const meta = ORDER_PROGRESS_META[status] || ORDER_PROGRESS_META.pending;
  const steps = ["Создан", "У менеджера", meta.finalLabel];

  return (
    <div
      className={`order-progress order-progress--${meta.tone}`}
      aria-label={`Статус заказа: ${ORDER_STATUS_LABELS[status] || status}`}
    >
      <div className="order-progress__track">
        <span className="order-progress__fill" style={{ width: `${meta.percent}%` }} />
      </div>
      <div className="order-progress__steps">
        {steps.map((step, index) => (
          <span
            className={index <= meta.activeIndex ? "order-progress__step is-active" : "order-progress__step"}
            key={`${status}-${step}`}
          >
            <span className="order-progress__dot" />
            <span>{step}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function OrderItems({ order }) {
  return (
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
  );
}

function OrderStatusCard({ order }) {
  const statusLabel = ORDER_STATUS_LABELS[order.status] || order.status;

  return (
    <article className="order-card order-card--client">
      <div className="order-card__head">
        <div>
          <strong>Заказ #{order.id}</strong>
          <p>
            Сумма: {formatCurrency(order.total_amount)} · Обновлён: {formatDateTime(order.updated_at)}
          </p>
        </div>
        <span className={`order-status-chip order-status-chip--${order.status}`}>{statusLabel}</span>
      </div>

      <OrderProgress status={order.status} />
      <OrderItems order={order} />

      {order.manager_name ? <p className="muted">Менеджер: {order.manager_name}</p> : null}
      {order.manager_comment ? <p className="muted">Комментарий менеджера: {order.manager_comment}</p> : null}
    </article>
  );
}

function PurchaseHistoryCard({ order }) {
  return (
    <article className="order-card purchase-card">
      <div className="order-card__head">
        <div>
          <strong>Покупка #{order.sale_id || order.id}</strong>
          <p>
            Заказ #{order.id} · {formatDateTime(order.updated_at || order.created_at)}
          </p>
        </div>
        <span>{formatCurrency(order.total_amount)}</span>
      </div>
      <OrderItems order={order} />
    </article>
  );
}

function ProfilePage() {
  const dispatch = useAppDispatch();
  const { profile, clientProfile, profileStatus, profileError } = useAppSelector((state) => state.user);
  const { myOrders, myOrdersStatus, myOrdersError } = useAppSelector((state) => state.orders);
  const isClient = profile?.role === "client";

  useEffect(() => {
    if (profile) {
      dispatch(fetchMyClientProfile());
    }
  }, [dispatch, profile]);

  useEffect(() => {
    if (isClient) {
      dispatch(fetchMyOrders());
      const refreshInterval = window.setInterval(() => {
        dispatch(fetchMyOrders());
      }, 15000);

      return () => window.clearInterval(refreshInterval);
    }
  }, [dispatch, isClient]);

  const displayLastName = clientProfile?.last_name || profile?.last_name || "";
  const displayFirstName = clientProfile?.first_name || profile?.first_name || "";
  const displayMiddleName = clientProfile?.middle_name || "";
  const displayFio = [displayLastName, displayFirstName, displayMiddleName].filter(Boolean).join(" ") || "Не заполнено";
  const displayPhone = clientProfile?.phone || "Не указан";
  const activeOrders = myOrders.filter((order) => ["pending", "approved"].includes(order.status));
  const purchaseHistory = myOrders.filter((order) => order.status === "completed");
  const closedOrders = myOrders.filter((order) => ["rejected", "cancelled"].includes(order.status));
  const isInitialOrdersLoading = myOrdersStatus === "loading" && !myOrders.length;

  if (!profile) {
    return (
      <section className="page-card">
        <h2>Профиль</h2>
        <p className="muted">Войдите в аккаунт, чтобы открыть профиль.</p>
      </section>
    );
  }

  return (
    <section className="page-card">
      <h2>Профиль пользователя</h2>
      <div className="profile-top">
        <article>
          <p className="muted">Username</p>
          <strong>{profile.username}</strong>
        </article>
        <article>
          <p className="muted">Email</p>
          <strong>{profile.email}</strong>
        </article>
        <article>
          <p className="muted">Роль</p>
          <strong>{getRoleLabel(profile.role)}</strong>
        </article>
        <article>
          <p className="muted">ФИО</p>
          <strong>{displayFio}</strong>
        </article>
        <article>
          <p className="muted">Телефон</p>
          <strong>{displayPhone}</strong>
        </article>
      </div>

      {profileStatus === "loading" ? <p className="muted">Загружаем данные...</p> : null}
      {profileError ? <p className="error-text">{String(profileError)}</p> : null}

      {isClient ? (
        <div className="client-orders-panel">
          <div className="orders-section-header">
            <div>
              <h3>Статус заказов</h3>
              <p className="muted">Здесь видно, прошёл ли заказ проверку менеджера.</p>
            </div>
            <button
              type="button"
              className="button button-secondary"
              onClick={() => dispatch(fetchMyOrders())}
              disabled={myOrdersStatus === "loading"}
            >
              {myOrdersStatus === "loading" ? "Обновляем..." : "Обновить"}
            </button>
          </div>

          {isInitialOrdersLoading ? <p className="muted">Загружаем заказы...</p> : null}
          {myOrdersError ? <p className="error-text">{String(myOrdersError)}</p> : null}

          {activeOrders.length ? (
            <div className="orders-queue">
              {activeOrders.map((order) => (
                <OrderStatusCard order={order} key={order.id} />
              ))}
            </div>
          ) : !isInitialOrdersLoading ? (
            <p className="muted">Активных заказов сейчас нет.</p>
          ) : null}

          <div className="orders-section-header orders-section-header--compact">
            <h3>История покупок</h3>
          </div>

          {purchaseHistory.length ? (
            <div className="orders-queue purchase-history">
              {purchaseHistory.map((order) => (
                <PurchaseHistoryCard order={order} key={order.id} />
              ))}
            </div>
          ) : !isInitialOrdersLoading ? (
            <p className="muted">Подтверждённых покупок пока нет.</p>
          ) : null}

          {closedOrders.length ? (
            <>
              <div className="orders-section-header orders-section-header--compact">
                <h3>Закрытые заявки</h3>
              </div>
              <div className="orders-queue">
                {closedOrders.map((order) => (
                  <OrderStatusCard order={order} key={order.id} />
                ))}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

export default ProfilePage;
