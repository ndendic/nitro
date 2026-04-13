"""
In-memory storage backend — ideal for testing and development.

Stores files in a plain ``dict``. No persistence across restarts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .base import FileMetadata, StorageBackend, StorageResult


@dataclass
class _StoredFile:
    """Internal representation of a stored file."""

    content: bytes
    metadata: FileMetadata


class MemoryBackend(StorageBackend):
    """In-memory file storage backend.

    Files are stored in a dict keyed by their full storage key.
    Useful for testing and rapid prototyping.

    Supports an optional ``fail`` flag to simulate errors.

    Example::

        backend = MemoryBackend()
        result = await backend.put("test.txt", b"hello")
        assert result.success
        assert await backend.get("test.txt") == b"hello"

    Testing with simulated failures::

        backend = MemoryBackend(fail=True)
        result = await backend.put("test.txt", b"hello")
        assert not result.success
    """

    def __init__(self, *, prefix: str = "", fail: bool = False):
        super().__init__(prefix=prefix)
        self.fail = fail
        self._files: Dict[str, _StoredFile] = {}

    async def put(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResult:
        if self.fail:
            return StorageResult(
                success=False, key=key, error="Simulated storage failure"
            )
        full_key = self._full_key(key)
        now = datetime.now(timezone.utc)
        checksum = hashlib.sha256(content).hexdigest()
        file_meta = FileMetadata(
            key=full_key,
            size=len(content),
            content_type=content_type,
            created_at=now,
            updated_at=now,
            checksum=checksum,
            metadata=metadata or {},
        )
        self._files[full_key] = _StoredFile(content=content, metadata=file_meta)
        return StorageResult(success=True, key=full_key, metadata=file_meta)

    async def get(self, key: str) -> Optional[bytes]:
        full_key = self._full_key(key)
        stored = self._files.get(full_key)
        return stored.content if stored else None

    async def delete(self, key: str) -> StorageResult:
        full_key = self._full_key(key)
        if full_key in self._files:
            del self._files[full_key]
            return StorageResult(success=True, key=full_key)
        return StorageResult(success=False, key=full_key, error="File not found")

    async def exists(self, key: str) -> bool:
        return self._full_key(key) in self._files

    async def info(self, key: str) -> Optional[FileMetadata]:
        full_key = self._full_key(key)
        stored = self._files.get(full_key)
        return stored.metadata if stored else None

    async def list_files(
        self, prefix: str = "", *, limit: int = 1000
    ) -> List[FileMetadata]:
        full_prefix = self._full_key(prefix)
        results: List[FileMetadata] = []
        for fk, stored in sorted(self._files.items()):
            if fk.startswith(full_prefix):
                results.append(stored.metadata)
                if len(results) >= limit:
                    break
        return results

    def reset(self) -> None:
        """Clear all stored files."""
        self._files.clear()

    @property
    def file_count(self) -> int:
        """Number of files currently stored."""
        return len(self._files)

    def find(self, **kwargs: str) -> List[FileMetadata]:
        """Find files matching metadata key-value pairs."""
        results: List[FileMetadata] = []
        for stored in self._files.values():
            match = all(
                stored.metadata.metadata.get(k) == v for k, v in kwargs.items()
            )
            if match:
                results.append(stored.metadata)
        return results
