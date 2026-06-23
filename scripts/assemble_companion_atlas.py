#!/usr/bin/env python3
"""Assemble web companion row strips into an atlas, previews, and QA assets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_DURATIONS = {
    "idle": [220, 160, 160, 260, 140, 140, 180, 320],
    "greeting": [120, 120, 120, 180, 120, 120, 160, 300],
    "listening": [180, 180, 140, 140, 180, 220, 140, 260],
    "thinking": [140, 120, 140, 180, 180, 140, 160, 260],
    "working": [100, 100, 110, 120, 120, 100, 120, 180],
    "answering": [90, 90, 100, 110, 100, 90, 120, 160],
    "success": [100, 100, 120, 120, 140, 160, 180, 320],
    "error": [130, 130, 160, 180, 180, 160, 140, 320],
    "confused": [160, 160, 180, 220, 160, 160, 180, 300],
    "sleeping": [300, 300, 360, 420, 300, 300, 360, 500],
}


SMOOTH_DURATION_TEMPLATES = {
    "idle": [180, 150, 150, 200, 140, 140, 180, 150, 150, 220, 160, 300],
    "greeting": [90, 90, 100, 110, 130, 120, 110, 100, 110, 140, 160, 260],
    "listening": [120, 120, 130, 140, 150, 160, 130, 120, 130, 150, 160, 240],
    "thinking": [120, 120, 140, 180, 120, 120, 160, 180, 120, 140, 180, 260],
    "working": [90, 100, 90, 110, 100, 90, 120, 100, 90, 110, 100, 170],
    "answering": [90, 90, 100, 110, 90, 100, 120, 90, 100, 110, 90, 160],
    "success": [90, 90, 110, 120, 140, 150, 130, 120, 130, 150, 160, 280],
    "error": [120, 130, 150, 170, 180, 160, 150, 140, 130, 140, 160, 300],
    "confused": [130, 140, 160, 180, 160, 140, 150, 180, 160, 150, 170, 280],
    "sleeping": [300, 320, 360, 420, 340, 320, 360, 450, 340, 320, 360, 500],
}


def default_durations_for_state(name: str, frames: int) -> list[int]:
    defaults = DEFAULT_DURATIONS.get(name)
    if defaults and len(defaults) == frames:
        return list(defaults)

    template = SMOOTH_DURATION_TEMPLATES.get(name, [120, 140, 160, 180, 140, 120, 160, 220])
    if frames == len(template):
        return list(template)
    if frames <= 1:
        return [template[0]]

    return [
        template[round(index * (len(template) - 1) / (frames - 1))]
        for index in range(frames)
    ]


def parse_hex_color(value: str) -> tuple[int, int, int]:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        raise ValueError(f"expected #RRGGBB color, got {value!r}")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def hex_from_chroma_key(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    hex_value = value.get("hex")
    if isinstance(hex_value, str) and hex_value.strip():
        return hex_value
    rgb = value.get("rgb")
    if isinstance(rgb, list) and len(rgb) == 3:
        return "#" + "".join(f"{int(channel):02X}" for channel in rgb)
    return None


def manifest_chroma_key(manifest: dict[str, Any]) -> str | None:
    style = manifest.get("style")
    if isinstance(style, dict):
        key = hex_from_chroma_key(style.get("chromaKey"))
        if key:
            return key
    return hex_from_chroma_key(manifest.get("chromaKey"))


def request_chroma_key(manifest_path: Path) -> str | None:
    request_path = manifest_path.parent / "companion_request.json"
    if not request_path.is_file():
        return None
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(request, dict):
        return None
    return hex_from_chroma_key(request.get("chromaKey"))


def resolve_key_color(manifest: dict[str, Any], manifest_path: Path, override: str | None) -> str:
    if override:
        return override
    return manifest_chroma_key(manifest) or request_chroma_key(manifest_path) or "#FF00FF"


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((left - right) ** 2 for left, right in zip(a, b)) ** 0.5


def is_key_spill(rgb: tuple[int, int, int], key: tuple[int, int, int], threshold: int) -> bool:
    r, g, b = rgb
    if key == (255, 0, 255):
        return (
            r >= 45
            and b >= 45
            and g <= 135
            and abs(r - b) <= 115
            and (r - g) >= threshold
            and (b - g) >= threshold
        )
    return color_distance(rgb, key) <= max(90, threshold * 2.5)


def key_to_alpha(
    image: Image.Image,
    key: tuple[int, int, int],
    tolerance: int,
    spill_threshold: int,
) -> Image.Image:
    rgba = image.convert("RGBA")
    pixel_data = rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata()
    pixels = []
    for r, g, b, a in pixel_data:
        if a == 0 or color_distance((r, g, b), key) <= tolerance or is_key_spill((r, g, b), key, spill_threshold):
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append((r, g, b, 255))
    rgba.putdata(pixels)
    return rgba


def has_transparent_neighbor(alpha_pixels: Any, x: int, y: int, width: int, height: int) -> bool:
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if nx == x and ny == y:
                continue
            if not alpha_pixels[nx, ny]:
                return True
    return False


def remove_edge_spill(
    image: Image.Image,
    key: tuple[int, int, int],
    threshold: int,
    passes: int,
) -> Image.Image:
    if passes <= 0:
        return image

    rgba = image.copy()
    for _pass in range(passes):
        alpha = rgba.getchannel("A")
        width, height = rgba.size
        pixels = rgba.load()
        alpha_pixels = alpha.load()
        clear_pixels: list[tuple[int, int]] = []

        for y in range(height):
            for x in range(width):
                if not alpha_pixels[x, y]:
                    continue
                r, g, b, _a = pixels[x, y]
                if is_key_spill((r, g, b), key, threshold) and has_transparent_neighbor(alpha_pixels, x, y, width, height):
                    clear_pixels.append((x, y))

        if not clear_pixels:
            break
        for x, y in clear_pixels:
            pixels[x, y] = (0, 0, 0, 0)

    return rgba


def clean_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.copy()
    pixel_data = rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata()
    pixels = [(0, 0, 0, 0) if a == 0 else (r, g, b, a) for r, g, b, a in pixel_data]
    rgba.putdata(pixels)
    return rgba


def quantile(sorted_values: list[int], ratio: float) -> int:
    if not sorted_values:
        return 0
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * ratio)))
    return sorted_values[index]


def core_bbox_from_pixels(
    pixels: list[tuple[int, int]],
    low: float = 0.10,
    high: float = 0.90,
) -> tuple[int, int, int, int]:
    if not pixels:
        return (0, 0, 1, 1)
    xs = sorted(x for x, _y in pixels)
    ys = sorted(y for _x, y in pixels)
    return (
        quantile(xs, low),
        quantile(ys, low),
        quantile(xs, high) + 1,
        quantile(ys, high) + 1,
    )


def replace_spill_colors(
    image: Image.Image,
    key: tuple[int, int, int],
    threshold: int,
    radius: int = 4,
) -> Image.Image:
    rgba = image.copy()
    width, height = rgba.size
    source = rgba.load()
    replacements: dict[tuple[int, int], tuple[int, int, int, int]] = {}

    for y in range(height):
        for x in range(width):
            r, g, b, a = source[x, y]
            if not a or not is_key_spill((r, g, b), key, threshold):
                continue

            replacement: tuple[int, int, int, int] | None = None
            for distance in range(1, radius + 1):
                found = False
                for ny in range(max(0, y - distance), min(height, y + distance + 1)):
                    for nx in range(max(0, x - distance), min(width, x + distance + 1)):
                        if abs(nx - x) != distance and abs(ny - y) != distance:
                            continue
                        nr, ng, nb, na = source[nx, ny]
                        if na and not is_key_spill((nr, ng, nb), key, threshold):
                            replacement = (nr, ng, nb, a)
                            found = True
                            break
                    if found:
                        break
                if replacement:
                    break

            replacements[(x, y)] = replacement if replacement else (0, 0, 0, a)

    for (x, y), value in replacements.items():
        source[x, y] = value
    return rgba


def count_outline_halo_pixels(image: Image.Image, key: tuple[int, int, int], threshold: int) -> int:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    pixels = rgba.load()
    alpha_pixels = alpha.load()
    count = 0

    for y in range(height):
        for x in range(width):
            if not alpha_pixels[x, y]:
                continue
            r, g, b, _a = pixels[x, y]
            if is_key_spill((r, g, b), key, threshold) and has_transparent_neighbor(alpha_pixels, x, y, width, height):
                count += 1

    return count


def resize_rgba_premultiplied(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    if image.size == size:
        return clean_transparent_rgb(image)

    rgba = clean_transparent_rgb(image.convert("RGBA"))
    premultiplied = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    premultiplied_pixels = []
    pixel_data = rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata()
    for r, g, b, a in pixel_data:
        premultiplied_pixels.append((r * a // 255, g * a // 255, b * a // 255, a))
    premultiplied.putdata(premultiplied_pixels)

    resized = premultiplied.resize(size, Image.Resampling.LANCZOS)
    unpremultiplied = Image.new("RGBA", size, (0, 0, 0, 0))
    output_pixels = []
    resized_data = resized.get_flattened_data() if hasattr(resized, "get_flattened_data") else resized.getdata()
    for r, g, b, a in resized_data:
        if a == 0:
            output_pixels.append((0, 0, 0, 0))
        else:
            output_pixels.append(
                (
                    min(255, round(r * 255 / a)),
                    min(255, round(g * 255 / a)),
                    min(255, round(b * 255 / a)),
                    a,
                )
            )
    unpremultiplied.putdata(output_pixels)
    return unpremultiplied


def crop_to_content(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    return image.crop(bbox)


def remove_small_components(image: Image.Image, min_area: int) -> Image.Image:
    if min_area <= 0:
        return image

    rgba = image.copy()
    alpha = rgba.getchannel("A")
    width, height = alpha.size
    alpha_pixels = alpha.load()
    visited = bytearray(width * height)
    clear_pixels: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or not alpha_pixels[x, y]:
                continue

            component: list[tuple[int, int]] = []
            stack = [(x, y)]
            visited[index] = 1

            while stack:
                px, py = stack.pop()
                component.append((px, py))
                for ny in range(max(0, py - 1), min(height, py + 2)):
                    for nx in range(max(0, px - 1), min(width, px + 2)):
                        nindex = ny * width + nx
                        if visited[nindex] or not alpha_pixels[nx, ny]:
                            continue
                        visited[nindex] = 1
                        stack.append((nx, ny))

            if len(component) < min_area:
                clear_pixels.extend(component)

    for x, y in clear_pixels:
        alpha_pixels[x, y] = 0
    rgba.putalpha(alpha)
    return rgba


def connected_components_with_pixels(alpha: Image.Image, min_area: int) -> list[dict[str, Any]]:
    width, height = alpha.size
    alpha_pixels = alpha.load()
    visited = bytearray(width * height)
    components: list[dict[str, Any]] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or not alpha_pixels[x, y]:
                continue

            pixels: list[tuple[int, int]] = []
            stack = [(x, y)]
            visited[index] = 1
            x0 = x1 = x
            y0 = y1 = y

            while stack:
                px, py = stack.pop()
                pixels.append((px, py))
                x0 = min(x0, px)
                x1 = max(x1, px)
                y0 = min(y0, py)
                y1 = max(y1, py)
                for ny in range(max(0, py - 1), min(height, py + 2)):
                    for nx in range(max(0, px - 1), min(width, px + 2)):
                        nindex = ny * width + nx
                        if visited[nindex] or not alpha_pixels[nx, ny]:
                            continue
                        visited[nindex] = 1
                        stack.append((nx, ny))

            area = len(pixels)
            if area >= min_area:
                bbox = (x0, y0, x1 + 1, y1 + 1)
                components.append(
                    {
                        "area": area,
                        "bbox": bbox,
                        "coreBbox": core_bbox_from_pixels(pixels),
                        "center": ((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2),
                        "pixels": pixels,
                    }
                )

    return components


def component_frame_slots(
    strip: Image.Image,
    expected: int,
    body_min_area: int,
    component_min_area: int,
) -> tuple[list[Image.Image], list[dict[str, Any]]]:
    components = connected_components_with_pixels(strip.getchannel("A"), component_min_area)
    body_candidates = [component for component in components if int(component["area"]) >= body_min_area]
    if len(body_candidates) < expected:
        raise ValueError(f"expected {expected} body components, found {len(body_candidates)}")
    if len(body_candidates) > expected:
        bodies = sorted(body_candidates, key=lambda component: int(component["area"]), reverse=True)[:expected]
    else:
        bodies = body_candidates
    if len(bodies) != expected:
        raise ValueError(f"expected {expected} body components, found {len(bodies)}")

    bodies = sorted(bodies, key=lambda component: float(component["center"][0]))
    centers = [float(component["center"][0]) for component in bodies]
    boundaries = [float("-inf")]
    for left, right in zip(centers, centers[1:]):
        boundaries.append((left + right) / 2)
    boundaries.append(float("inf"))

    assignments: list[list[dict[str, Any]]] = [[] for _index in range(expected)]
    for component in components:
        center_x = float(component["center"][0])
        slot_index = min(
            range(expected),
            key=lambda index: (
                0 if boundaries[index] <= center_x < boundaries[index + 1] else 1,
                abs(center_x - centers[index]),
            ),
        )
        assignments[slot_index].append(component)

    source_pixels = strip.load()
    slots: list[Image.Image] = []
    metadata: list[dict[str, Any]] = []
    for slot_index, slot_components in enumerate(assignments):
        slot = Image.new("RGBA", strip.size, (0, 0, 0, 0))
        slot_pixels = slot.load()
        x0 = strip.width
        y0 = strip.height
        x1 = 0
        y1 = 0
        component_areas: list[int] = []
        body_bbox = tuple(int(value) for value in bodies[slot_index]["bbox"])
        body_fit_bbox = tuple(int(value) for value in bodies[slot_index].get("coreBbox", body_bbox))
        for component in slot_components:
            component_areas.append(int(component["area"]))
            bx0, by0, bx1, by1 = component["bbox"]
            x0 = min(x0, bx0)
            y0 = min(y0, by0)
            x1 = max(x1, bx1)
            y1 = max(y1, by1)
            for x, y in component["pixels"]:
                slot_pixels[x, y] = source_pixels[x, y]
        slots.append(slot)
        metadata.append(
            {
                "index": slot_index,
                "bodyCenterX": centers[slot_index],
                "bbox": (x0, y0, x1, y1) if slot_components else None,
                "bodyBbox": body_bbox,
                "bodyFitBbox": body_fit_bbox,
                "components": len(slot_components),
                "componentAreas": sorted(component_areas, reverse=True),
            }
        )

    return slots, metadata


def column_runs(strip: Image.Image, expected: int) -> list[tuple[int, int]]:
    alpha = strip.getchannel("A")
    counts = [
        sum(1 for value in alpha.crop((x, 0, x + 1, strip.height)).tobytes() if value)
        for x in range(strip.width)
    ]

    last_merged: list[tuple[int, int]] = []
    for threshold in [140, 120, 100, 80, 60, 50, 40, 30, 20, 10]:
        runs: list[tuple[int, int]] = []
        start: int | None = None
        for x, count in enumerate(counts):
            if count > threshold and start is None:
                start = x
            elif count <= threshold and start is not None:
                runs.append((start, x - 1))
                start = None
        if start is not None:
            runs.append((start, strip.width - 1))

        for merge_gap in [10, 8, 6, 4, 2, 0]:
            merged: list[tuple[int, int]] = []
            for run in runs:
                if merged and run[0] - merged[-1][1] <= merge_gap:
                    merged[-1] = (merged[-1][0], run[1])
                else:
                    merged.append(run)

            last_merged = merged
            if len(merged) == expected:
                return merged

    raise ValueError(f"expected {expected} foreground runs, found {len(last_merged)}")


def frame_bounds_from_runs(strip_width: int, runs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    centers = [(start + end) / 2 for start, end in runs]
    bounds = [0]
    for left, right in zip(centers, centers[1:]):
        bounds.append(round((left + right) / 2))
    bounds.append(strip_width)
    return [(bounds[index], bounds[index + 1]) for index in range(len(runs))]


def equal_frame_bounds(width: int, frames: int) -> list[tuple[int, int]]:
    return [
        (round(width * index / frames), round(width * (index + 1) / frames))
        for index in range(frames)
    ]


def fit_to_cell(
    sprite: Image.Image,
    cell_width: int,
    cell_height: int,
    padding: int,
    key: tuple[int, int, int],
    spill_threshold: int,
    scale: float | None = None,
) -> Image.Image:
    max_width = max(1, cell_width - padding * 2)
    max_height = max(1, cell_height - padding * 2)
    if scale is None:
        scale = min(max_width / sprite.width, max_height / sprite.height, 1.0)
    width = max(1, int(round(sprite.width * scale)))
    height = max(1, int(round(sprite.height * scale)))
    if (width, height) != sprite.size:
        sprite = resize_rgba_premultiplied(sprite, (width, height))
    sprite = replace_spill_colors(sprite, key, spill_threshold)

    cell = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
    x = (cell_width - width) // 2
    y = cell_height - height - padding
    cell.alpha_composite(sprite, (x, y))
    return cell


def fit_scale_for_sprites(sprites: list[Image.Image], cell_width: int, cell_height: int, padding: int) -> float:
    max_width = max(1, cell_width - padding * 2)
    max_height = max(1, cell_height - padding * 2)
    sprite_width = max((sprite.width for sprite in sprites), default=1)
    sprite_height = max((sprite.height for sprite in sprites), default=1)
    return min(max_width / sprite_width, max_height / sprite_height, 1.0)


def fit_scale_for_body_anchored_sprites(
    sprite_infos: list[dict[str, Any]],
    cell_width: int,
    cell_height: int,
    padding: int,
    target_body_fit_size: tuple[float, float] | None = None,
) -> float:
    max_width = max(1, cell_width - padding * 2)
    max_height = max(1, cell_height - padding * 2)
    fit_boxes = [info.get("fit_bbox", info["body_bbox"]) for info in sprite_infos]
    body_width = max((bbox[2] - bbox[0] for bbox in fit_boxes), default=1)
    body_height = max((bbox[3] - bbox[1] for bbox in fit_boxes), default=1)
    if target_body_fit_size is not None:
        target_width, target_height = target_body_fit_size
        target_scale = min(target_width / body_width, target_height / body_height)
        cell_fit_scale = min(max_width / body_width, max_height / body_height)
        return min(target_scale, cell_fit_scale)
    return min(max_width / body_width, max_height / body_height, 1.0)


def alpha_composite_clipped(base: Image.Image, sprite: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + sprite.width)
    bottom = min(base.height, y + sprite.height)
    if right <= left or bottom <= top:
        return
    crop = sprite.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def body_anchor_state_y_offset(
    sprite_infos: list[dict[str, Any]],
    scale: float,
    cell_height: int,
    padding: int,
    edge_margin: int = 1,
    max_offset: int | None = None,
) -> int:
    needed_down = 0
    available_down: int | None = None
    for info in sprite_infos:
        sprite = info["sprite"]
        body_bbox = info["body_bbox"]
        height = max(1, int(round(sprite.height * scale)))
        body_bottom_y = body_bbox[3] * scale
        y = int(round(cell_height - padding - body_bottom_y))
        needed_down = max(needed_down, edge_margin - y)
        frame_available = cell_height - edge_margin - (y + height)
        available_down = frame_available if available_down is None else min(available_down, frame_available)
    if available_down is None or needed_down <= 0:
        return 0
    offset = max(0, min(needed_down, max(0, available_down)))
    if max_offset is not None:
        offset = min(offset, max(0, max_offset))
    return offset


def body_anchor_edges_clear(
    sprite_infos: list[dict[str, Any]],
    scale: float,
    cell_width: int,
    cell_height: int,
    padding: int,
    edge_margin: int = 1,
    max_y_offset: int | None = None,
) -> bool:
    y_offset = body_anchor_state_y_offset(sprite_infos, scale, cell_height, padding, edge_margin, max_y_offset)
    for info in sprite_infos:
        sprite = info["sprite"]
        body_bbox = info["body_bbox"]
        center_bbox = info.get("fit_bbox") or body_bbox
        width = max(1, int(round(sprite.width * scale)))
        height = max(1, int(round(sprite.height * scale)))
        center_x0, _center_y0, center_x1, _center_y1 = [value * scale for value in center_bbox]
        body_center_x = (center_x0 + center_x1) / 2
        x = int(round(cell_width / 2 - body_center_x))
        min_x = cell_width - padding - width
        max_x = padding
        if min_x <= max_x:
            x = min(max(x, min_x), max_x)
        body_bottom_y = body_bbox[3] * scale
        y = int(round(cell_height - padding - body_bottom_y)) + y_offset
        if x < edge_margin or x + width > cell_width - edge_margin:
            return False
        if y < edge_margin or y + height > cell_height - edge_margin:
            return False
    return True


def body_anchor_scale_for_edge_clearance(
    sprite_infos: list[dict[str, Any]],
    scale: float,
    cell_width: int,
    cell_height: int,
    padding: int,
    edge_margin: int = 1,
    max_y_offset: int | None = 2,
) -> float:
    if body_anchor_edges_clear(sprite_infos, scale, cell_width, cell_height, padding, edge_margin, max_y_offset):
        return scale

    low = 0.01
    high = scale
    for _attempt in range(24):
        middle = (low + high) / 2
        if body_anchor_edges_clear(sprite_infos, middle, cell_width, cell_height, padding, edge_margin, max_y_offset):
            low = middle
        else:
            high = middle
    return low


def fit_body_anchored_to_cell(
    sprite: Image.Image,
    body_bbox: tuple[int, int, int, int],
    cell_width: int,
    cell_height: int,
    padding: int,
    key: tuple[int, int, int],
    spill_threshold: int,
    scale: float,
    center_bbox: tuple[int, int, int, int] | None = None,
    y_offset: int = 0,
) -> Image.Image:
    width = max(1, int(round(sprite.width * scale)))
    height = max(1, int(round(sprite.height * scale)))
    if (width, height) != sprite.size:
        sprite = resize_rgba_premultiplied(sprite, (width, height))
    sprite = replace_spill_colors(sprite, key, spill_threshold)

    center_source_bbox = center_bbox or body_bbox
    center_x0, _center_y0, center_x1, _center_y1 = [value * scale for value in center_source_bbox]
    _body_x0, _body_y0, _body_x1, body_y1 = [value * scale for value in body_bbox]
    body_center_x = (center_x0 + center_x1) / 2
    body_bottom_y = body_y1

    x = int(round(cell_width / 2 - body_center_x))
    min_x = cell_width - padding - width
    max_x = padding
    if min_x <= max_x:
        x = min(max(x, min_x), max_x)
    y = int(round(cell_height - padding - body_bottom_y)) + y_offset

    cell = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
    alpha_composite_clipped(cell, sprite, x, y)
    return cell


def checkerboard(width: int, height: int, block: int = 16) -> Image.Image:
    image = Image.new("RGBA", (width, height), (245, 246, 248, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, block):
        for x in range(0, width, block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill=(226, 230, 235, 255))
    return image


def composite_on_checker(frame: Image.Image) -> Image.Image:
    base = checkerboard(frame.width, frame.height)
    base.alpha_composite(frame)
    return base.convert("RGB")


def state_items(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    states = manifest.get("states")
    if not isinstance(states, dict) or not states:
        raise ValueError("manifest must contain a non-empty states object")
    return sorted(states.items(), key=lambda item: int(item[1].get("row", 0)))


def median_float(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def body_fit_size_from_metadata(metadata: list[dict[str, Any]]) -> tuple[float, float] | None:
    widths: list[float] = []
    heights: list[float] = []
    for entry in metadata:
        bbox = entry.get("bodyFitBbox") or entry.get("bodyBbox")
        if not bbox:
            continue
        widths.append(float(bbox[2] - bbox[0]))
        heights.append(float(bbox[3] - bbox[1]))
    if not widths or not heights:
        return None
    return median_float(widths), median_float(heights)


def load_clean_row_strip(row_path: Path, args: argparse.Namespace) -> Image.Image:
    strip = key_to_alpha(Image.open(row_path), args.key_color_rgb, args.key_tolerance, args.spill_threshold)
    return remove_edge_spill(strip, args.key_color_rgb, args.spill_threshold, args.edge_spill_passes)


def measure_component_body_fit_size(
    row_path: Path,
    frame_count: int,
    args: argparse.Namespace,
) -> tuple[float, float] | None:
    strip = load_clean_row_strip(row_path, args)
    _slots, metadata = component_frame_slots(
        strip,
        frame_count,
        args.body_component_area,
        args.component_min_area,
    )
    return body_fit_size_from_metadata(metadata)


def resolve_body_fit_target(
    states: list[tuple[str, dict[str, Any]]],
    args: argparse.Namespace,
    report: dict[str, Any],
) -> tuple[float, float] | None:
    if args.extraction_mode != "component":
        return None

    requested_state = str(args.body_fit_target_state or "").strip()
    if requested_state.lower() in {"", "none", "off", "false"}:
        report["bodyFitTarget"] = {"enabled": False}
        return None

    state_sizes: dict[str, tuple[float, float]] = {}
    for name, state in states:
        row_path = args.row_dir / f"{name}.png"
        if not row_path.exists():
            continue
        try:
            size = measure_component_body_fit_size(row_path, int(state["frames"]), args)
        except ValueError as exc:
            report["warnings"].append(f"{name}: could not measure component body fit target: {exc}")
            continue
        if size is not None:
            state_sizes[name] = size

    if not state_sizes:
        report["bodyFitTarget"] = {"enabled": False, "reason": "no component body fit sizes measured"}
        return None

    if requested_state in state_sizes:
        selected_state = requested_state
        target_size = state_sizes[requested_state]
    else:
        selected_state = "pack-median"
        target_size = (
            median_float([size[0] for size in state_sizes.values()]),
            median_float([size[1] for size in state_sizes.values()]),
        )
        report["warnings"].append(
            f"body fit target state {requested_state!r} was not measured; used pack median body target"
        )

    report["bodyFitTarget"] = {
        "enabled": True,
        "targetState": requested_state,
        "selectedState": selected_state,
        "targetBodyFitSize": [round(target_size[0], 3), round(target_size[1], 3)],
        "measuredStateBodyFitSizes": {
            name: [round(size[0], 3), round(size[1], 3)]
            for name, size in sorted(state_sizes.items())
        },
    }
    return target_size


def normalize_manifest(manifest: dict[str, Any], columns: int, rows: int, cell_width: int, cell_height: int, atlas_path: str) -> dict[str, Any]:
    states = manifest["states"]
    for name, state in states.items():
        state["row"] = int(state["row"])
        frames = int(state["frames"])
        state["frames"] = frames
        durations = state.get("durations")
        if not isinstance(durations, list) or len(durations) != frames:
            state["durations"] = default_durations_for_state(name, frames)
        state.setdefault("loop", True)

    manifest["atlas"] = {
        "path": atlas_path,
        "width": columns * cell_width,
        "height": rows * cell_height,
        "columns": columns,
        "rows": rows,
        "cellWidth": cell_width,
        "cellHeight": cell_height,
    }
    return manifest


def extract_state_frames(
    row_path: Path,
    state_name: str,
    frame_count: int,
    args: argparse.Namespace,
    report: dict[str, Any],
) -> list[Image.Image]:
    strip = load_clean_row_strip(row_path, args)
    component_slots: list[Image.Image] | None = None
    component_metadata: list[dict[str, Any]] | None = None
    if args.extraction_mode == "component":
        component_slots, component_metadata = component_frame_slots(
            strip,
            frame_count,
            args.body_component_area,
            args.component_min_area,
        )
        bounds = [
            tuple(int(value) for value in metadata["bbox"]) if metadata.get("bbox") else (0, 0, 0, 0)
            for metadata in component_metadata
        ]
        extraction = "component-body"
    elif args.extraction_mode == "equal":
        bounds = equal_frame_bounds(strip.width, frame_count)
        extraction = "equal-grid"
    else:
        try:
            runs = column_runs(strip, frame_count)
            bounds = frame_bounds_from_runs(strip.width, runs)
            extraction = "foreground-center"
        except ValueError as exc:
            if args.no_equal_fallback or args.extraction_mode == "foreground":
                raise
            bounds = equal_frame_bounds(strip.width, frame_count)
            extraction = "equal-fallback"
            report["warnings"].append(f"{state_name}: {exc}; used equal-width fallback")

    frames: list[Image.Image] = []
    state_report = {
        "source": str(row_path),
        "sourceWidth": strip.width,
        "sourceHeight": strip.height,
        "extraction": extraction,
        "bounds": bounds,
        "frames": [],
    }
    if component_metadata is not None:
        state_report["components"] = component_metadata
    report["states"][state_name] = state_report

    out_dir = args.frames_dir / state_name
    out_dir.mkdir(parents=True, exist_ok=True)
    slots = component_slots if component_slots is not None else [strip.crop((x0, 0, x1, strip.height)) for x0, x1 in bounds]
    sprites: list[Image.Image] = []
    body_anchored_sprites: list[dict[str, Any]] = []
    for index, slot in enumerate(slots):
        slot = remove_small_components(slot, args.min_component_area)
        slot = remove_edge_spill(slot, args.key_color_rgb, args.spill_threshold, args.edge_spill_passes)
        slot = clean_transparent_rgb(slot)
        content_bbox = slot.getchannel("A").getbbox()
        sprite = crop_to_content(slot)
        sprites.append(sprite)
        if component_metadata is not None and content_bbox is not None:
            body_bbox = tuple(int(value) for value in component_metadata[index]["bodyBbox"])
            body_fit_bbox = tuple(int(value) for value in component_metadata[index].get("bodyFitBbox", body_bbox))
            body_anchored_sprites.append(
                {
                    "sprite": sprite,
                    "body_bbox": (
                        max(0, body_bbox[0] - content_bbox[0]),
                        max(0, body_bbox[1] - content_bbox[1]),
                        min(sprite.width, body_bbox[2] - content_bbox[0]),
                        min(sprite.height, body_bbox[3] - content_bbox[1]),
                    ),
                    "fit_bbox": (
                        max(0, body_fit_bbox[0] - content_bbox[0]),
                        max(0, body_fit_bbox[1] - content_bbox[1]),
                        min(sprite.width, body_fit_bbox[2] - content_bbox[0]),
                        min(sprite.height, body_fit_bbox[3] - content_bbox[1]),
                    ),
                }
            )
    if component_metadata is not None and len(body_anchored_sprites) == len(sprites):
        state_fit_scale = fit_scale_for_body_anchored_sprites(
            body_anchored_sprites,
            args.cell_width,
            args.cell_height,
            args.padding,
            target_body_fit_size=getattr(args, "body_fit_target_size", None),
        )
        if args.allow_edge_clearance_scale:
            target_fit_scale = state_fit_scale
            state_fit_scale = body_anchor_scale_for_edge_clearance(
                body_anchored_sprites,
                state_fit_scale,
                args.cell_width,
                args.cell_height,
                args.padding,
                max_y_offset=args.max_body_anchor_y_offset,
            )
            if state_fit_scale < target_fit_scale:
                state_report["edgeClearanceScaleAdjustment"] = {
                    "from": round(target_fit_scale, 6),
                    "to": round(state_fit_scale, 6),
                }
        if getattr(args, "body_fit_target_size", None) is not None:
            state_report["fitScaleMode"] = "body-anchor-pack-target"
            state_report["bodyFitTargetSize"] = [
                round(float(value), 3)
                for value in args.body_fit_target_size
            ]
        else:
            state_report["fitScaleMode"] = "body-anchor"
        state_y_offset = body_anchor_state_y_offset(
            body_anchored_sprites,
            state_fit_scale,
            args.cell_height,
            args.padding,
            max_offset=args.max_body_anchor_y_offset,
        )
        state_report["bodyAnchorYOffset"] = state_y_offset
    else:
        state_fit_scale = fit_scale_for_sprites(sprites, args.cell_width, args.cell_height, args.padding)
        state_report["fitScaleMode"] = "full-footprint"
        state_y_offset = 0
    state_report["fitScale"] = round(state_fit_scale, 6)
    for index, sprite in enumerate(sprites):
        if component_metadata is not None and len(body_anchored_sprites) == len(sprites):
            cell = fit_body_anchored_to_cell(
                sprite,
                tuple(int(value) for value in body_anchored_sprites[index]["body_bbox"]),
                args.cell_width,
                args.cell_height,
                args.padding,
                args.key_color_rgb,
                args.spill_threshold,
                scale=state_fit_scale,
                center_bbox=tuple(int(value) for value in body_anchored_sprites[index]["fit_bbox"]),
                y_offset=state_y_offset,
            )
        else:
            cell = fit_to_cell(
                sprite,
                args.cell_width,
                args.cell_height,
                args.padding,
                args.key_color_rgb,
                args.spill_threshold,
                scale=state_fit_scale,
            )
        outline_halo_pixels = count_outline_halo_pixels(cell, args.key_color_rgb, args.spill_threshold)
        state_report["frames"].append(
            {
                "index": index,
                "fitScale": round(state_fit_scale, 6),
                "outlineHaloPixels": outline_halo_pixels,
            }
        )
        report["outlineImprover"]["totalOutlineHaloPixels"] += outline_halo_pixels
        if outline_halo_pixels > args.max_outline_halo_pixels:
            report["warnings"].append(
                f"{state_name} frame {index}: {outline_halo_pixels} key-colored outline/halo pixels remain after cleanup"
            )
        cell.save(out_dir / f"{index:02d}.png")
        frames.append(cell)
    return frames


def make_contact_sheet(args: argparse.Namespace, states: list[tuple[str, dict[str, Any]]], atlas_frames: dict[str, list[Image.Image]]) -> None:
    label_height = 32
    margin = 12
    width = args.columns * args.cell_width + margin * 2
    height = len(states) * (args.cell_height + label_height) + margin * 2
    sheet = checkerboard(width, height)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    for row_index, (name, state) in enumerate(states):
        y = margin + row_index * (args.cell_height + label_height)
        draw.rectangle((0, y, width, y + label_height - 1), fill=(20, 24, 31, 255))
        draw.text((margin, y + 7), f"{name} - {state['frames']} frames", fill=(255, 255, 255, 255), font=font)
        for column in range(args.columns):
            x = margin + column * args.cell_width
            frame_y = y + label_height
            draw.rectangle((x, frame_y, x + args.cell_width - 1, frame_y + args.cell_height - 1), outline=(178, 185, 194, 255))
            if column < len(atlas_frames[name]):
                sheet.alpha_composite(atlas_frames[name][column], (x, frame_y))

    args.contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.contact_sheet)


def make_cutout_check(args: argparse.Namespace, states: list[tuple[str, dict[str, Any]]], atlas_frames: dict[str, list[Image.Image]]) -> None:
    label_width = 160
    margin = 12
    backgrounds = [
        ("dark", (15, 18, 26, 255)),
        ("white", (255, 255, 255, 255)),
        ("blue", (42, 85, 180, 255)),
        ("green", (28, 120, 96, 255)),
    ]
    width = label_width + len(backgrounds) * args.cell_width + margin * 2
    height = len(states) * args.cell_height + margin * 2
    sheet = Image.new("RGBA", (width, height), (245, 246, 248, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    for row_index, (name, _state) in enumerate(states):
        y = margin + row_index * args.cell_height
        draw.text((margin, y + 12), name, fill=(20, 24, 31, 255), font=font)
        frame = atlas_frames[name][0]
        for column, (label, color) in enumerate(backgrounds):
            x = margin + label_width + column * args.cell_width
            draw.rectangle((x, y, x + args.cell_width - 1, y + args.cell_height - 1), fill=color)
            if row_index == 0:
                draw.text((x + 8, y + 8), label, fill=(255, 255, 255, 210) if column != 1 else (20, 24, 31, 210), font=small_font)
            sheet.alpha_composite(frame, (x, y))
            draw.rectangle((x, y, x + args.cell_width - 1, y + args.cell_height - 1), outline=(30, 35, 45, 255))

    args.cutout_check.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(args.cutout_check)


def make_preview_gifs(states: list[tuple[str, dict[str, Any]]], atlas_frames: dict[str, list[Image.Image]], previews_dir: Path) -> None:
    previews_dir.mkdir(parents=True, exist_ok=True)
    for name, state in states:
        frames = [composite_on_checker(frame) for frame in atlas_frames[name]]
        durations = list(state["durations"])
        frames[0].save(
            previews_dir / f"{name}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            optimize=False,
        )


def assemble(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.frames_dir.mkdir(parents=True, exist_ok=True)
    args.previews_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    args.key_color = resolve_key_color(manifest, args.manifest, args.key_color)
    args.key_color_rgb = parse_hex_color(args.key_color)
    states = state_items(manifest)
    if args.columns is None:
        args.columns = max(int(state["frames"]) for _name, state in states)
    rows = max(int(state["row"]) for _name, state in states) + 1

    atlas = Image.new("RGBA", (args.columns * args.cell_width, rows * args.cell_height), (0, 0, 0, 0))
    report: dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "states": {},
        "cellWidth": args.cell_width,
        "cellHeight": args.cell_height,
        "columns": args.columns,
        "rows": rows,
        "keyColor": args.key_color,
        "keyTolerance": args.key_tolerance,
        "spillThreshold": args.spill_threshold,
        "edgeSpillPasses": args.edge_spill_passes,
        "premultipliedResize": True,
        "outlineImprover": {
            "enabled": True,
            "keyToAlpha": True,
            "edgeSpillRemoval": True,
            "spillColorReplacement": True,
            "transparentRgbCleanup": True,
            "premultipliedResize": True,
            "maxOutlineHaloPixelsPerFrame": args.max_outline_halo_pixels,
            "totalOutlineHaloPixels": 0,
        },
    }
    args.body_fit_target_size = resolve_body_fit_target(states, args, report)
    atlas_frames: dict[str, list[Image.Image]] = {}

    for name, state in states:
        frames = int(state["frames"])
        if frames > args.columns:
            raise ValueError(f"{name}: frames exceeds atlas columns")
        row_path = args.row_dir / f"{name}.png"
        if not row_path.exists():
            raise FileNotFoundError(f"missing row strip for {name}: {row_path}")
        extracted = extract_state_frames(row_path, name, frames, args, report)
        atlas_frames[name] = extracted
        row = int(state["row"])
        for column, frame in enumerate(extracted):
            atlas.alpha_composite(frame, (column * args.cell_width, row * args.cell_height))

    atlas_png = args.out_dir / args.atlas_png
    atlas_webp = args.out_dir / args.atlas_webp
    atlas_png.parent.mkdir(parents=True, exist_ok=True)
    atlas_webp.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(atlas_png)
    atlas.save(atlas_webp, lossless=True, quality=100, method=6)

    atlas_manifest_path = os.path.relpath(atlas_webp, args.manifest.parent).replace(os.sep, "/")
    manifest = normalize_manifest(manifest, args.columns, rows, args.cell_width, args.cell_height, atlas_manifest_path)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    make_contact_sheet(args, states, atlas_frames)
    make_cutout_check(args, states, atlas_frames)
    make_preview_gifs(states, atlas_frames, args.previews_dir)

    report.update(
        {
            "manifest": str(args.manifest),
            "atlasWebp": str(atlas_webp),
            "atlasPng": str(atlas_png),
            "contactSheet": str(args.contact_sheet),
            "cutoutCheck": str(args.cutout_check),
            "previewsDir": str(args.previews_dir),
        }
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Manifest to read/update")
    parser.add_argument("--row-dir", required=True, type=Path, help="Directory containing <state>.png row strips")
    parser.add_argument("--out-dir", type=Path, help="Output directory for atlas files")
    parser.add_argument("--frames-dir", type=Path, help="Directory for extracted frame PNGs")
    parser.add_argument("--previews-dir", type=Path, help="Directory for GIF previews")
    parser.add_argument("--contact-sheet", type=Path, help="Output contact sheet path")
    parser.add_argument("--cutout-check", type=Path, help="Output matte/cutout QA sheet path")
    parser.add_argument("--report", type=Path, help="Output assembly report JSON")
    parser.add_argument("--cell-width", type=int, default=256, help="Atlas cell width")
    parser.add_argument("--cell-height", type=int, default=288, help="Atlas cell height")
    parser.add_argument("--columns", type=int, help="Atlas columns; defaults to max state frames")
    parser.add_argument("--padding", type=int, default=10, help="Cell padding around fitted sprites")
    parser.add_argument(
        "--key-color",
        help="Chroma-key color as #RRGGBB; defaults to manifest/request chromaKey, then #FF00FF",
    )
    parser.add_argument("--key-tolerance", type=int, default=80, help="Euclidean RGB tolerance for key removal")
    parser.add_argument("--spill-threshold", type=int, default=45, help="Remove magenta spill when R/G and B/G exceed this threshold")
    parser.add_argument("--edge-spill-passes", type=int, default=2, help="Passes that remove key-colored edge pixels touching transparency")
    parser.add_argument("--max-outline-halo-pixels", type=int, default=0, help="Warn when a frame keeps more key-colored outline pixels than this after cleanup")
    parser.add_argument("--min-component-area", type=int, default=500, help="Drop isolated alpha components below this pixel area")
    parser.add_argument("--atlas-webp", default="atlas.webp", help="Atlas WebP filename relative to out-dir")
    parser.add_argument("--atlas-png", default="atlas.png", help="Atlas PNG filename relative to out-dir")
    parser.add_argument(
        "--extraction-mode",
        choices=["auto", "foreground", "equal", "component"],
        default="auto",
        help="Frame extraction mode. Use component for row strips with detached integrated effects that need body-centered grouping.",
    )
    parser.add_argument("--no-equal-fallback", action="store_true", help="Fail instead of equal-slicing if foreground run detection fails")
    parser.add_argument("--body-component-area", type=int, default=8000, help="Minimum alpha component area used as a body anchor in component extraction mode")
    parser.add_argument("--component-min-area", type=int, default=80, help="Minimum alpha component area retained for component extraction grouping")
    parser.add_argument(
        "--body-fit-target-state",
        default="idle",
        help="Component mode body/core scale target state; use 'none' to disable pack-level body scale locking",
    )
    parser.add_argument(
        "--max-body-anchor-y-offset",
        type=int,
        default=2,
        help="Maximum uniform downward row offset used for body-anchored edge clearance; keeps cues from moving the body baseline too much",
    )
    parser.add_argument(
        "--allow-edge-clearance-scale",
        action="store_true",
        help="Allow a last-resort uniform row scale reduction when a cue cannot fit after body-target scale and capped y offset",
    )
    args = parser.parse_args()

    args.manifest = args.manifest.expanduser().resolve()
    args.row_dir = args.row_dir.expanduser().resolve()
    args.out_dir = (args.out_dir.expanduser().resolve() if args.out_dir else args.manifest.parent)
    args.frames_dir = (args.frames_dir.expanduser().resolve() if args.frames_dir else args.out_dir / "frames")
    args.previews_dir = (args.previews_dir.expanduser().resolve() if args.previews_dir else args.out_dir / "qa" / "previews")
    args.contact_sheet = (args.contact_sheet.expanduser().resolve() if args.contact_sheet else args.out_dir / "qa" / "contact-sheet.png")
    args.cutout_check = (args.cutout_check.expanduser().resolve() if args.cutout_check else args.out_dir / "qa" / "cutout-check.png")
    args.report = (args.report.expanduser().resolve() if args.report else args.out_dir / "qa" / "assembly-report.json")

    report = assemble(args)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
