import api from "./api";
import type { ApiResponse } from "../types";

export interface Character {
  id: number;
  script_id: number;
  character_key: string;
  name: string;
  display_name: string | null;
  role_type: string;
  avatar_url: string | null;
  sprites: Record<string, string> | null;
  appearance: string | null;
  personality: Record<string, unknown> | null;
  background: string | null;
  stats: Record<string, unknown> | null;
  dialogue_style: string | null;
}

export interface Relationship {
  target_id: number;
  target_name: string;
  target_key: string;
  relation_type: string;
  description: string | null;
  attitude: string;
  intensity: number;
}

export interface RelationshipsData {
  character_id: number;
  character_name: string;
  relationships: Relationship[];
}

export const characterService = {
  get: (id: number) =>
    api.get<ApiResponse<Character>>(`/characters/${id}`),

  getRelationships: (id: number) =>
    api.get<ApiResponse<RelationshipsData>>(`/characters/${id}/relationships`),
};
