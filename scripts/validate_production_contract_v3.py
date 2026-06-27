#!/usr/bin/env python3
"""Validate the full production-v3 mascot quality contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3


REQUIRED_COMPAT_REVIEWS = (
    "anatomy-review.json",
    "state-performance-review.json",
    "eye-grammar-review.json",
    "art-direction-review.json",
)


def rel(run_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(run_dir.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def add(blockers: list[str], message: str) -> None:
    blockers.append(message)


def report_json(run_dir: Path, relative: str) -> dict[str, Any] | None:
    path = run_dir / relative
    if not path.exists():
        return None
    return v3.read_json(path)


def validate_state_cue_contract(
    blockers: list[str],
    *,
    manifest: dict[str, Any],
    identity: dict[str, Any] | None,
) -> None:
    if identity is None:
        return
    states = manifest.get("states")
    rules = identity.get("stateCueRules")
    if not isinstance(states, dict) or not isinstance(rules, dict):
        return
    for state_name, state in states.items():
        if not isinstance(state, dict):
            continue
        enhancer = state.get("enhancer")
        rule = rules.get(state_name)
        if not isinstance(enhancer, dict) or not isinstance(rule, dict):
            continue
        for key in ("componentPolicy", "attachment"):
            actual = enhancer.get(key)
            expected = rule.get(key)
            if actual is None or expected is None:
                continue
            if str(actual).strip().lower() != str(expected).strip().lower():
                add(
                    blockers,
                    f"states.{state_name}.enhancer.{key} changed after identity approval: "
                    f"manifest has {actual!r}, identity contract has {expected!r}",
                )


def validate_job_bindings(
    blockers: list[str],
    *,
    run_dir: Path,
    manifest: dict[str, Any],
    identity_sha: str | None,
) -> str | None:
    jobs = v3.jobs_data(run_dir)
    base_review_sha = None
    review_path = run_dir / v3.BASE_REVIEW_PATH
    if review_path.exists() and not v3.base_review_errors(run_dir, manifest):
        base_review_sha = v3.sha256_file(review_path)
    for job in v3.job_list(jobs):
        job_id = str(job.get("id") or "<unknown>")
        bindings = job.get("quality_gate_bindings")
        if not isinstance(bindings, dict):
            add(blockers, f"job {job_id} is missing v3 quality_gate_bindings")
            continue
        if identity_sha and bindings.get("identityContractSha256") != identity_sha:
            add(blockers, f"job {job_id} is not bound to the current identity contract")
        if job_id != "base":
            if base_review_sha is None:
                add(blockers, f"job {job_id} cannot be production-ready without a current canonical base review")
            elif bindings.get("canonicalBaseReviewSha256") != base_review_sha:
                add(blockers, f"job {job_id} is not bound to the current canonical base review")
        if job.get("status") == "complete" and job.get("source_recording_contract_version") != 3:
            add(blockers, f"job {job_id} was not recorded through record_companion_imagegen_result_v3.py")
        for code in job.get("source_style_strict_blocking_warning_codes_v3", []) or []:
            add(blockers, f"job {job_id} v3 source style blocker: {code}")
        cleanup = job.get("chroma_cleanup_verification_v3")
        if isinstance(cleanup, dict):
            for code in cleanup.get("blockingWarningCodes", []) or []:
                add(blockers, f"job {job_id} chroma cleanup blocker: {code}")
    return base_review_sha


def validate_report_evidence(blockers: list[str], run_dir: Path) -> list[Any]:
    approved_exceptions: list[Any] = []
    source_audit = report_json(run_dir, "qa/imagegen-source-style-audit-v3.json")
    if source_audit is None:
        add(blockers, "qa/imagegen-source-style-audit-v3.json is required")
    elif source_audit.get("ok") is not True:
        add(blockers, "qa/imagegen-source-style-audit-v3.json is not OK")

    quality = report_json(run_dir, "qa/quality-report-v3.json")
    if quality is None:
        add(blockers, "qa/quality-report-v3.json is required")
    else:
        approved_exceptions.extend(quality.get("approvedExceptions", []) or [])
        if quality.get("ok") is not True:
            add(blockers, "qa/quality-report-v3.json has unapproved errors or warnings")

    validation = report_json(run_dir, "qa/validation.json") or report_json(run_dir, "qa/validation-with-eye-base-gates.json")
    if validation is None:
        add(blockers, "strict validate_companion_manifest.py report is required")
    elif validation.get("ok") is not True:
        add(blockers, "strict validate_companion_manifest.py report is not OK")

    evidence_path = run_dir / "qa" / "review-evidence.json"
    if not evidence_path.exists():
        add(blockers, "qa/review-evidence.json is required")
    else:
        evidence_sha = v3.sha256_file(evidence_path)
        for filename in REQUIRED_COMPAT_REVIEWS:
            review = report_json(run_dir, f"qa/{filename}")
            if review is None:
                add(blockers, f"qa/{filename} is required")
                continue
            if review.get("status") != "pass" or review.get("productionUse") is not True:
                add(blockers, f"qa/{filename} must be pass with productionUse true")
            if review.get("evidenceSource") != "qa/review-evidence.json":
                add(blockers, f"qa/{filename} must reference qa/review-evidence.json")
            if review.get("reviewEvidenceSha256") != evidence_sha:
                add(blockers, f"qa/{filename} evidence hash is stale")
            checks = review.get("checks")
            if not isinstance(checks, dict) or not checks or any(value is not True for value in checks.values()):
                add(blockers, f"qa/{filename} checks must all be true")
    return approved_exceptions


def validate_contract(manifest_path: Path | str, *, json_out: Path | str | None = None) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    run_dir = manifest_path.parent
    manifest = v3.read_json(manifest_path)
    blockers: list[str] = []
    identity: dict[str, Any] | None = None
    identity_sha: str | None = None

    if manifest.get("qualityPipelineVersion") != 3:
        add(blockers, "manifest qualityPipelineVersion must be 3")
    try:
        _profile, _profile_path, _profile_sha = v3.load_locked_profile(run_dir, manifest, "production-v3")
    except SystemExit as exc:
        add(blockers, str(exc))
    try:
        identity, _identity_path, identity_sha = v3.load_approved_identity(run_dir, manifest)
    except SystemExit as exc:
        add(blockers, str(exc))

    for error in v3.base_review_errors(run_dir, manifest):
        add(blockers, error)
    validate_state_cue_contract(blockers, manifest=manifest, identity=identity)
    base_review_sha = validate_job_bindings(blockers, run_dir=run_dir, manifest=manifest, identity_sha=identity_sha)
    approved_exceptions = validate_report_evidence(blockers, run_dir)

    report = {
        "schemaVersion": 3,
        "ok": not blockers,
        "manifest": str(manifest_path),
        "identityContractSha256": identity_sha,
        "canonicalBaseReviewSha256": base_review_sha,
        "approvedExceptions": approved_exceptions,
        "blockers": blockers,
    }
    out_path = Path(json_out) if json_out else run_dir / "qa" / "production-contract-v3-report.json"
    if not out_path.is_absolute():
        out_path = run_dir / out_path
    v3.write_json(out_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = validate_contract(args.manifest, json_out=args.json_out)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
