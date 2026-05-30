from datetime import datetime

from pydantic import BaseModel, Field


class GameCreate(BaseModel):
    script_id: int
    player_name: str = Field(min_length=1, max_length=100)


class GameAction(BaseModel):
    action_type: str
    target_id: str | None = None
    target_position: dict | None = None
    input: str | None = None


class GameMessage(BaseModel):
    message: str | None = None
    choice_id: str | None = None


class GameOut(BaseModel):
    id: int
    script_id: int
    current_scene_id: int | None
    player_name: str | None
    player_stats: dict
    npc_states: dict
    story_flags: dict
    game_phase: str | None
    game_time: str | None
    alive_count: int
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AIResponse(BaseModel):
    narration: str = ""
    dialogs: list[dict] = Field(default_factory=list)
    choices: list[dict] = Field(default_factory=list)
    scene_change: dict | None = None
    character_movements: list[dict] = Field(default_factory=list)
    stat_changes: list[dict] = Field(default_factory=list)
    flags_set: list[dict] = Field(default_factory=list)
    is_game_over: bool = False
    ending: str | None = None