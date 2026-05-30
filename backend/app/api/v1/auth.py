from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserRegister, UserLogin, TokenRefresh, UserOut, TokenOut
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _make_tokens(user_id: int) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=3600,
    )


@router.post("/register", response_model=dict)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.create_user(data.username, data.email, data.password)
    tokens = _make_tokens(user.id)
    return {
        "code": 200,
        "data": {"user_id": user.id, "username": user.username, **tokens.model_dump()},
    }


@router.post("/login", response_model=dict)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.authenticate(data.username_or_email, data.password)
    tokens = _make_tokens(user.id)
    return {
        "code": 200,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            **tokens.model_dump(),
        },
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(data: TokenRefresh):
    user_id = decode_token(data.refresh_token, expected_type="refresh")
    tokens = _make_tokens(user_id)
    return {"code": 200, "data": tokens.model_dump()}