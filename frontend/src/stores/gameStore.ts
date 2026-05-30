import { create } from "zustand";

interface GameState {
  sessionId: number | null;
  narration: string;
  dialogs: Array<{ speaker: string; text: string; emotion?: string }>;
  choices: Array<{ id: string; text: string; is_custom?: boolean }>;
  isLoading: boolean;
  setSession: (id: number) => void;
  updateFromAI: (response: {
    narration: string;
    dialogs: Array<{ speaker: string; text: string; emotion?: string }>;
    choices: Array<{ id: string; text: string; is_custom?: boolean }>;
  }) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useGameStore = create<GameState>((set) => ({
  sessionId: null,
  narration: "",
  dialogs: [],
  choices: [],
  isLoading: false,
  setSession: (id) => set({ sessionId: id }),
  updateFromAI: (response) =>
    set({
      narration: response.narration,
      dialogs: response.dialogs,
      choices: response.choices,
    }),
  setLoading: (loading) => set({ isLoading: loading }),
  reset: () => set({ sessionId: null, narration: "", dialogs: [], choices: [], isLoading: false }),
}));
