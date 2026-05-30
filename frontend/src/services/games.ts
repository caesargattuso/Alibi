import api from "./api";
import type { ApiResponse, GameSession, AIResponse, PaginatedData } from "../types";

export interface GameHistoryItem {
  id: number;
  script_id: number;
  script_title: string;
  script_cover: string | null;
  player_name: string | null;
  status: string;
  current_ending: string | null;
  game_phase: string | null;
  game_time: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface DialogItem {
  id: number;
  type: string;
  content: string;
  metadata: Record<string, unknown> | null;
  player_input: string | null;
  created_at: string | null;
}

export const gameService = {
  create: (data: { script_id: number; player_name: string }) =>
    api.post<ApiResponse<GameSession>>("/games", data),

  get: (sessionId: number) => api.get<ApiResponse<GameSession>>(`/games/${sessionId}`),

  sendMessage: (sessionId: number, data: { message?: string; choice_id?: string }) =>
    api.post<ApiResponse<AIResponse>>(`/games/${sessionId}/messages`, data),

  pause: (sessionId: number) => api.post<ApiResponse<GameSession>>(`/games/${sessionId}/pause`),

  resume: (sessionId: number) => api.post<ApiResponse<GameSession>>(`/games/${sessionId}/resume`),

  end: (sessionId: number, reason: string) =>
    api.post<ApiResponse<GameSession>>(`/games/${sessionId}/end`, { reason }),

  list: (params?: { page?: number; per_page?: number; status?: string }) =>
    api.get<ApiResponse<PaginatedData<GameHistoryItem>>>("/games", { params }),

  getMessages: (sessionId: number, params?: { page?: number; per_page?: number; type?: string }) =>
    api.get<ApiResponse<PaginatedData<DialogItem>>>(`/games/${sessionId}/messages`, { params }),
};