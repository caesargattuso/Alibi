from datetime import datetime

from pydantic import BaseModel, Field


class ScriptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    genre: str
    difficulty: str = "normal"
    setting: dict
    rules: dict | None = None
    endings: dict | None = None
    tags: list[str] | None = None
    cover_image: str | None = None
    banner_image: str | None = None


class ScriptUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    genre: str | None = None
    difficulty: str | None = None
    setting: dict | None = None
    rules: dict | None = None
    endings: dict | None = None
    tags: list[str] | None = None
    cover_image: str | None = None
    banner_image: str | None = None
    status: str | None = None


class ScriptOut(BaseModel):
    id: int
    title: str
    description: str | None
    genre: str
    difficulty: str
    author_id: int
    cover_image: str | None
    rating: float
    play_count: int
    status: str
    tags: list[str] | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScriptDetailOut(ScriptOut):
    banner_image: str | None
    setting: dict
    rules: dict | None
    endings: dict | None
    rating_count: int