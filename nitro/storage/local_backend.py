"""
Local filesystem storage backend.

Stores files on disk under a configurable root directory.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .base import FileMetadata, StorageBackend, StorageResult


class LocalBackend(StorageBackend):
    """Local filesystem storage backend.

    Files are stored under ``root_dir``. Subdirectories are created
    automatically when needed.

    Args:
        root_dir: Base directory for file storage.
        prefix: Optional key prefix applied to all operations.
        create_dirs: If ``True`` (default), create ``root_dir`` on init.

    Example::

        backend = LocalBackend(root_dir="/tmp/uploads")
        result = await backend.put("photos/cat.jpg", image_bytes,
                                   content_type="image/jpeg")
        assert result.success
    """

    def __init__(
        self,
        root_dir: str | Path,
        *,
        prefix: str = "",
        create_dirs: bool = True,
    ):
        super().__init__(prefix=prefix)
        self.root_dir = Path(root_dir)
        if create_dirs:
            self.root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolve a storage key to an absolute filesystem path."""
        full_key = self._full_key(key)
        # Prevent directory traversal
        resolved = (self.root_dir / full_key).resolve()
        if not str(resolved).startswith(str(self.root_dir.resolve())):
            raise ValueError(f"Key {key!r} resolves outside root directory")
        return resolved

    async def put(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResult:
        try:
            path = self._resolve_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

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
            return StorageResult(success=True, key=full_key, metadata=file_meta)
        except Exception as exc:
            return StorageResult(
                success=False, key=self._full_key(key), error=str(exc)
            )

    async def get(self, key: str) -> Optional[bytes]:
        path = self._resolve_path(key)
        if path.is_file():
            return path.read_bytes()
        return None

    async def delete(self, key: str) -> StorageResult:
        full_key = self._full_key(key)
        path = self._resolve_path(key)
        if path.is_file():
            path.unlink()
            return StorageResult(success=True, key=full_key)
        return StorageResult(success=False, key=full_key, error="File not found")

    async def exists(self, key: str) -> bool:
        return self._resolve_path(key).is_file()

    async def info(self, key: str) -> Optional[FileMetadata]:
        path = self._resolve_path(key)
        if not path.is_file():
            return None
        stat = path.stat()
        full_key = self._full_key(key)
        return FileMetadata(
            key=full_key,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )

    async def list_files(
        self, prefix: str = "", *, limit: int = 1000
    ) -> List[FileMetadata]:
        full_prefix = self._full_key(prefix)
        scan_dir = self.root_dir / full_prefix if full_prefix else self.root_dir
        results: List[FileMetadata] = []

        if not scan_dir.exists():
            # prefix might be partial — try parent directory
            scan_dir = scan_dir.parent
            if not scan_dir.exists():
                return results

        root_str = str(self.root_dir.resolve())
        for dirpath, _, filenames in os.walk(scan_dir):
            for fname in sorted(filenames):
                fpath = Path(dirpath) / fname
                rel = str(fpath.resolve().relative_to(self.root_dir.resolve()))
                if rel.startswith(full_prefix):
                    stat = fpath.stat()
                    results.append(
                        FileMetadata(
                            key=rel,
                            size=stat.st_size,
                            created_at=datetime.fromtimestamp(
                                stat.st_ctime, tz=timezone.utc
                            ),
                            updated_at=datetime.fromtimestamp(
                                stat.st_mtime, tz=timezone.utc
                            ),
                        )
                    )
                    if len(results) >= limit:
                        return results
        return results
