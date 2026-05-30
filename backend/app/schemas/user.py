from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    avatar_url: str | None = None
    preferences: dict | None = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    avatar_url: str | None
    preferences: dict | None
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)