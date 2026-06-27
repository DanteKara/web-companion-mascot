#!/usr/bin/env python3
"""Create the production-v3 canonical base review that unlocks row recording."""

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


REQUIRED_CHECKS = [
    "native16BitPixelArt",
    "noSmooth3DRendering",
    "silhouetteReadableAt64px",
    "speciesOrFormReadable",
    "identityMatchesContract",
    "anatomyMatchesContract",
    "faceGrammarMatchesContract",
    "paletteRolesPreserved",
    "animationReadySimplification",
    "noChromaContamination",
]

REQUIRED_OBSERVATIONS = [
    "silhouette",
    "speciesOrForm",
    "anatomy",
    "faceGrammar",
    "palette",
    "pixelArt",
    "smallSize",
]


def parse_key_values(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"expected key=value, got {value!r}")
        key, raw = value.split("=", 1)
        text = raw.strip()
        if text.lower() in {"true", "false"}:
            result[key.strip()] = text.lower() == "true"
        else:
            result[key.strip()] = text
    return result


def create_review(
    *,
    manifest_path: Path | str,
    candidates: list[Path | str],
    status: str,
    production_use: bool,
    checks: dict[str, Any],
    observations: dict[str, Any],
    notes: str,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    run_dir = manifest_path.parent
    manifest = v3.read_json(manifest_path)
    _identity, _identity_path, identity_sha = v3.load_approved_identity(run_dir, manifest)
    base_path = v3.canonical_base_path(run_dir, manifest)
    if not base_path.exists():
        raise SystemExit("canonical base image is missing; record the base before review")
    candidates = [Path(candidate).expanduser().resolve() for candidate in candidates]
    if status == "pass" and production_use and len(candidates) < 2:
        raise SystemExit("production pass requires at least two candidate paths")
    missing_checks = [name for name in REQUIRED_CHECKS if checks.get(name) is not True]
    if status == "pass" and missing_checks:
        raise SystemExit("canonical base review pass requires true checks: " + ", ".join(missing_checks))
    missing_observations = [
        name for name in REQUIRED_OBSERVATIONS if not isinstance(observations.get(name), str) or not observations[name].strip()
    ]
    if status == "pass" and missing_observations:
        raise SystemExit("canonical base review pass requires observations: " + ", ".join(missing_observations))

    review = {
        "schemaVersion": 3,
        "status": status,
        "productionUse": bool(production_use),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "identityContractSha256": identity_sha,
        "canonicalBasePath": str(base_path),
        "canonicalBaseSha256": v3.sha256_file(base_path),
        "candidates": [
            {"path": str(candidate), "sha256": v3.sha256_file(candidate)}
            for candidate in candidates
            if candidate.exists()
        ],
        "checks": {name: bool(checks.get(name)) for name in REQUIRED_CHECKS},
        "observations": {name: str(observations.get(name, "")) for name in REQUIRED_OBSERVATIONS},
        "notes": notes,
    }
    out_path = run_dir / v3.BASE_REVIEW_PATH
    v3.write_json(out_path, review)
    review_sha = v3.sha256_file(out_path)

    jobs = v3.jobs_data(run_dir)
    bindings = jobs.setdefault("quality_gate_bindings", {})
    bindings["identityContractSha256"] = identity_sha
    bindings["canonicalBaseReviewSha256"] = review_sha
    for job in v3.job_list(jobs):
        if job.get("id") == "base":
            continue
        job_bindings = job.setdefault("quality_gate_bindings", {})
        job_bindings["identityContractSha256"] = identity_sha
        job_bindings["canonicalBaseReviewSha256"] = review_sha
    v3.write_jobs(run_dir, jobs)
    return {"ok": status == "pass", "review": str(out_path), "canonicalBaseReviewSha256": review_sha}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--candidate", action="append", default=[], type=Path)
    parser.add_argument("--status", choices=["pass", "fail"], default="fail")
    parser.add_argument("--production-use", action="store_true")
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--observation", action="append", default=[])
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv)
    result = create_review(
        manifest_path=args.manifest,
        candidates=args.candidate,
        status=args.status,
        production_use=args.production_use,
        checks=parse_key_values(args.check),
        observations=parse_key_values(args.observation),
        notes=args.notes,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
