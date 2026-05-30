export interface User {
  id: number;
  username: string;
  email: string | null;
  avatar_url: string | null;
  preferences: Record<string, unknown> | null;
  status: string;
}

export interface Script {
  id: number;
  title: string;
  description: string | null;
  genre: string;
  difficulty: string;
  author_id: number;
  cover_image: string | null;
  rating: number;
  play_count: number;
  status: string;
  tags: string[] | null;
  created_at: string | null;
}

export interface GameSession {
  id: number;
  script_id: number;
  current_scene_id: number | null;
  player_name: string | null;
  player_stats: Record<string, unknown>;
  npc_states: Record<string, unknown>;
  story_flags: Record<string, unknown>;
  game_phase: string | null;
  game_time: string | null;
  alive_count: number;
  status: string;
  created_at: string | null;
}

export interface AIResponse {
  narration: string;
  dialogs: Array<{ speaker: string; text: string; emotion?: string }>;
  choices: Array<{ id: string; text: string; is_custom?: boolean }>;
  scene_change: { to_scene_id: string; transition: string } | null;
  character_movements: Array<Record<string, unknown>>;
  stat_changes: Array<Record<string, unknown>>;
  flags_set: Array<Record<string, unknown>>;
  is_game_over: boolean;
  ending: string | null;
}

export interface ApiResponse<T = unknown> {
  code: number;
  message?: string;
  data: T;
  error?: Record<string, unknown>;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}