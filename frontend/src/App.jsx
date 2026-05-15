import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import CatalogPage from "./pages/CatalogPage";
import CartPage from "./pages/CartPage";
import AdminPanelPage from "./pages/AdminPanelPage";
import ProfilePage from "./pages/ProfilePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProjectsPage from "./pages/ProjectsPage";
import ContactsPage from "./pages/ContactsPage";
import BookDetailsPage from "./pages/BookDetailsPage";
import { useAppDispatch } from "./app/hooks";
import { hydrateSession } from "./features/user/userSlice";

function App() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(hydrateSession());
  }, [dispatch]);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<CatalogPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/admin" element={<AdminPanelPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/books/:bookId" element={<BookDetailsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
