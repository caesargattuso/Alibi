import { useCallback } from "react";
import { message } from "antd";
import { gameService } from "../services/games";
import { useGameStore } from "../stores/gameStore";

export function useGame(sessionId: number | null) {
  const turns = useGameStore((s) => s.turns);
  const isStreaming = useGameStore((s) => s.isStreaming);

  const sendMessage = useCallback(async (msg: string) => {
    if (!sessionId) return;
    try {
      await gameService.sendMessage(sessionId, { message: msg });
    } catch {
      message.error("操作失败");
    }
  }, [sessionId]);

  const sendChoice = useCallback(async (choiceId: string) => {
    if (!sessionId) return;
    try {
      await gameService.sendMessage(sessionId, { choice_id: choiceId });
    } catch {
      message.error("操作失败");
    }
  }, [sessionId]);

  const quit = useCallback(async () => {
    if (!sessionId) return;
    try {
      await gameService.end(sessionId, "abandoned");
    } catch {
      // ignore
    }
  }, [sessionId]);

  return { turns, isStreaming, sendMessage, sendChoice, quit };
}
