import io
from typing import BinaryIO

import httpx
from minio import Minio
from minio.error import S3Error

from app.services.storage.base import StorageBackend
from app.core.config import settings


class MinIOStorage(StorageBackend):
    """MinIO/S3-compatible storage backend."""

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error:
            pass

    async def save(self, path: str, data: bytes | BinaryIO, content_type: str = "application/octet-stream") -> str:
        try:
            if isinstance(data, bytes):
                data_stream = io.BytesIO(data)
                size = len(data)
            else:
                data_stream = data
                data_stream.seek(0, 2)
                size = data_stream.tell()
                data_stream.seek(0)

            self.client.put_object(
                bucket_name=self.bucket,
                object_name=path,
                data=data_stream,
                length=size,
                content_type=content_type,
            )
            return f"/storage/{path}"
        except S3Error as e:
            raise RuntimeError(f"MinIO save failed: {e}")

    async def delete(self, path: str) -> bool:
        try:
            self.client.remove_object(self.bucket, path)
            return True
        except S3Error:
            return False

    async def exists(self, path: str) -> bool:
        try:
            self.client.stat_object(self.bucket, path)
            return True
        except S3Error:
            return False

    async def get_url(self, path: str) -> str:
        return f"/storage/{path}"

    async def download_from_url(self, url: str, dest_path: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/png")
            return await self.save(dest_path, response.content, content_type)