#!/usr/bin/env python3
"""Create or update the manual art-direction QA review for a companion pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_CHECKS = [
    "referenceQualityMaintained",
    "identityPreserved",
    "stylePreserved",
    "pixelArtStyle",
    "creativeStateReadability",
    "themeNativeStateCues",
    "nativeEnhancers",
    "integratedEnhancers",
    "anatomyPreserved",
    "noExtraAnatomy",
    "believableOcclusion",
    "noPrototypeFlattening",
]

ALLOWED_PRODUCTION_GENERATION_METHODS = {
    "imagegen-integrated-row-art",
    "user-provided-integrated-row-art",
    "artist-provided-integrated-row-art",
}


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to companion manifest.json")
    parser.add_argument(
        "--status",
        choices=["pass", "fail"],
        default="fail",
        help="Manual art-direction status. Use pass only after visual review.",
    )
    parser.add_argument(
        "--generation-method",
        default="imagegen-integrated-row-art",
        help="How final frame art was produced. Production pass allows only integrated row art methods.",
    )
    parser.add_argument("--source-reference", help="Original reference image used for visual comparison")
    parser.add_argument("--production-use", action="store_true", help="Mark this review as accepted for production use")
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Set a required boolean check, e.g. --check identityPreserved=true",
    )
    parser.add_argument("--blocker", action="append", default=[], help="Record an unresolved visual blocker")
    parser.add_argument("--notes", default="", help="Short visual review notes")
    parser.add_argument("--out", type=Path, help="Output JSON; defaults to qa/art-direction-review.json")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()

    source_reference_value = args.source_reference

    if args.status == "pass" and args.production_use:
        if args.generation_method not in ALLOWED_PRODUCTION_GENERATION_METHODS:
            parser.error(
                "--generation-method must be one of "
                + ", ".join(sorted(ALLOWED_PRODUCTION_GENERATION_METHODS))
                + " for a production pass"
            )
        if not args.source_reference:
            parser.error("--source-reference is required for a production pass")
        source_reference_path = Path(args.source_reference).expanduser()
        if not source_reference_path.is_absolute():
            source_reference_path = manifest_path.parent / source_reference_path
        if not source_reference_path.exists():
            parser.error("--source-reference must point to an existing image for a production pass")
        source_reference_value = str(source_reference_path.resolve())

    checks = parse_check_values(args.check)
    if args.status == "pass" and args.production_use:
        false_checks = [key for key, value in checks.items() if value is not True]
        if false_checks:
            parser.error("all required --check values must be true for a production pass: " + ", ".join(false_checks))
    out_path = args.out.expanduser().resolve() if args.out else manifest_path.parent / "qa" / "art-direction-review.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    review = {
        "status": args.status,
        "generationMethod": args.generation_method,
        "sourceReference": source_reference_value,
        "productionUse": bool(args.production_use),
        "checks": checks,
        "blockers": args.blocker,
        "notes": args.notes,
    }
    out_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "artDirectionReview": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
