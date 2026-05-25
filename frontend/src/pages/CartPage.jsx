import { useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import {
  clearCart,
  decreaseQuantity,
  increaseQuantity,
  setQuantity,
  removeFromCart
} from "../features/cart/cartSlice";
import { createSale } from "../features/sales/salesSlice";
import { createOrder } from "../features/orders/ordersSlice";

const MAX_CART_QUANTITY = 99;

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2
  }).format(Number(value || 0));

function CartPage() {
  const dispatch = useAppDispatch();
  const cartItems = useAppSelector((state) => state.cart.items);
  const { profile } = useAppSelector((state) => state.user);
  const { status, error, lastSale } = useAppSelector((state) => state.sales);
  const { checkoutStatus, checkoutError, lastOrder } = useAppSelector((state) => state.orders);
  const [localMessage, setLocalMessage] = useState("");

  const isClient = profile?.role === "client";
  const canCreateSale = ["cashier", "manager", "admin"].includes(profile?.role);

  const total = useMemo(
    () =>
      cartItems.reduce((sum, item) => sum + Number(item.book.price || 0) * Number(item.quantity || 0), 0),
    [cartItems]
  );

  const onCheckout = async () => {
    if (!profile) {
      setLocalMessage("Для оформления продажи сначала войдите в аккаунт.");
      return;
    }

    if (!cartItems.length) {
      setLocalMessage("Корзина пустая.");
      return;
    }

    try {
      const payload = cartItems.map((item) => ({
        book_id: item.book.id,
        quantity: item.quantity
      }));

      if (isClient) {
        await dispatch(createOrder({ items: payload })).unwrap();
        dispatch(clearCart());
        setLocalMessage("Заказ передан менеджеру. Статус и историю покупок можно смотреть в профиле.");
        return;
      }

      if (!canCreateSale) {
        setLocalMessage("Текущая роль не может оформить продажу.");
        return;
      }

      await dispatch(createSale({ items: payload })).unwrap();
      dispatch(clearCart());
      setLocalMessage("Продажа успешно оформлена.");
    } catch {

    }
  };

  const onQuantityInputChange = (bookId, value) => {
    if (value === "") {
      return;
    }
    const parsedValue = Number(value);
    if (!Number.isFinite(parsedValue)) {
      return;
    }
    dispatch(setQuantity({ bookId, quantity: Math.min(MAX_CART_QUANTITY, parsedValue) }));
  };

  return (
    <section className="page-card">
      <h2>Корзина</h2>
      <p className="muted">
        {isClient
          ? "Клиент оформляет заказ, который поступает менеджеру на подтверждение."
          : "Для сотрудников данные отправляются в `POST /api/sales` по текущим товарам."}
      </p>

      {!cartItems.length ? (
        <p className="muted">Пока пусто. Добавьте книги из каталога.</p>
      ) : (
        <div className="cart-list">
          {cartItems.map((item) => (
            <article className="cart-item" key={item.book.id}>
              <div>
                <h3>{item.book.title}</h3>
                <p>{item.book.author}</p>
              </div>

              <div className="cart-actions">
                <button className="button button-secondary" onClick={() => dispatch(decreaseQuantity(item.book.id))}>
                  -
                </button>
                <input
                  className="input cart-qty-input"
                  type="number"
                  min="1"
                  max={MAX_CART_QUANTITY}
                  step="1"
                  inputMode="numeric"
                  value={item.quantity}
                  onChange={(event) => onQuantityInputChange(item.book.id, event.target.value)}
                />
                <button className="button button-secondary" onClick={() => dispatch(increaseQuantity(item.book.id))}>
                  +
                </button>
                <button className="button button-danger" onClick={() => dispatch(removeFromCart(item.book.id))}>
                  Удалить
                </button>
              </div>

              <strong>{formatCurrency(Number(item.book.price) * item.quantity)}</strong>
            </article>
          ))}
        </div>
      )}

      <div className="checkout-row">
        <strong>Итого: {formatCurrency(total)}</strong>
        <button
          type="button"
          className="button"
          onClick={onCheckout}
          disabled={isClient ? checkoutStatus === "loading" : status === "loading"}
        >
          {isClient
            ? checkoutStatus === "loading"
              ? "Передаём заказ..."
              : "Оформить заказ"
            : status === "loading"
              ? "Оформляем..."
              : "Оформить продажу"}
        </button>
      </div>

      {localMessage ? <p className="success-text">{localMessage}</p> : null}
      {isClient ? <>{checkoutError ? <p className="error-text">{String(checkoutError)}</p> : null}</> : null}
      {!isClient ? <>{error ? <p className="error-text">{String(error)}</p> : null}</> : null}
      {isClient ? (
        <>{lastOrder?.id ? <p className="muted">Номер последнего заказа: #{lastOrder.id}</p> : null}</>
      ) : null}
      {!isClient ? (
        <>{lastSale?.id ? <p className="muted">Номер последней продажи: #{lastSale.id}</p> : null}</>
      ) : null}
    </section>
  );
}

export default CartPage;
