from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, BigInteger, SmallInteger, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    scripts = relationship("Script", back_populates="author", lazy="selectin")
    game_sessions = relationship("GameSession", back_populates="user", lazy="noload")
    favorites = relationship("ScriptFavorite", back_populates="user", lazy="noload")
    ratings = relationship("ScriptRating", back_populates="user", lazy="noload")
    achievements = relationship("UserAchievement", back_populates="user", lazy="noload")


class Script(TimestampMixin, Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="normal")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(500))
    banner_image: Mapped[str | None] = mapped_column(String(500))
    setting: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rules: Mapped[dict | None] = mapped_column(JSONB)
    endings: Mapped[dict | None] = mapped_column(JSONB)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    author = relationship("User", back_populates="scripts")
    scenes = relationship("Scene", back_populates="script", lazy="selectin", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="script", lazy="selectin", cascade="all, delete-orphan")
    favorites_rel = relationship("ScriptFavorite", back_populates="script", lazy="noload", cascade="all, delete-orphan")
    ratings_rel = relationship("ScriptRating", back_populates="script", lazy="noload", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    scene_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    background_image: Mapped[str | None] = mapped_column(String(500))
    background_music: Mapped[str | None] = mapped_column(String(500))
    map_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    connected_scenes: Mapped[dict | None] = mapped_column(JSONB)
    initial_npcs: Mapped[dict | None] = mapped_column(JSONB)
    entry_conditions: Mapped[dict | None] = mapped_column(JSONB)
    on_enter: Mapped[dict | None] = mapped_column(JSONB)
    on_exit: Mapped[dict | None] = mapped_column(JSONB)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    script = relationship("Script", back_populates="scenes")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    character_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role_type: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    sprites: Mapped[dict | None] = mapped_column(JSONB)
    appearance: Mapped[str | None] = mapped_column(Text)
    personality: Mapped[dict | None] = mapped_column(JSONB)
    background: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict | None] = mapped_column(JSONB)
    relationships: Mapped[dict | None] = mapped_column(JSONB)
    secrets: Mapped[dict | None] = mapped_column(JSONB)
    dialogue_style: Mapped[str | None] = mapped_column(Text)
    ai_prompt: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    script = relationship("Script", back_populates="characters")


class GameSession(TimestampMixin, Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"), nullable=False)
    current_scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"))
    player_name: Mapped[str | None] = mapped_column(String(100))
    player_stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    npc_states: Mapped[dict] = mapped_column(JSONB, default=dict)
    story_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    game_phase: Mapped[str | None] = mapped_column(String(50))
    game_time: Mapped[str | None] = mapped_column(String(100))
    alive_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_ending: Mapped[str | None] = mapped_column(String(100))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="game_sessions")
    dialogs = relationship("DialogLog", back_populates="session", lazy="noload", cascade="all, delete-orphan")


class DialogLog(Base):
    __tablename__ = "dialog_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"))
    character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSONB)
    player_input: Mapped[str | None] = mapped_column(Text)
    ai_raw_response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("GameSession", back_populates="dialogs")


class ScriptFavorite(Base):
    __tablename__ = "script_favorites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="favorites")
    script = relationship("Script", back_populates="favorites_rel")


class ScriptRating(TimestampMixin, Base):
    __tablename__ = "script_ratings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="ratings")
    script = relationship("Script", back_populates="ratings_rel")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(500))
    condition_type: Mapped[str | None] = mapped_column(String(50))
    condition_data: Mapped[dict | None] = mapped_column(JSONB)
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user_achievements = relationship("UserAchievement", back_populates="achievement", lazy="noload")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")