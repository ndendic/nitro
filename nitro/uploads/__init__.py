"""
nitro.uploads — File upload handling for the Nitro framework.

Provides:
- UploadConfig          : Configuration for upload limits, extensions, and MIME types
- StorageConfig         : Storage backend configuration
- StorageBackend        : Abstract base class for storage backends
- LocalStorageBackend   : Local filesystem storage
- MemoryStorageBackend  : In-memory storage (ideal for testing)
- UploadHandler         : Validates and stores file uploads
- UploadResult          : Result of a successful upload
- BatchUploadError      : Raised when batch uploads partially fail
- UploadValidationError : Raised when file validation fails
- sanitize_filename     : Make a user-supplied filename safe
- validate_file_size    : Check file size against a limit
- validate_extension    : Check extension against an allowed set
- validate_mime_type    : Detect and validate MIME type from magic bytes
- detect_mime_type      : Detect MIME type without raising on mismatch

Optional image utilities (requires Pillow):
- ImageProcessor        : Resize, thumbnail, and format conversion
- validate_image_dimensions : Check image pixel dimensions

Quick start::

    from nitro.uploads import UploadHandler, UploadConfig
    from nitro.uploads.storage import MemoryStorageBackend

    config  = UploadConfig(
        max_file_size=5_000_000,
        allowed_extensions={".jpg", ".png", ".gif"},
        allowed_mime_types={"image/jpeg", "image/png", "image/gif"},
    )
    backend = MemoryStorageBackend()
    handler = UploadHandler(config=config, backend=backend)

    # In an async context:
    result = await handler.handle(image_bytes, "photo.jpg")
    print(result.stored_path)   # "a1b2c3d4...hex.jpg"
    print(result.mime_type)     # "image/jpeg"
    print(result.url)           # "/uploads/a1b2c3d4...hex.jpg"

Batch uploads::

    results = await handler.handle_batch([
        (img1_bytes, "img1.jpg"),
        (img2_bytes, "img2.png"),
    ])

Local filesystem storage::

    from nitro.uploads.storage import LocalStorageBackend

    backend = LocalStorageBackend(upload_dir="/var/app/uploads",
                                  url_prefix="/uploads")
    handler = UploadHandler(backend=backend)

Image processing (requires Pillow)::

    from nitro.uploads.image import ImageProcessor

    proc   = ImageProcessor()
    thumb  = proc.thumbnail(image_bytes, size=(128, 128))
    resized = proc.resize(image_bytes, width=800, height=600)
    webp   = proc.convert(image_bytes, target_format="WEBP")
"""

from .config import StorageBackendType, StorageConfig, UploadConfig
from .handler import BatchUploadError, UploadHandler, UploadResult
from .storage import LocalStorageBackend, MemoryStorageBackend, StorageBackend
from .validators import (
    UploadValidationError,
    detect_mime_type,
    sanitize_filename,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)

__all__ = [
    # Config
    "UploadConfig",
    "StorageConfig",
    "StorageBackendType",
    # Storage
    "StorageBackend",
    "LocalStorageBackend",
    "MemoryStorageBackend",
    # Handler
    "UploadHandler",
    "UploadResult",
    "BatchUploadError",
    # Validators
    "UploadValidationError",
    "sanitize_filename",
    "validate_file_size",
    "validate_extension",
    "validate_mime_type",
    "detect_mime_type",
]
