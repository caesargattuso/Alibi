import { create } from "zustand";

export interface DialogItem {
  speaker: string;
  text: string;
  emotion: string;
}

export interface ChoiceItem {
  id: string;
  text: string;
  is_custom: boolean;
}

export interface StatChange {
  target: string;
  target_id: string;
  stat: string;
  change: number;
}

export interface DialogTurn {
  id: string;
  playerInput: string;
  narration: string;
  dialogs: DialogItem[];
  choices: ChoiceItem[];
  sceneChange: { to_scene_id: string; transition: string } | null;
  statChanges: StatChange[];
  isStreaming: boolean;
  isComplete: boolean;
  timestamp: number;
}

interface GameState {
  turns: DialogTurn[];
  sceneBackground: string;
  sceneName: string;
  isStreaming: boolean;
  currentTurnId: string | null;

  addPlayerTurn: (input: string) => string;
  appendNarration: (turnId: string, text: string) => void;
  completeTurn: (turnId: string, data: {
    dialogs: DialogItem[];
    choices: ChoiceItem[];
    sceneChange: DialogTurn["sceneChange"];
    statChanges: StatChange[];
    narration?: string;
  }) => void;
  loadHistory: (items: Array<{
    player_input: string | null;
    content: string;
    meta_data: { choices?: ChoiceItem[]; dialogs?: DialogItem[] } | null;
    created_at: string | null;
  }>) => void;
  setSceneBackground: (url: string) => void;
  setSceneName: (name: string) => void;
  setStreaming: (val: boolean) => void;
  reset: () => void;
}

let turnCounter = 0;

export const useGameStore = create<GameState>((set) => ({
  turns: [],
  sceneBackground: "",
  sceneName: "",
  isStreaming: false,
  currentTurnId: null,

  addPlayerTurn: (input: string) => {
    const id = `turn_${++turnCounter}_${Date.now()}`;
    const newTurn: DialogTurn = {
      id,
      playerInput: input,
      narration: "",
      dialogs: [],
      choices: [],
      sceneChange: null,
      statChanges: [],
      isStreaming: true,
      isComplete: false,
      timestamp: Date.now(),
    };
    set((state) => ({
      turns: [...state.turns, newTurn],
      isStreaming: true,
      currentTurnId: id,
    }));
    return id;
  },

  appendNarration: (turnId, text) => {
    set((state) => ({
      turns: state.turns.map((t) =>
        t.id === turnId ? { ...t, narration: t.narration + text } : t
      ),
    }));
  },

  completeTurn: (turnId, data) => {
    set((state) => ({
      turns: state.turns.map((t) =>
        t.id === turnId
          ? {
              ...t,
              narration: data.narration ?? t.narration,
              dialogs: data.dialogs ?? [],
              choices: data.choices ?? [],
              sceneChange: data.sceneChange ?? null,
              statChanges: data.statChanges ?? [],
              isStreaming: false,
              isComplete: true,
            }
          : t
      ),
      isStreaming: false,
    }));
  },

  loadHistory: (items) => {
    const turns: DialogTurn[] = items.map((item, i) => ({
      id: `history_${i}`,
      playerInput: item.player_input || "",
      narration: item.content || "",
      dialogs: item.meta_data?.dialogs || [],
      choices: item.meta_data?.choices || [],
      sceneChange: null,
      statChanges: [],
      isStreaming: false,
      isComplete: true,
      timestamp: item.created_at ? new Date(item.created_at).getTime() : Date.now() - (items.length - i) * 60000,
    }));
    set({ turns });
  },

  setSceneBackground: (url) => set({ sceneBackground: url }),
  setSceneName: (name) => set({ sceneName: name }),
  setStreaming: (val) => set({ isStreaming: val }),
  reset: () => set({ turns: [], sceneBackground: "", sceneName: "", isStreaming: false, currentTurnId: null }),
}));
