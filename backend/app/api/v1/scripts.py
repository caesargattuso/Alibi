from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptOut, ScriptDetailOut
from app.services.script_service import ScriptService
from app.services.favorite_service import FavoriteService
from app.services.rating_service import RatingService

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("", response_model=dict)
async def list_scripts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    genre: str | None = None,
    difficulty: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = ScriptService(db)
    scripts, total = await svc.list_scripts(page, per_page, genre, difficulty)
    return {
        "code": 200,
        "data": {
            "items": [ScriptOut.model_validate(s).model_dump() for s in scripts],
            "total": total,
            "page": page,
            "per_page": per_page,
        },
    }


@router.get("/{script_id}", response_model=dict)
async def get_script(script_id: int, db: AsyncSession = Depends(get_db)):
    svc = ScriptService(db)
    script = await svc.get_script(script_id)
    return {"code": 200, "data": ScriptDetailOut.model_validate(script).model_dump()}


@router.post("", response_model=dict)
async def create_script(data: ScriptCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ScriptService(db)
    script = await svc.create_script(user.id, data)
    return {"code": 200, "data": ScriptOut.model_validate(script).model_dump()}


@router.put("/{script_id}", response_model=dict)
async def update_script(
    script_id: int, data: ScriptUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = ScriptService(db)
    script = await svc.update_script(script_id, user.id, data)
    return {"code": 200, "data": ScriptOut.model_validate(script).model_dump()}


@router.delete("/{script_id}", response_model=dict)
async def delete_script(script_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ScriptService(db)
    await svc.delete_script(script_id, user.id)
    return {"code": 200, "data": None}


# --- Favorite ---

@router.post("/{script_id}/favorite", response_model=dict)
async def add_favorite(script_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FavoriteService(db)
    result = await svc.add_favorite(user.id, script_id)
    return {"code": 200, "data": result}


@router.delete("/{script_id}/favorite", response_model=dict)
async def remove_favorite(script_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FavoriteService(db)
    result = await svc.remove_favorite(user.id, script_id)
    return {"code": 200, "data": result}


@router.get("/{script_id}/favorite", response_model=dict)
async def check_favorite(script_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FavoriteService(db)
    result = await svc.check_favorite(user.id, script_id)
    return {"code": 200, "data": result}


# --- Rating ---

class RateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(None, max_length=500)


@router.post("/{script_id}/rate", response_model=dict)
async def rate_script(
    script_id: int, data: RateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = RatingService(db)
    result = await svc.rate_script(user.id, script_id, data.rating, data.comment)
    return {"code": 200, "data": result}


@router.get("/{script_id}/ratings", response_model=dict)
async def get_ratings(
    script_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = RatingService(db)
    result = await svc.get_script_ratings(script_id, page, per_page)
    return {"code": 200, "data": result}