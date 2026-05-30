import api from "./api";
import type { ApiResponse, User } from "../types";

export const authService = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post<ApiResponse>("/auth/register", data),

  login: (data: { username_or_email: string; password: string }) =>
    api.post<ApiResponse>("/auth/login", data),

  refreshToken: (refreshToken: string) =>
    api.post<ApiResponse>("/auth/refresh", { refresh_token: refreshToken }),
};

export const userService = {
  getMe: () => api.get<ApiResponse<User>>("/users/me"),
  updateMe: (data: Partial<User>) => api.put<ApiResponse<User>>("/users/me", data),
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.put<ApiResponse<{ message: string }>>("/users/me/password", data),
};