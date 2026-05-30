from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.models import Script, Scene, Character
from app.schemas.script import ScriptCreate, ScriptUpdate


class ScriptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_scripts(
        self, page: int = 1, per_page: int = 20, genre: str | None = None, difficulty: str | None = None
    ) -> tuple[list[Script], int]:
        stmt = select(Script).where(Script.status == "published")
        if genre:
            stmt = stmt.where(Script.genre == genre)
        if difficulty:
            stmt = stmt.where(Script.difficulty == difficulty)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Script.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    async def get_script(self, script_id: int) -> Script:
        script = await self.db.get(Script, script_id)
        if not script:
            raise NotFoundError("剧本")
        return script

    async def create_script(self, author_id: int, data: ScriptCreate) -> Script:
        script = Script(
            title=data.title,
            description=data.description,
            genre=data.genre,
            difficulty=data.difficulty,
            author_id=author_id,
            setting=data.setting,
            rules=data.rules,
            endings=data.endings,
            tags=data.tags,
            cover_image=data.cover_image,
            banner_image=data.banner_image,
        )
        self.db.add(script)
        await self.db.flush()
        return script

    async def update_script(self, script_id: int, author_id: int, data: ScriptUpdate) -> Script:
        script = await self.get_script(script_id)
        if script.author_id != author_id:
            raise ForbiddenError("只能修改自己的剧本")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(script, field, value)
        await self.db.flush()
        return script

    async def delete_script(self, script_id: int, author_id: int) -> None:
        script = await self.get_script(script_id)
        if script.author_id != author_id:
            raise ForbiddenError("只能删除自己的剧本")
        await self.db.delete(script)
        await self.db.flush()

    async def get_opening_scene(self, script_id: int) -> Scene:
        stmt = select(Scene).where(Scene.script_id == script_id).order_by(Scene.sort_order).limit(1)
        result = await self.db.execute(stmt)
        scene = result.scalar_one_or_none()
        if not scene:
            raise NotFoundError("开场场景")
        return scene