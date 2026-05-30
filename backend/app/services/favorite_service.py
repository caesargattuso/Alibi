from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.models import ScriptFavorite, Script


class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_favorite(self, user_id: int, script_id: int) -> dict:
        script = await self.db.get(Script, script_id)
        if not script:
            raise NotFoundError("剧本")

        stmt = select(ScriptFavorite).where(
            ScriptFavorite.user_id == user_id,
            ScriptFavorite.script_id == script_id,
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return {"favorited": True, "favorite_count": await self._get_count(script_id)}

        fav = ScriptFavorite(user_id=user_id, script_id=script_id)
        self.db.add(fav)
        await self.db.flush()
        return {"favorited": True, "favorite_count": await self._get_count(script_id)}

    async def remove_favorite(self, user_id: int, script_id: int) -> dict:
        stmt = delete(ScriptFavorite).where(
            ScriptFavorite.user_id == user_id,
            ScriptFavorite.script_id == script_id,
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return {"favorited": False, "favorite_count": await self._get_count(script_id)}

    async def check_favorite(self, user_id: int, script_id: int) -> dict:
        stmt = select(ScriptFavorite).where(
            ScriptFavorite.user_id == user_id,
            ScriptFavorite.script_id == script_id,
        )
        result = await self.db.execute(stmt)
        return {"favorited": result.scalar_one_or_none() is not None}

    async def _get_count(self, script_id: int) -> int:
        stmt = select(func.count()).select_from(ScriptFavorite).where(ScriptFavorite.script_id == script_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
