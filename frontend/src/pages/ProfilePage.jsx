import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { fetchMyClientProfile } from "../features/user/userSlice";
import { getRoleLabel } from "../utils/roleLabels";

function ProfilePage() {
  const dispatch = useAppDispatch();
  const { profile, clientProfile, profileStatus, profileError } = useAppSelector((state) => state.user);

  useEffect(() => {
    if (profile) {
      dispatch(fetchMyClientProfile());
    }
  }, [dispatch, profile]);

  const displayLastName = clientProfile?.last_name || profile?.last_name || "";
  const displayFirstName = clientProfile?.first_name || profile?.first_name || "";
  const displayMiddleName = clientProfile?.middle_name || "";
  const displayFio = [displayLastName, displayFirstName, displayMiddleName].filter(Boolean).join(" ") || "Не заполнено";
  const displayPhone = clientProfile?.phone || "Не указан";

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
    </section>
  );
}

export default ProfilePage;
