import api from "./httpClient";

export const booksApi = {
  getAll: (status = "active") => api.get("/books", { params: { status } }),
  search: (query) => api.get("/books/search", { params: { q: query } }),
  getById: (bookId) => api.get(`/books/${bookId}`),
  create: (payload) => api.post("/books", payload)
};

export const authApi = {
  register: (payload) => api.post("/auth/register", payload),
  login: (payload) => api.post("/auth/login", payload),
  me: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout")
};

export const salesApi = {
  create: (payload) => api.post("/sales", payload),
  getSalesReport: (status) =>
    api.get("/reports/sales", { params: status ? { status } : {} })
};

export const ordersApi = {
  checkout: (payload) => api.post("/orders/checkout", payload),
  getMy: () => api.get("/orders/my"),
  getAll: (status = "pending") => api.get("/orders", { params: { status } }),
  approve: (orderId, payload = {}) => api.post(`/orders/${orderId}/approve`, payload),
  reject: (orderId, payload = {}) => api.post(`/orders/${orderId}/reject`, payload),
  cancel: (orderId) => api.post(`/orders/${orderId}/cancel`)
};

export const recommendationsApi = {
  getPopular: (limit = 6) => api.get("/recommendations/popular", { params: { limit } }),
  getByCart: (cartBookIds, limit = 5) =>
    api.post("/recommendations/cart", { cart_book_ids: cartBookIds, limit }),
  getPersonal: (cartBookIds = [], limit = 5) =>
    api.get("/recommendations/personal", {
      params: {
        limit,
        cart_book_ids: cartBookIds.join(",")
      }
    })
};

export const clientApi = {
  getAll: () => api.get("/clients"),
  create: (payload) => api.post("/clients", payload),
  updateById: (clientId, payload) => api.put(`/clients/${clientId}`, payload),
  getMyProfile: () => api.get("/clients/me"),
  updateMyProfile: (payload) => api.put("/clients/me", payload)
};

export const questionsApi = {
  create: (payload) => api.post("/questions", payload),
  getAll: (status = "new") => api.get("/questions", { params: { status } })
};

export const usersApi = {
  getAll: () => api.get("/users"),
  updateRole: (userId, role) => api.put(`/users/${userId}/role`, { role }),
  activate: (userId) => api.post(`/users/${userId}/activate`),
  deactivate: (userId) => api.post(`/users/${userId}/deactivate`),
  remove: (userId) => api.delete(`/users/${userId}`),
  getActivityLogs: (limit = 300) => api.get("/users/activity-logs", { params: { limit } })
};
