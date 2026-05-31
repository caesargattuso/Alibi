import { useEffect, useCallback, useRef } from "react";
import { gameWebSocket, type WSMessage } from "../services/websocket";
import { useAuthStore } from "../stores/authStore";

export function useWebSocket(sessionId: number | null) {
  const token = useAuthStore((s) => s.token);
  const connected = useRef(false);

  useEffect(() => {
    if (sessionId && token && !connected.current) {
      gameWebSocket.connect(sessionId, token);
      connected.current = true;
    }

    return () => {
      if (connected.current) {
        gameWebSocket.disconnect();
        connected.current = false;
      }
    };
  }, [sessionId, token]);

  const send = useCallback((type: string, data: unknown) => {
    gameWebSocket.send({ type, data, timestamp: new Date().toISOString() });
  }, []);

  const subscribe = useCallback((type: string, handler: (msg: WSMessage) => void) => {
    gameWebSocket.on(type, handler);
    return () => gameWebSocket.off(type, handler);
  }, []);

  return { send, subscribe, isConnected: gameWebSocket.isConnected };
}
