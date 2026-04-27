import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { recommendationsApi } from "../../api/endpoints";

const getErrorMessage = (error, fallback) =>
  error.response?.data?.message || error.response?.data?.errors || fallback;

export const fetchPopularBooks = createAsyncThunk(
  "recommendations/fetchPopularBooks",
  async (limit = 6, { rejectWithValue }) => {
    try {
      const response = await recommendationsApi.getPopular(limit);
      return response.data?.popular_books || [];
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось получить популярные книги"));
    }
  }
);

export const fetchCartRecommendations = createAsyncThunk(
  "recommendations/fetchCartRecommendations",
  async ({ cartBookIds, limit = 5 }, { rejectWithValue }) => {
    try {
      if (!cartBookIds?.length) {
        return [];
      }
      const response = await recommendationsApi.getByCart(cartBookIds, limit);
      return response.data?.recommendations || [];
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось получить рекомендации для корзины"));
    }
  }
);

export const fetchPersonalRecommendations = createAsyncThunk(
  "recommendations/fetchPersonalRecommendations",
  async ({ cartBookIds = [], limit = 5 } = {}, { rejectWithValue }) => {
    try {
      const response = await recommendationsApi.getPersonal(cartBookIds, limit);
      return response.data?.recommendations || [];
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось получить персональные рекомендации"));
    }
  }
);

const recommendationsSlice = createSlice({
  name: "recommendations",
  initialState: {
    popularBooks: [],
    cartRecommendations: [],
    personalRecommendations: [],
    status: "idle",
    error: null
  },
  reducers: {
    clearCartRecommendations: (state) => {
      state.cartRecommendations = [];
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPopularBooks.fulfilled, (state, action) => {
        state.popularBooks = action.payload;
      })
      .addCase(fetchCartRecommendations.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchCartRecommendations.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.cartRecommendations = action.payload;
      })
      .addCase(fetchCartRecommendations.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Ошибка загрузки рекомендаций";
      })
      .addCase(fetchPersonalRecommendations.fulfilled, (state, action) => {
        state.personalRecommendations = action.payload;
      });
  }
});

export const getRecommendations = fetchCartRecommendations;
export const { clearCartRecommendations } = recommendationsSlice.actions;
export const recommendationsReducer = recommendationsSlice.reducer;
