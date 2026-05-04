#!/usr/bin/env python3
"""Create a small-size readability QA sheet for companion mascot states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_SIZES = [64, 96, 128]


def parse_sizes(value: str) -> list[int]:
    sizes = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not sizes:
        raise ValueError("at least one size is required")
    return sizes


def choose_states(manifest: dict[str, Any], requested: str | None) -> list[tuple[str, int]]:
    states = manifest.get("states", {})
    if requested:
        return [(name.strip(), 0) for name in requested.split(",") if name.strip()]

    enhanced = [
        name
        for name, state in states.items()
        if isinstance(state, dict) and isinstance(state.get("enhancer"), dict)
    ]
    if enhanced:
        return [(name, min(1, int(states[name].get("frames", 1)) - 1)) for name in enhanced]

    fallback = [name for name in ["listening", "thinking", "working", "answering", "success", "error"] if name in states]
    return [(name, 0) for name in fallback]


def crop_frame(atlas: Image.Image, state: dict[str, Any], frame: int, cell_width: int, cell_height: int) -> Image.Image:
    frame = max(0, min(frame, int(state["frames"]) - 1))
    row = int(state["row"])
    cell = atlas.crop(
        (
            frame * cell_width,
            row * cell_height,
            (frame + 1) * cell_width,
            (row + 1) * cell_height,
        )
    )
    bbox = cell.getbbox()
    return cell.crop(bbox) if bbox else cell


def make_sheet(manifest_path: Path, out_path: Path, sizes: list[int], requested_states: str | None) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    atlas_meta = manifest["atlas"]
    atlas_path = Path(atlas_meta["path"])
    if not atlas_path.is_absolute():
        atlas_path = manifest_path.parent / atlas_path
    atlas = Image.open(atlas_path).convert("RGBA")

    cell_width = int(atlas_meta["cellWidth"])
    cell_height = int(atlas_meta["cellHeight"])
    states = choose_states(manifest, requested_states)
    if not states:
        raise ValueError("no states selected for readability sheet")

    font = ImageFont.load_default()
    label_width = 124
    tile = 156
    row_height = 166
    header_height = 34
    pad = 18
    width = label_width + len(sizes) * tile + pad
    height = header_height + len(states) * row_height + pad
    sheet = Image.new("RGBA", (width, height), (244, 246, 249, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 10), "state", fill=(20, 24, 31, 255), font=font)

    for column, size in enumerate(sizes):
        draw.text((label_width + column * tile + 12, 10), f"{size}px", fill=(20, 24, 31, 255), font=font)

    manifest_states = manifest["states"]
    for row_index, (name, frame) in enumerate(states):
        if name not in manifest_states:
            raise ValueError(f"manifest has no state named {name}")

        y = header_height + row_index * row_height
        row_fill = (255, 255, 255, 255) if row_index % 2 == 0 else (236, 240, 246, 255)
        draw.rectangle((0, y, width, y + row_height - 1), fill=row_fill)
        state = manifest_states[name]
        enhancer = state.get("enhancer", {}).get("kind", "") if isinstance(state, dict) else ""
        draw.text((12, y + 12), name, fill=(20, 24, 31, 255), font=font)
        draw.text((12, y + 28), str(enhancer)[:20], fill=(76, 86, 102, 255), font=font)

        crop = crop_frame(atlas, state, frame, cell_width, cell_height)
        for column, size in enumerate(sizes):
            thumb = crop.copy()
            thumb.thumbnail((size, size), Image.Resampling.LANCZOS)
            panel_x = label_width + column * tile + 12
            panel_y = y + 28
            draw.rounded_rectangle((panel_x - 8, panel_y - 8, panel_x + 132, panel_y + 132), radius=6, fill=(14, 18, 27, 255))
            sheet.alpha_composite(thumb, (panel_x + (124 - thumb.width) // 2, panel_y + (124 - thumb.height) // 2))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to companion manifest.json")
    parser.add_argument("--out", type=Path, help="Output QA PNG; defaults to qa/state-readability-check.png")
    parser.add_argument("--sizes", default="64,96,128", help="Comma-separated preview sizes")
    parser.add_argument("--states", help="Optional comma-separated states to include")
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    out_path = args.out.expanduser().resolve() if args.out else manifest_path.parent / "qa" / "state-readability-check.png"
    make_sheet(manifest_path, out_path, parse_sizes(args.sizes), args.states)
    print(json.dumps({"ok": True, "readabilitySheet": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
