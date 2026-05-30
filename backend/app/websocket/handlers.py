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
                input_text = self._build_action_input(action_type, target_id, player_input)
                ai_response = await self.game_svc.process_action(session_id, user_id, input_text)

            return {"type": "story_update", "data": ai_response}
        except Exception as e:
            return {"type": "error", "data": {"code": 500, "message": str(e)}}

    def _build_action_input(self, action_type: str, target_id: str | None, input_text: str) -> str:
        if action_type == "move":
            return f"[移动] 前往 {target_id}"
        if action_type == "interact":
            return f"[交互] 与 {target_id} 互动"
        if action_type == "talk":
            return f"[对话] 与 {target_id} 交谈: {input_text}"
        return input_text
