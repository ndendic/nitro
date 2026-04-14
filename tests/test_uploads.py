"""
Tests for the nitro.uploads module.

Covers: UploadConfig, StorageConfig, LocalStorageBackend, MemoryStorageBackend,
        validators (size, extension, mime, sanitize), UploadHandler single and
        batch uploads, UploadResult, BatchUploadError, and optional image
        processing via Pillow.
"""

from __future__ import annotations

import asyncio
import io
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest

from nitro.uploads import (
    BatchUploadError,
    LocalStorageBackend,
    MemoryStorageBackend,
    StorageBackend,
    StorageBackendType,
    StorageConfig,
    UploadConfig,
    UploadHandler,
    UploadResult,
    UploadValidationError,
    detect_mime_type,
    sanitize_filename,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)
from nitro.uploads.image import HAS_PILLOW, ImageProcessor, validate_image_dimensions


# ---------------------------------------------------------------------------
# Helpers — sample file bytes
# ---------------------------------------------------------------------------

# Minimal valid JPEG (SOI + EOI)
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 12 + b"\xff\xd9"

# Minimal valid PNG (PNG signature + minimal IHDR-like chunk)
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24

# Minimal GIF
GIF_BYTES = b"GIF89a" + b"\x00" * 10 + b"\x3b"

# PDF magic
PDF_BYTES = b"%PDF-1.4\n" + b"\x00" * 20

# Generic binary
BINARY_BYTES = b"\x00\x01\x02\x03\x04\x05\x06\x07"

# Plain text
TEXT_BYTES = b"Hello, world!"


def _run(coro):
    """Run a coroutine synchronously (test helper)."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# UploadConfig
# ---------------------------------------------------------------------------


class TestUploadConfig:
    def test_defaults(self):
        cfg = UploadConfig()
        assert cfg.max_file_size == 10 * 1024 * 1024  # 10 MB
        assert cfg.allowed_extensions == set()
        assert cfg.allowed_mime_types == set()
        assert cfg.generate_unique_names is True
        assert cfg.preserve_original_name is True

    def test_custom_max_size(self):
        cfg = UploadConfig(max_file_size=500_000)
        assert cfg.max_file_size == 500_000

    def test_extension_normalisation_adds_dot(self):
        cfg = UploadConfig(allowed_extensions=["jpg", "png"])
        assert ".jpg" in cfg.allowed_extensions
        assert ".png" in cfg.allowed_extensions

    def test_extension_normalisation_lowercases(self):
        cfg = UploadConfig(allowed_extensions=[".JPG", ".PNG"])
        assert ".jpg" in cfg.allowed_extensions
        assert ".png" in cfg.allowed_extensions

    def test_mime_normalisation_lowercases(self):
        cfg = UploadConfig(allowed_mime_types=["Image/JPEG", "IMAGE/PNG"])
        assert "image/jpeg" in cfg.allowed_mime_types
        assert "image/png" in cfg.allowed_mime_types

    def test_storage_config_defaults(self):
        cfg = UploadConfig()
        assert cfg.storage.backend == StorageBackendType.LOCAL
        assert cfg.storage.local_path is not None

    def test_upload_dir(self):
        cfg = UploadConfig(upload_dir="media/photos")
        assert cfg.upload_dir == "media/photos"

    def test_generate_unique_names_false(self):
        cfg = UploadConfig(generate_unique_names=False)
        assert cfg.generate_unique_names is False


class TestStorageConfig:
    def test_defaults(self):
        sc = StorageConfig()
        assert sc.backend == StorageBackendType.LOCAL

    def test_memory_backend(self):
        sc = StorageConfig(backend=StorageBackendType.MEMORY)
        assert sc.backend == StorageBackendType.MEMORY

    def test_s3_fields(self):
        sc = StorageConfig(
            backend=StorageBackendType.S3,
            s3_bucket="my-bucket",
            s3_region="us-east-1",
        )
        assert sc.s3_bucket == "my-bucket"
        assert sc.s3_region == "us-east-1"

    def test_url_base(self):
        sc = StorageConfig(url_base="https://cdn.example.com")
        assert sc.url_base == "https://cdn.example.com"


# ---------------------------------------------------------------------------
# LocalStorageBackend
# ---------------------------------------------------------------------------


class TestLocalStorageBackend:
    @pytest.fixture
    def backend(self, tmp_path):
        return LocalStorageBackend(upload_dir=tmp_path / "uploads")

    def test_save_and_get_file(self, backend):
        path = _run(backend.save(b"hello", "test.txt"))
        data = _run(backend.get_file(path))
        assert data == b"hello"

    def test_exists_true(self, backend):
        path = _run(backend.save(b"data", "file.bin"))
        assert _run(backend.exists(path)) is True

    def test_exists_false(self, backend):
        assert _run(backend.exists("nonexistent.txt")) is False

    def test_delete_returns_true(self, backend):
        path = _run(backend.save(b"data", "del.txt"))
        assert _run(backend.delete(path)) is True

    def test_delete_nonexistent_returns_false(self, backend):
        assert _run(backend.delete("ghost.txt")) is False

    def test_delete_removes_file(self, backend):
        path = _run(backend.save(b"data", "removeme.txt"))
        _run(backend.delete(path))
        assert _run(backend.exists(path)) is False

    def test_get_url(self, backend):
        url = _run(backend.get_url("photo.jpg"))
        assert url.endswith("/photo.jpg")

    def test_get_file_not_found_raises(self, backend):
        with pytest.raises(FileNotFoundError):
            _run(backend.get_file("missing.txt"))

    def test_overwrite_existing(self, backend):
        _run(backend.save(b"v1", "file.txt"))
        _run(backend.save(b"v2", "file.txt"))
        assert _run(backend.get_file("file.txt")) == b"v2"

    def test_path_traversal_blocked(self, backend):
        with pytest.raises(ValueError):
            _run(backend.save(b"bad", "../escape.txt"))

    def test_subdirectory_created(self, backend):
        path = _run(backend.save(b"data", "sub/dir/file.txt"))
        assert _run(backend.exists(path)) is True

    def test_url_prefix_customization(self, tmp_path):
        b = LocalStorageBackend(
            upload_dir=tmp_path / "u", url_prefix="/media"
        )
        url = _run(b.get_url("img.png"))
        assert url == "/media/img.png"

    def test_is_abstract_base_instance(self, backend):
        assert isinstance(backend, StorageBackend)


# ---------------------------------------------------------------------------
# MemoryStorageBackend
# ---------------------------------------------------------------------------


class TestMemoryStorageBackend:
    @pytest.fixture
    def backend(self):
        return MemoryStorageBackend()

    def test_save_and_retrieve(self, backend):
        path = _run(backend.save(b"content", "note.txt"))
        assert _run(backend.get_file(path)) == b"content"

    def test_exists_after_save(self, backend):
        path = _run(backend.save(b"x", "x.bin"))
        assert _run(backend.exists(path)) is True

    def test_not_exists_initially(self, backend):
        assert _run(backend.exists("nope.bin")) is False

    def test_delete(self, backend):
        path = _run(backend.save(b"y", "y.bin"))
        result = _run(backend.delete(path))
        assert result is True
        assert _run(backend.exists(path)) is False

    def test_delete_missing_returns_false(self, backend):
        assert _run(backend.delete("ghost.bin")) is False

    def test_get_url(self, backend):
        url = _run(backend.get_url("file.jpg"))
        assert "/file.jpg" in url

    def test_get_file_missing_raises(self, backend):
        with pytest.raises(FileNotFoundError):
            _run(backend.get_file("no_file.txt"))

    def test_file_count(self, backend):
        assert backend.file_count == 0
        _run(backend.save(b"a", "a.txt"))
        _run(backend.save(b"b", "b.txt"))
        assert backend.file_count == 2

    def test_reset(self, backend):
        _run(backend.save(b"data", "f.bin"))
        backend.reset()
        assert backend.file_count == 0

    def test_overwrite(self, backend):
        _run(backend.save(b"v1", "same.txt"))
        _run(backend.save(b"v2", "same.txt"))
        assert _run(backend.get_file("same.txt")) == b"v2"

    def test_is_abstract_base_instance(self, backend):
        assert isinstance(backend, StorageBackend)

    def test_url_prefix_customization(self):
        b = MemoryStorageBackend(url_prefix="/files")
        url = _run(b.get_url("doc.pdf"))
        assert url == "/files/doc.pdf"


# ---------------------------------------------------------------------------
# Validators — file size
# ---------------------------------------------------------------------------


class TestValidateFileSize:
    def test_exact_limit_passes(self):
        validate_file_size(b"x" * 100, 100)  # should not raise

    def test_under_limit_passes(self):
        validate_file_size(b"hi", 1000)

    def test_over_limit_raises(self):
        with pytest.raises(UploadValidationError) as exc_info:
            validate_file_size(b"x" * 101, 100)
        assert exc_info.value.field == "size"

    def test_empty_file_passes(self):
        validate_file_size(b"", 100)

    def test_error_message_contains_sizes(self):
        with pytest.raises(UploadValidationError) as exc_info:
            validate_file_size(b"x" * 200, 100)
        assert "200" in str(exc_info.value)
        assert "100" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Validators — extension
# ---------------------------------------------------------------------------


class TestValidateExtension:
    def test_allowed_extension_passes(self):
        validate_extension("photo.jpg", {".jpg", ".png"})

    def test_disallowed_extension_raises(self):
        with pytest.raises(UploadValidationError) as exc_info:
            validate_extension("script.exe", {".jpg", ".png"})
        assert exc_info.value.field == "extension"

    def test_empty_allowed_set_permits_all(self):
        validate_extension("anything.exe", set())  # no restriction

    def test_case_insensitive(self):
        validate_extension("PHOTO.JPG", {".jpg", ".png"})

    def test_no_extension_disallowed(self):
        with pytest.raises(UploadValidationError):
            validate_extension("no_extension", {".txt"})

    def test_error_lists_allowed(self):
        with pytest.raises(UploadValidationError) as exc_info:
            validate_extension("file.pdf", {".jpg"})
        assert ".jpg" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Validators — MIME type
# ---------------------------------------------------------------------------


class TestDetectMimeType:
    def test_jpeg(self):
        assert detect_mime_type(JPEG_BYTES) == "image/jpeg"

    def test_png(self):
        assert detect_mime_type(PNG_BYTES) == "image/png"

    def test_gif(self):
        assert detect_mime_type(GIF_BYTES) == "image/gif"

    def test_pdf(self):
        assert detect_mime_type(PDF_BYTES) == "application/pdf"

    def test_unknown_bytes_returns_octet_stream(self):
        assert detect_mime_type(BINARY_BYTES) == "application/octet-stream"

    def test_fallback_to_extension(self):
        mime = detect_mime_type(BINARY_BYTES, filename="data.json")
        assert mime == "application/json"

    def test_text_fallback(self):
        mime = detect_mime_type(BINARY_BYTES, filename="notes.txt")
        assert mime == "text/plain"


class TestValidateMimeType:
    def test_allowed_passes(self):
        result = validate_mime_type(JPEG_BYTES, {"image/jpeg"})
        assert result == "image/jpeg"

    def test_disallowed_raises(self):
        with pytest.raises(UploadValidationError) as exc_info:
            validate_mime_type(JPEG_BYTES, {"image/png"})
        assert exc_info.value.field == "mime_type"

    def test_empty_allowed_set_permits_all(self):
        result = validate_mime_type(JPEG_BYTES, set())
        assert result == "image/jpeg"

    def test_returns_detected_mime(self):
        result = validate_mime_type(PNG_BYTES, {"image/png"})
        assert result == "image/png"


# ---------------------------------------------------------------------------
# Validators — filename sanitization
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_normal_name_unchanged(self):
        assert sanitize_filename("photo.jpg") == "photo.jpg"

    def test_path_traversal_stripped(self):
        result = sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_backslash_traversal_stripped(self):
        result = sanitize_filename("..\\..\\windows\\system32\\file.dll")
        assert "\\" not in result

    def test_special_chars_removed(self):
        result = sanitize_filename("my file! @#$.txt")
        assert "!" not in result
        assert "@" not in result
        assert "#" not in result

    def test_spaces_become_underscores(self):
        result = sanitize_filename("my file.txt")
        assert " " not in result
        assert "_" in result

    def test_empty_string_returns_upload(self):
        assert sanitize_filename("") == "upload"

    def test_only_unsafe_chars_returns_upload(self):
        result = sanitize_filename("!!!")
        assert result == "upload"

    def test_null_bytes_stripped(self):
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    def test_leading_dots_stripped(self):
        result = sanitize_filename(".hidden")
        assert not result.startswith(".")

    def test_double_dots_collapsed(self):
        result = sanitize_filename("file..txt")
        assert ".." not in result

    def test_unicode_normalised(self):
        # Basic latin letters survive normalisation
        result = sanitize_filename("résumé.pdf")
        assert result.endswith(".pdf")

    def test_preserves_extension(self):
        result = sanitize_filename("document.pdf")
        assert result.endswith(".pdf")


# ---------------------------------------------------------------------------
# UploadHandler — single upload
# ---------------------------------------------------------------------------


class TestUploadHandler:
    @pytest.fixture
    def backend(self):
        return MemoryStorageBackend()

    @pytest.fixture
    def handler(self, backend):
        return UploadHandler(config=UploadConfig(), backend=backend)

    def test_basic_upload_returns_result(self, handler):
        result = _run(handler.handle(TEXT_BYTES, "note.txt"))
        assert isinstance(result, UploadResult)

    def test_original_filename_preserved(self, handler):
        result = _run(handler.handle(TEXT_BYTES, "document.txt"))
        assert result.original_filename == "document.txt"

    def test_size_correct(self, handler):
        result = _run(handler.handle(TEXT_BYTES, "note.txt"))
        assert result.size == len(TEXT_BYTES)

    def test_mime_type_detected(self, handler):
        result = _run(handler.handle(JPEG_BYTES, "photo.jpg"))
        assert result.mime_type == "image/jpeg"

    def test_stored_path_not_empty(self, handler):
        result = _run(handler.handle(TEXT_BYTES, "note.txt"))
        assert result.stored_path

    def test_url_in_result(self, handler):
        result = _run(handler.handle(TEXT_BYTES, "note.txt"))
        assert result.url is not None

    def test_unique_filename_generated(self, handler):
        r1 = _run(handler.handle(TEXT_BYTES, "same.txt"))
        r2 = _run(handler.handle(TEXT_BYTES, "same.txt"))
        assert r1.stored_path != r2.stored_path

    def test_non_unique_names_when_disabled(self, backend):
        cfg = UploadConfig(generate_unique_names=False)
        h = UploadHandler(config=cfg, backend=backend)
        result = _run(h.handle(TEXT_BYTES, "my file.txt"))
        # sanitized, no UUID prefix — but same each time
        r2 = _run(h.handle(TEXT_BYTES, "my file.txt"))
        assert Path(result.stored_path).name == Path(r2.stored_path).name

    def test_file_too_large_raises(self, backend):
        cfg = UploadConfig(max_file_size=5)
        h = UploadHandler(config=cfg, backend=backend)
        with pytest.raises(UploadValidationError) as exc_info:
            _run(h.handle(b"too large data", "big.txt"))
        assert exc_info.value.field == "size"

    def test_disallowed_extension_raises(self, backend):
        cfg = UploadConfig(allowed_extensions={".jpg", ".png"})
        h = UploadHandler(config=cfg, backend=backend)
        with pytest.raises(UploadValidationError) as exc_info:
            _run(h.handle(TEXT_BYTES, "script.exe"))
        assert exc_info.value.field == "extension"

    def test_disallowed_mime_raises(self, backend):
        cfg = UploadConfig(allowed_mime_types={"image/jpeg"})
        h = UploadHandler(config=cfg, backend=backend)
        with pytest.raises(UploadValidationError) as exc_info:
            _run(h.handle(PDF_BYTES, "doc.pdf"))
        assert exc_info.value.field == "mime_type"

    def test_upload_dir_prefixes_path(self, backend):
        cfg = UploadConfig(upload_dir="photos")
        h = UploadHandler(config=cfg, backend=backend)
        result = _run(h.handle(TEXT_BYTES, "note.txt"))
        assert result.stored_path.startswith("photos/")

    def test_file_retrievable_from_backend(self, backend, handler):
        result = _run(handler.handle(TEXT_BYTES, "note.txt"))
        data = _run(backend.get_file(result.stored_path))
        assert data == TEXT_BYTES

    def test_auto_backend_creation_memory(self):
        cfg = UploadConfig(storage=StorageConfig(backend=StorageBackendType.MEMORY))
        h = UploadHandler(config=cfg)
        result = _run(h.handle(TEXT_BYTES, "note.txt"))
        assert result.stored_path

    def test_auto_backend_creation_local(self, tmp_path):
        cfg = UploadConfig(
            storage=StorageConfig(
                backend=StorageBackendType.LOCAL,
                local_path=tmp_path / "auto_uploads",
            )
        )
        h = UploadHandler(config=cfg)
        result = _run(h.handle(TEXT_BYTES, "note.txt"))
        assert result.stored_path


# ---------------------------------------------------------------------------
# UploadHandler — batch uploads
# ---------------------------------------------------------------------------


class TestBatchUpload:
    @pytest.fixture
    def backend(self):
        return MemoryStorageBackend()

    @pytest.fixture
    def handler(self, backend):
        return UploadHandler(config=UploadConfig(), backend=backend)

    def test_batch_two_files(self, handler):
        files = [(TEXT_BYTES, "a.txt"), (JPEG_BYTES, "b.jpg")]
        results = _run(handler.handle_batch(files))
        assert len(results) == 2

    def test_batch_returns_upload_results(self, handler):
        files = [(TEXT_BYTES, "a.txt")]
        results = _run(handler.handle_batch(files))
        assert isinstance(results[0], UploadResult)

    def test_batch_partial_failure_raises(self, backend):
        cfg = UploadConfig(max_file_size=5)
        h = UploadHandler(config=cfg, backend=backend)
        files = [
            (b"ok", "small.txt"),
            (b"too large data exceeds limit", "big.txt"),
        ]
        with pytest.raises(BatchUploadError) as exc_info:
            _run(h.handle_batch(files))
        err = exc_info.value
        assert len(err.errors) == 1
        assert len(err.successful) == 1

    def test_batch_all_fail_raises(self, backend):
        cfg = UploadConfig(max_file_size=1)
        h = UploadHandler(config=cfg, backend=backend)
        files = [(b"too big", "a.txt"), (b"also too big", "b.txt")]
        with pytest.raises(BatchUploadError) as exc_info:
            _run(h.handle_batch(files))
        assert len(exc_info.value.errors) == 2

    def test_batch_empty_list(self, handler):
        results = _run(handler.handle_batch([]))
        assert results == []

    def test_batch_error_message(self, backend):
        cfg = UploadConfig(max_file_size=1)
        h = UploadHandler(config=cfg, backend=backend)
        with pytest.raises(BatchUploadError) as exc_info:
            _run(h.handle_batch([(b"too big", "file.txt")]))
        assert "file.txt" in str(exc_info.value)


# ---------------------------------------------------------------------------
# UploadResult model
# ---------------------------------------------------------------------------


class TestUploadResult:
    def test_fields_present(self):
        r = UploadResult(
            original_filename="photo.jpg",
            stored_path="abc123.jpg",
            size=1024,
            mime_type="image/jpeg",
        )
        assert r.original_filename == "photo.jpg"
        assert r.stored_path == "abc123.jpg"
        assert r.size == 1024
        assert r.mime_type == "image/jpeg"
        assert r.created_at is not None

    def test_url_optional(self):
        r = UploadResult(
            original_filename="x.txt",
            stored_path="x.txt",
            size=5,
            mime_type="text/plain",
        )
        assert r.url is None


# ---------------------------------------------------------------------------
# Image processing (optional — skipped if Pillow is not installed)
# ---------------------------------------------------------------------------

pytestmark_no_pillow = pytest.mark.skipif(
    not HAS_PILLOW, reason="Pillow not installed"
)


def _make_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a real PNG using Pillow (only called when Pillow is available)."""
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytestmark_no_pillow
class TestImageProcessor:
    @pytest.fixture
    def proc(self):
        return ImageProcessor()

    @pytest.fixture
    def png(self):
        return _make_png_bytes(200, 150)

    def test_resize_reduces_dimensions(self, proc, png):
        result = proc.resize(png, width=50, height=50)
        from PIL import Image

        img = Image.open(io.BytesIO(result))
        assert img.width <= 50
        assert img.height <= 50

    def test_resize_without_aspect(self, proc, png):
        result = proc.resize(png, width=60, height=40, keep_aspect=False)
        from PIL import Image

        img = Image.open(io.BytesIO(result))
        assert img.width == 60
        assert img.height == 40

    def test_thumbnail_fits_within_size(self, proc, png):
        result = proc.thumbnail(png, size=(64, 64))
        from PIL import Image

        img = Image.open(io.BytesIO(result))
        assert img.width <= 64
        assert img.height <= 64

    def test_convert_to_jpeg(self, proc, png):
        result = proc.convert(png, target_format="JPEG")
        assert result[:3] == b"\xff\xd8\xff"  # JPEG magic

    def test_get_info_returns_dict(self, proc, png):
        info = proc.get_info(png)
        assert info["width"] == 200
        assert info["height"] == 150
        assert "format" in info
        assert "mode" in info

    def test_resize_preserves_bytes_type(self, proc, png):
        result = proc.resize(png, width=50, height=50)
        assert isinstance(result, bytes)


@pytestmark_no_pillow
class TestValidateImageDimensions:
    def test_within_limits_passes(self):
        png = _make_png_bytes(100, 100)
        w, h = validate_image_dimensions(png, max_width=200, max_height=200)
        assert w == 100
        assert h == 100

    def test_exceeds_width_raises(self):
        png = _make_png_bytes(300, 100)
        with pytest.raises(ValueError, match="width"):
            validate_image_dimensions(png, max_width=200)

    def test_exceeds_height_raises(self):
        png = _make_png_bytes(100, 300)
        with pytest.raises(ValueError, match="height"):
            validate_image_dimensions(png, max_height=200)

    def test_no_limits_passes(self):
        png = _make_png_bytes(9999, 9999)
        w, h = validate_image_dimensions(png)
        assert w == 9999
        assert h == 9999


def test_image_processor_raises_without_pillow(monkeypatch):
    """ImageProcessor raises ImportError when Pillow is absent."""
    import nitro.uploads.image as img_module

    monkeypatch.setattr(img_module, "HAS_PILLOW", False)
    proc = ImageProcessor()
    with pytest.raises(ImportError, match="Pillow"):
        proc.get_info(b"fake")


def test_validate_image_dimensions_raises_without_pillow(monkeypatch):
    """validate_image_dimensions raises ImportError when Pillow is absent."""
    import nitro.uploads.image as img_module

    monkeypatch.setattr(img_module, "HAS_PILLOW", False)
    with pytest.raises(ImportError, match="Pillow"):
        validate_image_dimensions(b"fake")
