#!/usr/bin/env python3
"""Stitch generated row-strip parts into one source row.

This script does not draw or synthesize mascot art. It only concatenates
imagegen/user-provided row parts so long animation rows can be generated in
shorter, more reliable chunks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16), 255)


def stitch_parts(
    parts: list[Path],
    out: Path,
    *,
    key_color: tuple[int, int, int, int] = (255, 0, 255, 255),
    align: str = "center",
) -> dict[str, Any]:
    if len(parts) < 2:
        raise ValueError("At least two row parts are required")
    images = [Image.open(part).convert("RGBA") for part in parts]
    width = sum(image.width for image in images)
    height = max(image.height for image in images)
    stitched = Image.new("RGBA", (width, height), key_color)

    x = 0
    part_reports = []
    for part, image in zip(parts, images):
        if align == "top":
            y = 0
        elif align == "bottom":
            y = height - image.height
        else:
            y = (height - image.height) // 2
        stitched.alpha_composite(image, (x, y))
        part_reports.append(
            {
                "path": str(part),
                "width": image.width,
                "height": image.height,
                "x": x,
                "y": y,
            }
        )
        x += image.width

    out.parent.mkdir(parents=True, exist_ok=True)
    stitched.save(out)
    return {
        "ok": True,
        "out": str(out),
        "width": width,
        "height": height,
        "align": align,
        "parts": part_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", nargs="+", required=True, help="Generated row-strip part images in left-to-right order")
    parser.add_argument("--out", required=True, help="Output stitched row-strip image")
    parser.add_argument("--key-color", default="#FF00FF", help="Background color for any empty canvas areas")
    parser.add_argument("--align", choices=["top", "center", "bottom"], default="center", help="Vertical alignment for parts with different heights")
    parser.add_argument("--json-out", help="Optional JSON report path")
    args = parser.parse_args()

    result = stitch_parts(
        [Path(part) for part in args.parts],
        Path(args.out),
        key_color=parse_hex_color(args.key_color),
        align=args.align,
    )

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
