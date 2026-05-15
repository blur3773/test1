const ROLE_LABELS = {
  admin: "Администратор",
  manager: "Менеджер",
  cashier: "Кассир",
  client: "Клиент"
};

export const getRoleLabel = (role) => ROLE_LABELS[role] || role || "—";

