from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, AuthError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.models import User
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, username: str, email: str, password: str) -> User:
        # Check uniqueness
        existing = await self.db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            raise ValidationError("用户名已存在", "username")
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValidationError("邮箱已注册", "email")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, username_or_email: str, password: str) -> User:
        stmt = select(User).where(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("用户名或密码错误")
        if user.status != "active":
            raise AuthError("账户已被禁用")
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("用户")
        if data.username is not None:
            user.username = data.username
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        if data.preferences is not None:
            user.preferences = data.preferences
        await self.db.flush()
        return user