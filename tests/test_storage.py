"""
Tests for the nitro.storage module.

Covers: FileMetadata, StorageResult, MemoryBackend, LocalBackend,
        sanic_storage integration, copy/move, prefix handling,
        directory traversal protection, and edge cases.
"""

from __future__ import annotations

import asyncio
import hashlib
import tempfile
from pathlib import Path

import pytest

from nitro.storage import (
    FileMetadata,
    LocalBackend,
    MemoryBackend,
    StorageBackend,
    StorageResult,
    sanic_storage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mem():
    """Fresh MemoryBackend."""
    return MemoryBackend()


@pytest.fixture
def tmp_dir(tmp_path):
    """Temporary directory for LocalBackend tests."""
    return tmp_path / "storage"


@pytest.fixture
def local(tmp_dir):
    """Fresh LocalBackend in a temp directory."""
    return LocalBackend(root_dir=tmp_dir)


# ---------------------------------------------------------------------------
# FileMetadata
# ---------------------------------------------------------------------------


class TestFileMetadata:
    def test_defaults(self):
        m = FileMetadata(key="test.txt")
        assert m.key == "test.txt"
        assert m.size == 0
        assert m.content_type == "application/octet-stream"
        assert m.checksum == ""
        assert m.metadata == {}

    def test_to_dict_minimal(self):
        m = FileMetadata(key="a.txt")
        d = m.to_dict()
        assert d["key"] == "a.txt"
        assert "created_at" in d
        assert "checksum" not in d  # empty → omitted
        assert "metadata" not in d  # empty → omitted

    def test_to_dict_full(self):
        m = FileMetadata(
            key="b.txt",
            size=42,
            checksum="abc123",
            metadata={"owner": "test"},
        )
        d = m.to_dict()
        assert d["size"] == 42
        assert d["checksum"] == "abc123"
        assert d["metadata"] == {"owner": "test"}


# ---------------------------------------------------------------------------
# StorageResult
# ---------------------------------------------------------------------------


class TestStorageResult:
    def test_success(self):
        r = StorageResult(success=True, key="x.txt")
        d = r.to_dict()
        assert d["success"] is True
        assert d["key"] == "x.txt"
        assert "error" not in d

    def test_failure(self):
        r = StorageResult(success=False, key="x.txt", error="boom")
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "boom"

    def test_with_metadata(self):
        m = FileMetadata(key="x.txt", size=10)
        r = StorageResult(success=True, key="x.txt", metadata=m)
        d = r.to_dict()
        assert "metadata" in d
        assert d["metadata"]["size"] == 10


# ---------------------------------------------------------------------------
# MemoryBackend — core CRUD
# ---------------------------------------------------------------------------


class TestMemoryBackendCRUD:
    @pytest.mark.asyncio
    async def test_put_and_get(self, mem):
        result = await mem.put("hello.txt", b"hello world")
        assert result.success
        assert result.metadata is not None
        assert result.metadata.size == 11
        assert result.metadata.content_type == "application/octet-stream"

        data = await mem.get("hello.txt")
        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, mem):
        assert await mem.get("nope.txt") is None

    @pytest.mark.asyncio
    async def test_exists(self, mem):
        assert not await mem.exists("f.txt")
        await mem.put("f.txt", b"x")
        assert await mem.exists("f.txt")

    @pytest.mark.asyncio
    async def test_delete(self, mem):
        await mem.put("f.txt", b"x")
        result = await mem.delete("f.txt")
        assert result.success
        assert not await mem.exists("f.txt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, mem):
        result = await mem.delete("nope.txt")
        assert not result.success
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_overwrite(self, mem):
        await mem.put("f.txt", b"v1")
        await mem.put("f.txt", b"v2-longer")
        data = await mem.get("f.txt")
        assert data == b"v2-longer"
        info = await mem.info("f.txt")
        assert info.size == 9

    @pytest.mark.asyncio
    async def test_info(self, mem):
        await mem.put("doc.pdf", b"pdf-data", content_type="application/pdf")
        info = await mem.info("doc.pdf")
        assert info is not None
        assert info.content_type == "application/pdf"
        assert info.size == 8
        assert info.checksum == hashlib.sha256(b"pdf-data").hexdigest()

    @pytest.mark.asyncio
    async def test_info_nonexistent(self, mem):
        assert await mem.info("nope") is None


# ---------------------------------------------------------------------------
# MemoryBackend — listing, prefix, metadata
# ---------------------------------------------------------------------------


class TestMemoryBackendListing:
    @pytest.mark.asyncio
    async def test_list_empty(self, mem):
        files = await mem.list_files()
        assert files == []

    @pytest.mark.asyncio
    async def test_list_all(self, mem):
        await mem.put("a.txt", b"a")
        await mem.put("b.txt", b"b")
        await mem.put("c.txt", b"c")
        files = await mem.list_files()
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_list_with_prefix(self, mem):
        await mem.put("photos/a.jpg", b"a")
        await mem.put("photos/b.jpg", b"b")
        await mem.put("docs/x.pdf", b"x")
        files = await mem.list_files("photos/")
        assert len(files) == 2
        assert all(f.key.startswith("photos/") for f in files)

    @pytest.mark.asyncio
    async def test_list_with_limit(self, mem):
        for i in range(10):
            await mem.put(f"file_{i:02d}.txt", b"x")
        files = await mem.list_files(limit=3)
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_custom_metadata(self, mem):
        await mem.put("f.txt", b"x", metadata={"owner": "alice", "tag": "important"})
        info = await mem.info("f.txt")
        assert info.metadata == {"owner": "alice", "tag": "important"}


# ---------------------------------------------------------------------------
# MemoryBackend — prefix, find, reset, fail mode
# ---------------------------------------------------------------------------


class TestMemoryBackendExtras:
    @pytest.mark.asyncio
    async def test_prefix(self):
        mem = MemoryBackend(prefix="uploads/")
        await mem.put("photo.jpg", b"img")
        # Stored under prefixed key
        assert await mem.exists("photo.jpg")
        info = await mem.info("photo.jpg")
        assert info.key == "uploads/photo.jpg"

    @pytest.mark.asyncio
    async def test_find_by_metadata(self, mem):
        await mem.put("a.txt", b"a", metadata={"owner": "alice"})
        await mem.put("b.txt", b"b", metadata={"owner": "bob"})
        await mem.put("c.txt", b"c", metadata={"owner": "alice"})
        results = mem.find(owner="alice")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_reset(self, mem):
        await mem.put("f.txt", b"x")
        assert mem.file_count == 1
        mem.reset()
        assert mem.file_count == 0

    @pytest.mark.asyncio
    async def test_fail_mode(self):
        mem = MemoryBackend(fail=True)
        result = await mem.put("f.txt", b"data")
        assert not result.success
        assert "simulated" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_count(self, mem):
        assert mem.file_count == 0
        await mem.put("a", b"a")
        await mem.put("b", b"b")
        assert mem.file_count == 2
        await mem.delete("a")
        assert mem.file_count == 1


# ---------------------------------------------------------------------------
# MemoryBackend — copy and move
# ---------------------------------------------------------------------------


class TestMemoryBackendCopyMove:
    @pytest.mark.asyncio
    async def test_copy(self, mem):
        await mem.put("src.txt", b"content", content_type="text/plain")
        result = await mem.copy("src.txt", "dst.txt")
        assert result.success
        assert await mem.get("dst.txt") == b"content"
        # Source still exists
        assert await mem.exists("src.txt")

    @pytest.mark.asyncio
    async def test_copy_nonexistent(self, mem):
        result = await mem.copy("nope.txt", "dst.txt")
        assert not result.success
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_move(self, mem):
        await mem.put("src.txt", b"data")
        result = await mem.move("src.txt", "dst.txt")
        assert result.success
        assert await mem.get("dst.txt") == b"data"
        assert not await mem.exists("src.txt")


# ---------------------------------------------------------------------------
# LocalBackend — core CRUD
# ---------------------------------------------------------------------------


class TestLocalBackendCRUD:
    @pytest.mark.asyncio
    async def test_put_and_get(self, local):
        result = await local.put("test.txt", b"hello local")
        assert result.success
        assert result.metadata.size == 11

        data = await local.get("test.txt")
        assert data == b"hello local"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, local):
        assert await local.get("nope.txt") is None

    @pytest.mark.asyncio
    async def test_exists(self, local):
        assert not await local.exists("f.txt")
        await local.put("f.txt", b"x")
        assert await local.exists("f.txt")

    @pytest.mark.asyncio
    async def test_delete(self, local):
        await local.put("f.txt", b"x")
        result = await local.delete("f.txt")
        assert result.success
        assert not await local.exists("f.txt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, local):
        result = await local.delete("nope.txt")
        assert not result.success

    @pytest.mark.asyncio
    async def test_overwrite(self, local):
        await local.put("f.txt", b"v1")
        await local.put("f.txt", b"v2-new")
        assert await local.get("f.txt") == b"v2-new"

    @pytest.mark.asyncio
    async def test_info(self, local):
        await local.put("doc.pdf", b"pdf-data", content_type="application/pdf")
        info = await local.info("doc.pdf")
        assert info is not None
        assert info.size == 8

    @pytest.mark.asyncio
    async def test_info_nonexistent(self, local):
        assert await local.info("nope") is None


# ---------------------------------------------------------------------------
# LocalBackend — subdirectories and listing
# ---------------------------------------------------------------------------


class TestLocalBackendSubdirs:
    @pytest.mark.asyncio
    async def test_nested_put(self, local):
        result = await local.put("a/b/c/deep.txt", b"deep")
        assert result.success
        assert await local.get("a/b/c/deep.txt") == b"deep"

    @pytest.mark.asyncio
    async def test_list_files(self, local):
        await local.put("docs/a.txt", b"a")
        await local.put("docs/b.txt", b"b")
        await local.put("images/c.jpg", b"c")
        files = await local.list_files("docs/")
        assert len(files) == 2
        assert all("docs/" in f.key for f in files)

    @pytest.mark.asyncio
    async def test_list_empty_prefix(self, local):
        await local.put("a.txt", b"a")
        await local.put("b.txt", b"b")
        files = await local.list_files()
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_list_with_limit(self, local):
        for i in range(10):
            await local.put(f"f{i:02d}.txt", b"x")
        files = await local.list_files(limit=3)
        assert len(files) == 3


# ---------------------------------------------------------------------------
# LocalBackend — security
# ---------------------------------------------------------------------------


class TestLocalBackendSecurity:
    @pytest.mark.asyncio
    async def test_directory_traversal_put_blocked(self, local):
        # put() catches exceptions — check result instead
        result = await local.put("../../etc/passwd", b"evil")
        assert not result.success
        assert "outside root" in result.error.lower()

    @pytest.mark.asyncio
    async def test_directory_traversal_get_blocked(self, local):
        with pytest.raises(ValueError, match="outside root"):
            await local.get("../../etc/passwd")


# ---------------------------------------------------------------------------
# LocalBackend — copy and move
# ---------------------------------------------------------------------------


class TestLocalBackendCopyMove:
    @pytest.mark.asyncio
    async def test_copy(self, local):
        await local.put("src.txt", b"content")
        result = await local.copy("src.txt", "dst.txt")
        assert result.success
        assert await local.get("dst.txt") == b"content"
        assert await local.exists("src.txt")

    @pytest.mark.asyncio
    async def test_move(self, local):
        await local.put("src.txt", b"data")
        result = await local.move("src.txt", "dst.txt")
        assert result.success
        assert await local.get("dst.txt") == b"data"
        assert not await local.exists("src.txt")


# ---------------------------------------------------------------------------
# LocalBackend — prefix
# ---------------------------------------------------------------------------


class TestLocalBackendPrefix:
    @pytest.mark.asyncio
    async def test_prefix_applied(self, tmp_dir):
        backend = LocalBackend(root_dir=tmp_dir, prefix="uploads/")
        await backend.put("photo.jpg", b"img")
        info = await backend.info("photo.jpg")
        assert info.key == "uploads/photo.jpg"
        # File actually on disk under prefix path
        assert (tmp_dir / "uploads" / "photo.jpg").is_file()


# ---------------------------------------------------------------------------
# Sanic integration
# ---------------------------------------------------------------------------


class TestSanicIntegration:
    def test_sanic_storage_attaches_backend(self):
        class FakeApp:
            class ctx:
                storage = None

            _listeners = {}

            def listener(self, event):
                def decorator(fn):
                    self._listeners[event] = fn
                    return fn

                return decorator

        app = FakeApp()
        backend = MemoryBackend()
        sanic_storage(app, backend)
        assert app.ctx.storage is backend
        assert "after_server_stop" in app._listeners


# ---------------------------------------------------------------------------
# StorageBackend — abstract interface
# ---------------------------------------------------------------------------


class TestStorageBackendABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            StorageBackend()

    def test_repr(self, mem):
        assert "MemoryBackend" in repr(mem)

    def test_repr_with_prefix(self):
        b = MemoryBackend(prefix="test/")
        assert "test/" in repr(b)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_file(self, mem):
        result = await mem.put("empty.txt", b"")
        assert result.success
        assert result.metadata.size == 0
        assert await mem.get("empty.txt") == b""

    @pytest.mark.asyncio
    async def test_large_key(self, mem):
        key = "a" * 500 + ".txt"
        result = await mem.put(key, b"x")
        assert result.success
        assert await mem.get(key) == b"x"

    @pytest.mark.asyncio
    async def test_binary_content(self, mem):
        content = bytes(range(256))
        await mem.put("binary.bin", content)
        assert await mem.get("binary.bin") == content

    @pytest.mark.asyncio
    async def test_content_type_preserved(self, mem):
        await mem.put("img.png", b"png", content_type="image/png")
        info = await mem.info("img.png")
        assert info.content_type == "image/png"

    @pytest.mark.asyncio
    async def test_checksum_sha256(self, mem):
        content = b"checksum test"
        expected = hashlib.sha256(content).hexdigest()
        await mem.put("f.txt", content)
        info = await mem.info("f.txt")
        assert info.checksum == expected
