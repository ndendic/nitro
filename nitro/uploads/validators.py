"""
File validation utilities for the Nitro uploads module.

Provides helpers to validate file size, extension, MIME type, and filename safety.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Optional, Set


class UploadValidationError(Exception):
    """Raised when a file fails upload validation.

    Attributes:
        message: Human-readable error description.
        field: Which validation check failed (size, extension, mime_type, filename).
    """

    def __init__(self, message: str, field: str = "unknown") -> None:
        super().__init__(message)
        self.message = message
        self.field = field

    def __str__(self) -> str:
        return self.message


# ---------------------------------------------------------------------------
# Magic byte signatures for MIME detection
# ---------------------------------------------------------------------------

_MAGIC_SIGNATURES: list[tuple[bytes, int, str]] = [
    # (signature_bytes, offset, mime_type)
    (b"\xff\xd8\xff", 0, "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "image/png"),
    (b"GIF87a", 0, "image/gif"),
    (b"GIF89a", 0, "image/gif"),
    (b"RIFF", 0, "image/webp"),  # checked further below
    (b"BM", 0, "image/bmp"),
    (b"\x49\x49\x2a\x00", 0, "image/tiff"),
    (b"\x4d\x4d\x00\x2a", 0, "image/tiff"),
    (b"%PDF", 0, "application/pdf"),
    (b"PK\x03\x04", 0, "application/zip"),
    (b"PK\x05\x06", 0, "application/zip"),
    (b"PK\x07\x08", 0, "application/zip"),
    (b"\x1f\x8b", 0, "application/gzip"),
    (b"BZh", 0, "application/x-bzip2"),
    (b"\xfd7zXZ\x00", 0, "application/x-xz"),
    (b"Rar!\x1a\x07", 0, "application/x-rar-compressed"),
    (b"\x7fELF", 0, "application/x-elf"),
    (b"MZ", 0, "application/x-msdownload"),
    (b"\xcf\xfa\xed\xfe", 0, "application/x-mach-binary"),
    (b"\xce\xfa\xed\xfe", 0, "application/x-mach-binary"),
    (b"OggS", 0, "audio/ogg"),
    (b"fLaC", 0, "audio/flac"),
    (b"ID3", 0, "audio/mpeg"),
    (b"\xff\xfb", 0, "audio/mpeg"),
    (b"\xff\xf3", 0, "audio/mpeg"),
    (b"\xff\xf2", 0, "audio/mpeg"),
    (b"<!DOCTYPE html", 0, "text/html"),
    (b"<html", 0, "text/html"),
    (b"<?xml", 0, "application/xml"),
]

# MIME extension fallback map
_EXT_TO_MIME: dict[str, str] = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".xml": "application/xml",
    ".js": "application/javascript",
    ".css": "text/css",
    ".md": "text/markdown",
}


def detect_mime_type(data: bytes, filename: Optional[str] = None) -> str:
    """Detect MIME type from magic bytes, falling back to extension or octet-stream.

    Args:
        data: Raw file bytes (only the first 16 bytes are examined).
        filename: Original filename used as fallback hint.

    Returns:
        Detected MIME type string.
    """
    header = data[:16] if len(data) >= 16 else data

    for sig, offset, mime in _MAGIC_SIGNATURES:
        chunk = header[offset : offset + len(sig)]
        if chunk == sig:
            # Distinguish WebP from other RIFF formats
            if mime == "image/webp" and len(data) >= 12:
                if data[8:12] == b"WEBP":
                    return "image/webp"
                return "video/x-msvideo"  # AVI is also RIFF
            return mime

    if filename:
        ext = Path(filename).suffix.lower()
        if ext in _EXT_TO_MIME:
            return _EXT_TO_MIME[ext]

    return "application/octet-stream"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def validate_file_size(data: bytes, max_size: int) -> None:
    """Raise UploadValidationError if data exceeds max_size bytes.

    Args:
        data: Raw file bytes.
        max_size: Maximum allowed size in bytes.

    Raises:
        UploadValidationError: If file exceeds max_size.
    """
    size = len(data)
    if size > max_size:
        raise UploadValidationError(
            f"File size {size} bytes exceeds maximum of {max_size} bytes.",
            field="size",
        )


def validate_extension(filename: str, allowed: Set[str]) -> None:
    """Raise UploadValidationError if the file extension is not in allowed set.

    Args:
        filename: Original filename (or just the extension).
        allowed: Set of permitted extensions (e.g. {".jpg", ".png"}).
                 An empty set means all extensions are permitted.

    Raises:
        UploadValidationError: If extension not in allowed set.
    """
    if not allowed:
        return  # no restriction
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise UploadValidationError(
            f"File extension {ext!r} is not allowed. "
            f"Allowed extensions: {sorted(allowed)}",
            field="extension",
        )


def validate_mime_type(
    data: bytes,
    allowed_mimes: Set[str],
    filename: Optional[str] = None,
) -> str:
    """Detect and validate the MIME type from magic bytes.

    Args:
        data: Raw file bytes.
        allowed_mimes: Set of permitted MIME type strings.
                       An empty set means all MIME types are permitted.
        filename: Optional filename for extension-based fallback detection.

    Returns:
        The detected MIME type string.

    Raises:
        UploadValidationError: If detected MIME type is not in allowed_mimes.
    """
    detected = detect_mime_type(data, filename)
    if allowed_mimes and detected not in allowed_mimes:
        raise UploadValidationError(
            f"File MIME type {detected!r} is not allowed. "
            f"Allowed types: {sorted(allowed_mimes)}",
            field="mime_type",
        )
    return detected


def sanitize_filename(filename: str) -> str:
    """Return a safe version of filename, preventing path traversal and stripping unsafe chars.

    - Strips directory components (path traversal prevention)
    - Normalises unicode to ASCII where possible
    - Removes characters that are unsafe on most filesystems
    - Collapses whitespace to underscores
    - Falls back to "upload" if nothing safe remains

    Args:
        filename: Original user-supplied filename.

    Returns:
        A sanitised filename string (basename only, no directories).
    """
    if not filename:
        return "upload"

    # Normalise unicode → ASCII
    try:
        normalised = unicodedata.normalize("NFKD", filename)
        normalised = normalised.encode("ascii", "ignore").decode("ascii")
    except Exception:
        normalised = filename

    # Strip any directory components — guard against path traversal
    basename = os.path.basename(normalised.replace("\\", "/"))

    # Remove null bytes and other control chars
    basename = re.sub(r"[\x00-\x1f\x7f]", "", basename)

    # Remove characters that are unsafe on common filesystems
    # Allow: alphanumeric, dash, underscore, dot
    basename = re.sub(r"[^\w\s.\-]", "", basename)

    # Collapse whitespace / multiple dots
    basename = re.sub(r"\s+", "_", basename)
    basename = re.sub(r"\.{2,}", ".", basename)

    # Strip leading dots and dashes (hidden files / relative paths)
    basename = basename.lstrip(".-")

    # Ensure we have something left
    if not basename or basename == ".":
        return "upload"

    return basename
