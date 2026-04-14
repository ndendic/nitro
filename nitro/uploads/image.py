"""
Image-specific utilities for the Nitro uploads module.

Requires Pillow (``pip install Pillow``). All public symbols degrade gracefully
when Pillow is not installed: functions raise ``ImportError`` with a helpful
message instead of crashing at import time.
"""

from __future__ import annotations

import io
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Pillow availability check
# ---------------------------------------------------------------------------

try:
    from PIL import Image as _PILImage

    HAS_PILLOW = True
except ImportError:  # pragma: no cover
    HAS_PILLOW = False
    _PILImage = None  # type: ignore[assignment]


def _require_pillow() -> None:
    if not HAS_PILLOW:
        raise ImportError(
            "Pillow is required for image processing. "
            "Install it with: pip install Pillow"
        )


# ---------------------------------------------------------------------------
# Dimension validation
# ---------------------------------------------------------------------------


def validate_image_dimensions(
    data: bytes,
    *,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
) -> Tuple[int, int]:
    """Validate image dimensions.

    Args:
        data: Raw image bytes.
        max_width: Maximum allowed width in pixels (None = no limit).
        max_height: Maximum allowed height in pixels (None = no limit).

    Returns:
        (width, height) tuple for the image.

    Raises:
        ImportError: If Pillow is not installed.
        ValueError: If dimensions exceed the specified limits.
        OSError: If the bytes cannot be decoded as an image.
    """
    _require_pillow()
    img = _PILImage.open(io.BytesIO(data))
    width, height = img.size
    if max_width is not None and width > max_width:
        raise ValueError(
            f"Image width {width}px exceeds maximum of {max_width}px."
        )
    if max_height is not None and height > max_height:
        raise ValueError(
            f"Image height {height}px exceeds maximum of {max_height}px."
        )
    return width, height


# ---------------------------------------------------------------------------
# ImageProcessor
# ---------------------------------------------------------------------------


class ImageProcessor:
    """Utility class for common image transformations.

    All methods return the processed image as bytes in the requested format.

    Requires Pillow — methods will raise ``ImportError`` if it's not installed.

    Example::

        from nitro.uploads.image import ImageProcessor

        proc = ImageProcessor()
        resized = proc.resize(image_bytes, width=800, height=600)
        thumb   = proc.thumbnail(image_bytes, size=(128, 128))
        webp    = proc.convert(image_bytes, target_format="WEBP")
    """

    def resize(
        self,
        data: bytes,
        *,
        width: int,
        height: int,
        keep_aspect: bool = True,
        output_format: Optional[str] = None,
    ) -> bytes:
        """Resize an image to the given dimensions.

        Args:
            data: Raw image bytes.
            width: Target width in pixels.
            height: Target height in pixels.
            keep_aspect: If True, maintain aspect ratio (may result in smaller image).
            output_format: Output image format (e.g. "JPEG", "PNG"). Defaults to
                           the source format.

        Returns:
            Processed image bytes.
        """
        _require_pillow()
        img = _PILImage.open(io.BytesIO(data))
        fmt = output_format or img.format or "PNG"

        if keep_aspect:
            img.thumbnail((width, height), _PILImage.LANCZOS)
        else:
            img = img.resize((width, height), _PILImage.LANCZOS)

        buf = io.BytesIO()
        # JPEG doesn't support alpha channel
        if fmt.upper() in ("JPEG", "JPG") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        return buf.getvalue()

    def thumbnail(
        self,
        data: bytes,
        *,
        size: Tuple[int, int] = (128, 128),
        output_format: Optional[str] = None,
    ) -> bytes:
        """Generate a thumbnail (preserves aspect ratio, fits within size box).

        Args:
            data: Raw image bytes.
            size: (max_width, max_height) bounding box.
            output_format: Output image format. Defaults to source format.

        Returns:
            Thumbnail bytes.
        """
        _require_pillow()
        img = _PILImage.open(io.BytesIO(data))
        fmt = output_format or img.format or "PNG"
        img.thumbnail(size, _PILImage.LANCZOS)
        buf = io.BytesIO()
        if fmt.upper() in ("JPEG", "JPG") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        return buf.getvalue()

    def convert(
        self,
        data: bytes,
        *,
        target_format: str,
        quality: int = 85,
    ) -> bytes:
        """Convert an image to a different format.

        Args:
            data: Raw image bytes.
            target_format: Target format string (e.g. "WEBP", "PNG", "JPEG").
            quality: Compression quality for lossy formats (1-95).

        Returns:
            Converted image bytes.
        """
        _require_pillow()
        img = _PILImage.open(io.BytesIO(data))
        buf = io.BytesIO()
        fmt = target_format.upper()
        save_kwargs: dict = {}
        if fmt in ("JPEG", "JPG", "WEBP"):
            save_kwargs["quality"] = quality
        if fmt in ("JPEG", "JPG") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=fmt, **save_kwargs)
        return buf.getvalue()

    def get_info(self, data: bytes) -> dict:
        """Return basic image metadata.

        Args:
            data: Raw image bytes.

        Returns:
            Dict with keys: width, height, format, mode.
        """
        _require_pillow()
        img = _PILImage.open(io.BytesIO(data))
        width, height = img.size
        return {
            "width": width,
            "height": height,
            "format": img.format,
            "mode": img.mode,
        }
