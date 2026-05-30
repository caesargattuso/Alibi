from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("")
async def list_achievements(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AchievementService(db)
    achievements = await svc.list_all(user.id)
    return {"code": 200, "data": achievements}


@router.get("/me")
async def list_my_achievements(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AchievementService(db)
    achievements = await svc.list_user_achievements(user.id)
    return {"code": 200, "data": achievements}
