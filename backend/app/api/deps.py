from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise AuthError("无效的认证头")
    token = authorization[7:]
    user_id = decode_token(token, expected_type="access")
    from app.services.user_service import UserService

    svc = UserService(db)
    user = await svc.get_user_by_id(user_id)
    if not user:
        raise AuthError("用户不存在")
    return user