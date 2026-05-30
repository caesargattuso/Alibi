from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.game import GameCreate, GameAction, GameMessage, GameOut, AIResponse
from app.services.game_service import GameService

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=dict)
async def create_game(data: GameCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = GameService(db)
    session = await svc.create_game(user.id, data.script_id, data.player_name)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.get("/{session_id}", response_model=dict)
async def get_game(session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = GameService(db)
    session = await svc.get_game(session_id, user.id)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.post("/{session_id}/actions", response_model=dict)
async def process_action(
    session_id: int, data: GameAction, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = GameService(db)
    ai_response = await svc.process_action(session_id, user.id, data.input or "")
    return {"code": 200, "data": ai_response}


@router.post("/{session_id}/messages", response_model=dict)
async def send_message(
    session_id: int, data: GameMessage, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = GameService(db)
    ai_response = await svc.process_action(session_id, user.id, data.message or "")
    return {"code": 200, "data": ai_response}


@router.post("/{session_id}/pause", response_model=dict)
async def pause_game(session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = GameService(db)
    session = await svc.pause_game(session_id, user.id)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.post("/{session_id}/resume", response_model=dict)
async def resume_game(session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = GameService(db)
    session = await svc.resume_game(session_id, user.id)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.post("/{session_id}/end", response_model=dict)
async def end_game(
    session_id: int, data: dict = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    reason = (data or {}).get("reason", "abandoned")
    svc = GameService(db)
    session = await svc.end_game(session_id, user.id, reason)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.get("", response_model=dict)
async def list_games(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GameService(db)
    result = await svc.list_user_games(user.id, page, per_page, status)
    return {"code": 200, "data": result}


@router.get("/{session_id}/messages", response_model=dict)
async def get_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GameService(db)
    result = await svc.get_dialog_history_paginated(session_id, user.id, page, per_page, type)
    return {"code": 200, "data": result}