from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import GameSession
from app.websocket.manager import manager
from app.websocket.handlers import MessageHandler

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/v1/games/{session_id}")
async def game_websocket(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = decode_token(token, expected_type="access")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    session = await db.get(GameSession, session_id)
    if not session or session.user_id != user_id:
        await websocket.close(code=4003, reason="Forbidden")
        return

    await manager.connect(websocket, session_id, user_id)

    await manager.send_to_user({
        "type": "connected",
        "data": {"session_id": session_id, "user_id": user_id},
    }, user_id)

    handler = MessageHandler(db)

    try:
        while True:
            data = await websocket.receive_json()
            response = await handler.handle(websocket, data, session_id, user_id)
            if response:
                await manager.send_to_user(response, user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, user_id)
    except Exception:
        manager.disconnect(websocket, session_id, user_id)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
