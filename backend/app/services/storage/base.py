from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save(self, path: str, data: bytes | BinaryIO, content_type: str = "application/octet-stream") -> str:
        """Save data to storage and return the access URL."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file at path. Returns True if successful."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists at path."""
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Get access URL for file at path."""
        pass

    @abstractmethod
    async def download_from_url(self, url: str, dest_path: str) -> str:
        """Download from external URL and save to storage. Returns access URL."""
        pass