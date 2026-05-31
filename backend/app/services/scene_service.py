from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.models import GameSession, Scene, InvestigationLog


class SceneService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_scene(self, scene_id: int) -> Scene:
        scene = await self.db.get(Scene, scene_id)
        if not scene:
            raise NotFoundError("场景")
        return scene

    async def get_scene_by_key(self, script_id: int, scene_key: str) -> Scene:
        stmt = select(Scene).where(
            Scene.script_id == script_id,
            Scene.scene_key == scene_key,
        )
        result = await self.db.execute(stmt)
        scene = result.scalar_one_or_none()
        if not scene:
            raise NotFoundError("场景")
        return scene

    async def get_map_data(self, scene_id: int) -> dict:
        scene = await self.get_scene(scene_id)
        return scene.map_data

    async def get_interactables(self, scene_id: int) -> list[dict]:
        scene = await self.get_scene(scene_id)
        return scene.map_data.get("interactable_points", [])

    async def execute_interaction(
        self,
        scene_id: int,
        session_id: int,
        interactable_id: str,
        action_id: str,
    ) -> dict:
        scene = await self.get_scene(scene_id)
        game_session = await self.db.get(GameSession, session_id)
        if not game_session:
            raise NotFoundError("游戏会话")

        interactables = scene.map_data.get("interactable_points", [])
        interactable = next(
            (i for i in interactables if i["id"] == interactable_id),
            None,
        )
        if not interactable:
            raise NotFoundError("交互点")

        available_actions = interactable.get("actions", [])
        if action_id not in available_actions:
            raise ValidationError(f"该交互点不支持动作: {action_id}")

        conditions = interactable.get("conditions", {}).get(action_id, [])
        for cond in conditions:
            if not self._check_condition(cond, game_session):
                raise ValidationError("不满足交互条件")

        effects = self._calculate_effects(interactable, action_id)

        # Check for investigation-specific data
        investigation_data = interactable.get("investigation", {})
        clues_revealed = []
        detailed_message = None

        if action_id == "examine" and investigation_data:
            # Check required flags
            required_flags = investigation_data.get("required_flags", [])
            can_reveal = all(game_session.story_flags.get(f) for f in required_flags)

            if can_reveal:
                clue_text = investigation_data.get("clue_text")
                if clue_text:
                    detailed_message = clue_text
                    revealed_flags = investigation_data.get("revealed_flags", [])
                    clues_revealed = revealed_flags
                    for flag in revealed_flags:
                        effects.append({"type": "set_flag", "target": flag, "value": True})

        # Log investigation
        log = InvestigationLog(
            session_id=session_id,
            scene_id=scene_id,
            interactable_id=interactable_id,
            action_id=action_id,
            action_type="investigate" if action_id == "examine" else "talk" if action_id == "talk" else "other",
            content=detailed_message or self._get_interaction_message(interactable, action_id),
            clues_revealed=clues_revealed,
            meta_data={"interactable_name": interactable["name"], "interactable_type": interactable["type"]},
        )
        self.db.add(log)
        await self.db.flush()

        return {
            "success": True,
            "message": detailed_message or self._get_interaction_message(interactable, action_id),
            "effects": effects,
            "clues_revealed": clues_revealed,
            "ai_trigger": {
                "should_generate": True,
                "context": f"玩家对{interactable['name']}执行了{action_id}",
            },
        }

    async def get_investigation_logs(self, session_id: int, scene_id: int | None = None) -> list[dict]:
        """Get investigation logs for a game session."""
        from sqlalchemy import select as sa_select
        stmt = sa_select(InvestigationLog).where(InvestigationLog.session_id == session_id)
        if scene_id:
            stmt = stmt.where(InvestigationLog.scene_id == scene_id)
        stmt = stmt.order_by(InvestigationLog.created_at.desc())
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "interactable_id": log.interactable_id,
                "action_id": log.action_id,
                "action_type": log.action_type,
                "content": log.content,
                "clues_revealed": log.clues_revealed,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    def _check_condition(self, condition: dict, session: GameSession) -> bool:
        cond_type = condition.get("type")
        if cond_type == "flag":
            flag = condition.get("flag")
            expected = condition.get("value", True)
            return session.story_flags.get(flag) == expected
        if cond_type == "stat":
            stat = condition.get("stat")
            operator = condition.get("operator", ">=")
            value = condition.get("value", 0)
            current = session.player_stats.get(stat, 0)
            return self._compare(current, operator, value)
        return True

    def _compare(self, a: int, op: str, b: int) -> bool:
        ops = {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
        }
        return ops.get(op, lambda x, y: True)(a, b)

    def _calculate_effects(self, interactable: dict, action_id: str) -> list[dict]:
        effects = [{"type": "set_flag", "target": f"{interactable['id']}_{action_id}", "value": True}]

        if interactable["type"] == "exit" and action_id == "enter":
            effects.append({
                "type": "change_scene",
                "target": interactable.get("target_scene"),
                "position": interactable.get("target_position"),
            })

        return effects

    def _get_interaction_message(self, interactable: dict, action_id: str) -> str:
        messages = {
            "examine": f"你仔细观察{interactable['name']}...",
            "talk": f"你走向{interactable['name']}，准备交谈...",
            "touch": f"你伸手触碰{interactable['name']}...",
            "enter": f"你走向{interactable['name']}...",
            "sit": f"你坐上了{interactable['name']}...",
            "use": f"你使用了{interactable['name']}...",
            "pick_up": f"你拾起了{interactable['name']}...",
            "search": f"你搜索了{interactable['name']}...",
        }
        return messages.get(action_id, f"你对{interactable['name']}执行了{action_id}")

    async def npc_dialogue(
        self,
        scene_id: int,
        session_id: int,
        npc_id: str,
        player_message: str,
        dialogue_history: list[dict],
    ) -> dict:
        """Handle NPC dialogue with AI-generated responses."""
        from app.services.ai_service import ai_service
        from app.models.models import GameSession, Character
        from sqlalchemy import select as sa_select

        # Get game session
        game_session = await self.db.get(GameSession, session_id)
        if not game_session:
            raise NotFoundError("游戏会话")

        # Get NPC character data
        stmt = sa_select(Character).where(
            Character.script_id == game_session.script_id,
            Character.character_key == npc_id,
        )
        result = await self.db.execute(stmt)
        npc = result.scalar_one_or_none()

        if not npc:
            return {
                "text": "...（对方似乎没听见你在说什么）",
                "emotion": "neutral",
                "clues_revealed": [],
                "trust_change": 0,
            }

        # Build NPC context
        npc_context = f"""你是一个互动小说游戏中的NPC角色。

角色信息：
- 姓名：{npc.name}
- 外观：{npc.appearance or '未知'}
- 性格：{', '.join(npc.personality.get('traits', [])) if npc.personality else '未知'}
- 背景：{npc.background or '未知'}
- 对话风格：{npc.dialogue_style or '普通'}

当前玩家对你说：{player_message}

请根据角色设定回复。回复要符合角色性格，保持角色视角。"""

        # Call AI service for response
        try:
            response = await ai_service.client.chat.completions.create(
                model=ai_service.model if hasattr(ai_service, 'model') else "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": npc_context},
                    {"role": "user", "content": player_message},
                ],
                max_tokens=200,
                temperature=0.8,
            )

            npc_text = response.choices[0].message.content or "..."

            return {
                "text": npc_text,
                "emotion": "neutral",
                "clues_revealed": [],
                "trust_change": 0,
            }
        except Exception as e:
            # Fallback response
            return {
                "text": f"{npc.name}看了你一眼，说道：\"这件事...我暂时不能告诉你。\"",
                "emotion": "suspicious",
                "clues_revealed": [],
                "trust_change": 0,
            }


scene_service = SceneService
