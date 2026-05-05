#!/usr/bin/env python3
"""Analyze companion mascot animation quality and semantic enhancer stability."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SEPARATE_ENHANCER_ATTACHMENTS = {"near-head", "near-hand", "aura"}


def quantile(sorted_values: list[int], ratio: float) -> int:
    if not sorted_values:
        return 0
    index = int(round((len(sorted_values) - 1) * ratio))
    return sorted_values[min(len(sorted_values) - 1, max(0, index))]


def component_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def component_size(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = bbox
    return x1 - x0, y1 - y0


def core_bbox(xs: list[int], ys: list[int], low: float = 0.10, high: float = 0.90) -> tuple[int, int, int, int]:
    sorted_xs = sorted(xs)
    sorted_ys = sorted(ys)
    return (
        quantile(sorted_xs, low),
        quantile(sorted_ys, low),
        quantile(sorted_xs, high) + 1,
        quantile(sorted_ys, high) + 1,
    )


def connected_components(alpha: Image.Image, min_area: int) -> list[dict[str, Any]]:
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    components: list[dict[str, Any]] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or not pixels[x, y]:
                continue

            stack = [(x, y)]
            visited[index] = 1
            area = 0
            x0 = x1 = x
            y0 = y1 = y
            xs: list[int] = []
            ys: list[int] = []

            while stack:
                px, py = stack.pop()
                area += 1
                xs.append(px)
                ys.append(py)
                x0 = min(x0, px)
                x1 = max(x1, px)
                y0 = min(y0, py)
                y1 = max(y1, py)
                for ny in range(max(0, py - 1), min(height, py + 2)):
                    for nx in range(max(0, px - 1), min(width, px + 2)):
                        nindex = ny * width + nx
                        if visited[nindex] or not pixels[nx, ny]:
                            continue
                        visited[nindex] = 1
                        stack.append((nx, ny))

            if area >= min_area:
                bbox = (x0, y0, x1 + 1, y1 + 1)
                core = core_bbox(xs, ys)
                components.append(
                    {
                        "area": area,
                        "bbox": bbox,
                        "center": component_center(bbox),
                        "size": component_size(bbox),
                        "coreBbox": core,
                        "coreCenter": component_center(core),
                        "coreSize": component_size(core),
                    }
                )

    return sorted(components, key=lambda component: int(component["area"]), reverse=True)


def union_bbox(components: list[dict[str, Any]]) -> tuple[int, int, int, int] | None:
    if not components:
        return None
    boxes = [component["bbox"] for component in components]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def frame_delta(left: Image.Image, right: Image.Image) -> float:
    size = (48, 54)
    left_small = left.convert("RGBA").resize(size, Image.Resampling.BILINEAR)
    right_small = right.convert("RGBA").resize(size, Image.Resampling.BILINEAR)
    left_data = left_small.tobytes()
    right_data = right_small.tobytes()
    total = sum(abs(a - b) for a, b in zip(left_data, right_data))
    return total / max(1, len(left_data))


def crop_state_frames(atlas: Image.Image, state: dict[str, Any], columns: int, cell_width: int, cell_height: int) -> list[Image.Image]:
    row = int(state["row"])
    frames = int(state["frames"])
    result = []
    for column in range(min(frames, columns)):
        box = (
            column * cell_width,
            row * cell_height,
            (column + 1) * cell_width,
            (row + 1) * cell_height,
        )
        result.append(atlas.crop(box).convert("RGBA"))
    return result


def checkerboard(width: int, height: int, block: int = 16) -> Image.Image:
    image = Image.new("RGBA", (width, height), (245, 246, 248, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, block):
        for x in range(0, width, block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill=(226, 230, 235, 255))
    return image


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_scaled_frame(
    sheet: Image.Image,
    frame: Image.Image,
    metrics: dict[str, Any],
    dest: tuple[int, int],
    size: tuple[int, int],
) -> None:
    x, y = dest
    width, height = size
    tile = Image.new("RGBA", size, (15, 18, 26, 255))
    scale_x = width / frame.width
    scale_y = height / frame.height
    scaled = frame.resize(size, Image.Resampling.NEAREST)
    tile.alpha_composite(scaled)
    draw = ImageDraw.Draw(tile)

    body = metrics.get("body")
    if body:
        bx0, by0, bx1, by1 = body["bbox"]
        draw.rectangle(
            (bx0 * scale_x, by0 * scale_y, bx1 * scale_x, by1 * scale_y),
            outline=(80, 190, 255, 255),
            width=2,
        )
        cx0, cy0, cx1, cy1 = body.get("coreBbox", body["bbox"])
        draw.rectangle(
            (cx0 * scale_x, cy0 * scale_y, cx1 * scale_x, cy1 * scale_y),
            outline=(86, 255, 162, 255),
            width=1,
        )
    semantic = metrics.get("semantic")
    if semantic:
        sx0, sy0, sx1, sy1 = semantic["bbox"]
        draw.rectangle(
            (sx0 * scale_x, sy0 * scale_y, sx1 * scale_x, sy1 * scale_y),
            outline=(255, 205, 72, 255),
            width=2,
        )

    sheet.alpha_composite(tile, (x, y))


def make_semantic_anchor_sheet(
    out_path: Path,
    manifest: dict[str, Any],
    frames_by_state: dict[str, list[Image.Image]],
    metrics_by_state: dict[str, list[dict[str, Any]]],
) -> None:
    states = [
        (name, state)
        for name, state in manifest["states"].items()
        if isinstance(state, dict) and isinstance(state.get("enhancer"), dict)
    ]
    if not states:
        return

    tile = (128, 144)
    label_width = 190
    margin = 12
    gap = 10
    max_frames = max(len(frames_by_state[name]) for name, _state in states)
    width = label_width + max_frames * (tile[0] + gap) + margin * 2
    height = len(states) * (tile[1] + gap) + margin * 2
    sheet = Image.new("RGBA", (width, height), (245, 246, 248, 255))
    draw = ImageDraw.Draw(sheet)
    font = load_font(14)
    small_font = load_font(11)

    for row_index, (name, state) in enumerate(states):
        y = margin + row_index * (tile[1] + gap)
        enhancer = state.get("enhancer", {})
        draw.text((margin, y + 8), name, fill=(20, 24, 31, 255), font=font)
        draw.text((margin, y + 28), str(enhancer.get("kind", "")), fill=(55, 65, 80, 255), font=small_font)
        draw.text((margin, y + 44), str(enhancer.get("attachment", "")), fill=(55, 65, 80, 255), font=small_font)
        for index, frame in enumerate(frames_by_state[name]):
            x = margin + label_width + index * (tile[0] + gap)
            draw_scaled_frame(sheet, frame, metrics_by_state[name][index], (x, y), tile)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def make_motion_quality_sheet(
    out_path: Path,
    frames_by_state: dict[str, list[Image.Image]],
    metrics_by_state: dict[str, list[dict[str, Any]]],
) -> None:
    tile = (96, 108)
    label_width = 150
    margin = 12
    gap = 8
    states = list(frames_by_state)
    max_frames = max(len(frames) for frames in frames_by_state.values())
    width = label_width + max_frames * (tile[0] + gap) + margin * 2
    height = len(states) * (tile[1] + gap) + margin * 2
    sheet = checkerboard(width, height)
    draw = ImageDraw.Draw(sheet)
    font = load_font(13)
    small_font = load_font(10)

    for row_index, name in enumerate(states):
        y = margin + row_index * (tile[1] + gap)
        draw.text((margin, y + 8), name, fill=(20, 24, 31, 255), font=font)
        deltas = metrics_by_state[name][0].get("stateDeltas", [])
        if deltas:
            avg_delta = sum(deltas) / len(deltas)
            draw.text((margin, y + 26), f"avg delta {avg_delta:.1f}", fill=(55, 65, 80, 255), font=small_font)
        for index, frame in enumerate(frames_by_state[name]):
            x = margin + label_width + index * (tile[0] + gap)
            draw_scaled_frame(sheet, frame, metrics_by_state[name][index], (x, y), tile)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def analyze_manifest_quality(
    manifest_path: Path | str,
    *,
    min_component_area: int = 80,
    fragment_min_area: int = 12,
    near_duplicate_delta: float = 1.0,
    max_duplicate_ratio: float = 0.45,
    min_average_motion_delta: float = 1.2,
    max_body_jump_ratio: float = 0.35,
    max_area_jump_ratio: float = 0.45,
    max_core_scale_drift_ratio: float = 0.12,
    max_core_scale_range_ratio: float = 0.05,
    max_core_center_drift_ratio: float = 0.08,
    max_fragment_area_ratio: float = 0.015,
    max_semantic_drift_ratio: float = 0.55,
    min_semantic_presence_ratio: float = 0.35,
    semantic_anchor_check: str = "qa/semantic-anchor-check.png",
    motion_quality_check: str = "qa/motion-quality-check.png",
    json_out: str = "qa/quality-report.json",
) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    atlas_info = manifest.get("atlas", {})
    atlas_path = Path(atlas_info.get("path", ""))
    if not atlas_path.is_absolute():
        atlas_path = manifest_path.parent / atlas_path

    columns = int(atlas_info["columns"])
    cell_width = int(atlas_info["cellWidth"])
    cell_height = int(atlas_info["cellHeight"])
    states = manifest.get("states", {})

    warnings: list[str] = []
    errors: list[str] = []
    qa: dict[str, Any] = {}
    frames_by_state: dict[str, list[Image.Image]] = {}
    metrics_by_state: dict[str, list[dict[str, Any]]] = {}

    with Image.open(atlas_path) as atlas_image:
        atlas = atlas_image.convert("RGBA")
        for state_name, state in sorted(states.items(), key=lambda item: int(item[1].get("row", 0))):
            if not isinstance(state, dict):
                continue
            frames = crop_state_frames(atlas, state, columns, cell_width, cell_height)
            frames_by_state[state_name] = frames
            state_metrics: list[dict[str, Any]] = []
            for frame in frames:
                all_components = connected_components(frame.getchannel("A"), fragment_min_area)
                components = [
                    component for component in all_components if int(component["area"]) >= min_component_area
                ]
                fragments = [
                    component for component in all_components if int(component["area"]) < min_component_area
                ]
                body = components[0] if components else None
                semantic_components = components[1:]
                semantic_box = union_bbox(semantic_components)
                semantic = (
                    {
                        "bbox": semantic_box,
                        "center": component_center(semantic_box),
                        "componentCount": len(semantic_components),
                        "area": sum(int(component["area"]) for component in semantic_components),
                    }
                    if semantic_box
                    else None
                )
                state_metrics.append(
                    {
                        "componentCount": len(components),
                        "body": body,
                        "semantic": semantic,
                        "foregroundArea": sum(int(component["area"]) for component in components),
                        "fragmentCount": len(fragments),
                        "fragmentArea": sum(int(component["area"]) for component in fragments),
                    }
                )

            deltas = [frame_delta(left, right) for left, right in zip(frames, frames[1:])]
            duplicate_count = sum(1 for delta in deltas if delta <= near_duplicate_delta)
            duplicate_ratio = duplicate_count / max(1, len(deltas))
            average_delta = sum(deltas) / max(1, len(deltas))
            for metric in state_metrics:
                metric["stateDeltas"] = deltas

            if len(frames) > 3 and duplicate_ratio > max_duplicate_ratio:
                warnings.append(
                    f"states.{state_name} has {duplicate_count}/{len(deltas)} near-duplicate frame transitions; add more meaningful motion"
                )
            if len(frames) > 3 and average_delta < min_average_motion_delta:
                warnings.append(
                    f"states.{state_name} average motion delta is {average_delta:.2f}; animation may feel static"
                )

            body_centers = [metric["body"]["center"] for metric in state_metrics if metric.get("body")]
            if len(body_centers) > 1:
                jump_limit = min(cell_width, cell_height) * max_body_jump_ratio
                for index, (left, right) in enumerate(zip(body_centers, body_centers[1:])):
                    jump = math.dist(left, right)
                    if jump > jump_limit:
                        warnings.append(
                            f"states.{state_name} frame {index}->{index + 1} body center jumps {jump:.1f}px; check for jitter or inconsistent extraction"
                        )

            body_areas = [int(metric["body"]["area"]) for metric in state_metrics if metric.get("body")]
            if len(body_areas) > 1:
                for index, (left, right) in enumerate(zip(body_areas, body_areas[1:])):
                    ratio = abs(right - left) / max(1, max(left, right))
                    if ratio > max_area_jump_ratio:
                        warnings.append(
                            f"states.{state_name} frame {index}->{index + 1} foreground area changes {ratio:.0%}; check for extra limbs, missing props, or crop artifacts"
                        )

            core_scales = []
            core_centers = []
            for metric in state_metrics:
                body = metric.get("body")
                if not body:
                    continue
                core_w, core_h = body.get("coreSize", body["size"])
                core_scales.append(math.sqrt(max(1, core_w * core_h)))
                core_centers.append(body.get("coreCenter", body["center"]))
            if len(core_scales) > 1:
                median_scale = sorted(core_scales)[len(core_scales) // 2]
                max_scale_drift = max(abs(scale - median_scale) / max(1.0, median_scale) for scale in core_scales)
                if max_scale_drift > max_core_scale_drift_ratio:
                    warnings.append(
                        f"states.{state_name} silhouette core scale drifts {max_scale_drift:.0%}; keep the mascot body size/proportions consistent across frames"
                    )
                scale_range_ratio = (max(core_scales) - min(core_scales)) / max(1.0, median_scale)
                if scale_range_ratio > max_core_scale_range_ratio:
                    warnings.append(
                        f"states.{state_name} silhouette core scale range is {scale_range_ratio:.0%}; body size changes too much across the row"
                    )
            if len(core_centers) > 1:
                x_values = sorted(center[0] for center in core_centers)
                y_values = sorted(center[1] for center in core_centers)
                median_center = (x_values[len(x_values) // 2], y_values[len(y_values) // 2])
                max_center_drift = max(math.dist(center, median_center) for center in core_centers)
                center_ratio = max_center_drift / max(1, min(cell_width, cell_height))
                if center_ratio > max_core_center_drift_ratio:
                    warnings.append(
                        f"states.{state_name} silhouette core center drifts {center_ratio:.0%} of cell size; check for body jitter or inconsistent cuts"
                    )

            for index, metric in enumerate(state_metrics):
                foreground_area = int(metric.get("foregroundArea", 0))
                fragment_area = int(metric.get("fragmentArea", 0))
                if foreground_area and fragment_area / foreground_area > max_fragment_area_ratio:
                    warnings.append(
                        f"states.{state_name} frame {index} has detached fragment area {fragment_area}px; check for neighboring-frame slivers or broken cuts"
                    )

            enhancer = state.get("enhancer")
            if isinstance(enhancer, dict):
                attachment = str(enhancer.get("attachment", ""))
                semantic_metrics = [metric for metric in state_metrics if metric.get("semantic") and metric.get("body")]
                presence_ratio = len(semantic_metrics) / max(1, len(state_metrics))
                if attachment in SEPARATE_ENHANCER_ATTACHMENTS and presence_ratio < min_semantic_presence_ratio:
                    warnings.append(
                        f"states.{state_name} semantic enhancer appears in only {presence_ratio:.0%} of frames; check missing or unstable enhancer placement"
                    )
                if semantic_metrics:
                    relative_positions = []
                    for metric in semantic_metrics:
                        body = metric["body"]
                        semantic = metric["semantic"]
                        body_center = body["center"]
                        semantic_center = semantic["center"]
                        body_w, body_h = body["size"]
                        scale = max(body_w, body_h, 1)
                        relative_positions.append(
                            (
                                (semantic_center[0] - body_center[0]) / scale,
                                (semantic_center[1] - body_center[1]) / scale,
                            )
                        )
                    x_values = [position[0] for position in relative_positions]
                    y_values = [position[1] for position in relative_positions]
                    drift = max(max(x_values) - min(x_values), max(y_values) - min(y_values))
                    if drift > max_semantic_drift_ratio:
                        warnings.append(
                            f"states.{state_name} semantic enhancer anchor drifts {drift:.2f} body-widths; regenerate or repair prop placement"
                        )

            metrics_by_state[state_name] = state_metrics
            qa[state_name] = {
                "frames": len(frames),
                "averageMotionDelta": round(average_delta, 3),
                "nearDuplicateTransitions": duplicate_count,
                "nearDuplicateRatio": round(duplicate_ratio, 3),
                "componentCounts": [metric["componentCount"] for metric in state_metrics],
                "fragmentCounts": [metric["fragmentCount"] for metric in state_metrics],
                "bodyCoreScales": [
                    round(math.sqrt(max(1, metric["body"].get("coreSize", metric["body"]["size"])[0] * metric["body"].get("coreSize", metric["body"]["size"])[1])), 3)
                    for metric in state_metrics
                    if metric.get("body")
                ],
                "bodyCoreScaleRangeRatio": (
                    round((max(core_scales) - min(core_scales)) / max(1.0, sorted(core_scales)[len(core_scales) // 2]), 3)
                    if len(core_scales) > 1
                    else 0.0
                ),
            }

    semantic_path = manifest_path.parent / semantic_anchor_check
    motion_path = manifest_path.parent / motion_quality_check
    make_semantic_anchor_sheet(semantic_path, manifest, frames_by_state, metrics_by_state)
    make_motion_quality_sheet(motion_path, frames_by_state, metrics_by_state)

    result = {
        "ok": not errors and not warnings,
        "manifest": str(manifest_path),
        "errors": errors,
        "warnings": warnings,
        "qa": qa,
        "semanticAnchorCheck": str(semantic_path),
        "motionQualityCheck": str(motion_path),
    }
    json_path = manifest_path.parent / json_out
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.json")
    parser.add_argument("--min-component-area", type=int, default=80, help="Minimum alpha component area to inspect")
    parser.add_argument("--fragment-min-area", type=int, default=12, help="Minimum detached fragment area to inspect")
    parser.add_argument("--near-duplicate-delta", type=float, default=1.0, help="Frame delta at or below this value counts as near-duplicate")
    parser.add_argument("--max-duplicate-ratio", type=float, default=0.45, help="Maximum near-duplicate transition ratio")
    parser.add_argument("--min-average-motion-delta", type=float, default=1.2, help="Minimum average frame delta before a state is considered too static")
    parser.add_argument("--max-body-jump-ratio", type=float, default=0.35, help="Max body center jump as a ratio of cell min dimension")
    parser.add_argument("--max-area-jump-ratio", type=float, default=0.45, help="Max consecutive body area jump ratio")
    parser.add_argument("--max-core-scale-drift-ratio", type=float, default=0.12, help="Max mascot core scale drift within one state")
    parser.add_argument("--max-core-scale-range-ratio", type=float, default=0.05, help="Max full mascot core scale range within one state")
    parser.add_argument("--max-core-center-drift-ratio", type=float, default=0.08, help="Max mascot core center drift as a ratio of cell min dimension")
    parser.add_argument("--max-fragment-area-ratio", type=float, default=0.015, help="Max detached fragment area as a ratio of foreground area")
    parser.add_argument("--max-semantic-drift-ratio", type=float, default=0.55, help="Max semantic anchor drift in body-widths")
    parser.add_argument("--min-semantic-presence-ratio", type=float, default=0.35, help="Minimum presence ratio for separate semantic enhancers")
    parser.add_argument("--json-out", default="qa/quality-report.json", help="Quality report path relative to manifest directory")
    args = parser.parse_args()

    result = analyze_manifest_quality(
        args.manifest,
        min_component_area=args.min_component_area,
        fragment_min_area=args.fragment_min_area,
        near_duplicate_delta=args.near_duplicate_delta,
        max_duplicate_ratio=args.max_duplicate_ratio,
        min_average_motion_delta=args.min_average_motion_delta,
        max_body_jump_ratio=args.max_body_jump_ratio,
        max_area_jump_ratio=args.max_area_jump_ratio,
        max_core_scale_drift_ratio=args.max_core_scale_drift_ratio,
        max_core_scale_range_ratio=args.max_core_scale_range_ratio,
        max_core_center_drift_ratio=args.max_core_center_drift_ratio,
        max_fragment_area_ratio=args.max_fragment_area_ratio,
        max_semantic_drift_ratio=args.max_semantic_drift_ratio,
        min_semantic_presence_ratio=args.min_semantic_presence_ratio,
        json_out=args.json_out,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
