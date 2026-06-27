#!/usr/bin/env python3
"""Analyze companion quality with the locked production-v3 QA profile."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3


ANALYZE_SCRIPT = SCRIPT_DIR / "analyze_companion_quality.py"
_analyze_spec = importlib.util.spec_from_file_location("analyze_companion_quality", ANALYZE_SCRIPT)
analyze = importlib.util.module_from_spec(_analyze_spec)
assert _analyze_spec.loader is not None
_analyze_spec.loader.exec_module(analyze)


PROFILE_ARG_MAP = {
    "nearDuplicateDelta": "near_duplicate_delta",
    "maxDuplicateRatio": "max_duplicate_ratio",
    "minAverageMotionDelta": "min_average_motion_delta",
    "maxBodyJumpRatio": "max_body_jump_ratio",
    "maxAreaJumpRatio": "max_area_jump_ratio",
    "maxCoreScaleDriftRatio": "max_core_scale_drift_ratio",
    "maxCoreScaleRangeRatio": "max_core_scale_range_ratio",
    "maxCrossStateCoreScaleDriftRatio": "max_cross_state_core_scale_drift_ratio",
    "maxCoreCenterDriftRatio": "max_core_center_drift_ratio",
    "maxFragmentAreaRatio": "max_fragment_area_ratio",
    "maxSemanticDriftRatio": "max_semantic_drift_ratio",
    "minSemanticPresenceRatio": "min_semantic_presence_ratio",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.json")
    parser.add_argument("--profile", default="production-v3", help="Locked QA profile name")
    parser.add_argument("--json-out", default="qa/quality-report-v3.json", help="Output path relative to the run")
    return parser


def allowances_by_state(identity: dict[str, Any]) -> dict[str, list[str]]:
    quality = identity.get("qualityProfile")
    raw = quality.get("stateAllowances") if isinstance(quality, dict) else {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[str]] = {}
    for state, value in raw.items():
        if isinstance(value, list):
            result[str(state)] = [str(item) for item in value if item]
        elif isinstance(value, dict):
            items = value.get("allowances") or value.get("approvedAllowances") or value.get("codes")
            if isinstance(items, list):
                result[str(state)] = [str(item) for item in items if item]
    return result


def state_from_warning(message: str) -> str | None:
    if not message.startswith("states."):
        return None
    rest = message[len("states.") :]
    if " " not in rest:
        return None
    return rest.split(" ", 1)[0]


def apply_approved_allowances(raw_report: dict[str, Any], allowances: dict[str, list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
    unapproved: list[str] = []
    approved: list[dict[str, Any]] = []
    for warning in raw_report.get("warnings", []):
        message = str(warning)
        state = state_from_warning(message)
        state_allowances = allowances.get(state or "", [])
        if state and state_allowances:
            approved.append({"state": state, "warning": message, "allowances": state_allowances})
        else:
            unapproved.append(message)
    return unapproved, approved


def analyze_quality_v3(
    manifest_path: Path | str,
    *,
    profile: str = "production-v3",
    json_out: str | Path = "qa/quality-report-v3.json",
) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    run_dir = manifest_path.parent
    manifest = v3.read_json(manifest_path)
    locked_profile, profile_path, profile_sha = v3.load_locked_profile(run_dir, manifest, profile)
    identity, _identity_path, identity_sha = v3.load_approved_identity(run_dir, manifest)

    kwargs = {
        arg_name: locked_profile[key]
        for key, arg_name in PROFILE_ARG_MAP.items()
        if key in locked_profile
    }
    raw_json_out = "qa/quality-report-v3-raw.json"
    raw_report = analyze.analyze_manifest_quality(
        manifest_path,
        json_out=raw_json_out,
        semantic_anchor_check="qa/semantic-anchor-check.png",
        motion_quality_check="qa/motion-quality-check.png",
        **kwargs,
    )
    unapproved_warnings, approved_exceptions = apply_approved_allowances(raw_report, allowances_by_state(identity))
    errors = [str(error) for error in raw_report.get("errors", []) if error]
    report = {
        "schemaVersion": 3,
        "ok": not errors and not unapproved_warnings,
        "profile": profile,
        "profilePath": str(profile_path),
        "profileSha256": profile_sha,
        "identityContractSha256": identity_sha,
        "rawReport": str(run_dir / raw_json_out),
        "errors": errors,
        "warnings": unapproved_warnings,
        "approvedExceptions": approved_exceptions,
        "qa": raw_report.get("qa", {}),
        "semanticAnchorCheck": raw_report.get("semanticAnchorCheck"),
        "motionQualityCheck": raw_report.get("motionQualityCheck"),
    }
    out_path = Path(json_out)
    if not out_path.is_absolute():
        out_path = run_dir / out_path
    v3.write_json(out_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze_quality_v3(args.manifest, profile=args.profile, json_out=args.json_out)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
