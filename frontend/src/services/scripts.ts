import api from "./api";
import type { ApiResponse, Script, PaginatedData } from "../types";

export const scriptService = {
  list: (params?: { page?: number; per_page?: number; genre?: string; difficulty?: string }) =>
    api.get<ApiResponse<PaginatedData<Script>>>("/scripts", { params }),

  get: (id: number) => api.get<ApiResponse<Script>>(`/scripts/${id}`),

  create: (data: Record<string, unknown>) => api.post<ApiResponse<Script>>("/scripts", data),
};