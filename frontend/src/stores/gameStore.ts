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
  isGameOver: boolean;
  ending: string | null;
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
  appendDialogText: (turnId: string, speaker: string, text: string) => void;
  completeTurn: (turnId: string, data: {
    dialogs: DialogItem[];
    choices: ChoiceItem[];
    sceneChange: DialogTurn["sceneChange"];
    statChanges: StatChange[];
    narration?: string;
    isGameOver?: boolean;
    ending?: string | null;
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
      isGameOver: false,
      ending: null,
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

  appendDialogText: (turnId, speaker, text) => {
    set((state) => ({
      turns: state.turns.map((t) => {
        if (t.id !== turnId) return t;
        const dialogs = [...t.dialogs];
        const last = dialogs[dialogs.length - 1];
        if (last && last.speaker === speaker) {
          dialogs[dialogs.length - 1] = { ...last, text: last.text + text };
        } else {
          dialogs.push({ speaker, text, emotion: "neutral" });
        }
        return { ...t, dialogs };
      }),
    }));
  },

  completeTurn: (turnId, data) => {
    set((state) => ({
      turns: state.turns.map((t) =>
        t.id === turnId
          ? {
              ...t,
              narration: data.narration ?? t.narration,
              // Only use complete dialogs if streaming didn't produce any
              dialogs: t.dialogs.length > 0 ? t.dialogs : (data.dialogs ?? []),
              choices: data.choices ?? [],
              sceneChange: data.sceneChange ?? null,
              statChanges: data.statChanges ?? [],
              isStreaming: false,
              isComplete: true,
              isGameOver: data.isGameOver ?? false,
              ending: data.ending ?? null,
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
      isGameOver: false,
      ending: null,
      timestamp: item.created_at ? new Date(item.created_at).getTime() : Date.now() - (items.length - i) * 60000,
    }));
    set({ turns });
  },

  setSceneBackground: (url) => set({ sceneBackground: url }),
  setSceneName: (name) => set({ sceneName: name }),
  setStreaming: (val) => set({ isStreaming: val }),
  reset: () => set({ turns: [], sceneBackground: "", sceneName: "", isStreaming: false, currentTurnId: null }),
}));