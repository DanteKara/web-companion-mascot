#!/usr/bin/env python3
"""Audit recorded production-v3 imagegen sources for native pixel-art suitability."""

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


CHROMA_CLEANUP_PROVENANCES = {
    "built-in-imagegen-chroma-cleanup",
    "codex-app-imagegen-chroma-cleanup",
}


def resolve_path(run_dir: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return path.resolve()


def audit_job(run_dir: Path, job: dict[str, Any], chroma_key: tuple[int, int, int]) -> dict[str, Any]:
    job_id = str(job.get("id") or "<unknown>")
    source_path = resolve_path(run_dir, job.get("source_path") or job.get("source"))
    item: dict[str, Any] = {
        "id": job_id,
        "kind": job.get("kind"),
        "status": job.get("status"),
        "sourcePath": str(source_path) if source_path else "",
        "sourceProvenance": job.get("source_provenance"),
        "strictBlockingWarningCodes": [],
        "advisoryWarningCodes": [],
        "errors": [],
    }
    if job.get("status") != "complete":
        return item
    if source_path is None or not source_path.exists():
        item["errors"].append("recorded source path is missing")
        return item

    analysis = v3.analyze_source_style(source_path, chroma_key)
    item["sourceStyleAnalysisV3"] = analysis
    item["strictBlockingWarningCodes"] = list(analysis.get("blockingWarningCodes", []))
    item["advisoryWarningCodes"] = list(analysis.get("advisoryWarningCodes", []))

    if job.get("source_provenance") in CHROMA_CLEANUP_PROVENANCES:
        cleanup = job.get("chroma_cleanup")
        original = resolve_path(run_dir, cleanup.get("originalSourcePath")) if isinstance(cleanup, dict) else None
        if original is None or not original.exists():
            item["strictBlockingWarningCodes"].append("missing_chroma_cleanup_original_source")
        else:
            verification = v3.verify_background_only_cleanup(original, source_path, chroma_key)
            item["chromaCleanupVerificationV3"] = verification
            item["strictBlockingWarningCodes"].extend(verification.get("blockingWarningCodes", []))

    item["strictBlockingWarningCodes"] = sorted(set(str(code) for code in item["strictBlockingWarningCodes"] if code))
    return item


def audit_sources_v3(run_dir: Path | str, *, json_out: Path | str | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir).expanduser().resolve()
    manifest = v3.read_json(run_dir / "manifest.json")
    jobs = v3.jobs_data(run_dir)
    chroma_key = v3.chroma_key_from_run(run_dir)
    base_jobs: list[dict[str, Any]] = []
    row_jobs: list[dict[str, Any]] = []
    other_jobs: list[dict[str, Any]] = []
    for job in v3.job_list(jobs):
        item = audit_job(run_dir, job, chroma_key)
        if job.get("id") == "base":
            base_jobs.append(item)
        elif job.get("kind") == "row-strip":
            row_jobs.append(item)
        else:
            other_jobs.append(item)

    blockers = [
        f"{item['id']}: {code}"
        for item in base_jobs + row_jobs + other_jobs
        for code in item.get("strictBlockingWarningCodes", [])
    ]
    errors = [
        f"{item['id']}: {error}"
        for item in base_jobs + row_jobs + other_jobs
        for error in item.get("errors", [])
    ]
    report = {
        "schemaVersion": 3,
        "ok": not blockers and not errors,
        "qualityPipelineVersion": manifest.get("qualityPipelineVersion"),
        "chromaKey": list(chroma_key),
        "baseJobs": base_jobs,
        "rowJobs": row_jobs,
        "otherJobs": other_jobs,
        "blockers": blockers,
        "errors": errors,
    }
    out_path = Path(json_out) if json_out else run_dir / "qa" / "imagegen-source-style-audit-v3.json"
    if not out_path.is_absolute():
        out_path = run_dir / out_path
    v3.write_json(out_path, report)
    latest = run_dir / "qa" / "imagegen-source-style-audit-latest.json"
    v3.write_json(latest, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = audit_sources_v3(args.run_dir, json_out=args.json_out)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
