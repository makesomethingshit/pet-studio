"""Shared image helpers for Project Room Kit assets."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


def is_near_white_margin_pixel(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    if alpha == 0:
        return False
    return red >= 238 and green >= 238 and blue >= 238 and max(red, green, blue) - min(red, green, blue) <= 24


def edge_connected_margin_points(image: Image.Image) -> set[tuple[int, int]]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    for x in range(width):
        for y in (0, height - 1):
            if is_near_white_margin_pixel(pixels[x, y]):
                queue.append((x, y))
                seen.add((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if (x, y) not in seen and is_near_white_margin_pixel(pixels[x, y]):
                queue.append((x, y))
                seen.add((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in seen:
                continue
            if is_near_white_margin_pixel(pixels[nx, ny]):
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


def remove_room_edge_margin(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    points = edge_connected_margin_points(rgba)
    if not points:
        return clear_transparent_rgb(rgba)
    pixels = rgba.load()
    for point in points:
        pixels[point] = (0, 0, 0, 0)
    return clear_transparent_rgb(rgba)


def cleanup_room_image(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        remove_room_edge_margin(image).save(target)


def room_edge_margin_pixel_count(path: Path) -> int:
    with Image.open(path) as image:
        return len(edge_connected_margin_points(image))
