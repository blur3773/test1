import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { salesApi } from "../../api/endpoints";

const getErrorMessage = (error, fallback) =>
  error.response?.data?.message || error.response?.data?.errors || fallback;

export const createSale = createAsyncThunk(
  "sales/createSale",
  async ({ items, clientId }, { rejectWithValue }) => {
    try {
      const response = await salesApi.create({
        items,
        client_id: clientId || null
      });
      return response.data?.sale || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось оформить продажу"));
    }
  }
);

export const fetchSalesReport = createAsyncThunk(
  "sales/fetchSalesReport",
  async ({ status } = {}, { rejectWithValue }) => {
    try {
      const response = await salesApi.getSalesReport(status);
      return response.data || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось загрузить отчёт"));
    }
  }
);

const salesSlice = createSlice({
  name: "sales",
  initialState: {
    lastSale: null,
    report: null,
    status: "idle",
    reportStatus: "idle",
    error: null,
    reportError: null
  },
  reducers: {
    resetSaleState: (state) => {
      state.lastSale = null;
      state.error = null;
      state.status = "idle";
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(createSale.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(createSale.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.lastSale = action.payload;
      })
      .addCase(createSale.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Ошибка оформления продажи";
      })
      .addCase(fetchSalesReport.pending, (state) => {
        state.reportStatus = "loading";
        state.reportError = null;
      })
      .addCase(fetchSalesReport.fulfilled, (state, action) => {
        state.reportStatus = "succeeded";
        state.report = action.payload;
      })
      .addCase(fetchSalesReport.rejected, (state, action) => {
        state.reportStatus = "failed";
        state.reportError = action.payload || "Ошибка загрузки отчёта";
      });
  }
});

export const { resetSaleState } = salesSlice.actions;
export const salesReducer = salesSlice.reducer;
