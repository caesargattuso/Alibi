import json as json_lib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.db.session import get_db, AsyncSessionLocal
from app.models.models import DialogLog, GameSession, GameSave, Scene, Script, User
from app.schemas.game import GameCreate, GameAction, GameMessage, GameOut, AIResponse
from app.services.ai_service import ai_service
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


@router.get("/{session_id}/history", response_model=dict)
async def get_game_history(session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "游戏不存在")

    result = await db.execute(
        select(DialogLog)
        .where(DialogLog.session_id == session_id)
        .order_by(DialogLog.created_at)
    )
    dialog_logs = result.scalars().all()

    items = []
    for log in dialog_logs:
        items.append({
            "id": log.id,
            "player_input": log.player_input,
            "content": log.content,
            "meta_data": log.meta_data,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {"code": 200, "data": items}


@router.post("/{session_id}/actions/stream")
async def stream_action(session_id: int, data: GameMessage, user: User = Depends(get_current_user)):
    # Verify session ownership
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id, GameSession.user_id == user.id)
        )
        session = result.scalar()
        if not session:
            raise HTTPException(404, "游戏不存在")
        script = await db.get(Script, session.script_id)
        current_scene = await db.get(Scene, session.current_scene_id) if session.current_scene_id else None
        # Eagerly detach data we need
        session_id_val = session.id
        script_obj = script
        scene_obj = current_scene
        history = await GameService(db)._get_dialog_history(session_id, limit=5)

    input_text = data.choice_id or data.message or ""
    complete_result = {}

    async def event_stream():
        nonlocal complete_result
        try:
            async for event_type, event_data in ai_service.generate_story_stream(
                session, script_obj, scene_obj, input_text, history
            ):
                if event_type == "complete":
                    complete_result = event_data
                sse_data = json_lib.dumps(event_data, ensure_ascii=False)
                yield f"event: {event_type}\ndata: {sse_data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json_lib.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        # Persist the result after streaming completes
        if complete_result:
            try:
                async with AsyncSessionLocal() as save_db:
                    svc = GameService(save_db)
                    save_session = await svc.get_game(session_id_val, user.id)
                    if save_session:
                        await svc.save_action_result(save_session, input_text, complete_result)
                        await save_db.commit()
            except Exception:
                pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/generate-image", response_model=dict)
async def generate_scene_image(
    session_id: int,
    size: str = "1024x576",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "游戏不存在")

    current_scene = await db.get(Scene, session.current_scene_id) if session.current_scene_id else None
    script = await db.get(Script, session.script_id)

    prompt = f"游戏场景插画，{script.genre if script else ''}风格"
    if current_scene:
        prompt = f"游戏场景插画：{current_scene.name}，{current_scene.description[:200]}，{script.genre if script else ''}风格，暗色调，氛围感"

    image_url = await ai_service.generate_image(prompt, size)
    if not image_url:
        raise HTTPException(500, "图片生成失败")

    # Download and store in object storage
    from app.services.file_service import file_service
    stored_url = await file_service.store_ai_image(
        script_id=session.script_id,
        session_id=session_id,
        image_url=image_url,
        image_type="scene",
    )

    return {"code": 200, "data": {"url": stored_url, "prompt": prompt}}


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
    session_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    reason = "abandoned"
    svc = GameService(db)
    session = await svc.end_game(session_id, user.id, reason)
    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}


@router.get("", response_model=dict)
async def list_games(
    page: int = 1,
    per_page: int = 10,
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
    page: int = 1,
    per_page: int = 50,
    type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GameService(db)
    result = await svc.get_dialog_history_paginated(session_id, user.id, page, per_page, type)
    return {"code": 200, "data": result}


@router.post("/{session_id}/saves", response_model=dict)
async def create_save(
    session_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save current game state."""
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "游戏不存在")

    save_name = data.get("save_name", f"存档 {datetime.now(timezone.utc).strftime('%m/%d %H:%M')}")

    # Collect all dialog logs for this session
    result = await db.execute(
        select(DialogLog).where(DialogLog.session_id == session_id).order_by(DialogLog.created_at)
    )
    dialog_logs = result.scalars().all()
    dialog_data = [
        {
            "id": log.id,
            "type": log.type,
            "content": log.content,
            "player_input": log.player_input,
            "meta_data": log.meta_data,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in dialog_logs
    ]

    save = GameSave(
        session_id=session_id,
        save_name=save_name,
        save_data={
            "player_stats": session.player_stats,
            "npc_states": session.npc_states,
            "story_flags": session.story_flags,
            "game_phase": session.game_phase,
            "game_time": session.game_time,
            "current_scene_id": session.current_scene_id,
            "alive_count": session.alive_count,
            "dialog_logs": dialog_data,
        },
    )
    db.add(save)
    await db.flush()

    return {
        "code": 200,
        "data": {
            "id": save.id,
            "save_name": save.save_name,
            "created_at": save.created_at.isoformat() if save.created_at else None,
        },
    }


@router.get("/{session_id}/saves", response_model=dict)
async def list_saves(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all saves for a game session."""
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "游戏不存在")

    result = await db.execute(
        select(GameSave)
        .where(GameSave.session_id == session_id)
        .order_by(GameSave.created_at.desc())
    )
    saves = result.scalars().all()

    return {
        "code": 200,
        "data": [
            {
                "id": s.id,
                "save_name": s.save_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in saves
        ],
    }


@router.post("/{session_id}/saves/{save_id}/load", response_model=dict)
async def load_save(
    session_id: int,
    save_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Load a saved game state."""
    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "游戏不存在")

    save = await db.get(GameSave, save_id)
    if not save or save.session_id != session_id:
        raise HTTPException(404, "存档不存在")

    data = save.save_data

    # Restore game session state
    session.player_stats = data.get("player_stats", {})
    session.npc_states = data.get("npc_states", {})
    session.story_flags = data.get("story_flags", {})
    session.game_phase = data.get("game_phase")
    session.game_time = data.get("game_time")
    session.current_scene_id = data.get("current_scene_id")
    session.alive_count = data.get("alive_count", 0)
    session.status = "active"

    # Delete dialog logs after the save point and re-create from save data
    await db.execute(
        DialogLog.__table__.delete().where(DialogLog.session_id == session_id)
    )
    for log_data in data.get("dialog_logs", []):
        log = DialogLog(
            session_id=session_id,
            type=log_data.get("type", "narration"),
            content=log_data.get("content", ""),
            player_input=log_data.get("player_input"),
            meta_data=log_data.get("meta_data"),
        )
        db.add(log)

    await db.flush()

    return {"code": 200, "data": GameOut.model_validate(session).model_dump()}
