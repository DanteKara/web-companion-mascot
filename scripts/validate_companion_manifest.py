#!/usr/bin/env python3
"""Validate a web companion mascot manifest and optional atlas image."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_ATLAS_FIELDS = {
    "path",
    "width",
    "height",
    "columns",
    "rows",
    "cellWidth",
    "cellHeight",
}

CHATBOT_RECOMMENDED_FRAMES = {
    "idle": 10,
    "greeting": 10,
    "listening": 10,
    "thinking": 12,
    "working": 12,
    "answering": 12,
    "success": 10,
    "error": 10,
    "confused": 10,
    "sleeping": 10,
}

CHATBOT_CORE_STATES = {"idle", "thinking", "working", "answering", "success", "error"}
MIN_USED_CELL_COVERAGE = 0.015
STATE_CLARITY_PROFILES = {"pose-only", "semantic-enhancers"}
SEMANTIC_ENHANCER_STATES = {"listening", "thinking", "working", "answering"}
ALLOWED_ENHANCER_ATTACHMENTS = {
    "held",
    "worn",
    "attached",
    "near-head",
    "near-face",
    "near-hand",
    "aura",
    "gesture",
    "body-pose",
}
TEXT_DEPENDENT_KIND_TERMS = {"text", "label", "caption", "word", "question-mark", "punctuation"}


def parse_hex_color(value: str) -> tuple[int, int, int]:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        raise ValueError(f"expected #RRGGBB color, got {value!r}")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


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


def has_transparent_neighbor(alpha_pixels: Any, x: int, y: int, width: int, height: int) -> bool:
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if nx == x and ny == y:
                continue
            if not alpha_pixels[nx, ny]:
                return True
    return False


def count_outline_halo_pixels(image: Any, key: tuple[int, int, int], threshold: int) -> int:
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


def load_assembly_report(manifest_path: Path) -> dict[str, Any] | None:
    report_path = manifest_path.parent / "qa" / "assembly-report.json"
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return report if isinstance(report, dict) else None


def load_quality_report(manifest_path: Path) -> dict[str, Any] | None:
    report_path = manifest_path.parent / "qa" / "quality-report.json"
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return report if isinstance(report, dict) else None


def inspect_atlas(
    path: Path,
    states: dict[str, Any],
    columns: int | None,
    cell_width: int | None,
    cell_height: int | None,
    key_color: tuple[int, int, int] | None = None,
    spill_threshold: int = 45,
    max_outline_halo_pixels: int = 0,
) -> tuple[dict[str, Any], list[str], list[str]] | None:
    try:
        from PIL import Image
    except Exception:
        return None

    errors: list[str] = []
    warnings: list[str] = []

    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        info: dict[str, Any] = {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "cells": [],
        }

        if columns is None or cell_width is None or cell_height is None:
            return info, errors, warnings

        cell_area = cell_width * cell_height
        for state_name, state in states.items():
            if not isinstance(state, dict):
                continue
            row = state.get("row")
            frames = state.get("frames")
            if not isinstance(row, int) or not isinstance(frames, int):
                continue
            for column in range(columns):
                box = (
                    column * cell_width,
                    row * cell_height,
                    (column + 1) * cell_width,
                    (row + 1) * cell_height,
                )
                if box[2] > rgba.width or box[3] > rgba.height:
                    continue
                cell = rgba.crop(box)
                alpha = cell.getchannel("A")
                nontransparent = sum(1 for value in alpha.tobytes() if value)
                used = column < frames

                edge_pixels = 0
                if nontransparent:
                    top = [alpha.getpixel((x, 0)) for x in range(cell_width)]
                    bottom = [alpha.getpixel((x, cell_height - 1)) for x in range(cell_width)]
                    left = [alpha.getpixel((0, y)) for y in range(cell_height)]
                    right = [alpha.getpixel((cell_width - 1, y)) for y in range(cell_height)]
                    edge_pixels = sum(1 for value in top + bottom + left + right if value)
                outline_halo_pixels = (
                    count_outline_halo_pixels(cell, key_color, spill_threshold)
                    if key_color is not None and used
                    else 0
                )

                info["cells"].append(
                    {
                        "state": state_name,
                        "row": row,
                        "column": column,
                        "used": used,
                        "nontransparentPixels": nontransparent,
                        "edgePixels": edge_pixels,
                        "outlineHaloPixels": outline_halo_pixels,
                    }
                )

                if used and nontransparent == 0:
                    errors.append(f"state {state_name} frame {column} is empty")
                if used and nontransparent and nontransparent < cell_area * MIN_USED_CELL_COVERAGE:
                    warnings.append(f"state {state_name} frame {column} is very sparse")
                if used and edge_pixels:
                    errors.append(f"state {state_name} frame {column} touches the cell edge")
                if used and outline_halo_pixels > max_outline_halo_pixels:
                    errors.append(
                        f"state {state_name} frame {column} has {outline_halo_pixels} key-colored outline/halo pixels"
                    )
                if not used and nontransparent:
                    errors.append(f"state {state_name} unused cell {column} is not transparent")

        return info, errors, warnings


def require_int(errors: list[str], value: Any, name: str, minimum: int = 1) -> int | None:
    if not isinstance(value, int):
        errors.append(f"{name} must be an integer")
        return None
    if value < minimum:
        errors.append(f"{name} must be >= {minimum}")
        return None
    return value


def require_non_empty_string(errors: list[str], value: Any, name: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name} must be a non-empty string")
        return None
    return value


def validate_enhancer(
    errors: list[str],
    warnings: list[str],
    value: Any,
    name: str,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return

    kind = require_non_empty_string(errors, value.get("kind"), f"{name}.kind")
    attachment = require_non_empty_string(errors, value.get("attachment"), f"{name}.attachment")
    require_non_empty_string(errors, value.get("description"), f"{name}.description")

    if kind:
        normalized_kind = kind.lower().replace("_", "-").replace(" ", "-")
        if any(term in normalized_kind for term in TEXT_DEPENDENT_KIND_TERMS):
            warnings.append(f"{name}.kind appears text-dependent; prefer a visual non-text enhancer")

    if attachment:
        if attachment in {"floating", "detached"}:
            errors.append(f"{name}.attachment must be anchored to the mascot")
        elif attachment not in ALLOWED_ENHANCER_ATTACHMENTS:
            errors.append(
                f"{name}.attachment must be one of: {', '.join(sorted(ALLOWED_ENHANCER_ATTACHMENTS))}"
            )


def validate_style_metadata(
    data: dict[str, Any],
    states: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    qa: dict[str, Any],
    require_state_clarity: bool,
) -> None:
    style = data.get("style")
    if style is None:
        if require_state_clarity:
            errors.append("style.stateClarity is required when --require-state-clarity is used")
        return
    if not isinstance(style, dict):
        errors.append("style must be an object")
        return

    state_clarity = style.get("stateClarity")
    if state_clarity is None:
        errors.append("style.stateClarity is required when style is present")
        return
    if not isinstance(state_clarity, str):
        errors.append("style.stateClarity must be a string")
        return
    if state_clarity not in STATE_CLARITY_PROFILES:
        errors.append(f"style.stateClarity must be one of: {', '.join(sorted(STATE_CLARITY_PROFILES))}")
        return

    enhancer_theme = style.get("enhancerTheme")
    if enhancer_theme is not None and not isinstance(enhancer_theme, str):
        errors.append("style.enhancerTheme must be a string when present")

    states_with_enhancers: list[str] = []
    for state_name, state in states.items():
        if not isinstance(state, dict):
            continue
        if "enhancer" in state:
            states_with_enhancers.append(state_name)
            validate_enhancer(errors, warnings, state.get("enhancer"), f"states.{state_name}.enhancer")

    if state_clarity == "pose-only" and states_with_enhancers:
        errors.append("style.stateClarity is pose-only but one or more states include enhancer metadata")

    if state_clarity == "semantic-enhancers":
        for state_name in sorted(SEMANTIC_ENHANCER_STATES & set(states)):
            state = states.get(state_name)
            if isinstance(state, dict) and "enhancer" not in state:
                warnings.append(
                    f"states.{state_name}.enhancer metadata is recommended when style.stateClarity is semantic-enhancers"
                )

    qa["stateClarity"] = {
        "profile": state_clarity,
        "enhancerTheme": enhancer_theme,
        "statesWithEnhancers": sorted(states_with_enhancers),
        "recommendedSemanticStates": sorted(SEMANTIC_ENHANCER_STATES & set(states)),
    }


def validate_manifest(
    manifest_path: Path,
    profile: str = "generic",
    require_state_clarity: bool = False,
    require_quality_report: bool = False,
    key_color: str | None = None,
    spill_threshold: int | None = None,
    max_outline_halo_pixels: int = 0,
) -> tuple[dict[str, Any], list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    qa: dict[str, Any] = {}

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {}, [f"could not read manifest JSON: {exc}"], [], qa

    if not isinstance(data, dict):
        return {}, ["manifest root must be an object"], [], qa

    assembly_report = load_assembly_report(manifest_path)
    if assembly_report is None:
        warnings.append("qa/assembly-report.json is missing or unreadable")
    else:
        qa["assemblyReport"] = {
            "ok": assembly_report.get("ok"),
            "outlineImprover": assembly_report.get("outlineImprover"),
        }
        for warning in assembly_report.get("warnings", []):
            warnings.append(f"assembly report warning: {warning}")

    quality_report = load_quality_report(manifest_path)
    if quality_report is None:
        if require_quality_report:
            warnings.append("qa/quality-report.json is missing or unreadable")
    else:
        qa["qualityReport"] = {
            "ok": quality_report.get("ok"),
            "semanticAnchorCheck": quality_report.get("semanticAnchorCheck"),
            "motionQualityCheck": quality_report.get("motionQualityCheck"),
        }
        for error in quality_report.get("errors", []):
            errors.append(f"quality report error: {error}")
        for warning in quality_report.get("warnings", []):
            warnings.append(f"quality report warning: {warning}")

    if key_color is None and assembly_report:
        report_key_color = assembly_report.get("keyColor")
        key_color = report_key_color if isinstance(report_key_color, str) else None
    if spill_threshold is None and assembly_report:
        report_spill_threshold = assembly_report.get("spillThreshold")
        spill_threshold = report_spill_threshold if isinstance(report_spill_threshold, int) else None
    if key_color is None:
        key_color = "#FF00FF"
    if spill_threshold is None:
        spill_threshold = 45

    try:
        key_color_rgb = parse_hex_color(key_color)
    except ValueError as exc:
        errors.append(str(exc))
        key_color_rgb = None

    for key in ["id", "displayName", "atlas", "states"]:
        if key not in data:
            errors.append(f"missing required key: {key}")

    atlas = data.get("atlas")
    if not isinstance(atlas, dict):
        errors.append("atlas must be an object")
        atlas = {}

    missing_atlas = sorted(REQUIRED_ATLAS_FIELDS - set(atlas))
    for key in missing_atlas:
        errors.append(f"atlas missing required key: {key}")

    atlas_path_raw = atlas.get("path")
    if atlas_path_raw is not None and not isinstance(atlas_path_raw, str):
        errors.append("atlas.path must be a string")

    width = require_int(errors, atlas.get("width"), "atlas.width") if "width" in atlas else None
    height = require_int(errors, atlas.get("height"), "atlas.height") if "height" in atlas else None
    columns = require_int(errors, atlas.get("columns"), "atlas.columns") if "columns" in atlas else None
    rows = require_int(errors, atlas.get("rows"), "atlas.rows") if "rows" in atlas else None
    cell_width = require_int(errors, atlas.get("cellWidth"), "atlas.cellWidth") if "cellWidth" in atlas else None
    cell_height = require_int(errors, atlas.get("cellHeight"), "atlas.cellHeight") if "cellHeight" in atlas else None

    if width and columns and cell_width and width != columns * cell_width:
        errors.append("atlas.width must equal atlas.columns * atlas.cellWidth")
    if height and rows and cell_height and height != rows * cell_height:
        errors.append("atlas.height must equal atlas.rows * atlas.cellHeight")

    states = data.get("states")
    if not isinstance(states, dict) or not states:
        errors.append("states must be a non-empty object")
        states = {}

    if profile == "chatbot":
        missing_core = sorted(CHATBOT_CORE_STATES - set(states))
        for state_name in missing_core:
            warnings.append(f"chatbot profile missing core state: {state_name}")

    validate_style_metadata(data, states, errors, warnings, qa, require_state_clarity)
    style = data.get("style")
    if (
        isinstance(style, dict)
        and style.get("stateClarity") == "semantic-enhancers"
        and not (manifest_path.parent / "qa" / "state-readability-check.png").exists()
    ):
        warnings.append("semantic-enhancers pack is missing qa/state-readability-check.png")

    seen_rows: dict[int, str] = {}
    for state_name, state in states.items():
        if not isinstance(state_name, str) or not state_name:
            errors.append("state names must be non-empty strings")
            continue
        if not isinstance(state, dict):
            errors.append(f"states.{state_name} must be an object")
            continue

        row = require_int(errors, state.get("row"), f"states.{state_name}.row", minimum=0)
        frames = require_int(errors, state.get("frames"), f"states.{state_name}.frames")
        durations = state.get("durations")

        if not isinstance(durations, list) or not durations:
            errors.append(f"states.{state_name}.durations must be a non-empty array")
        else:
            for index, duration in enumerate(durations):
                require_int(errors, duration, f"states.{state_name}.durations[{index}]")
            if frames is not None and len(durations) != frames:
                errors.append(f"states.{state_name}.frames must equal durations.length")

        if columns is not None and frames is not None and frames > columns:
            errors.append(f"states.{state_name}.frames exceeds atlas.columns")
        if profile == "chatbot" and frames is not None:
            recommended = CHATBOT_RECOMMENDED_FRAMES.get(state_name)
            if recommended and frames < recommended:
                warnings.append(
                    f"states.{state_name}.frames is {frames}; chatbot profile recommends {recommended}+ for smoother motion"
                )
        if rows is not None and row is not None and row >= rows:
            errors.append(f"states.{state_name}.row exceeds atlas.rows")
        if row is not None:
            previous = seen_rows.get(row)
            if previous:
                errors.append(f"states.{state_name}.row duplicates state {previous}")
            seen_rows[row] = state_name

    if "idle" not in states:
        warnings.append("manifest has no idle state")

    if atlas_path_raw and isinstance(atlas_path_raw, str):
        atlas_path = Path(atlas_path_raw)
        if not atlas_path.is_absolute():
            atlas_path = manifest_path.parent / atlas_path
        if not atlas_path.exists():
            warnings.append(f"atlas image does not exist at {atlas_path}")
        else:
            image_info = inspect_atlas(
                atlas_path,
                states,
                columns,
                cell_width,
                cell_height,
                key_color=key_color_rgb,
                spill_threshold=spill_threshold,
                max_outline_halo_pixels=max_outline_halo_pixels,
            )
            if image_info is None:
                warnings.append("Pillow is unavailable; skipped atlas image dimension check")
            else:
                info, image_errors, image_warnings = image_info
                qa["atlasImage"] = info
                image_width = info["width"]
                image_height = info["height"]
                mode = info["mode"]
                if width and image_width != width:
                    errors.append(f"atlas image width {image_width} does not match manifest {width}")
                if height and image_height != height:
                    errors.append(f"atlas image height {image_height} does not match manifest {height}")
                if "A" not in mode:
                    warnings.append(f"atlas image mode {mode} has no alpha channel")
                errors.extend(image_errors)
                warnings.extend(image_warnings)

    return data, errors, warnings, qa


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to companion manifest.json")
    parser.add_argument(
        "--profile",
        choices=["generic", "chatbot"],
        default="generic",
        help="Validation profile. Use chatbot for website assistant companion packs.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--key-color", help="Chroma-key color used by the assembler; defaults to assembly report or #FF00FF")
    parser.add_argument("--spill-threshold", type=int, help="Spill threshold used by the assembler; defaults to assembly report or 45")
    parser.add_argument("--max-outline-halo-pixels", type=int, default=0, help="Maximum key-colored outline pixels allowed per used frame")
    parser.add_argument(
        "--require-state-clarity",
        action="store_true",
        help="Require style.stateClarity metadata for newly generated companion packs",
    )
    parser.add_argument(
        "--require-quality-report",
        action="store_true",
        help="Require qa/quality-report.json and include quality warnings in strict validation",
    )
    parser.add_argument("--json-out", help="Optional path to write validation JSON")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    _data, errors, warnings, qa = validate_manifest(
        manifest_path,
        profile=args.profile,
        require_state_clarity=args.require_state_clarity,
        require_quality_report=args.require_quality_report,
        key_color=args.key_color,
        spill_threshold=args.spill_threshold,
        max_outline_halo_pixels=args.max_outline_halo_pixels,
    )
    ok = not errors and not (args.strict and warnings)
    result = {
        "ok": ok,
        "manifest": str(manifest_path),
        "profile": args.profile,
        "strict": args.strict,
        "requireStateClarity": args.require_state_clarity,
        "requireQualityReport": args.require_quality_report,
        "errors": errors,
        "warnings": warnings,
        "qa": qa,
    }

    text = json.dumps(result, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).expanduser().resolve().write_text(text + "\n", encoding="utf-8")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
