import httpx
from pathlib import Path
from typing import BinaryIO

import aiofiles

from app.services.storage.base import StorageBackend
from app.core.config import settings


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, path: str, data: bytes | BinaryIO, content_type: str = "application/octet-stream") -> str:
        full_path = self.upload_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, bytes):
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(data)
        else:
            content = data.read()
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)

        return f"/uploads/{path}"

    async def delete(self, path: str) -> bool:
        full_path = self.upload_dir / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        return (self.upload_dir / path).exists()

    async def get_url(self, path: str) -> str:
        return f"/uploads/{path}"

    async def download_from_url(self, url: str, dest_path: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(url)
            response.raise_for_status()
            return await self.save(dest_path, response.content)