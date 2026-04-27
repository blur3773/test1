import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { clearAuthError, registerUser } from "../features/user/userSlice";

function RegisterPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { profile, status, error } = useAppSelector((state) => state.user);
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: ""
  });

  useEffect(() => {
    dispatch(clearAuthError());
  }, [dispatch]);

  useEffect(() => {
    if (profile) {
      navigate("/", { replace: true });
    }
  }, [navigate, profile]);

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!form.email || !form.username || !form.password) {
      return;
    }
    await dispatch(registerUser(form));
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
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
          />
          <input
            className="input"
            type="text"
            placeholder="Username"
            value={form.username}
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

        {error ? <p className="error-text">{String(error)}</p> : null}
        <p className="muted">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </article>
    </section>
  );
}

export default RegisterPage;
