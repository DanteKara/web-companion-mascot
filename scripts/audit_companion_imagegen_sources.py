#!/usr/bin/env python3
"""Audit completed companion imagegen sources without recording or mutating jobs."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


RECORD_SCRIPT = Path(__file__).with_name("record_companion_imagegen_result.py")
_record_spec = importlib.util.spec_from_file_location("record_companion_imagegen_result", RECORD_SCRIPT)
record = importlib.util.module_from_spec(_record_spec)
assert _record_spec.loader is not None
_record_spec.loader.exec_module(record)


def load_jobs(run_dir: Path) -> list[dict[str, Any]]:
    jobs_path = run_dir / "imagegen-jobs.json"
    try:
        data = json.loads(jobs_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise SystemExit(f"could not read {jobs_path}: {exc}") from exc
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in jobs if isinstance(job, dict)]


def resolve_source_path(run_dir: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return path.resolve()


def audit_sources(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    jobs = load_jobs(run_dir)
    chroma_key = record.read_chroma_key_rgb(run_dir)

    base_reports: list[dict[str, Any]] = []
    row_reports: list[dict[str, Any]] = []
    for job in jobs:
        if job.get("kind") == "base-companion" and job.get("status") == "complete":
            job_id = str(job.get("id", "<unknown>"))
            source = resolve_source_path(run_dir, job.get("source_path") or job.get("source"))
            if source is None:
                base_reports.append(
                    {
                        "id": job_id,
                        "ok": False,
                        "sourcePath": None,
                        "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                        "strictBlockingWarningCodes": ["missing_source_path"],
                        "warnings": [
                            {
                                "code": "missing_source_path",
                                "message": "Completed base job has no source_path to audit.",
                            }
                        ],
                    }
                )
                continue
            if not source.exists():
                base_reports.append(
                    {
                        "id": job_id,
                        "ok": False,
                        "sourcePath": str(source),
                        "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                        "strictBlockingWarningCodes": ["source_path_missing_on_disk"],
                        "warnings": [
                            {
                                "code": "source_path_missing_on_disk",
                                "message": "Completed base job source_path does not exist on disk.",
                            }
                        ],
                    }
                )
                continue

            analysis = record.analyze_base_style(source, chroma_key)
            source_provenance = str(job.get("source_provenance") or job.get("sourceProvenance") or "")
            blockers = record.blocking_base_style_warnings(
                analysis,
                source_provenance=source_provenance,
            )
            base_reports.append(
                {
                    "id": job_id,
                    "ok": not blockers,
                    "sourcePath": str(source),
                    "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                    "strictBlockingWarningCodes": [str(warning.get("code")) for warning in blockers],
                    "warnings": analysis.get("warnings", []),
                    "analysis": analysis,
                }
            )
            continue
        if job.get("kind") != "row-strip" or job.get("status") != "complete":
            continue
        job_id = str(job.get("id", "<unknown>"))
        source = resolve_source_path(run_dir, job.get("source_path") or job.get("source"))
        if source is None:
            row_reports.append(
                {
                    "id": job_id,
                    "ok": False,
                    "sourcePath": None,
                    "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                    "strictBlockingWarningCodes": ["missing_source_path"],
                    "warnings": [
                        {
                            "code": "missing_source_path",
                            "message": "Completed row job has no source_path to audit.",
                        }
                    ],
                }
            )
            continue
        if not source.exists():
            row_reports.append(
                {
                    "id": job_id,
                    "ok": False,
                    "sourcePath": str(source),
                    "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                    "strictBlockingWarningCodes": ["source_path_missing_on_disk"],
                    "warnings": [
                        {
                            "code": "source_path_missing_on_disk",
                            "message": "Completed row job source_path does not exist on disk.",
                        }
                    ],
                }
            )
            continue

        analysis = record.analyze_base_style(source, chroma_key)
        blockers = record.blocking_row_source_style_warnings(analysis)
        row_reports.append(
            {
                "id": job_id,
                "ok": not blockers,
                "sourcePath": str(source),
                "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
                "strictBlockingWarningCodes": [str(warning.get("code")) for warning in blockers],
                "warnings": analysis.get("warnings", []),
                "analysis": analysis,
            }
        )

    blocking_bases = [base for base in base_reports if base["strictBlockingWarningCodes"]]
    blocking_rows = [row for row in row_reports if row["strictBlockingWarningCodes"]]
    return {
        "ok": not blocking_bases and not blocking_rows,
        "runDir": str(run_dir),
        "chromaKeyRgb": list(chroma_key),
        "summary": {
            "completedBaseJobs": len(base_reports),
            "blockingBaseJobs": len(blocking_bases),
            "completedRowJobs": len(row_reports),
            "blockingRowJobs": len(blocking_rows),
        },
        "baseJobs": base_reports,
        "rowJobs": row_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    report = audit_sources(args.run_dir)
    if args.json_out:
        out_path = args.json_out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
