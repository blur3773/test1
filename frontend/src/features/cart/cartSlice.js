import { createSlice } from "@reduxjs/toolkit";

const MAX_CART_QUANTITY = 99;

const cartSlice = createSlice({
  name: "cart",
  initialState: {
    items: []
  },
  reducers: {
    addToCart: (state, action) => {
      const book = action.payload;
      const existing = state.items.find((item) => item.book.id === book.id);
      if (existing) {
        existing.quantity = Math.min(MAX_CART_QUANTITY, existing.quantity + 1);
      } else {
        state.items.push({ book, quantity: 1 });
      }
    },
    removeFromCart: (state, action) => {
      state.items = state.items.filter((item) => item.book.id !== action.payload);
    },
    increaseQuantity: (state, action) => {
      const item = state.items.find((entry) => entry.book.id === action.payload);
      if (item) {
        item.quantity = Math.min(MAX_CART_QUANTITY, item.quantity + 1);
      }
    },
    decreaseQuantity: (state, action) => {
      const item = state.items.find((entry) => entry.book.id === action.payload);
      if (item && item.quantity > 1) {
        item.quantity -= 1;
      }
    },
    setQuantity: (state, action) => {
      const { bookId, quantity } = action.payload || {};
      const item = state.items.find((entry) => entry.book.id === bookId);
      if (!item) {
        return;
      }

      const parsedQuantity = Number(quantity);
      if (!Number.isFinite(parsedQuantity)) {
        return;
      }

      item.quantity = Math.min(MAX_CART_QUANTITY, Math.max(1, Math.floor(parsedQuantity)));
    },
    clearCart: (state) => {
      state.items = [];
    }
  }
});

export const { addToCart, removeFromCart, increaseQuantity, decreaseQuantity, setQuantity, clearCart } =
  cartSlice.actions;
export const cartReducer = cartSlice.reducer;
