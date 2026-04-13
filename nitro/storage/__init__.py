"""
nitro.storage — Framework-agnostic file storage for the Nitro framework.

Provides:
- FileMetadata       : Metadata about a stored file
- StorageBackend     : Abstract base for storage backends
- StorageResult      : Result of a storage operation
- MemoryBackend      : In-memory storage (testing and development)
- LocalBackend       : Local filesystem storage

Optional backends (requires extra dependencies):
- S3Backend          : AWS S3 / S3-compatible storage (pip install aioboto3)

Sanic integration:
- sanic_storage      : Attach storage backend to app context

Quick start::

    from nitro.storage import MemoryBackend

    backend = MemoryBackend()
    result = await backend.put("photo.jpg", image_bytes,
                               content_type="image/jpeg")
    assert result.success

    data = await backend.get("photo.jpg")
    assert data == image_bytes

Local filesystem::

    from nitro.storage import LocalBackend

    backend = LocalBackend(root_dir="/var/uploads")
    await backend.put("docs/report.pdf", pdf_bytes,
                      content_type="application/pdf")

S3-compatible::

    from nitro.storage.s3_backend import S3Backend

    backend = S3Backend(
        bucket="my-bucket",
        region="us-east-1",
        access_key="...", secret_key="...",
    )

Sanic integration::

    from sanic import Sanic
    from nitro.storage import LocalBackend, sanic_storage

    app = Sanic("MyApp")
    sanic_storage(app, LocalBackend(root_dir="./uploads"))

    # In handlers: request.app.ctx.storage
"""

from .base import FileMetadata, StorageBackend, StorageResult
from .local_backend import LocalBackend
from .memory_backend import MemoryBackend
from .sanic_integration import sanic_storage

__all__ = [
    "FileMetadata",
    "StorageBackend",
    "StorageResult",
    "LocalBackend",
    "MemoryBackend",
    "sanic_storage",
]

# S3Backend is imported lazily to avoid hard dependency on aioboto3.
# Import it explicitly when needed:
#
#   from nitro.storage.s3_backend import S3Backend
