"""
Storage backend abstraction for the Nitro uploads module.

Provides an ABC for storage backends plus local filesystem and in-memory
implementations. The interface is intentionally simpler than nitro.storage
because uploads are write-once objects — we don't need list, copy, or move.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


class StorageBackend(ABC):
    """Abstract base class for upload storage backends.

    Implement this to create custom storage backends (S3, GCS, Azure, etc.).
    """

    @abstractmethod
    async def save(self, file_data: bytes, filename: str) -> str:
        """Persist file data and return the stored path / key.

        Args:
            file_data: Raw bytes to store.
            filename: Desired storage filename or key.

        Returns:
            The path/key under which the file was stored.
        """

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete a stored file.

        Args:
            path: Path/key returned by ``save()``.

        Returns:
            True if deleted, False if the file did not exist.
        """

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check whether a file exists at the given path/key.

        Args:
            path: Path/key returned by ``save()``.

        Returns:
            True if the file exists.
        """

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Return a URL (or URI) for accessing the stored file.

        Args:
            path: Path/key returned by ``save()``.

        Returns:
            A URL string.
        """

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """Retrieve the raw bytes of a stored file.

        Args:
            path: Path/key returned by ``save()``.

        Returns:
            File bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """


# ---------------------------------------------------------------------------
# Local filesystem backend
# ---------------------------------------------------------------------------


class LocalStorageBackend(StorageBackend):
    """Store uploaded files on the local filesystem.

    Args:
        upload_dir: Root directory for uploads. Created if it doesn't exist.
        url_prefix: URL prefix used by ``get_url`` (e.g. ``"/uploads"``).

    Example::

        backend = LocalStorageBackend(upload_dir="/var/app/uploads",
                                      url_prefix="/uploads")
        path = await backend.save(image_bytes, "photo.jpg")
        url  = await backend.get_url(path)   # "/uploads/photo.jpg"
    """

    def __init__(
        self,
        upload_dir: str | Path = "uploads",
        *,
        url_prefix: str = "/uploads",
    ) -> None:
        self.upload_dir = Path(upload_dir)
        self.url_prefix = url_prefix.rstrip("/")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, filename: str) -> Path:
        """Resolve a filename to an absolute path, blocking traversal."""
        resolved = (self.upload_dir / filename).resolve()
        root = self.upload_dir.resolve()
        if not str(resolved).startswith(str(root)):
            raise ValueError(f"Filename {filename!r} resolves outside upload directory")
        return resolved

    async def save(self, file_data: bytes, filename: str) -> str:
        path = self._resolve(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file_data)
        return filename

    async def delete(self, path: str) -> bool:
        fpath = self._resolve(path)
        if fpath.is_file():
            fpath.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        return self._resolve(path).is_file()

    async def get_url(self, path: str) -> str:
        return f"{self.url_prefix}/{path}"

    async def get_file(self, path: str) -> bytes:
        fpath = self._resolve(path)
        if not fpath.is_file():
            raise FileNotFoundError(f"No file at path {path!r}")
        return fpath.read_bytes()


# ---------------------------------------------------------------------------
# In-memory backend (ideal for testing)
# ---------------------------------------------------------------------------


class MemoryStorageBackend(StorageBackend):
    """In-memory upload storage — no disk I/O, perfect for tests.

    Args:
        url_prefix: URL prefix used by ``get_url``.

    Example::

        backend = MemoryStorageBackend()
        path = await backend.save(b"hello", "note.txt")
        assert await backend.get_file(path) == b"hello"
        assert await backend.exists(path)
        await backend.delete(path)
        assert not await backend.exists(path)
    """

    def __init__(self, *, url_prefix: str = "/uploads") -> None:
        self.url_prefix = url_prefix.rstrip("/")
        self._store: Dict[str, bytes] = {}

    async def save(self, file_data: bytes, filename: str) -> str:
        self._store[filename] = file_data
        return filename

    async def delete(self, path: str) -> bool:
        if path in self._store:
            del self._store[path]
            return True
        return False

    async def exists(self, path: str) -> bool:
        return path in self._store

    async def get_url(self, path: str) -> str:
        return f"{self.url_prefix}/{path}"

    async def get_file(self, path: str) -> bytes:
        if path not in self._store:
            raise FileNotFoundError(f"No file at path {path!r}")
        return self._store[path]

    def reset(self) -> None:
        """Clear all stored files."""
        self._store.clear()

    @property
    def file_count(self) -> int:
        """Number of files currently in memory."""
        return len(self._store)
