import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchMyClientProfile, updateMyClientProfile } from "../features/user/userSlice";

const emptyForm = {
  first_name: "",
  last_name: "",
  middle_name: "",
  phone: "",
  email: ""
};

function ProfilePage() {
  const dispatch = useAppDispatch();
  const { profile, clientProfile, profileStatus, profileError } = useAppSelector((state) => state.user);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (profile) {
      dispatch(fetchMyClientProfile());
    }
  }, [dispatch, profile]);

  useEffect(() => {
    if (clientProfile) {
      setForm({
        first_name: clientProfile.first_name || "",
        last_name: clientProfile.last_name || "",
        middle_name: clientProfile.middle_name || "",
        phone: clientProfile.phone || "",
        email: clientProfile.email || ""
      });
    }
  }, [clientProfile]);

  const onSubmit = async (event) => {
    event.preventDefault();
    try {
      await dispatch(updateMyClientProfile(form)).unwrap();
      setMessage("Профиль обновлён.");
    } catch {
      setMessage("Обновить профиль не удалось.");
    }
  };

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
          <strong>{profile.role}</strong>
        </article>
      </div>

      <h3>Профиль клиента (`/api/clients/me`)</h3>
      {profileStatus === "loading" ? <p className="muted">Загружаем данные...</p> : null}
      {profileError ? <p className="error-text">{String(profileError)}</p> : null}

      <form className="profile-form" onSubmit={onSubmit}>
        <input
          className="input"
          placeholder="Имя"
          value={form.first_name}
          onChange={(event) => setForm((prev) => ({ ...prev, first_name: event.target.value }))}
        />
        <input
          className="input"
          placeholder="Фамилия"
          value={form.last_name}
          onChange={(event) => setForm((prev) => ({ ...prev, last_name: event.target.value }))}
        />
        <input
          className="input"
          placeholder="Отчество"
          value={form.middle_name}
          onChange={(event) => setForm((prev) => ({ ...prev, middle_name: event.target.value }))}
        />
        <input
          className="input"
          placeholder="Телефон"
          value={form.phone}
          onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
        />
        <input
          className="input"
          type="email"
          placeholder="Email клиента"
          value={form.email}
          onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
        />
        <button className="button" type="submit">
          Сохранить профиль
        </button>
      </form>

      {message ? <p className="success-text">{message}</p> : null}
    </section>
  );
}

export default ProfilePage;
