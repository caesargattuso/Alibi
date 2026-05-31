from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse

from app.core.config import settings

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/{path:path}")
async def get_storage_file(path: str):
    """Proxy endpoint for MinIO storage files."""
    if settings.STORAGE_TYPE != "minio":
        return Response(status_code=404, content="Not using MinIO storage")

    from app.services.storage.minio import MinIOStorage
    from minio.error import S3Error

    storage = MinIOStorage()
    try:
        response = storage.client.get_object(settings.MINIO_BUCKET, path)
        stat = storage.client.stat_object(settings.MINIO_BUCKET, path)
        content_type = stat.content_type or "application/octet-stream"

        def iterfile():
            try:
                for chunk in response.stream(32 * 1024):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",
                "ETag": stat.etag,
            },
        )
    except S3Error:
        return Response(status_code=404, content="File not found")