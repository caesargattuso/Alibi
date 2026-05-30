from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User
from app.schemas.scene import InteractRequest, SceneData
from app.services.scene_service import SceneService

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.get("/{scene_id}")
async def get_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = SceneService(db)
    scene = await svc.get_scene(scene_id)
    return {"code": 200, "data": SceneData.model_validate(scene).model_dump()}


@router.get("/{scene_id}/map")
async def get_scene_map(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = SceneService(db)
    map_data = await svc.get_map_data(scene_id)
    return {"code": 200, "data": map_data}


@router.get("/{scene_id}/interactables")
async def get_interactables(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = SceneService(db)
    interactables = await svc.get_interactables(scene_id)
    return {"code": 200, "data": {"interactables": interactables}}


@router.post("/{scene_id}/interact")
async def execute_interaction(
    scene_id: int,
    request: InteractRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = SceneService(db)
    result = await svc.execute_interaction(
        scene_id, request.session_id, request.interactable_id, request.action_id
    )
    return {"code": 200, "data": result}
