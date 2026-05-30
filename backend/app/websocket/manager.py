from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.game_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}
        self.last_ping: Dict[WebSocket, datetime] = {}

    async def connect(self, websocket: WebSocket, game_id: int, user_id: int):
        await websocket.accept()
        self.game_connections.setdefault(game_id, set()).add(websocket)
        self.user_connections[user_id] = websocket
        self.last_ping[websocket] = datetime.now(timezone.utc)

    def disconnect(self, websocket: WebSocket, game_id: int, user_id: int):
        if game_id in self.game_connections:
            self.game_connections[game_id].discard(websocket)
            if not self.game_connections[game_id]:
                del self.game_connections[game_id]
        self.user_connections.pop(user_id, None)
        self.last_ping.pop(websocket, None)

    def update_ping(self, websocket: WebSocket):
        self.last_ping[websocket] = datetime.now(timezone.utc)

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
                pass

    async def _send(self, websocket: WebSocket, message: dict):
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        await websocket.send_json(message)

    async def check_timeouts(self):
        now = datetime.now(timezone.utc)
        timeout_seconds = 60
        to_remove = []

        for ws, last in self.last_ping.items():
            if (now - last).total_seconds() > timeout_seconds:
                to_remove.append(ws)

        for ws in to_remove:
            for game_id, conns in self.game_connections.items():
                if ws in conns:
                    for user_id, user_ws in list(self.user_connections.items()):
                        if user_ws is ws:
                            self.disconnect(ws, game_id, user_id)
                            try:
                                await ws.close(code=1001, reason="timeout")
                            except Exception:
                                pass
                            break
                    break


manager = ConnectionManager()
