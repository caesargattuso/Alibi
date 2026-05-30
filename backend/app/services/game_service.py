import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.models import GameSession, DialogLog, Script, Scene
from app.services.ai_service import ai_service
from app.services.script_service import ScriptService


class GameService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.script_svc = ScriptService(db)

    async def create_game(self, user_id: int, script_id: int, player_name: str) -> GameSession:
        script = await self.script_svc.get_script(script_id)
        opening_scene = await self.script_svc.get_opening_scene(script_id)

        session = GameSession(
            user_id=user_id,
            script_id=script_id,
            current_scene_id=opening_scene.id,
            player_name=player_name,
            player_stats={},
            npc_states=self._init_npc_states(script),
            story_flags={},
            game_phase="opening",
            game_time="第1天 上午",
            alive_count=0,
            status="active",
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_game(self, session_id: int, user_id: int) -> GameSession:
        session = await self.db.get(GameSession, session_id)
        if not session:
            raise NotFoundError("游戏会话")
        if session.user_id != user_id:
            raise ForbiddenError("无权访问此游戏")
        return session

    async def process_action(self, session_id: int, user_id: int, player_input: str) -> dict:
        session = await self.get_game(session_id, user_id)
        if session.status != "active":
            raise ForbiddenError("游戏已结束")

        history = await self._get_dialog_history(session_id, limit=5)
        input_text = player_input or "继续"

        # Eager load script and scene for prompt building
        if not session.script:
            session.script = await self.db.get(Script, session.script_id)
        if not session.current_scene and session.current_scene_id:
            session.current_scene = await self.db.get(Scene, session.current_scene_id)

        ai_response = await ai_service.generate_story(session, input_text, history)
        await self._update_game_state(session, ai_response)
        await self._save_dialog_log(session_id, input_text, ai_response)

        return ai_response

    async def pause_game(self, session_id: int, user_id: int) -> GameSession:
        session = await self.get_game(session_id, user_id)
        session.status = "paused"
        await self.db.flush()
        return session

    async def resume_game(self, session_id: int, user_id: int) -> GameSession:
        session = await self.get_game(session_id, user_id)
        if session.status != "paused":
            raise ForbiddenError("只能恢复暂停中的游戏")
        session.status = "active"
        await self.db.flush()
        return session

    async def end_game(self, session_id: int, user_id: int, reason: str = "abandoned") -> GameSession:
        session = await self.get_game(session_id, user_id)
        session.status = reason
        session.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return session

    async def _get_dialog_history(self, session_id: int, limit: int = 5) -> list[dict]:
        stmt = (
            select(DialogLog)
            .where(DialogLog.session_id == session_id)
            .order_by(DialogLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        return [{"type": log.type, "content": log.content} for log in reversed(logs)]

    async def _update_game_state(self, session: GameSession, response: dict) -> None:
        if response.get("scene_change"):
            to_scene_key = response["scene_change"].get("to_scene_id")
            if to_scene_key:
                stmt = select(Scene).where(Scene.script_id == session.script_id, Scene.scene_key == to_scene_key)
                result = await self.db.execute(stmt)
                scene = result.scalar_one_or_none()
                if scene:
                    session.current_scene_id = scene.id

        for change in response.get("stat_changes", []):
            stat = change.get("stat")
            delta = change.get("change", 0)
            current = session.player_stats.get(stat, 0)
            session.player_stats[stat] = current + delta

        for flag_item in response.get("flags_set", []):
            flag = flag_item.get("flag") if isinstance(flag_item, dict) else flag_item
            value = flag_item.get("value", True) if isinstance(flag_item, dict) else True
            session.story_flags[flag] = value

        if response.get("is_game_over"):
            session.status = "completed"
            session.current_ending = response.get("ending")
            session.completed_at = datetime.now(timezone.utc)

        await self.db.flush()

    async def _save_dialog_log(self, session_id: int, player_input: str, ai_response: dict) -> None:
        log = DialogLog(
            session_id=session_id,
            type="narration",
            content=ai_response.get("narration", ""),
            player_input=player_input,
            ai_raw_response=json.dumps(ai_response, ensure_ascii=False),
            metadata={
                "choices": ai_response.get("choices", []),
                "dialogs": ai_response.get("dialogs", []),
            },
        )
        self.db.add(log)
        await self.db.flush()

    def _init_npc_states(self, script: Script) -> dict:
        states = {}
        if script.characters:
            for char in script.characters:
                states[char.character_key] = {
                    "name": char.name,
                    "status": "alive",
                    "affection": 0,
                }
        return states