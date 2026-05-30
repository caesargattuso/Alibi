from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SceneData(BaseModel):
    id: int
    script_id: int
    scene_key: str
    name: str
    description: str | None = None
    background_image: str | None = None
    background_music: str | None = None
    connected_scenes: list[dict[str, Any]] | None = None
    on_enter: dict[str, Any] | None = None
    on_exit: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class MapData(BaseModel):
    width: int
    height: int
    grid_size: int
    layers: list[dict[str, Any]]
    walkable_areas: list[dict[str, Any]]
    obstacles: list[dict[str, Any]]
    spawn_points: list[dict[str, Any]]
    lighting: dict[str, Any] | None = None


class Interactable(BaseModel):
    id: str
    name: str
    type: str
    position: list[int]
    icon: str | None = None
    description: str | None = None
    actions: list[str] = []
    conditions: dict[str, list[dict[str, Any]]] | None = None
    npc_id: str | None = None
    target_scene: str | None = None
    target_position: list[int] | None = None


class InteractRequest(BaseModel):
    session_id: int
    interactable_id: str
    action_id: str


class InteractEffect(BaseModel):
    type: str
    target: str
    value: Any = None
    position: list[int] | None = None


class AITrigger(BaseModel):
    should_generate: bool
    context: str


class InteractResult(BaseModel):
    success: bool
    message: str
    effects: list[InteractEffect]
    ai_trigger: AITrigger
