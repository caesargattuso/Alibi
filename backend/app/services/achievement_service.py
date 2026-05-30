from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Achievement, UserAchievement, User


class AchievementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, user_id: int | None = None) -> list[dict]:
        stmt = select(Achievement).order_by(Achievement.points.desc())
        result = await self.db.execute(stmt)
        achievements = result.scalars().all()

        unlocked_ids = set()
        if user_id:
            stmt2 = select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
            result2 = await self.db.execute(stmt2)
            unlocked_ids = {row[0] for row in result2.all()}

        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "condition_type": a.condition_type,
                "points": a.points,
                "unlocked": a.id in unlocked_ids,
            }
            for a in achievements
        ]

    async def list_user_achievements(self, user_id: int) -> list[dict]:
        stmt = (
            select(UserAchievement, Achievement)
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "points": a.points,
                "unlocked": True,
                "unlocked_at": ua.unlocked_at.isoformat() if ua.unlocked_at else None,
            }
            for ua, a in rows
        ]

    async def check_and_unlock(self, user_id: int, condition_type: str, context: dict) -> list[dict]:
        stmt = select(Achievement).where(Achievement.condition_type == condition_type)
        result = await self.db.execute(stmt)
        achievements = result.scalars().all()

        unlocked = []
        for a in achievements:
            if await self._check_condition(a, user_id, context):
                if await self._unlock(user_id, a.id):
                    unlocked.append({
                        "id": a.id,
                        "name": a.name,
                        "description": a.description,
                        "icon": a.icon,
                        "points": a.points,
                    })
        return unlocked

    async def _check_condition(self, achievement: Achievement, user_id: int, context: dict) -> bool:
        data = achievement.condition_data or {}
        cond_type = achievement.condition_type

        if cond_type == "game_complete":
            required = data.get("count", 1)
            stmt = select(func.count()).select_from(UserAchievement).where(
                UserAchievement.user_id == user_id
            )
            # Count completed games instead
            from app.models.models import GameSession
            stmt = select(func.count()).select_from(GameSession).where(
                GameSession.user_id == user_id,
                GameSession.status == "completed",
            )
            count = (await self.db.execute(stmt)).scalar() or 0
            return count >= required

        if cond_type == "ending_unlock":
            ending_key = data.get("ending")
            return context.get("ending") == ending_key

        return False

    async def _unlock(self, user_id: int, achievement_id: int) -> bool:
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return False

        ua = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        self.db.add(ua)
        await self.db.flush()
        return True
