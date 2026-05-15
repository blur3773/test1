import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { authApi, clientApi } from "../../api/endpoints";
import { tokenStorage } from "../../api/httpClient";

const stringifyValidationError = (value) => {
  if (!value) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => stringifyValidationError(item)).filter(Boolean).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([field, fieldError]) => {
        const text = stringifyValidationError(fieldError);
        return text ? `${field}: ${text}` : "";
      })
      .filter(Boolean)
      .join("; ");
  }
  return "";
};

const getErrorMessage = (error, fallback) => {
  const payload = error.response?.data;
  const message = payload?.message;
  if (typeof message === "string" && message.trim()) {
    return message.trim();
  }
  const validationErrors = stringifyValidationError(payload?.errors);
  if (validationErrors) {
    return validationErrors;
  }
  return fallback;
};

export const hydrateSession = createAsyncThunk(
  "user/hydrateSession",
  async (_, { rejectWithValue }) => {
    const accessToken = tokenStorage.getAccessToken();
    const refreshToken = tokenStorage.getRefreshToken();
    if (!accessToken || !refreshToken) {
      return null;
    }

    try {
      const response = await authApi.me();
      return {
        accessToken,
        refreshToken,
        profile: response.data?.user || null
      };
    } catch (error) {
      tokenStorage.clear();
      return rejectWithValue(getErrorMessage(error, "Сессия устарела, войдите снова"));
    }
  }
);

export const registerUser = createAsyncThunk(
  "user/registerUser",
  async ({ email, username, password, first_name, last_name, middle_name, phone }, { rejectWithValue }) => {
    try {
      const registerResponse = await authApi.register({
        email,
        username,
        password,
        role: "client"
      });
      const { access_token: accessToken, refresh_token: refreshToken } = registerResponse.data || {};

      if (!accessToken || !refreshToken) {
        return rejectWithValue("Сервер не вернул токены после регистрации");
      }

      tokenStorage.setTokens(accessToken, refreshToken);
      const meResponse = await authApi.me();
      const profileResponse = await clientApi.updateMyProfile({
        first_name,
        last_name,
        middle_name,
        phone,
        email
      });

      return {
        accessToken,
        refreshToken,
        profile: meResponse.data?.user || registerResponse.data?.user || null,
        clientProfile: profileResponse.data?.client || null
      };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось зарегистрироваться"));
    }
  }
);

export const loginUser = createAsyncThunk(
  "user/loginUser",
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const loginResponse = await authApi.login({ email, password });
      const { access_token: accessToken, refresh_token: refreshToken } = loginResponse.data || {};

      if (!accessToken || !refreshToken) {
        return rejectWithValue("Сервер не вернул токены");
      }

      tokenStorage.setTokens(accessToken, refreshToken);
      const meResponse = await authApi.me();

      return {
        accessToken,
        refreshToken,
        profile: meResponse.data?.user || null
      };
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Неверный email или пароль"));
    }
  }
);

export const logoutUser = createAsyncThunk("user/logoutUser", async () => {
  try {
    await authApi.logout();
  } catch {

  } finally {
    tokenStorage.clear();
  }
});

export const fetchMyClientProfile = createAsyncThunk(
  "user/fetchMyClientProfile",
  async (_, { rejectWithValue }) => {
    try {
      const response = await clientApi.getMyProfile();
      return response.data?.client || null;
    } catch (error) {
      if (error.response?.status === 404) {
        return null;
      }
      return rejectWithValue(getErrorMessage(error, "Профиль клиента не найден"));
    }
  }
);

export const updateMyClientProfile = createAsyncThunk(
  "user/updateMyClientProfile",
  async (payload, { rejectWithValue }) => {
    try {
      const response = await clientApi.updateMyProfile(payload);
      return response.data?.client || null;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error, "Не удалось обновить профиль"));
    }
  }
);

const userSlice = createSlice({
  name: "user",
  initialState: {
    accessToken: tokenStorage.getAccessToken(),
    refreshToken: tokenStorage.getRefreshToken(),
    profile: null,
    clientProfile: null,
    status: "idle",
    profileStatus: "idle",
    error: null,
    profileError: null
  },
  reducers: {
    clearAuthError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(hydrateSession.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(hydrateSession.fulfilled, (state, action) => {
        state.status = "succeeded";
        if (action.payload) {
          state.accessToken = action.payload.accessToken;
          state.refreshToken = action.payload.refreshToken;
          state.profile = action.payload.profile;
        } else {
          state.accessToken = null;
          state.refreshToken = null;
          state.profile = null;
        }
      })
      .addCase(hydrateSession.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Сессия недействительна";
        state.accessToken = null;
        state.refreshToken = null;
        state.profile = null;
      })
      .addCase(registerUser.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.accessToken = action.payload.accessToken;
        state.refreshToken = action.payload.refreshToken;
        state.profile = action.payload.profile;
        state.clientProfile = action.payload.clientProfile || state.clientProfile;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Ошибка регистрации";
      })
      .addCase(loginUser.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.accessToken = action.payload.accessToken;
        state.refreshToken = action.payload.refreshToken;
        state.profile = action.payload.profile;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Ошибка авторизации";
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.accessToken = null;
        state.refreshToken = null;
        state.profile = null;
        state.clientProfile = null;
        state.status = "idle";
        state.error = null;
      })
      .addCase(fetchMyClientProfile.pending, (state) => {
        state.profileStatus = "loading";
        state.profileError = null;
      })
      .addCase(fetchMyClientProfile.fulfilled, (state, action) => {
        state.profileStatus = "succeeded";
        state.clientProfile = action.payload;
      })
      .addCase(fetchMyClientProfile.rejected, (state, action) => {
        state.profileStatus = "failed";
        state.profileError = action.payload || "Не удалось загрузить профиль клиента";
      })
      .addCase(updateMyClientProfile.fulfilled, (state, action) => {
        state.clientProfile = action.payload;
      });
  }
});

export const { clearAuthError } = userSlice.actions;
export const userReducer = userSlice.reducer;
