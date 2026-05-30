from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1 import auth, users, scripts, games, scenes, characters, ws, upload, achievements, leaderboards
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="AI互动游戏平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
            "error": exc.detail,
        },
    )

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(scripts.router, prefix="/api/v1")
app.include_router(games.router, prefix="/api/v1")
app.include_router(scenes.router, prefix="/api/v1")
app.include_router(characters.router, prefix="/api/v1")
app.include_router(ws.router)
app.include_router(upload.router, prefix="/api/v1")
app.include_router(achievements.router, prefix="/api/v1")
app.include_router(leaderboards.router, prefix="/api/v1")

# 静态文件服务（上传文件）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")