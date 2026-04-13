"""
S3-compatible storage backend (optional dependency: ``aioboto3``).

Supports AWS S3, MinIO, DigitalOcean Spaces, and other S3-compatible services.

Install::

    pip install aioboto3

Example::

    from nitro.storage.s3_backend import S3Backend

    backend = S3Backend(
        bucket="my-bucket",
        region="us-east-1",
        access_key="...",
        secret_key="...",
    )
    result = await backend.put("photos/cat.jpg", image_bytes,
                               content_type="image/jpeg")
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import FileMetadata, StorageBackend, StorageResult

try:
    import aioboto3

    HAS_AIOBOTO3 = True
except ImportError:
    HAS_AIOBOTO3 = False


class S3Backend(StorageBackend):
    """AWS S3 / S3-compatible storage backend.

    Requires ``aioboto3`` (``pip install aioboto3``).

    Args:
        bucket: S3 bucket name.
        region: AWS region (default: ``"us-east-1"``).
        access_key: AWS access key ID (or use env / IAM role).
        secret_key: AWS secret access key.
        endpoint_url: Custom endpoint for S3-compatible services.
        prefix: Optional key prefix applied to all operations.
    """

    def __init__(
        self,
        bucket: str,
        *,
        region: str = "us-east-1",
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
        prefix: str = "",
    ):
        if not HAS_AIOBOTO3:
            raise ImportError(
                "S3Backend requires aioboto3. Install it with: pip install aioboto3"
            )
        super().__init__(prefix=prefix)
        self.bucket = bucket
        self.region = region
        self._session = aioboto3.Session(
            aws_access_key_id=access_key or None,
            aws_secret_access_key=secret_key or None,
            region_name=region,
        )
        self._endpoint_url = endpoint_url or None

    def _client_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return kwargs

    async def put(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResult:
        full_key = self._full_key(key)
        try:
            put_kwargs: Dict[str, Any] = {
                "Bucket": self.bucket,
                "Key": full_key,
                "Body": content,
                "ContentType": content_type,
            }
            if metadata:
                put_kwargs["Metadata"] = metadata

            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.put_object(**put_kwargs)

            checksum = hashlib.sha256(content).hexdigest()
            now = datetime.now(timezone.utc)
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
            return StorageResult(success=False, key=full_key, error=str(exc))

    async def get(self, key: str) -> Optional[bytes]:
        full_key = self._full_key(key)
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                resp = await s3.get_object(Bucket=self.bucket, Key=full_key)
                return await resp["Body"].read()
        except Exception:
            return None

    async def delete(self, key: str) -> StorageResult:
        full_key = self._full_key(key)
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.delete_object(Bucket=self.bucket, Key=full_key)
            return StorageResult(success=True, key=full_key)
        except Exception as exc:
            return StorageResult(success=False, key=full_key, error=str(exc))

    async def exists(self, key: str) -> bool:
        full_key = self._full_key(key)
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.head_object(Bucket=self.bucket, Key=full_key)
            return True
        except Exception:
            return False

    async def info(self, key: str) -> Optional[FileMetadata]:
        full_key = self._full_key(key)
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                resp = await s3.head_object(Bucket=self.bucket, Key=full_key)
            return FileMetadata(
                key=full_key,
                size=resp.get("ContentLength", 0),
                content_type=resp.get("ContentType", "application/octet-stream"),
                created_at=resp.get("LastModified", datetime.now(timezone.utc)),
                updated_at=resp.get("LastModified", datetime.now(timezone.utc)),
                metadata=resp.get("Metadata", {}),
            )
        except Exception:
            return None

    async def list_files(
        self, prefix: str = "", *, limit: int = 1000
    ) -> List[FileMetadata]:
        full_prefix = self._full_key(prefix)
        results: List[FileMetadata] = []
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(
                    Bucket=self.bucket,
                    Prefix=full_prefix,
                    PaginationConfig={"MaxItems": limit},
                ):
                    for obj in page.get("Contents", []):
                        results.append(
                            FileMetadata(
                                key=obj["Key"],
                                size=obj.get("Size", 0),
                                updated_at=obj.get(
                                    "LastModified", datetime.now(timezone.utc)
                                ),
                            )
                        )
                        if len(results) >= limit:
                            return results
        except Exception:
            pass
        return results

    async def copy(self, src_key: str, dst_key: str) -> StorageResult:
        """Server-side copy within the same bucket."""
        full_src = self._full_key(src_key)
        full_dst = self._full_key(dst_key)
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await s3.copy_object(
                    Bucket=self.bucket,
                    CopySource={"Bucket": self.bucket, "Key": full_src},
                    Key=full_dst,
                )
            return StorageResult(success=True, key=full_dst)
        except Exception as exc:
            return StorageResult(success=False, key=full_dst, error=str(exc))

    async def move(self, src_key: str, dst_key: str) -> StorageResult:
        """Server-side move (copy + delete)."""
        result = await self.copy(src_key, dst_key)
        if result.success:
            await self.delete(src_key)
        return result
