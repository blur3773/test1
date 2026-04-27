import { useState } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { loginUser, logoutUser } from "../features/user/userSlice";

function AuthPanel() {
  const dispatch = useAppDispatch();
  const { profile, status, error } = useAppSelector((state) => state.user);
  const [form, setForm] = useState({ email: "", password: "" });

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!form.email || !form.password) {
      return;
    }

    await dispatch(loginUser(form));
    setForm((prev) => ({ ...prev, password: "" }));
  };

  if (profile) {
    return (
      <div className="auth-panel auth-panel--logged">
        <div>
          <p className="auth-title">{profile.username}</p>
          <p className="auth-subtitle">Роль: {profile.role}</p>
        </div>
        <button
          type="button"
          className="button button-secondary"
          onClick={() => dispatch(logoutUser())}
        >
          Выйти
        </button>
      </div>
    );
  }

  return (
    <form className="auth-panel" onSubmit={onSubmit}>
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
        {status === "loading" ? "Вход..." : "Войти"}
      </button>
      {error ? <p className="error-text">{String(error)}</p> : null}
    </form>
  );
}

export default AuthPanel;
