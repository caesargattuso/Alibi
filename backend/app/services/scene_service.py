from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.models import GameSession, Scene


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

        return {
            "success": True,
            "message": self._get_interaction_message(interactable, action_id),
            "effects": effects,
            "ai_trigger": {
                "should_generate": True,
                "context": f"玩家对{interactable['name']}执行了{action_id}",
            },
        }

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
        }
        return messages.get(action_id, f"你对{interactable['name']}执行了{action_id}")
