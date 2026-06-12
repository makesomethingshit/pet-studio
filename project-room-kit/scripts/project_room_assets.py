"""Shared image helpers for Project Room Kit assets."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


ROOM_ALPHA_MODES = {"safe", "balanced", "aggressive"}


def is_near_white_margin_pixel(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    if alpha == 0:
        return False
    return red >= 238 and green >= 238 and blue >= 238 and max(red, green, blue) - min(red, green, blue) <= 24


def is_room_margin_pixel(pixel: tuple[int, int, int, int], mode: str = "balanced") -> bool:
    if mode not in ROOM_ALPHA_MODES:
        raise ValueError(f"Unknown room alpha cleanup mode: {mode}")
    red, green, blue, alpha = pixel
    if alpha == 0:
        return False
    brightness = (red + green + blue) / 3
    spread = max(red, green, blue) - min(red, green, blue)
    if mode == "safe":
        return is_near_white_margin_pixel(pixel)
    if mode == "balanced":
        return (min(red, green, blue) >= 230 and spread <= 36) or (alpha <= 64 and brightness >= 160)
    return (brightness >= 218 and spread <= 84) or (alpha <= 112 and brightness >= 96)


def edge_connected_margin_points(image: Image.Image, mode: str = "balanced") -> set[tuple[int, int]]:
    if mode not in ROOM_ALPHA_MODES:
        raise ValueError(f"Unknown room alpha cleanup mode: {mode}")
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    for x in range(width):
        for y in (0, height - 1):
            if is_room_margin_pixel(pixels[x, y], mode):
                queue.append((x, y))
                seen.add((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if (x, y) not in seen and is_room_margin_pixel(pixels[x, y], mode):
                queue.append((x, y))
                seen.add((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in seen:
                continue
            if is_room_margin_pixel(pixels[nx, ny], mode):
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for index in range(0, len(data), 4):
        if data[index + 3] == 0:
            data[index] = 0
            data[index + 1] = 0
            data[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(data))


def remove_room_edge_margin(image: Image.Image, mode: str = "balanced") -> Image.Image:
    rgba = image.convert("RGBA")
    points = edge_connected_margin_points(rgba, mode)
    if not points:
        return clear_transparent_rgb(rgba)
    pixels = rgba.load()
    for point in points:
        pixels[point] = (0, 0, 0, 0)
    return clear_transparent_rgb(rgba)


def cleanup_room_image(source: Path, target: Path, mode: str = "balanced") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        remove_room_edge_margin(image, mode).save(target)


def room_edge_margin_pixel_count(path: Path, mode: str = "balanced") -> int:
    with Image.open(path) as image:
        return len(edge_connected_margin_points(image, mode))
