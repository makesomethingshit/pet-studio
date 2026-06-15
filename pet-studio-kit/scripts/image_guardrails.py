"""Shared image resource guards for Pet Studio assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


MAX_IMAGE_FILE_BYTES = 25 * 1024 * 1024
MAX_IMAGE_PIXEL_COUNT = 4_000_000


@dataclass(frozen=True)
class ImageResourceInfo:
    width: int
    height: int
    file_size: int


class ImageResourceError(ValueError):
    """Raised when an image is malformed or exceeds resource limits."""


def image_resource_info(path: Path) -> ImageResourceInfo:
    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_FILE_BYTES:
        raise ImageResourceError(f"Image file is too large: {file_size} bytes")
    try:
        with Image.open(path) as image:
            image.verify()
            width, height = image.size
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ImageResourceError(f"Image cannot be read: {path}") from exc
    pixels = width * height
    if pixels > MAX_IMAGE_PIXEL_COUNT:
        raise ImageResourceError(f"Image is too large: {width}x{height} pixels")
    return ImageResourceInfo(width=width, height=height, file_size=file_size)


def safe_image_size(path: Path) -> tuple[int, int]:
    info = image_resource_info(path)
    return info.width, info.height


def safe_rgba_image(path: Path) -> Image.Image:
    image_resource_info(path)
    with Image.open(path) as image:
        return image.convert("RGBA")


def average_opaque_rgb(path: Path, thumbnail_size: tuple[int, int] = (96, 96)) -> tuple[int, int, int] | None:
    try:
        image = safe_rgba_image(path)
        try:
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            source_pixels = image.load()
            pixels = [
                source_pixels[x, y][:3]
                for y in range(image.height)
                for x in range(image.width)
                if source_pixels[x, y][3] >= 96
            ]
        finally:
            image.close()
    except ImageResourceError:
        return None
    if not pixels:
        return None
    count = len(pixels)
    return (
        sum(pixel[0] for pixel in pixels) // count,
        sum(pixel[1] for pixel in pixels) // count,
        sum(pixel[2] for pixel in pixels) // count,
    )
