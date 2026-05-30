export interface WSMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

export type MessageHandler = (message: WSMessage) => void;

class GameWebSocket {
  private ws: WebSocket | null = null;
  private url = "";
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pendingActions: WSMessage[] = [];
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private pingInterval: number | null = null;

  connect(sessionId: number, token: string) {
    const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
    this.url = `${wsUrl}/ws/v1/games/${sessionId}?token=${token}`;
    this._createConnection();
  }

  private _createConnection() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._startPing();
      this._flushPendingActions();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        this._dispatch(message);
      } catch {
        // ignore parse errors
      }
    };

    this.ws.onclose = () => {
      this._stopPing();
      this._handleDisconnect();
    };

    this.ws.onerror = () => {
      // onclose will fire after this
    };
  }

  private _handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
      setTimeout(() => {
        this.reconnectAttempts++;
        this._createConnection();
      }, delay);
    } else {
      this._dispatch({
        type: "error",
        data: { code: 0, message: "连接已断开，请刷新页面重试" },
        timestamp: new Date().toISOString(),
      });
    }
  }

  private _startPing() {
    this.pingInterval = window.setInterval(() => {
      this.send({ type: "ping", data: {}, timestamp: new Date().toISOString() });
    }, 30000);
  }

  private _stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  send(message: WSMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.pendingActions.push(message);
    }
  }

  private _flushPendingActions() {
    while (this.pendingActions.length > 0) {
      const action = this.pendingActions.shift()!;
      this.send(action);
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  off(type: string, handler: MessageHandler) {
    this.handlers.get(type)?.delete(handler);
  }

  private _dispatch(message: WSMessage) {
    this.handlers.get(message.type)?.forEach((h) => h(message));
    this.handlers.get("*")?.forEach((h) => h(message));
  }

  disconnect() {
    this._stopPing();
    this.ws?.close(1000, "User disconnect");
    this.ws = null;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const gameWebSocket = new GameWebSocket();
