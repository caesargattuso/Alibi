import api from "./api";
import type { ApiResponse } from "../types";

export interface Scene {
  id: number;
  script_id: number;
  scene_key: string;
  name: string;
  description: string | null;
  background_image: string | null;
  background_music: string | null;
  connected_scenes: ConnectedScene[] | null;
  on_enter: Record<string, unknown> | null;
  on_exit: Record<string, unknown> | null;
}

export interface ConnectedScene {
  scene_id: number;
  direction: string;
  description: string;
}

export interface MapData {
  width: number;
  height: number;
  grid_size: number;
  layers: Layer[];
  walkable_areas: WalkableArea[];
  obstacles: Obstacle[];
  spawn_points: SpawnPoint[];
  lighting: Lighting | null;
}

export interface Layer {
  id: string;
  name: string;
  type: string;
  z_index: number;
}

export interface WalkableArea {
  id: string;
  name: string;
  polygon: number[][];
}

export interface Obstacle {
  id: string;
  name: string;
  polygon: number[][];
  is_solid: boolean;
}

export interface SpawnPoint {
  id: string;
  name?: string;
  position: number[];
  is_default: boolean;
}

export interface Lighting {
  ambient_color: string;
  ambient_intensity: number;
  light_sources: LightSource[];
}

export interface LightSource {
  id: string;
  position: number[];
  color: string;
  radius: number;
  intensity: number;
  flicker?: boolean;
}

export interface Interactable {
  id: string;
  name: string;
  type: "object" | "npc" | "exit" | "event" | "item";
  position: number[];
  icon: string | null;
  description: string | null;
  actions: string[];
  conditions: Record<string, Condition[]> | null;
  npc_id?: string;
  target_scene?: string;
  target_position?: number[];
}

export interface Condition {
  type: "flag" | "stat" | "item";
  flag?: string;
  stat?: string;
  operator?: string;
  value: unknown;
}

export interface InteractResult {
  success: boolean;
  message: string;
  effects: Effect[];
  clues_revealed?: string[];
  ai_trigger: {
    should_generate: boolean;
    context: string;
  };
}

export interface Effect {
  type: string;
  target: string;
  value?: unknown;
  position?: number[];
}

export const sceneService = {
  get: (id: number) =>
    api.get<ApiResponse<Scene>>(`/scenes/${id}`),

  getMap: (id: number) =>
    api.get<ApiResponse<MapData>>(`/scenes/${id}/map`),

  getInteractables: (id: number) =>
    api.get<ApiResponse<{ interactables: Interactable[] }>>(`/scenes/${id}/interactables`),

  interact: (sceneId: number, data: { session_id: number; interactable_id: string; action_id: string }) =>
    api.post<ApiResponse<InteractResult>>(`/scenes/${sceneId}/interact`, data),

  npcDialogue: (sceneId: number, data: {
    session_id: number;
    npc_id: string;
    player_message: string;
    dialogue_history: Array<{ speaker: string; text: string }>;
  }) =>
    api.post<ApiResponse<{
      text: string;
      emotion: string;
      clues_revealed: string[];
      trust_change: number;
    }>>(`/scenes/${sceneId}/npc-dialogue`, data),
};
