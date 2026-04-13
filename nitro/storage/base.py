"""
Abstract base interface and data types for the Nitro storage system.

All storage backends must subclass ``StorageBackend`` and implement the
core file operations. This ensures backends are interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FileMetadata:
    """Metadata about a stored file.

    Attributes:
        key: Unique storage key / path (e.g. ``"uploads/photo.jpg"``).
        size: File size in bytes.
        content_type: MIME type.
        created_at: When the file was stored.
        updated_at: When the file was last updated.
        checksum: Optional content hash (e.g. MD5, SHA-256).
        metadata: Arbitrary key-value metadata.
    """

    key: str
    size: int = 0
    content_type: str = "application/octet-stream"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    checksum: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict."""
        d: Dict[str, Any] = {
            "key": self.key,
            "size": self.size,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.checksum:
            d["checksum"] = self.checksum
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class StorageResult:
    """Result of a storage operation.

    Attributes:
        success: Whether the operation succeeded.
        key: Storage key of the affected file.
        error: Error description on failure.
        metadata: File metadata (populated on successful put/info).
    """

    success: bool
    key: str = ""
    error: str = ""
    metadata: Optional[FileMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.key:
            d["key"] = self.key
        if self.error:
            d["error"] = self.error
        if self.metadata:
            d["metadata"] = self.metadata.to_dict()
        return d


class StorageBackend(ABC):
    """Abstract base class for file storage backends.

    Subclass this and implement the abstract methods to create a custom
    storage backend.

    Args:
        prefix: Optional key prefix applied to all operations
            (e.g. ``"uploads/"``).
    """

    def __init__(self, *, prefix: str = ""):
        self.prefix = prefix

    def _full_key(self, key: str) -> str:
        """Prepend the configured prefix to a key."""
        if self.prefix:
            return f"{self.prefix}{key}"
        return key

    @abstractmethod
    async def put(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResult:
        """Store file content under the given key.

        If a file already exists at that key, it is overwritten.
        """

    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        """Retrieve file content by key. Returns ``None`` if not found."""

    @abstractmethod
    async def delete(self, key: str) -> StorageResult:
        """Delete a file by key."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether a file exists at the given key."""

    @abstractmethod
    async def info(self, key: str) -> Optional[FileMetadata]:
        """Get metadata for a file. Returns ``None`` if not found."""

    @abstractmethod
    async def list_files(
        self, prefix: str = "", *, limit: int = 1000
    ) -> List[FileMetadata]:
        """List files matching a key prefix.

        Args:
            prefix: Filter files whose key starts with this string.
            limit: Maximum number of results.
        """

    async def copy(self, src_key: str, dst_key: str) -> StorageResult:
        """Copy a file from one key to another. Default: get + put."""
        content = await self.get(src_key)
        if content is None:
            return StorageResult(success=False, key=dst_key, error="Source not found")
        meta = await self.info(src_key)
        return await self.put(
            dst_key,
            content,
            content_type=meta.content_type if meta else "application/octet-stream",
            metadata=meta.metadata if meta else None,
        )

    async def move(self, src_key: str, dst_key: str) -> StorageResult:
        """Move a file from one key to another. Default: copy + delete."""
        result = await self.copy(src_key, dst_key)
        if result.success:
            await self.delete(src_key)
        return result

    async def close(self) -> None:
        """Clean up resources. Default: no-op."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(prefix={self.prefix!r})"
