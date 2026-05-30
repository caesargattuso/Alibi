from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.models import ScriptRating, Script, User


class RatingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def rate_script(self, user_id: int, script_id: int, rating: int, comment: str | None) -> dict:
        script = await self.db.get(Script, script_id)
        if not script:
            raise NotFoundError("剧本")

        if not 1 <= rating <= 5:
            raise ValidationError("评分必须在1-5之间", "rating")

        # Check if user already rated
        stmt = select(ScriptRating).where(
            ScriptRating.user_id == user_id,
            ScriptRating.script_id == script_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.rating = rating
            existing.comment = comment
        else:
            new_rating = ScriptRating(
                user_id=user_id,
                script_id=script_id,
                rating=rating,
                comment=comment,
            )
            self.db.add(new_rating)

        await self.db.flush()
        await self._update_script_average(script_id)

        # Re-read script for updated values
        await self.db.refresh(script)
        return {
            "rating": rating,
            "comment": comment,
            "average_rating": float(script.rating),
            "rating_count": script.rating_count,
        }

    async def get_script_ratings(self, script_id: int, page: int, per_page: int) -> dict:
        offset = (page - 1) * per_page

        count_stmt = select(func.count()).select_from(ScriptRating).where(ScriptRating.script_id == script_id)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(ScriptRating, User.username, User.avatar_url)
            .join(User, ScriptRating.user_id == User.id)
            .where(ScriptRating.script_id == script_id)
            .order_by(ScriptRating.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            rating_obj = row[0]
            items.append({
                "id": rating_obj.id,
                "user_id": rating_obj.user_id,
                "username": row[1],
                "avatar_url": row[2],
                "rating": rating_obj.rating,
                "comment": rating_obj.comment,
                "created_at": rating_obj.created_at.isoformat() if rating_obj.created_at else None,
            })

        return {"items": items, "total": total, "page": page, "per_page": per_page}

    async def _update_script_average(self, script_id: int) -> None:
        stmt = select(
            func.avg(ScriptRating.rating),
            func.count(ScriptRating.id),
        ).where(ScriptRating.script_id == script_id)
        result = await self.db.execute(stmt)
        avg_rating, count = result.one()

        script = await self.db.get(Script, script_id)
        if script:
            script.rating = round(avg_rating, 1) if avg_rating else 0
            script.rating_count = count or 0
            await self.db.flush()
