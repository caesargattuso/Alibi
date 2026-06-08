import json
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.models import GameSession, DialogLog, Script, Scene, Character
from app.services.ai_service import ai_service
from app.services.script_service import ScriptService


class GameService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.script_svc = ScriptService(db)

    async def create_game(self, user_id: int, script_id: int, player_name: str) -> GameSession:
        script = await self.script_svc.get_script(script_id)
        opening_scene = await self.script_svc.get_opening_scene(script_id)
        npc_states = self._init_npc_states(script)

        session = GameSession(
            user_id=user_id,
            script_id=script_id,
            current_scene_id=opening_scene.id,
            player_name=player_name,
            player_stats={},
            npc_states=npc_states,
            story_flags={},
            game_phase="opening",
            game_time="第1天 上午",
            alive_count=sum(1 for s in npc_states.values() if s.get("status") == "alive"),
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

        # Load script and scene for prompt building
        stmt = select(Script).where(Script.id == session.script_id)
        result = await self.db.execute(stmt)
        script = result.scalar_one_or_none()
        # Eagerly load characters for AI prompt
        if script:
            char_result = await self.db.execute(
                select(Character).where(Character.script_id == script.id)
            )
            script.characters = char_result.scalars().all()
        current_scene = await self.db.get(Scene, session.current_scene_id) if session.current_scene_id else None

        ai_response = await ai_service.generate_story(session, script, current_scene, input_text, history)
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

    async def save_action_result(self, session: GameSession, player_input: str, ai_response: dict) -> None:
        """Save AI response result without calling AI again (used after streaming)."""
        await self._update_game_state(session, ai_response)
        await self._save_dialog_log(session.id, player_input, ai_response)

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
                    # Check entry conditions
                    entry_conditions = scene.entry_conditions
                    if entry_conditions and entry_conditions.get("type") == "flag":
                        required_flag = entry_conditions.get("flag")
                        required_value = entry_conditions.get("value", True)
                        if session.story_flags.get(required_flag) != required_value:
                            # Deny entry, set flag so AI knows
                            session.story_flags["_scene_entry_denied"] = to_scene_key
                        else:
                            session.current_scene_id = scene.id
                            # Process on_enter events
                            if scene.on_enter:
                                for flag in scene.on_enter.get("set_flags", []):
                                    session.story_flags[flag] = True
                    else:
                        session.current_scene_id = scene.id

        for change in response.get("stat_changes", []):
            target = change.get("target", "player")
            target_id = change.get("target_id", "")
            stat = change.get("stat")
            delta = change.get("change", 0)

            if target == "npc" and target_id:
                if target_id in session.npc_states:
                    npc = session.npc_states[target_id]
                    npc[stat] = npc.get(stat, 0) + delta
            else:
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
            meta_data={
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

    async def list_user_games(self, user_id: int, page: int, per_page: int, status: str | None) -> dict:
        offset = (page - 1) * per_page

        base_stmt = select(GameSession).where(GameSession.user_id == user_id)
        if status:
            base_stmt = base_stmt.where(GameSession.status == status)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            base_stmt
            .order_by(GameSession.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        items = []
        for session in sessions:
            script = await self.db.get(Script, session.script_id)
            items.append({
                "id": session.id,
                "script_id": session.script_id,
                "script_title": script.title if script else "未知剧本",
                "script_cover": script.cover_image if script else None,
                "player_name": session.player_name,
                "status": session.status,
                "current_ending": session.current_ending,
                "game_phase": session.game_phase,
                "game_time": session.game_time,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            })

        return {"items": items, "total": total, "page": page, "per_page": per_page}

    async def get_dialog_history_paginated(
        self, session_id: int, user_id: int, page: int, per_page: int, log_type: str | None
    ) -> dict:
        session = await self.get_game(session_id, user_id)
        offset = (page - 1) * per_page

        base_stmt = select(DialogLog).where(DialogLog.session_id == session.id)
        if log_type:
            base_stmt = base_stmt.where(DialogLog.type == log_type)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            base_stmt
            .order_by(DialogLog.created_at.asc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        items = [
            {
                "id": log.id,
                "type": log.type,
                "content": log.content,
                "metadata": log.meta_data,
                "player_input": log.player_input,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

        return {"items": items, "total": total, "page": page, "per_page": per_page}