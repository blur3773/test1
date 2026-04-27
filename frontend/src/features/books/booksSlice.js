import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { booksApi } from "../../api/endpoints";

const getErrorMessage = (error, fallback) =>
  error.response?.data?.message || error.response?.data?.errors || fallback;

export const fetchBooks = createAsyncThunk(
  "books/fetchBooks",
  async ({ status = "active", query = "" } = {}, { rejectWithValue }) => {
    try {
      const response = query.trim()
        ? await booksApi.search(query.trim())
        : await booksApi.getAll(status);

      return {
        books: response.data?.books || [],
        filters: { status, query }
      };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось загрузить каталог"));
    }
  }
);

export const fetchBookById = createAsyncThunk(
  "books/fetchBookById",
  async (bookId, { rejectWithValue }) => {
    try {
      const response = await booksApi.getById(bookId);
      return response.data?.book || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось загрузить книгу"));
    }
  }
);

const booksSlice = createSlice({
  name: "books",
  initialState: {
    items: [],
    selectedBook: null,
    status: "idle",
    error: null,
    filters: {
      status: "active",
      query: ""
    }
  },
  reducers: {
    setStatusFilter: (state, action) => {
      state.filters.status = action.payload;
    },
    setSearchQuery: (state, action) => {
      state.filters.query = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBooks.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchBooks.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload.books;
        state.filters = action.payload.filters;
      })
      .addCase(fetchBooks.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Ошибка загрузки каталога";
      })
      .addCase(fetchBookById.fulfilled, (state, action) => {
        state.selectedBook = action.payload;
      });
  }
});

export const { setStatusFilter, setSearchQuery } = booksSlice.actions;
export const booksReducer = booksSlice.reducer;
