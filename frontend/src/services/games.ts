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
  player_input: string | null;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
}

export interface SSEEvent {
  event: "narration_chunk" | "dialog_chunk" | "complete" | "error" | string;
  data: unknown;
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

  getHistory: (sessionId: number) =>
    api.get(`/games/${sessionId}/history`),

  sendActionStream: async function* (
    sessionId: number,
    data: { message?: string; choice_id?: string }
  ): AsyncGenerator<SSEEvent> {
    const token = localStorage.getItem("access_token");
    const baseURL = import.meta.env.VITE_API_URL || "/api/v1";

    const response = await fetch(`${baseURL}/games/${sessionId}/actions/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      yield { event: "error", data: { error: `HTTP ${response.status}` } };
      return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        if (!part.trim()) continue;
        const lines = part.split("\n");
        let eventType = "";
        let eventData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7);
          } else if (line.startsWith("data: ")) {
            eventData = line.slice(6);
          }
        }

        if (eventType && eventData) {
          try {
            yield { event: eventType, data: JSON.parse(eventData) };
          } catch {
            yield { event: eventType, data: eventData };
          }
        }
      }
    }
  },

  generateImage: (sessionId: number, size?: string) =>
    api.post<ApiResponse<{ url: string; prompt: string }>>(`/games/${sessionId}/generate-image`, null, { params: { size } }),

  save: (sessionId: number, saveName?: string) =>
    api.post<ApiResponse<{ id: number; save_name: string; created_at: string }>>(`/games/${sessionId}/saves`, { save_name: saveName }),

  listSaves: (sessionId: number) =>
    api.get<ApiResponse<Array<{ id: number; save_name: string; created_at: string }>>>(`/games/${sessionId}/saves`),

  loadSave: (sessionId: number, saveId: number) =>
    api.post<ApiResponse<GameSession>>(`/games/${sessionId}/saves/${saveId}/load`),
};