from typing import Any

from pydantic import BaseModel


class CharacterData(BaseModel):
    id: int
    script_id: int
    character_key: str
    name: str
    display_name: str | None = None
    role_type: str
    avatar_url: str | None = None
    sprites: dict[str, str] | None = None
    appearance: str | None = None
    personality: dict[str, Any] | None = None
    background: str | None = None
    stats: dict[str, Any] | None = None
    dialogue_style: str | None = None

    model_config = {"from_attributes": True}


class Relationship(BaseModel):
    target_id: int
    target_name: str
    target_key: str
    relation_type: str
    description: str | None = None
    attitude: str
    intensity: int


class RelationshipsData(BaseModel):
    character_id: int
    character_name: str
    relationships: list[Relationship]
