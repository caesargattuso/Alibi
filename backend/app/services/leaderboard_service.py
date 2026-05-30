from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Script, GameSession, User, UserAchievement, Achievement


class LeaderboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def scripts_leaderboard(
        self, sort_by: str, period: str, page: int, per_page: int
    ) -> dict:
        offset = (page - 1) * per_page
        base_stmt = select(Script).where(Script.status == "published")

        # Apply time filter for play_count
        if period != "all" and sort_by == "play_count":
            start_date = self._get_period_start(period)
            # For simplicity, we use total play_count (no time filtering on play_count field)
            # In production, would need a separate play_logs table

        # Sort
        if sort_by == "play_count":
            base_stmt = base_stmt.order_by(Script.play_count.desc())
        elif sort_by == "rating":
            base_stmt = base_stmt.order_by(Script.rating.desc())
        else:
            base_stmt = base_stmt.order_by(Script.play_count.desc())

        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Paginate
        stmt = base_stmt.offset(offset).limit(per_page)
        result = await self.db.execute(stmt)
        scripts = result.scalars().all()

        items = [
            {
                "rank": offset + i + 1,
                "id": s.id,
                "title": s.title,
                "cover_image": s.cover_image,
                "play_count": s.play_count,
                "rating": float(s.rating),
            }
            for i, s in enumerate(scripts)
        ]

        return {"items": items, "total": total, "page": page, "per_page": per_page}

    async def players_leaderboard(
        self, sort_by: str, period: str, page: int, per_page: int
    ) -> dict:
        offset = (page - 1) * per_page

        # Build subquery for player stats
        if sort_by == "completed_games":
            subq = (
                select(
                    GameSession.user_id,
                    func.count(GameSession.id).label("completed_games"),
                )
                .where(GameSession.status == "completed")
                .group_by(GameSession.user_id)
                .subquery()
            )
            order_col = subq.c.completed_games.desc()
        elif sort_by == "achievement_points":
            subq = (
                select(
                    UserAchievement.user_id,
                    func.sum(Achievement.points).label("points"),
                )
                .join(Achievement, UserAchievement.achievement_id == Achievement.id)
                .group_by(UserAchievement.user_id)
                .subquery()
            )
            order_col = subq.c.points.desc()
        else:
            subq = (
                select(
                    GameSession.user_id,
                    func.count(GameSession.id).label("completed_games"),
                )
                .where(GameSession.status == "completed")
                .group_by(GameSession.user_id)
                .subquery()
            )
            order_col = subq.c.completed_games.desc()

        # Join with users
        stmt = (
            select(User, subq)
            .join(subq, User.id == subq.c.user_id)
            .order_by(order_col)
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Count total
        count_stmt = select(func.count()).select_from(subq)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        items = [
            {
                "rank": offset + i + 1,
                "id": row[0].id,
                "username": row[0].username,
                "avatar_url": row[0].avatar_url,
                "completed_games": row[1] if sort_by == "completed_games" else 0,
                "achievement_points": row[1] if sort_by == "achievement_points" else 0,
            }
            for i, row in enumerate(rows)
        ]

        return {"items": items, "total": total, "page": page, "per_page": per_page}

    def _get_period_start(self, period: str) -> datetime:
        now = datetime.now(timezone.utc)
        if period == "week":
            return now - timedelta(days=7)
        if period == "month":
            return now - timedelta(days=30)
        return now - timedelta(days=365)
