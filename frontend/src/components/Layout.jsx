import { Link, NavLink } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "../app/hooks";
import { logoutUser } from "../features/user/userSlice";
import { getRoleLabel } from "../utils/roleLabels";

const navigationLinks = [
  { to: "/", label: "Главная" },
  { href: "/#catalog", label: "Каталог" },
  { to: "/projects", label: "Проекты" },
  { to: "/contacts", label: "Контакты" }
];

function Layout({ children }) {
  const dispatch = useAppDispatch();
  const { profile } = useAppSelector((state) => state.user);
  const cartItemsCount = useAppSelector((state) =>
    state.cart.items.reduce((total, item) => total + item.quantity, 0)
  );
  const canViewReports = ["manager", "admin"].includes(profile?.role);
  const canProcessOrders = profile?.role === "cashier";
  const currentYear = new Date().getFullYear();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-main">
          <div className="brand">
            <div className="brand-badge">КВ</div>
            <div>
              <p>Интернет-книжный магазин</p>
            </div>
          </div>

          <div className="header-right">
            <div className="header-meta">
              <a className="phone-chip" href="tel:+79999999999">
                +7 999 999 99 99
              </a>
            </div>

            <div className="header-auth-actions">
              {profile ? (
                <>
                  <span className="auth-user-tag">
                    {profile.role === "client"
                      ? profile.username
                      : `${profile.username} (${getRoleLabel(profile.role)})`}
                  </span>
                  <NavLink to="/profile" className="auth-link-button">
                    Профиль
                  </NavLink>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => dispatch(logoutUser())}
                  >
                    Выйти
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/register" className="auth-link-button">
                    Авторизоваться
                  </NavLink>
                  <NavLink to="/login" className="auth-link-button auth-link-button--primary">
                    Войти
                  </NavLink>
                </>
              )}
            </div>
          </div>
        </div>

        <nav className="top-nav">
          <div className="nav-links">
            {navigationLinks.map((link) =>
              link.href ? (
                <a key={link.href} href={link.href} className="nav-link">
                  {link.label}
                </a>
              ) : (
                <NavLink key={link.to} to={link.to} className="nav-link">
                  {link.label}
                </NavLink>
              )
            )}
          </div>

          <div className="nav-utilities">
            <Link to="/cart" className="cart-pill">
              Корзина ({cartItemsCount})
            </Link>
            {canViewReports ? (
              <Link to="/admin" className="mini-link">
                Отчеты
              </Link>
            ) : null}
            {canProcessOrders ? (
              <Link to="/admin" className="mini-link">
                Заказы
              </Link>
            ) : null}
          </div>
        </nav>
      </header>

      <main className="page-container">{children}</main>
      <footer className="app-footer">
        <div className="app-footer__inner">
          <p>Книжная вселенная</p>
          <span>© {currentYear} Интернет-книжный магазин</span>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
