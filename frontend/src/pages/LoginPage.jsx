import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { clearAuthError, loginUser } from "../features/user/userSlice";

function LoginPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { profile, status, error } = useAppSelector((state) => state.user);
  const [form, setForm] = useState({
    email: "",
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
    if (!form.email || !form.password) {
      return;
    }
    await dispatch(loginUser(form));
  };

  return (
    <section className="auth-page">
      <article className="auth-card">
        <p className="hero-eyebrow">Страница входа</p>
        <h2>Войти в аккаунт</h2>
        <p className="muted">Для уже зарегистрированных пользователей магазина.</p>

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
            type="password"
            placeholder="Пароль"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
          />
          <button className="button" type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Входим..." : "Войти"}
          </button>
        </form>

        {error ? <p className="error-text">{String(error)}</p> : null}
        <p className="muted">
          Нет аккаунта? <Link to="/register">Авторизоваться</Link>
        </p>
      </article>
    </section>
  );
}

export default LoginPage;
