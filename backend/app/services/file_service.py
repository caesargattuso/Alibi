import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.services.storage import get_storage


class FileService:
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/ogg", "audio/wav"}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.storage = get_storage()

    async def upload_image(self, file: UploadFile) -> dict:
        content_type = file.content_type or ""
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValidationError(f"不支持的图片格式: {content_type}", "file")

        content = await file.read()
        if len(content) > self.MAX_IMAGE_SIZE:
            raise ValidationError("图片大小不能超过5MB", "file")

        filename = self._generate_filename(file.filename or "image.jpg")
        path = f"uploads/images/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{filename}"
        url = await self.storage.save(path, content, content_type)

        return {
            "url": url,
            "filename": filename,
            "size": len(content),
            "content_type": content_type,
        }

    async def upload_audio(self, file: UploadFile) -> dict:
        content_type = file.content_type or ""
        if content_type not in self.ALLOWED_AUDIO_TYPES:
            raise ValidationError(f"不支持的音频格式: {content_type}", "file")

        content = await file.read()
        if len(content) > self.MAX_AUDIO_SIZE:
            raise ValidationError("音频大小不能超过10MB", "file")

        filename = self._generate_filename(file.filename or "audio.mp3")
        path = f"uploads/audio/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{filename}"
        url = await self.storage.save(path, content, content_type)

        return {
            "url": url,
            "filename": filename,
            "size": len(content),
            "content_type": content_type,
        }

    # --- Game-specific upload methods ---

    async def upload_script_cover(self, script_id: int, file: UploadFile) -> str:
        content = await file.read()
        ext = Path(file.filename or "cover.png").suffix or ".png"
        path = f"scripts/{script_id}/cover{ext}"
        return await self.storage.save(path, content, file.content_type or "image/png")

    async def upload_scene_background(self, script_id: int, scene_key: str, file: UploadFile) -> str:
        content = await file.read()
        ext = Path(file.filename or "bg.png").suffix or ".png"
        path = f"scripts/{script_id}/scenes/{scene_key}/bg{ext}"
        return await self.storage.save(path, content, file.content_type or "image/png")

    async def upload_character_avatar(self, script_id: int, character_key: str, file: UploadFile) -> str:
        content = await file.read()
        ext = Path(file.filename or "avatar.png").suffix or ".png"
        path = f"scripts/{script_id}/characters/{character_key}/avatar{ext}"
        return await self.storage.save(path, content, file.content_type or "image/png")

    async def store_ai_image(self, script_id: int, session_id: int, image_url: str, image_type: str = "scene") -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = f"scripts/{script_id}/generated/{session_id}/{image_type}_{timestamp}.png"
        return await self.storage.download_from_url(image_url, path)

    def _generate_filename(self, original: str) -> str:
        ext = Path(original).suffix or ".bin"
        return f"{uuid.uuid4().hex[:12]}{ext}"


file_service = FileService()