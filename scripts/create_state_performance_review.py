#!/usr/bin/env python3
"""Create a frame-by-frame state-performance QA sheet and review record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


REQUIRED_CHECKS = [
    "frameByFrameStateReadReviewed",
    "intendedStateReadable",
    "noWrongStateRead",
    "expressionMatchesState",
    "cueMotionMatchesState",
    "noTiredPantingUnlessStateRequiresIt",
    "noOffVibeGenericCue",
]


def parse_check_values(values: list[str]) -> dict[str, bool]:
    checks = {key: False for key in REQUIRED_CHECKS}
    for value in values:
        if "=" not in value:
            raise ValueError(f"expected check=value, got {value!r}")
        key, raw = value.split("=", 1)
        key = key.strip()
        if key not in checks:
            raise ValueError(f"unknown check {key!r}; expected one of: {', '.join(REQUIRED_CHECKS)}")
        normalized = raw.strip().lower()
        if normalized not in {"true", "false"}:
            raise ValueError(f"check {key!r} must be true or false")
        checks[key] = normalized == "true"
    return checks


def parse_expected_state_reads(values: list[str]) -> dict[str, str]:
    reads: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"expected state=read, got {value!r}")
        key, raw = value.split("=", 1)
        key = key.strip()
        read = raw.strip()
        if not key:
            raise ValueError(f"expected non-empty state name in {value!r}")
        if not read:
            raise ValueError(f"expected non-empty read for state {key!r}")
        reads[key] = read
    return reads


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def checkerboard(width: int, height: int, block: int = 16) -> Image.Image:
    image = Image.new("RGBA", (width, height), (245, 246, 248, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, block):
        for x in range(0, width, block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill=(226, 230, 235, 255))
    return image


def crop_frame(atlas: Image.Image, state: dict[str, Any], frame_index: int, cell_width: int, cell_height: int) -> Image.Image:
    row = int(state["row"])
    cell = atlas.crop(
        (
            frame_index * cell_width,
            row * cell_height,
            (frame_index + 1) * cell_width,
            (row + 1) * cell_height,
        )
    )
    bbox = cell.getbbox()
    return cell.crop(bbox) if bbox else cell


def make_sheet(manifest_path: Path, out_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    atlas_meta = manifest["atlas"]
    atlas_path = Path(atlas_meta["path"])
    if not atlas_path.is_absolute():
        atlas_path = manifest_path.parent / atlas_path
    atlas = Image.open(atlas_path).convert("RGBA")
    cell_width = int(atlas_meta["cellWidth"])
    cell_height = int(atlas_meta["cellHeight"])
    states = [
        (name, state)
        for name, state in sorted(manifest["states"].items(), key=lambda item: int(item[1].get("row", 0)))
        if isinstance(state, dict)
    ]
    if not states:
        raise ValueError("manifest has no states")

    tile = (148, 166)
    label_width = 210
    margin = 14
    gap = 10
    max_frames = max(int(state.get("frames", 0)) for _name, state in states)
    width = label_width + max_frames * (tile[0] + gap) + margin * 2
    height = len(states) * (tile[1] + gap) + margin * 2
    sheet = checkerboard(width, height)
    draw = ImageDraw.Draw(sheet)
    font = load_font(14)
    small_font = load_font(11)

    for row_index, (name, state) in enumerate(states):
        y = margin + row_index * (tile[1] + gap)
        draw.rectangle((margin, y, margin + label_width - 14, y + tile[1]), fill=(255, 255, 255, 235))
        draw.text((margin + 8, y + 10), name, fill=(20, 24, 31, 255), font=font)
        draw.text((margin + 8, y + 30), f"{int(state['frames'])} frames", fill=(55, 65, 80, 255), font=small_font)
        draw.text((margin + 8, y + 48), "read intended state", fill=(55, 65, 80, 255), font=small_font)
        draw.text((margin + 8, y + 64), "face/cue/acting match", fill=(55, 65, 80, 255), font=small_font)
        draw.text((margin + 8, y + 80), "reject wrong-state read", fill=(55, 65, 80, 255), font=small_font)
        for index in range(int(state["frames"])):
            x = margin + label_width + index * (tile[0] + gap)
            frame = crop_frame(atlas, state, index, cell_width, cell_height)
            frame.thumbnail((tile[0] - 24, tile[1] - 34), Image.Resampling.NEAREST)
            panel = Image.new("RGBA", tile, (16, 19, 28, 255))
            panel_draw = ImageDraw.Draw(panel)
            panel_draw.rectangle((0, 0, tile[0] - 1, tile[1] - 1), outline=(112, 130, 160, 255), width=1)
            panel_draw.text((8, 7), f"{index + 1}", fill=(255, 255, 255, 255), font=font)
            panel.alpha_composite(frame, ((tile[0] - frame.width) // 2, 28 + (tile[1] - 34 - frame.height) // 2))
            sheet.alpha_composite(panel, (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def reviewed_frames_for_manifest(manifest_path: Path) -> tuple[list[str], dict[str, list[int]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    states = manifest.get("states", {})
    state_names: list[str] = []
    reviewed_frames: dict[str, list[int]] = {}
    for name, state in states.items():
        if not isinstance(name, str) or not isinstance(state, dict) or not isinstance(state.get("frames"), int):
            continue
        state_names.append(name)
        reviewed_frames[name] = list(range(1, int(state["frames"]) + 1))
    return state_names, reviewed_frames


def manifest_state_names(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    states = manifest.get("states", {})
    return [
        name
        for name, state in states.items()
        if isinstance(name, str) and isinstance(state, dict) and isinstance(state.get("frames"), int)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to companion manifest.json")
    parser.add_argument("--status", choices=["pass", "fail"], default="fail")
    parser.add_argument("--production-use", action="store_true", help="Mark this state-performance review as accepted for production")
    parser.add_argument("--review-all-frames", action="store_true", help="Declare every used state frame reviewed")
    parser.add_argument(
        "--expected-state-read",
        action="append",
        default=[],
        help="Expected state read in state=description form, e.g. --expected-state-read working='active tool use, not panting'",
    )
    parser.add_argument("--check", action="append", default=[], help="Set a required boolean check, e.g. --check noWrongStateRead=true")
    parser.add_argument("--blocker", action="append", default=[], help="Record an unresolved visual state-performance blocker")
    parser.add_argument("--notes", default="", help="Short frame-by-frame state-performance review notes")
    parser.add_argument("--out-json", type=Path, help="Output JSON; defaults to qa/state-performance-review.json")
    parser.add_argument("--out-sheet", type=Path, help="Output sheet; defaults to qa/state-performance-review.png")
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    checks = parse_check_values(args.check)
    expected_state_reads = parse_expected_state_reads(args.expected_state_read)
    states_reviewed, reviewed_frames = reviewed_frames_for_manifest(manifest_path) if args.review_all_frames else ([], {})
    state_names = manifest_state_names(manifest_path)

    if args.status == "pass" and args.production_use:
        false_checks = [key for key, value in checks.items() if value is not True]
        if false_checks:
            parser.error("all required --check values must be true for a production pass: " + ", ".join(false_checks))
        if not args.review_all_frames:
            parser.error("--review-all-frames is required for a production pass")
        missing_reads = [state for state in state_names if not expected_state_reads.get(state, "").strip()]
        if missing_reads:
            parser.error(
                "--expected-state-read is required for every state in a production pass: "
                + ", ".join(missing_reads)
            )

    out_json = args.out_json.expanduser().resolve() if args.out_json else manifest_path.parent / "qa" / "state-performance-review.json"
    out_sheet = args.out_sheet.expanduser().resolve() if args.out_sheet else manifest_path.parent / "qa" / "state-performance-review.png"
    make_sheet(manifest_path, out_sheet)

    review = {
        "status": args.status,
        "productionUse": bool(args.production_use),
        "statesReviewed": states_reviewed,
        "reviewedFrames": reviewed_frames,
        "expectedStateReads": expected_state_reads,
        "checks": checks,
        "blockers": args.blocker,
        "notes": args.notes,
        "statePerformanceReviewSheet": str(out_sheet),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "statePerformanceReview": str(out_json), "statePerformanceReviewSheet": str(out_sheet)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
