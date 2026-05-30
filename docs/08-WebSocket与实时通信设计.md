# WebSocket与实时通信设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | WebSocket与实时通信设计 |
| 版本 | v1.0 |
| 更新日期 | 2026-05-30 |

---

## 一、模块概述

### 1.1 功能范围

WebSocket模块负责处理游戏中的实时通信，包括：
- WebSocket连接管理（建立、维护、断开）
- 游戏会话的实时状态同步
- AI剧情流式输出
- 角色移动同步
- 系统通知推送

### 1.2 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI WebSocket | 原生支持，与现有框架集成 |
| 前端 | 原生 WebSocket API | 无额外依赖，轻量级 |
| 认证 | JWT Token | 连接时通过URL参数传递 |

---

## 二、WebSocket连接流程

### 2.1 连接建立

```
客户端                              服务端
   │                                  │
   │  ws://api/ws/v1/games/{session_id}?token={jwt}
   │ ────────────────────────────────►│
   │                                  │ 验证Token
   │                                  │ 验证session归属
   │                                  │ 存储连接
   │  ◄───────────────────────────────│ {"type":"connected","data":{...}}
   │                                  │
```

### 2.2 心跳机制

```
客户端                              服务端
   │                                  │
   │  {"type":"ping"}                 │
   │ ────────────────────────────────►│
   │  ◄───────────────────────────────│ {"type":"pong"}
   │                                  │
```

- 客户端每30秒发送ping
- 服务端超时60秒未收到ping则断开

### 2.3 断线重连

```
客户端                              服务端
   │                                  │
   │  连接断开                         │
   │                                  │
   │  等待 1s, 2s, 4s, 8s, 16s        │
   │  (指数退避，最多5次)              │
   │                                  │
   │  重新连接                         │
   │ ────────────────────────────────►│
   │                                  │
   │  发送离线期间缓存的操作           │
   │ ────────────────────────────────►│
   │                                  │
```

---

## 三、消息格式

### 3.1 通用消息结构

```typescript
interface WSMessage {
  type: string;
  data: unknown;
  timestamp: string;
}
```

### 3.2 消息类型定义

| 类型 | 方向 | 说明 |
|------|------|------|
| `ping` | C→S | 心跳请求 |
| `pong` | S→C | 心跳响应 |
| `connected` | S→C | 连接成功确认 |
| `action` | C→S | 游戏动作 |
| `story_update` | S→C | AI剧情更新 |
| `character_move` | S→C | 角色移动 |
| `scene_change` | S→C | 场景切换 |
| `system` | S→C | 系统通知 |
| `error` | S→C | 错误消息 |

### 3.3 客户端→服务端消息

**游戏动作：**
```json
{
  "type": "action",
  "data": {
    "action_type": "move|interact|talk|custom",
    "target_id": "string",
    "input": "string"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

### 3.4 服务端→客户端消息

**剧情更新：**
```json
{
  "type": "story_update",
  "data": {
    "narration": "string",
    "dialogs": [...],
    "choices": [...],
    "commands": {...}
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

**角色移动：**
```json
{
  "type": "character_move",
  "data": {
    "character_id": "string",
    "from": {"x": 0, "y": 0},
    "to": {"x": 100, "y": 200}
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

**场景切换：**
```json
{
  "type": "scene_change",
  "data": {
    "from_scene_id": 1,
    "to_scene_id": 2,
    "transition": "fade"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

**系统通知：**
```json
{
  "type": "system",
  "data": {
    "message": "string",
    "level": "info|warning|error"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

**错误消息：**
```json
{
  "type": "error",
  "data": {
    "code": 400,
    "message": "string"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

---

## 四、后端实现

### 4.1 项目结构

```
backend/app/
├── websocket/
│   ├── __init__.py
│   ├── manager.py      # 连接管理器
│   └── handlers.py     # 消息处理器
├── api/
│   └── v1/
│       └── ws.py       # WebSocket路由
```

### 4.2 连接管理器

```python
# app/websocket/manager.py

from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
import asyncio
import json


class ConnectionManager:
    def __init__(self):
        # session_id -> set of connections (for future multi-tab support)
        self.game_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> websocket (single connection per user)
        self.user_connections: Dict[int, WebSocket] = {}
        # connection -> last_ping timestamp
        self.last_ping: Dict[WebSocket, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        game_id: int,
        user_id: int
    ):
        await websocket.accept()
        self.game_connections.setdefault(game_id, set()).add(websocket)
        self.user_connections[user_id] = websocket
        self.last_ping[websocket] = datetime.utcnow()

    def disconnect(self, websocket: WebSocket, game_id: int, user_id: int):
        if game_id in self.game_connections:
            self.game_connections[game_id].discard(websocket)
            if not self.game_connections[game_id]:
                del self.game_connections[game_id]
        self.user_connections.pop(user_id, None)
        self.last_ping.pop(websocket, None)

    def update_ping(self, websocket: WebSocket):
        self.last_ping[websocket] = datetime.utcnow()

    async def send_to_user(self, message: dict, user_id: int):
        ws = self.user_connections.get(user_id)
        if ws:
            await self._send(ws, message)

    async def broadcast_to_game(self, message: dict, game_id: int):
        connections = self.game_connections.get(game_id, set())
        for ws in list(connections):
            try:
                await self._send(ws, message)
            except Exception:
                pass  # Connection will be cleaned up by heartbeat check

    async def _send(self, websocket: WebSocket, message: dict):
        message["timestamp"] = datetime.utcnow().isoformat() + "Z"
        await websocket.send_json(message)

    async def check_timeouts(self):
        """检查超时连接并清理"""
        now = datetime.utcnow()
        timeout_seconds = 60
        to_remove = []

        for ws, last in self.last_ping.items():
            if (now - last).total_seconds() > timeout_seconds:
                to_remove.append(ws)

        for ws in to_remove:
            # Find associated game_id and user_id
            for game_id, conns in self.game_connections.items():
                if ws in conns:
                    for user_id, user_ws in self.user_connections.items():
                        if user_ws == ws:
                            self.disconnect(ws, game_id, user_id)
                            try:
                                await ws.close(code=1001, reason="timeout")
                            except Exception:
                                pass
                            break
                    break


manager = ConnectionManager()
```

### 4.3 消息处理器

```python
# app/websocket/handlers.py

import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.game_service import GameService
from app.websocket.manager import manager


class MessageHandler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.game_svc = GameService(db)

    async def handle(self, websocket, message: dict, session_id: int, user_id: int) -> dict | None:
        msg_type = message.get("type")

        if msg_type == "ping":
            manager.update_ping(websocket)
            return {"type": "pong", "data": {}}

        if msg_type == "action":
            return await self._handle_action(message, session_id, user_id)

        return None

    async def _handle_action(self, message: dict, session_id: int, user_id: int) -> dict:
        data = message.get("data", {})
        action_type = data.get("action_type", "custom")
        target_id = data.get("target_id")
        player_input = data.get("input", "")

        try:
            if action_type == "custom":
                ai_response = await self.game_svc.process_action(session_id, user_id, player_input)
            else:
                # For move/interact/talk, construct appropriate input
                input_text = self._build_action_input(action_type, target_id, player_input)
                ai_response = await self.game_svc.process_action(session_id, user_id, input_text)

            return {
                "type": "story_update",
                "data": ai_response
            }
        except Exception as e:
            return {
                "type": "error",
                "data": {"code": 500, "message": str(e)}
            }

    def _build_action_input(self, action_type: str, target_id: str | None, input_text: str) -> str:
        if action_type == "move":
            return f"[移动] 前往 {target_id}"
        if action_type == "interact":
            return f"[交互] 与 {target_id} 互动"
        if action_type == "talk":
            return f"[对话] 与 {target_id} 交谈: {input_text}"
        return input_text
```

### 4.4 WebSocket路由

```python
# app/api/v1/ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.exceptions import AuthError
from app.db.session import get_db
from app.models.models import GameSession
from app.websocket.manager import manager
from app.websocket.handlers import MessageHandler

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/v1/games/{session_id}")
async def game_websocket(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 验证Token
    try:
        user_id = decode_token(token, expected_type="access")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 验证游戏会话归属
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user_id:
        await websocket.close(code=4003, reason="Forbidden")
        return

    # 建立连接
    await manager.connect(websocket, session_id, user_id)

    # 发送连接成功消息
    await manager.send_to_user({
        "type": "connected",
        "data": {"session_id": session_id, "user_id": user_id}
    }, user_id)

    handler = MessageHandler(db)

    try:
        while True:
            data = await websocket.receive_json()
            response = await handler.handle(websocket, data, session_id, user_id)
            if response:
                await manager.send_to_user(response, user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, user_id)
    except Exception:
        manager.disconnect(websocket, session_id, user_id)
        await websocket.close(code=1011, reason="Internal error")
```

---

## 五、前端实现

### 5.1 WebSocket服务

```typescript
// frontend/src/services/websocket.ts

export interface WSMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

export type MessageHandler = (message: WSMessage) => void;

class GameWebSocket {
  private ws: WebSocket | null = null;
  private url: string = "";
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
      console.log("[WS] Connected");
      this.reconnectAttempts = 0;
      this._startPing();
      this._flushPendingActions();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        this._dispatch(message);
      } catch (e) {
        console.error("[WS] Parse error:", e);
      }
    };

    this.ws.onclose = (event) => {
      console.log("[WS] Disconnected:", event.code, event.reason);
      this._stopPing();
      this._handleDisconnect();
    };

    this.ws.onerror = (error) => {
      console.error("[WS] Error:", error);
    };
  }

  private _handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
      console.log(`[WS] Reconnecting in ${delay}ms...`);
      setTimeout(() => {
        this.reconnectAttempts++;
        this._createConnection();
      }, delay);
    } else {
      console.error("[WS] Max reconnect attempts reached");
      this._dispatch({ type: "error", data: { code: 0, message: "连接已断开" }, timestamp: new Date().toISOString() });
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
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach((h) => h(message));
    }
    // Also dispatch to wildcard handlers
    const wildcardHandlers = this.handlers.get("*");
    if (wildcardHandlers) {
      wildcardHandlers.forEach((h) => h(message));
    }
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
```

### 5.2 useWebSocket Hook

```typescript
// frontend/src/hooks/useWebSocket.ts

import { useEffect, useCallback, useRef } from "react";
import { gameWebSocket, WSMessage } from "../services/websocket";
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
```

---

## 六、实现步骤

### 6.1 后端实现顺序

1. 创建 `app/websocket/manager.py` - 连接管理器
2. 创建 `app/websocket/handlers.py` - 消息处理器
3. 创建 `app/api/v1/ws.py` - WebSocket路由
4. 在 `app/main.py` 中注册WebSocket路由

### 6.2 前端实现顺序

1. 创建 `frontend/src/services/websocket.ts` - WebSocket服务
2. 创建 `frontend/src/hooks/useWebSocket.ts` - Hook

---

## 文档修订记录

| 版本 | 日期 | 修订内容 | 修订人 |
|------|------|----------|--------|
| v1.0 | 2026-05-30 | 初始版本 | - |
