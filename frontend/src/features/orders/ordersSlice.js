import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { ordersApi } from "../../api/endpoints";

const getErrorMessage = (error, fallback) =>
  error.response?.data?.message || error.response?.data?.errors || fallback;

export const createOrder = createAsyncThunk(
  "orders/createOrder",
  async ({ items, customerComment }, { rejectWithValue }) => {
    try {
      const response = await ordersApi.checkout({
        items,
        customer_comment: customerComment || null
      });
      return response.data?.order || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось оформить заказ"));
    }
  }
);

export const fetchMyOrders = createAsyncThunk(
  "orders/fetchMyOrders",
  async (_, { rejectWithValue }) => {
    try {
      const response = await ordersApi.getMy();
      return response.data?.orders || [];
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось загрузить ваши заказы"));
    }
  }
);

export const fetchPendingOrders = createAsyncThunk(
  "orders/fetchPendingOrders",
  async (_, { rejectWithValue }) => {
    try {
      const response = await ordersApi.getAll("pending");
      return response.data?.orders || [];
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось загрузить заказы"));
    }
  }
);

export const approveOrder = createAsyncThunk(
  "orders/approveOrder",
  async ({ orderId, managerComment }, { rejectWithValue }) => {
    try {
      const response = await ordersApi.approve(orderId, {
        manager_comment: managerComment || null
      });
      return response.data?.order || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось подтвердить заказ"));
    }
  }
);

export const rejectOrder = createAsyncThunk(
  "orders/rejectOrder",
  async ({ orderId, managerComment }, { rejectWithValue }) => {
    try {
      const response = await ordersApi.reject(orderId, {
        manager_comment: managerComment || null
      });
      return response.data?.order || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось отклонить заказ"));
    }
  }
);

const upsertOrder = (orders, nextOrder) => {
  if (!nextOrder?.id) {
    return orders;
  }

  return [nextOrder, ...orders.filter((order) => order.id !== nextOrder.id)];
};

const ordersSlice = createSlice({
  name: "orders",
  initialState: {
    lastOrder: null,
    checkoutStatus: "idle",
    checkoutError: null,
    myOrders: [],
    myOrdersStatus: "idle",
    myOrdersError: null,
    managerOrders: [],
    managerOrdersStatus: "idle",
    managerOrdersError: null,
    actionStatus: "idle",
    actionError: null
  },
  reducers: {
    resetOrderCheckoutState: (state) => {
      state.checkoutStatus = "idle";
      state.checkoutError = null;
      state.lastOrder = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(createOrder.pending, (state) => {
        state.checkoutStatus = "loading";
        state.checkoutError = null;
      })
      .addCase(createOrder.fulfilled, (state, action) => {
        state.checkoutStatus = "succeeded";
        state.lastOrder = action.payload;
        state.myOrders = upsertOrder(state.myOrders, action.payload);
      })
      .addCase(createOrder.rejected, (state, action) => {
        state.checkoutStatus = "failed";
        state.checkoutError = action.payload || "Ошибка оформления заказа";
      })
      .addCase(fetchMyOrders.pending, (state) => {
        state.myOrdersStatus = "loading";
        state.myOrdersError = null;
      })
      .addCase(fetchMyOrders.fulfilled, (state, action) => {
        state.myOrdersStatus = "succeeded";
        state.myOrders = action.payload;
      })
      .addCase(fetchMyOrders.rejected, (state, action) => {
        state.myOrdersStatus = "failed";
        state.myOrdersError = action.payload || "Ошибка загрузки заказов";
      })
      .addCase(fetchPendingOrders.pending, (state) => {
        state.managerOrdersStatus = "loading";
        state.managerOrdersError = null;
      })
      .addCase(fetchPendingOrders.fulfilled, (state, action) => {
        state.managerOrdersStatus = "succeeded";
        state.managerOrders = action.payload;
      })
      .addCase(fetchPendingOrders.rejected, (state, action) => {
        state.managerOrdersStatus = "failed";
        state.managerOrdersError = action.payload || "Ошибка загрузки заказов";
      })
      .addCase(approveOrder.pending, (state) => {
        state.actionStatus = "loading";
        state.actionError = null;
      })
      .addCase(approveOrder.fulfilled, (state, action) => {
        state.actionStatus = "succeeded";
        state.managerOrders = state.managerOrders.filter((order) => order.id !== action.payload?.id);
      })
      .addCase(approveOrder.rejected, (state, action) => {
        state.actionStatus = "failed";
        state.actionError = action.payload || "Ошибка подтверждения заказа";
      })
      .addCase(rejectOrder.pending, (state) => {
        state.actionStatus = "loading";
        state.actionError = null;
      })
      .addCase(rejectOrder.fulfilled, (state, action) => {
        state.actionStatus = "succeeded";
        state.managerOrders = state.managerOrders.filter((order) => order.id !== action.payload?.id);
      })
      .addCase(rejectOrder.rejected, (state, action) => {
        state.actionStatus = "failed";
        state.actionError = action.payload || "Ошибка отклонения заказа";
      });
  }
});

export const { resetOrderCheckoutState } = ordersSlice.actions;
export const ordersReducer = ordersSlice.reducer;
