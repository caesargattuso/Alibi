from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptOut, ScriptDetailOut
from app.services.script_service import ScriptService

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