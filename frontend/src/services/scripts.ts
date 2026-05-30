import api from "./api";
import type { ApiResponse, Script, PaginatedData } from "../types";

export interface RateResult {
  rating: number;
  comment: string | null;
  average_rating: number;
  rating_count: number;
}

export interface RatingItem {
  id: number;
  user_id: number;
  username: string;
  avatar_url: string | null;
  rating: number;
  comment: string | null;
  created_at: string | null;
}

export const scriptService = {
  list: (params?: { page?: number; per_page?: number; genre?: string; difficulty?: string }) =>
    api.get<ApiResponse<PaginatedData<Script>>>("/scripts", { params }),

  get: (id: number) => api.get<ApiResponse<Script>>(`/scripts/${id}`),

  create: (data: Record<string, unknown>) => api.post<ApiResponse<Script>>("/scripts", data),

  favorite: (scriptId: number) =>
    api.post<ApiResponse<{ favorited: boolean; favorite_count: number }>>(`/scripts/${scriptId}/favorite`),

  unfavorite: (scriptId: number) =>
    api.delete<ApiResponse<{ favorited: boolean; favorite_count: number }>>(`/scripts/${scriptId}/favorite`),

  checkFavorite: (scriptId: number) =>
    api.get<ApiResponse<{ favorited: boolean }>>(`/scripts/${scriptId}/favorite`),

  rate: (scriptId: number, data: { rating: number; comment?: string }) =>
    api.post<ApiResponse<RateResult>>(`/scripts/${scriptId}/rate`, data),

  getRatings: (scriptId: number, params?: { page?: number; per_page?: number }) =>
    api.get<ApiResponse<PaginatedData<RatingItem>>>(`/scripts/${scriptId}/ratings`, { params }),
};