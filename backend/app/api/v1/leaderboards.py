from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])


@router.get("/scripts")
async def scripts_leaderboard(
    sort_by: str = Query("play_count", regex="^(play_count|rating)$"),
    period: str = Query("week", regex="^(week|month|all)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = LeaderboardService(db)
    result = await svc.scripts_leaderboard(sort_by, period, page, per_page)
    return {"code": 200, "data": result}


@router.get("/players")
async def players_leaderboard(
    sort_by: str = Query("completed_games", regex="^(completed_games|achievement_points)$"),
    period: str = Query("week", regex="^(week|month|all)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = LeaderboardService(db)
    result = await svc.players_leaderboard(sort_by, period, page, per_page)
    return {"code": 200, "data": result}
