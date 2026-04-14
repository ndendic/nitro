"""
Upload processing handler for the Nitro uploads module.

Validates, names, and stores uploaded files via a pluggable storage backend.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from .config import UploadConfig
from .storage import LocalStorageBackend, MemoryStorageBackend, StorageBackend
from .validators import (
    UploadValidationError,
    sanitize_filename,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)


class UploadResult(BaseModel):
    """Result of a successful file upload.

    Attributes:
        original_filename: The original filename as provided by the uploader.
        stored_path: The path/key under which the file is stored.
        size: File size in bytes.
        mime_type: Detected MIME type of the file.
        created_at: Timestamp when the file was stored (UTC).
        url: Public URL for accessing the file (if available).
    """

    original_filename: str
    stored_path: str
    size: int
    mime_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class UploadHandler:
    """Validates and stores file uploads.

    The handler orchestrates the full upload pipeline:
    1. Validate file size
    2. Validate file extension
    3. Detect and validate MIME type
    4. Generate a safe, unique filename
    5. Delegate to the storage backend

    Args:
        config: Upload configuration.
        backend: Storage backend. If None, one is created from config.

    Example::

        from nitro.uploads import UploadHandler, UploadConfig
        from nitro.uploads.storage import MemoryStorageBackend

        config  = UploadConfig(max_file_size=5_000_000,
                               allowed_extensions={".jpg", ".png"})
        backend = MemoryStorageBackend()
        handler = UploadHandler(config=config, backend=backend)

        result = await handler.handle(b"...", "photo.jpg")
        print(result.stored_path)   # "<uuid>.jpg"
        print(result.mime_type)     # "image/jpeg"
    """

    def __init__(
        self,
        config: Optional[UploadConfig] = None,
        *,
        backend: Optional[StorageBackend] = None,
    ) -> None:
        self.config = config or UploadConfig()
        if backend is not None:
            self.backend = backend
        else:
            self.backend = self._create_backend()

    def _create_backend(self) -> StorageBackend:
        """Instantiate a backend from the config's StorageConfig."""
        from .config import StorageBackendType

        sc = self.config.storage
        if sc.backend == StorageBackendType.MEMORY:
            return MemoryStorageBackend()
        # Default → local
        root = sc.local_path or Path("uploads")
        return LocalStorageBackend(upload_dir=root)

    def _generate_filename(self, original: str) -> str:
        """Create a storage filename from the original name.

        If ``generate_unique_names`` is True (default), a UUID prefix is added
        to prevent collisions while preserving the file extension.
        """
        safe = sanitize_filename(original)
        if self.config.generate_unique_names:
            ext = Path(safe).suffix.lower()
            unique_name = f"{uuid.uuid4().hex}{ext}"
            return unique_name
        return safe

    def _build_storage_key(self, filename: str) -> str:
        """Prefix filename with upload_dir if configured."""
        if self.config.upload_dir:
            return f"{self.config.upload_dir.rstrip('/')}/{filename}"
        return filename

    async def handle(
        self,
        file_data: bytes,
        filename: str,
    ) -> UploadResult:
        """Process a single file upload.

        Args:
            file_data: Raw file bytes.
            filename: Original filename supplied by the uploader.

        Returns:
            UploadResult with stored path, size, MIME type, and URL.

        Raises:
            UploadValidationError: If validation fails.
        """
        cfg = self.config

        # 1. Size
        validate_file_size(file_data, cfg.max_file_size)

        # 2. Extension
        validate_extension(filename, cfg.allowed_extensions)

        # 3. MIME type detection and validation
        detected_mime = validate_mime_type(file_data, cfg.allowed_mime_types, filename)

        # 4. Filename generation
        storage_filename = self._generate_filename(filename)
        storage_key = self._build_storage_key(storage_filename)

        # 5. Store
        stored_path = await self.backend.save(file_data, storage_key)

        # 6. URL
        url = await self.backend.get_url(stored_path)

        return UploadResult(
            original_filename=filename,
            stored_path=stored_path,
            size=len(file_data),
            mime_type=detected_mime,
            url=url,
        )

    async def handle_batch(
        self,
        files: List[Tuple[bytes, str]],
    ) -> List[UploadResult]:
        """Process multiple file uploads.

        Each file is validated and stored independently. If one file fails
        validation, processing continues for the remaining files. Errors are
        collected and re-raised as a BatchUploadError only when all files
        have been attempted.

        Args:
            files: List of (file_data, filename) tuples.

        Returns:
            List of UploadResult for each successfully stored file.

        Raises:
            BatchUploadError: If any file fails validation.
        """
        results: List[UploadResult] = []
        errors: List[Tuple[str, UploadValidationError]] = []

        for file_data, filename in files:
            try:
                result = await self.handle(file_data, filename)
                results.append(result)
            except UploadValidationError as exc:
                errors.append((filename, exc))

        if errors:
            raise BatchUploadError(errors, successful=results)

        return results


class BatchUploadError(Exception):
    """Raised when one or more files in a batch upload fail validation.

    Attributes:
        errors: List of (filename, UploadValidationError) pairs for failed files.
        successful: UploadResult list for files that were stored successfully
                    before the error was detected.
    """

    def __init__(
        self,
        errors: List[Tuple[str, UploadValidationError]],
        successful: Optional[List[UploadResult]] = None,
    ) -> None:
        self.errors = errors
        self.successful = successful or []
        messages = [f"{fname}: {err}" for fname, err in errors]
        super().__init__(f"Batch upload failed for {len(errors)} file(s): {'; '.join(messages)}")
