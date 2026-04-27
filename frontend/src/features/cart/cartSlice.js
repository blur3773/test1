import { createSlice } from "@reduxjs/toolkit";

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
        existing.quantity += 1;
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
        item.quantity += 1;
      }
    },
    decreaseQuantity: (state, action) => {
      const item = state.items.find((entry) => entry.book.id === action.payload);
      if (item && item.quantity > 1) {
        item.quantity -= 1;
      }
    },
    clearCart: (state) => {
      state.items = [];
    }
  }
});

export const { addToCart, removeFromCart, increaseQuantity, decreaseQuantity, clearCart } =
  cartSlice.actions;
export const cartReducer = cartSlice.reducer;
