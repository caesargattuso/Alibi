import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError


class FileService:
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/ogg", "audio/wav"}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB

    async def upload_image(self, file: UploadFile) -> dict:
        content_type = file.content_type or ""
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValidationError(f"不支持的图片格式: {content_type}", "file")

        content = await file.read()
        if len(content) > self.MAX_IMAGE_SIZE:
            raise ValidationError("图片大小不能超过5MB", "file")

        filename = self._generate_filename(file.filename or "image.jpg")
        path = f"images/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{filename}"
        url = self._save(content, path)

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
        path = f"audio/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{filename}"
        url = self._save(content, path)

        return {
            "url": url,
            "filename": filename,
            "size": len(content),
            "content_type": content_type,
        }

    def _generate_filename(self, original: str) -> str:
        ext = Path(original).suffix or ".bin"
        return f"{uuid.uuid4().hex[:12]}{ext}"

    def _save(self, content: bytes, path: str) -> str:
        upload_dir = Path(settings.UPLOAD_DIR)
        full_path = upload_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return f"/uploads/{path}"


file_service = FileService()
