#!/usr/bin/env python3
"""Create and consume frame-level production-v3 visual review evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3


RESULT_FIELDS = [
    "anatomy",
    "identity",
    "stateRead",
    "eyeGrammar",
    "cueBehavior",
    "pixelArt",
    "appendagesAccountedFor",
    "identityAnchorsVisible",
]

REVIEW_CHECKS_BY_FILE = {
    "art-direction-review.json": (
        "referenceQualityMaintained",
        "identityPreserved",
        "eyeGrammarPreserved",
        "eyeGrammarStableEveryFrame",
        "stylePreserved",
        "pixelArtStyle",
        "cleanupReadyFlatChroma",
        "creativeStateReadability",
        "themeNativeStateCues",
        "nativeEnhancers",
        "integratedEnhancers",
        "anatomyPreserved",
        "noExtraAnatomy",
        "believableOcclusion",
        "noPrototypeFlattening",
        "identityCleanupAndAnatomyOverrideStateRead",
    ),
    "anatomy-review.json": (
        "frameByFrameAnatomyReviewed",
        "appendageCountStable",
        "noExtraAppendages",
        "noDuplicatedAppendages",
        "identityPropsStable",
        "stateCuesNotMisreadAsAnatomy",
        "contactAndOverlapBelievable",
    ),
    "state-performance-review.json": (
        "frameByFrameStateReadReviewed",
        "intendedStateReadable",
        "noWrongStateRead",
        "expressionMatchesState",
        "cueMotionMatchesState",
        "coherentStateStoryArc",
        "mascotActingVariesAcrossFrames",
        "noTiredPantingUnlessStateRequiresIt",
        "noOffVibeGenericCue",
    ),
    "eye-grammar-review.json": (
        "frameByFrameEyeGrammarReviewed",
        "eyeCountStable",
        "eyeShapeStable",
        "eyeFillAndHighlightStable",
        "eyePlacementStable",
        "noWhiteScleraOrCrescentSwap",
        "noMismatchedOrSymbolEyes",
        "blinkStyleMatchesSource",
    ),
}

QA_ARTIFACTS = (
    "qa/contact-sheet.png",
    "qa/cutout-check.png",
    "qa/state-readability-check.png",
    "qa/semantic-anchor-check.png",
    "qa/motion-quality-check.png",
)


def manifest_frame_entries(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = v3.read_json(manifest_path)
    run_dir = manifest_path.parent
    states = manifest.get("states", {})
    if not isinstance(states, dict):
        raise SystemExit("manifest.states must be an object")
    entries: list[dict[str, Any]] = []
    for state_name, state in sorted(states.items(), key=lambda item: int(item[1].get("row", 0)) if isinstance(item[1], dict) else 0):
        if not isinstance(state, dict):
            continue
        frames = int(state.get("frames") or 0)
        for index in range(frames):
            relative = Path("frames") / str(state_name) / f"{index:03d}.png"
            frame_path = run_dir / relative
            entry = {
                "state": str(state_name),
                "frame": index,
                "path": str(relative).replace("\\", "/"),
            }
            if frame_path.exists():
                entry["sha256"] = v3.sha256_file(frame_path)
            entries.append(entry)
    return entries


def write_template(manifest_path: Path | str, out_path: Path | str) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    out_path = Path(out_path).expanduser().resolve()
    template = {
        "schemaVersion": 3,
        "manifest": str(manifest_path),
        "resultFields": RESULT_FIELDS,
        "observations": [
            {
                **entry,
                **{field: "" for field in RESULT_FIELDS},
                "notes": "",
            }
            for entry in manifest_frame_entries(manifest_path)
        ],
    }
    v3.write_json(out_path, template)
    return template


def observation_key(item: dict[str, Any]) -> tuple[str, int]:
    return str(item.get("state")), int(item.get("frame"))


def validate_observations(manifest_path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    expected = manifest_frame_entries(manifest_path)
    observations = data.get("observations")
    if not isinstance(observations, list):
        raise SystemExit("observations must be a list")
    by_key = {
        observation_key(item): item
        for item in observations
        if isinstance(item, dict) and "state" in item and "frame" in item
    }
    for entry in expected:
        key = observation_key(entry)
        if key not in by_key:
            raise SystemExit(f"missing observation for {key[0]} frame {key[1]}")
        item = by_key[key]
        for field in RESULT_FIELDS:
            if str(item.get(field, "")).strip().lower() != "pass":
                raise SystemExit(f"observation for {key[0]} frame {key[1]} must pass {field}")
        notes = str(item.get("notes") or "").strip()
        if len(notes) < 20:
            raise SystemExit(f"observation for {key[0]} frame {key[1]} needs concrete notes")
    return [by_key[observation_key(entry)] for entry in expected]


def artifact_hashes(run_dir: Path) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    manifest = v3.read_json(run_dir / "manifest.json")
    atlas = manifest.get("atlas")
    if isinstance(atlas, dict) and isinstance(atlas.get("path"), str):
        atlas_path = run_dir / atlas["path"]
        if atlas_path.exists():
            artifacts[str(atlas["path"])] = v3.sha256_file(atlas_path)
    for relative in QA_ARTIFACTS:
        path = run_dir / relative
        if path.exists():
            artifacts[relative] = v3.sha256_file(path)
    return artifacts


def write_compat_reviews(run_dir: Path, evidence_sha: str, observation_count: int) -> list[str]:
    created: list[str] = []
    for filename, checks in REVIEW_CHECKS_BY_FILE.items():
        review = {
            "schemaVersion": 3,
            "status": "pass",
            "productionUse": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "evidenceSource": "qa/review-evidence.json",
            "reviewEvidenceSha256": evidence_sha,
            "reviewedFrames": observation_count,
            "checks": {check: True for check in checks},
            "blockers": [],
        }
        v3.write_json(run_dir / "qa" / filename, review)
        created.append(str(run_dir / "qa" / filename))
    return created


def consume_observations(manifest_path: Path | str, observations_json: Path | str) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    run_dir = manifest_path.parent
    observations_path = Path(observations_json).expanduser().resolve()
    data = v3.read_json(observations_path)
    observations = validate_observations(manifest_path, data)
    evidence = {
        "schemaVersion": 3,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "sourceObservations": str(observations_path),
        "evidenceArtifactHashes": artifact_hashes(run_dir),
        "observations": observations,
    }
    evidence_path = run_dir / "qa" / "review-evidence.json"
    v3.write_json(evidence_path, evidence)
    evidence_sha = v3.sha256_file(evidence_path)
    reviews = write_compat_reviews(run_dir, evidence_sha, len(observations))
    return {"ok": True, "evidence": str(evidence_path), "reviewEvidenceSha256": evidence_sha, "reviews": reviews}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    template_parser = subparsers.add_parser("template")
    template_parser.add_argument("--manifest", required=True, type=Path)
    template_parser.add_argument("--out", required=True, type=Path)
    consume_parser = subparsers.add_parser("consume")
    consume_parser.add_argument("--manifest", required=True, type=Path)
    consume_parser.add_argument("--observations", required=True, type=Path)
    args = parser.parse_args(argv)

    if args.command == "template":
        result = write_template(args.manifest, args.out)
    else:
        result = consume_observations(args.manifest, args.observations)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
