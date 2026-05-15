import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { clearAuthError, registerUser } from "../features/user/userSlice";
import { formatRuPhoneForStore, isValidEmail, isValidRuPhone, normalizePhoneDigits } from "../utils/validators";

const REGISTER_LIMITS = {
  first_name: 50,
  last_name: 50,
  middle_name: 50,
  phone: 11,
  email: 120,
  username: 80
};

function RegisterPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { profile, status, error } = useAppSelector((state) => state.user);
  const [localError, setLocalError] = useState("");
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    middle_name: "",
    phone: "",
    email: "",
    username: "",
    password: ""
  });

  useEffect(() => {
    dispatch(clearAuthError());
    setLocalError("");
  }, [dispatch]);

  useEffect(() => {
    if (profile) {
      navigate("/", { replace: true });
    }
  }, [navigate, profile]);

  const onSubmit = async (event) => {
    event.preventDefault();
    const firstName = form.first_name.trim();
    const lastName = form.last_name.trim();
    const middleName = form.middle_name.trim();
    const email = form.email.trim();
    const username = form.username.trim();
    const password = form.password;
    const phone = form.phone.trim();

    if (!firstName || !lastName || !email || !username || !password) {
      setLocalError("Заполните все обязательные поля.");
      return;
    }
    if (!isValidEmail(email)) {
      setLocalError("Введите корректный email.");
      return;
    }
    if (!isValidRuPhone(phone)) {
      setLocalError("Введите корректный номер телефона (10–11 цифр).");
      return;
    }
    setLocalError("");
    await dispatch(
      registerUser({
        first_name: firstName,
        last_name: lastName,
        middle_name: middleName,
        phone: formatRuPhoneForStore(phone),
        email,
        username,
        password
      })
    );
  };

  return (
    <section className="auth-page">
      <article className="auth-card">
        <p className="hero-eyebrow">Страница авторизации</p>
        <h2>Авторизоваться</h2>
        <p className="muted">Создайте новый аккаунт, чтобы покупать книги.</p>

        <form className="auth-form" onSubmit={onSubmit}>
          <input
            className="input"
            type="text"
            placeholder="Имя"
            value={form.first_name}
            maxLength={REGISTER_LIMITS.first_name}
            onChange={(event) => setForm((prev) => ({ ...prev, first_name: event.target.value }))}
          />
          <input
            className="input"
            type="text"
            placeholder="Фамилия"
            value={form.last_name}
            maxLength={REGISTER_LIMITS.last_name}
            onChange={(event) => setForm((prev) => ({ ...prev, last_name: event.target.value }))}
          />
          <input
            className="input"
            type="text"
            placeholder="Отчество"
            value={form.middle_name}
            maxLength={REGISTER_LIMITS.middle_name}
            onChange={(event) => setForm((prev) => ({ ...prev, middle_name: event.target.value }))}
          />
          <input
            className="input"
            type="text"
            placeholder="Телефон"
            value={form.phone}
            maxLength={REGISTER_LIMITS.phone}
            inputMode="numeric"
            pattern="[0-9]*"
            onChange={(event) =>
              setForm((prev) => ({
                ...prev,
                phone: normalizePhoneDigits(event.target.value).slice(0, REGISTER_LIMITS.phone)
              }))
            }
          />
          <input
            className="input"
            type="email"
            placeholder="Email"
            value={form.email}
            maxLength={REGISTER_LIMITS.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
          />
          <input
            className="input"
            type="text"
            placeholder="Username"
            value={form.username}
            maxLength={REGISTER_LIMITS.username}
            onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
          />
          <input
            className="input"
            type="password"
            placeholder="Пароль"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
          />
          <button className="button" type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Создаём..." : "Авторизоваться"}
          </button>
        </form>

        {localError ? <p className="error-text">{localError}</p> : null}
        {error ? <p className="error-text">{String(error)}</p> : null}
        <p className="muted">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </article>
    </section>
  );
}

export default RegisterPage;
