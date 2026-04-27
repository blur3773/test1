import { configureStore } from "@reduxjs/toolkit";

import { booksReducer } from "../features/books/booksSlice";
import { cartReducer } from "../features/cart/cartSlice";
import { userReducer } from "../features/user/userSlice";
import { salesReducer } from "../features/sales/salesSlice";
import { ordersReducer } from "../features/orders/ordersSlice";
import { recommendationsReducer } from "../features/recommendations/recommendationsSlice";

export const store = configureStore({
  reducer: {
    books: booksReducer,
    cart: cartReducer,
    user: userReducer,
    sales: salesReducer,
    orders: ordersReducer,
    recommendations: recommendationsReducer
  }
});
