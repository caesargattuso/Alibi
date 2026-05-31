from app.services.storage.base import StorageBackend
from app.core.config import settings

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Get singleton storage backend instance based on STORAGE_TYPE config."""
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_TYPE == "minio":
            try:
                from app.services.storage.minio import MinIOStorage
                _storage_instance = MinIOStorage()
            except Exception:
                # Fallback to local if MinIO is unavailable
                import logging
                logging.warning("MinIO unavailable, falling back to local storage")
                from app.services.storage.local import LocalStorage
                _storage_instance = LocalStorage()
        else:
            from app.services.storage.local import LocalStorage
            _storage_instance = LocalStorage()
    return _storage_instance