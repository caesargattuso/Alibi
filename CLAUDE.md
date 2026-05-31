# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alibi is an Chinese AI-driven interactive text adventure game platform. Players interact with AI-generated narratives through choices and free-text input.

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16
- **Frontend**: React 19 + TypeScript + Vite + Ant Design + Tailwind CSS + Zustand
- **AI**: SiliconFlow API (OpenAI-compatible) with tool_calls structured output
- **Storage**: MinIO object storage (S3-compatible) with local fallback
- **Deploy**: Docker Compose (api, web, db, redis, minio)

## Common Commands

### Backend

```bash
cd backend
pip install -e ".[dev]"          # Install with dev dependencies
uvicorn app.main:app --reload     # Run dev server
pytest                            # Run tests (async mode auto)
ruff check .                      # Lint
ruff format .                     # Format
```

### Frontend

```bash
cd frontend
npm install
npm run dev                       # Dev server (Vite, port 5173)
npm run build                     # Production build (tsc + vite)
npm run lint                      # ESLint
```

### Docker Compose (Full Stack)

```bash
docker compose up -d --build      # Build and start all services
docker compose up -d --build api  # Rebuild only backend
docker compose up -d --build web  # Rebuild only frontend
```

Services: api (8000), web (3000), db (5432), redis (6379), minio (9000/9001)

## Architecture

### Backend Structure

```
backend/app/
├── api/v1/           # FastAPI routers: auth, users, scripts, games, scenes,
│                     #   characters, achievements, leaderboards, storage, ws, upload
├── core/             # Settings (pydantic-settings), security, exceptions
├── db/               # AsyncSessionLocal, Base declarative base
├── models/           # SQLAlchemy ORM models (User, Script, Scene, Character, GameSession, etc.)
├── schemas/          # Pydantic request/response models
├── services/         # Business logic layer
│   ├── ai_service.py         # SiliconFlow streaming with tool_calls JSON extraction
│   ├── storage/              # Storage abstraction (local/minio)
│   │   ├── base.py           # StorageBackend ABC
│   │   ├── local.py          # Local filesystem storage
│   │   └── minio.py          # MinIO S3-compatible storage
│   └── file_service.py       # Uses get_storage() factory
└── websocket/        # WebSocket connection manager
```

### Storage Abstraction

`STORAGE_TYPE` env var controls backend (`local` or `minio`). `get_storage()` returns a singleton `StorageBackend` instance. Both backends expose: `save()`, `delete()`, `exists()`, `get_url()`, `download_from_url()`.

- Local: files under `./uploads/`, served via `/uploads/` static mount
- MinIO: files in `alibi-game-assets` bucket, accessed via `/storage/` proxy endpoint (`backend/app/api/v1/storage.py`)

### AI Streaming

`backend/app/services/ai_service.py::generate_story_stream()` uses SiliconFlow's tool_calls streaming. It runs a JSON state machine to extract narration text in real-time from the streaming JSON, yielding `("narration_chunk", {"text": "..."})` events. Escape sequences (`\n`, `\t`, `\r`) are handled during streaming.

### Frontend Structure

```
frontend/src/
├── pages/            # Home, ScriptDetail, Game, Auth, Profile
├── services/         # API clients (axios with JWT interceptors)
├── stores/           # Zustand stores (authStore, gameStore)
├── types/            # TypeScript type definitions
└── utils/            # Pathfinding (A*), offline (IndexedDB)
```

### Game State Flow

1. Frontend calls `gameService.sendActionStream()` → SSE streaming
2. Backend `ai_service.generate_story_stream()` yields narration chunks
3. Frontend `gameStore.appendNarration()` appends text to current turn
4. On `complete` event, `gameStore.completeTurn()` finalizes with choices
5. Choices render as buttons; custom input also triggers `handleAction()`

## Key Configuration

Backend settings in `backend/app/core/config.py` (loaded from `.env`):
- `STORAGE_TYPE`: `local` or `minio`
- `SILICONFLOW_API_KEY`, `SILICONFLOW_BASE_URL`, `SILICONFLOW_MODEL`
- `DATABASE_URL`, `REDIS_URL`
- `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

Frontend API base URL: `import.meta.env.VITE_API_URL` or `http://localhost:8000/api/v1`

## Design Docs

Reference docs in `/docs/`:
- `01-游戏概述与架构设计.md`
- `03-前后端API与技术实现.md`
- `07-剧本互动功能设计.md`
- `08-WebSocket与实时通信设计.md`

## Development Workflow

### Feature Development

1. **Write design doc first** in `docs/{NN}-{feature-name}.md` before writing any code
2. **Implement** the feature based on the design doc
3. **Commit** with a descriptive message

### Bug Fixes / Refactors

1. **Record in `docs/records.md`** (or create it) with a brief note of what was fixed/refactored and why
2. **Commit** the code change

This applies to all changes in this repository.
