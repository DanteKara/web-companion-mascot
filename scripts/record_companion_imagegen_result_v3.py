#!/usr/bin/env python3
"""Record imagegen outputs under the production-v3 quality contract."""

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


RECORD_SCRIPT = SCRIPT_DIR / "record_companion_imagegen_result.py"
_record_spec = importlib.util.spec_from_file_location("record_companion_imagegen_result", RECORD_SCRIPT)
record = importlib.util.module_from_spec(_record_spec)
assert _record_spec.loader is not None
_record_spec.loader.exec_module(record)


CHROMA_CLEANUP_PROVENANCES = {
    "built-in-imagegen-chroma-cleanup",
    "codex-app-imagegen-chroma-cleanup",
}


def current_base_review_sha(run_dir: Path, manifest: dict[str, Any]) -> str:
    errors = v3.base_review_errors(run_dir, manifest)
    if errors:
        raise SystemExit("canonical base review is not current: " + "; ".join(errors))
    return v3.sha256_file(run_dir / v3.BASE_REVIEW_PATH)


def enforce_quality_gates(run_dir: Path, job: dict[str, Any]) -> tuple[dict[str, Any], str, str | None]:
    manifest_path = run_dir / "manifest.json"
    manifest = v3.read_json(manifest_path)
    _identity, _identity_path, identity_sha = v3.load_approved_identity(run_dir, manifest)
    bindings = job.setdefault("quality_gate_bindings", {})
    if bindings.get("identityContractSha256") != identity_sha:
        raise SystemExit(f"job {job.get('id')} is not bound to the current approved identity contract")

    base_review_sha = None
    if job.get("id") != "base":
        base_review_sha = current_base_review_sha(run_dir, manifest)
        if bindings.get("canonicalBaseReviewSha256") != base_review_sha:
            raise SystemExit(f"job {job.get('id')} is not bound to the current canonical base review")
    return manifest, identity_sha, base_review_sha


def strict_codes_for_job(job: dict[str, Any], analysis: dict[str, Any]) -> list[str]:
    codes = [str(code) for code in analysis.get("blockingWarningCodes", []) if code]
    if job.get("id") == "base":
        return codes
    if job.get("kind") == "row-strip":
        return codes
    return codes


def format_strict_style_failure(job_id: str, strict_codes: list[str], analysis: dict[str, Any]) -> str:
    foreground = analysis.get("foreground") if isinstance(analysis.get("foreground"), dict) else {}
    payload = {
        "blockingWarningCodes": analysis.get("blockingWarningCodes", strict_codes),
        "advisoryWarningCodes": analysis.get("advisoryWarningCodes", []),
        "rawUniqueRgbCount": foreground.get("rawUniqueRgbCount"),
        "quantizedColorCount": foreground.get("quantizedColorCount"),
        "partialAlphaRatio": foreground.get("partialAlphaRatio"),
        "sameOrSmallDeltaRampRatio": foreground.get("sameOrSmallDeltaRampRatio"),
        "hardTransitionRatio": foreground.get("hardTransitionRatio"),
    }
    return (
        f"v3 source style analysis failed for {job_id}: {', '.join(strict_codes)}\n"
        + json.dumps(payload, indent=2)
    )


def update_recorded_job_v3(
    *,
    run_dir: Path,
    job_id: str,
    analysis: dict[str, Any],
    cleanup_verification: dict[str, Any] | None,
    identity_sha: str,
    base_review_sha: str | None,
) -> dict[str, Any]:
    jobs = v3.jobs_data(run_dir)
    job = v3.find_job(jobs, job_id)
    bindings = job.setdefault("quality_gate_bindings", {})
    bindings["identityContractSha256"] = identity_sha
    if base_review_sha is not None:
        bindings["canonicalBaseReviewSha256"] = base_review_sha

    strict_codes = strict_codes_for_job(job, analysis)
    job["source_recording_contract_version"] = 3
    job["source_style_analysis_v3"] = analysis
    job["source_style_strict_blocking_warning_codes_v3"] = strict_codes
    if cleanup_verification is not None:
        job["chroma_cleanup_verification_v3"] = cleanup_verification
    else:
        job.pop("chroma_cleanup_verification_v3", None)

    if not strict_codes:
        legacy_base = job.get("base_style_strict_blocking_warning_codes")
        if legacy_base == ["smooth_or_overdetailed_foreground_palette"]:
            job["base_style_strict_blocking_warning_codes"] = []
        legacy_row = job.get("row_source_style_strict_blocking_warning_codes")
        if legacy_row == ["smooth_or_overdetailed_foreground_palette"]:
            job["row_source_style_strict_blocking_warning_codes"] = []

    v3.write_jobs(run_dir, jobs)
    return job


def record_result_v3(
    *,
    run_dir: Path,
    job_id: str,
    source: Path,
    source_provenance: str,
    force: bool,
    allow_synthetic_test_source: bool,
    strict_base_style: bool = False,
    strict_row_style: bool = False,
    chroma_cleanup_source: Path | None = None,
    codex_app_capture_metadata: Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(run_dir).expanduser().resolve()
    source = Path(source).expanduser().resolve()
    jobs = v3.jobs_data(run_dir)
    job = v3.find_job(jobs, job_id)
    manifest, identity_sha, base_review_sha = enforce_quality_gates(run_dir, job)

    chroma_key = v3.chroma_key_from_run(run_dir)
    analysis = v3.analyze_source_style(source, chroma_key)
    strict_requested = strict_base_style if job_id == "base" else strict_row_style
    strict_codes = strict_codes_for_job(job, analysis)
    if strict_requested and strict_codes:
        raise SystemExit(format_strict_style_failure(job_id, strict_codes, analysis))

    cleanup_verification = None
    if source_provenance in CHROMA_CLEANUP_PROVENANCES:
        if chroma_cleanup_source is None:
            raise SystemExit(f"{source_provenance} requires --chroma-cleanup-source")
        cleanup_verification = v3.verify_background_only_cleanup(chroma_cleanup_source, source, chroma_key)
        if cleanup_verification.get("blockingWarningCodes"):
            codes = ", ".join(str(code) for code in cleanup_verification["blockingWarningCodes"])
            raise SystemExit("chroma cleanup changed protected foreground pixels: " + codes)

    result = record.record_result(
        run_dir=run_dir,
        job_id=job_id,
        source=source,
        source_provenance=source_provenance,
        force=force,
        allow_synthetic_test_source=allow_synthetic_test_source,
        strict_base_style=False,
        strict_row_style=False,
        chroma_cleanup_source=chroma_cleanup_source,
        codex_app_capture_metadata=codex_app_capture_metadata,
    )
    recorded_job = update_recorded_job_v3(
        run_dir=run_dir,
        job_id=job_id,
        analysis=analysis,
        cleanup_verification=cleanup_verification,
        identity_sha=identity_sha,
        base_review_sha=base_review_sha,
    )
    result["qualityPipelineVersion"] = 3
    result["source_style_analysis_v3"] = analysis
    result["source_style_strict_blocking_warning_codes_v3"] = recorded_job[
        "source_style_strict_blocking_warning_codes_v3"
    ]
    if cleanup_verification is not None:
        result["chroma_cleanup_verification_v3"] = cleanup_verification
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--source-provenance",
        choices=[
            "auto",
            "built-in-imagegen",
            "codex-app-imagegen",
            "built-in-imagegen-chroma-cleanup",
            "codex-app-imagegen-chroma-cleanup",
            "user-provided-integrated-row-art",
            "artist-provided-integrated-row-art",
        ],
        default="auto",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--strict-base-style", action="store_true")
    parser.add_argument("--strict-row-style", action="store_true")
    parser.add_argument("--chroma-cleanup-source", type=Path)
    parser.add_argument("--codex-app-capture-metadata", type=Path)
    parser.add_argument("--allow-synthetic-test-source", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = record_result_v3(
        run_dir=args.run_dir,
        job_id=args.job_id,
        source=args.source,
        source_provenance=args.source_provenance,
        force=args.force,
        allow_synthetic_test_source=args.allow_synthetic_test_source,
        strict_base_style=args.strict_base_style,
        strict_row_style=args.strict_row_style,
        chroma_cleanup_source=args.chroma_cleanup_source,
        codex_app_capture_metadata=args.codex_app_capture_metadata,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
