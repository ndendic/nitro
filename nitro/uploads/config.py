"""
Upload configuration models for the Nitro uploads module.

Provides Pydantic models for configuring upload behavior and storage backends.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class StorageBackendType(str, Enum):
    """Available storage backend types."""

    LOCAL = "local"
    MEMORY = "memory"
    S3 = "s3"


class StorageConfig(BaseModel):
    """Storage backend configuration.

    Attributes:
        backend: Which storage backend to use.
        local_path: Root directory for local storage (used with LOCAL backend).
        s3_bucket: S3 bucket name (used with S3 backend).
        s3_region: AWS region (used with S3 backend).
        s3_access_key: AWS access key ID (used with S3 backend).
        s3_secret_key: AWS secret access key (used with S3 backend).
        s3_endpoint_url: Custom endpoint URL for S3-compatible services.
        url_base: Base URL for generating public file URLs.
    """

    backend: StorageBackendType = StorageBackendType.LOCAL
    local_path: Optional[Path] = Field(default=Path("uploads"))
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    url_base: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class UploadConfig(BaseModel):
    """Configuration for the upload handler.

    Attributes:
        max_file_size: Maximum allowed file size in bytes (default 10 MB).
        allowed_extensions: Set of allowed file extensions (e.g. {".jpg", ".png"}).
            Empty set means all extensions allowed.
        allowed_mime_types: Set of allowed MIME types (e.g. {"image/jpeg"}).
            Empty set means all MIME types allowed.
        storage: Storage backend configuration.
        upload_dir: Subdirectory within the storage root to place uploads.
        generate_unique_names: If True, generate UUID-based filenames to prevent collisions.
        preserve_original_name: Store original filename in result metadata.
    """

    max_file_size: int = Field(default=10 * 1024 * 1024, gt=0)  # 10 MB
    allowed_extensions: Set[str] = Field(default_factory=set)
    allowed_mime_types: Set[str] = Field(default_factory=set)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    upload_dir: str = ""
    generate_unique_names: bool = True
    preserve_original_name: bool = True

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def normalise_extensions(cls, v: object) -> Set[str]:
        """Ensure extensions are lowercase and prefixed with '.'."""
        if not v:
            return set()
        result: Set[str] = set()
        for ext in v:
            ext = str(ext).lower().strip()
            if not ext.startswith("."):
                ext = f".{ext}"
            result.add(ext)
        return result

    @field_validator("allowed_mime_types", mode="before")
    @classmethod
    def normalise_mimes(cls, v: object) -> Set[str]:
        """Ensure MIME types are lowercase."""
        if not v:
            return set()
        return {str(m).lower().strip() for m in v}
