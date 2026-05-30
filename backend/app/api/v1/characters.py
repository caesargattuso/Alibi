from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.schemas.character import CharacterData, RelationshipsData
from app.services.character_service import CharacterService

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("/{character_id}")
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = CharacterService(db)
    character = await svc.get_character(character_id)
    return {"code": 200, "data": CharacterData.model_validate(character).model_dump()}


@router.get("/{character_id}/relationships")
async def get_relationships(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = CharacterService(db)
    relationships = await svc.get_relationships(character_id)
    return {"code": 200, "data": relationships}
