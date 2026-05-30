from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.exceptions import AuthError
from app.db.session import get_db
from app.schemas.user import UserUpdate, UserOut, PasswordChange
from app.services.user_service import UserService
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=dict)
async def get_me(user=Depends(get_current_user)):
    return {"code": 200, "data": UserOut.model_validate(user).model_dump()}


@router.put("/me", response_model=dict)
async def update_me(data: UserUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.update_user(user.id, data)
    return {"code": 200, "data": UserOut.model_validate(user).model_dump()}


@router.put("/me/password", response_model=dict)
async def change_password(
    data: PasswordChange, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = UserService(db)
    await svc.change_password(user.id, data.old_password, data.new_password)
    return {"code": 200, "data": {"message": "密码修改成功"}}