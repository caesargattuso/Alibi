import api from "./api";
import type { ApiResponse, GameSession, AIResponse } from "../types";

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
};