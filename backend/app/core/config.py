from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI互动游戏平台"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-secure-random-string"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_game"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI - SiliconFlow (OpenAI compatible)
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "deepseek-ai/DeepSeek-V4-Pro"
    AI_MAX_TOKENS: int = 4096
    AI_TIMEOUT: int = 60
    AI_MAX_RETRIES: int = 3
    AI_MAX_CONCURRENCY: int = 10
    SILICONFLOW_IMAGE_MODEL: str = "stabilityai/stable-diffusion-3-5-large"

    # JWT
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # 限流
    RATE_LIMIT_API: str = "100/minute"
    RATE_LIMIT_AI: str = "30/minute"

    # 文件存储
    STORAGE_TYPE: str = "local"
    UPLOAD_DIR: str = "./uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()