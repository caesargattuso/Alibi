import { useCallback } from "react";
import { message } from "antd";
import { gameService } from "../services/games";
import { useGameStore } from "../stores/gameStore";

export function useGame(sessionId: number | null) {
  const narration = useGameStore((s) => s.narration);
  const dialogs = useGameStore((s) => s.dialogs);
  const choices = useGameStore((s) => s.choices);
  const isLoading = useGameStore((s) => s.isLoading);
  const updateFromAI = useGameStore((s) => s.updateFromAI);
  const setLoading = useGameStore((s) => s.setLoading);

  const sendMessage = useCallback(async (msg: string) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const { data } = await gameService.sendMessage(sessionId, { message: msg });
      updateFromAI(data.data);
    } catch {
      message.error("操作失败");
    } finally {
      setLoading(false);
    }
  }, [sessionId, setLoading, updateFromAI]);

  const sendChoice = useCallback(async (choiceId: string) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const { data } = await gameService.sendMessage(sessionId, { choice_id: choiceId });
      updateFromAI(data.data);
    } catch {
      message.error("操作失败");
    } finally {
      setLoading(false);
    }
  }, [sessionId, setLoading, updateFromAI]);

  const quit = useCallback(async () => {
    if (!sessionId) return;
    try {
      await gameService.end(sessionId, "abandoned");
    } catch {
      // ignore
    }
  }, [sessionId]);

  return { narration, dialogs, choices, isLoading, sendMessage, sendChoice, quit };
}
