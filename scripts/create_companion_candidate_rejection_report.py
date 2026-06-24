#!/usr/bin/env python3
"""Write a non-mutating QA report for rejected companion row candidates."""

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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise SystemExit(f"could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def load_jobs(run_dir: Path) -> list[dict[str, Any]]:
    jobs_path = run_dir / "imagegen-jobs.json"
    data = load_json(jobs_path)
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in jobs if isinstance(job, dict)]


def find_job(run_dir: Path, job_id: str) -> dict[str, Any] | None:
    for job in load_jobs(run_dir):
        if job.get("id") == job_id:
            return job
    return None


def resolve_path(run_dir: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return path.resolve()


def path_hash(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return record.file_sha256(path)


def current_kept_row(run_dir: Path, job_id: str) -> dict[str, Any]:
    job = find_job(run_dir, job_id)
    if job is None:
        return {
            "jobId": job_id,
            "status": "missing",
            "decision": "none",
            "sourcePath": None,
            "sourceSha256": None,
            "sourceProvenance": None,
            "rowSourceStrictBlockingWarningCodes": [],
        }

    source = resolve_path(run_dir, job.get("source_path") or job.get("source"))
    return {
        "jobId": job_id,
        "status": job.get("status"),
        "decision": "keep-current-for-now" if job.get("status") == "complete" and source else "none",
        "sourcePath": str(source) if source else None,
        "sourceSha256": path_hash(source),
        "sourceProvenance": job.get("source_provenance") or job.get("sourceProvenance"),
        "rowSourceStrictBlockingWarningCodes": job.get("row_source_style_strict_blocking_warning_codes", []),
    }


def normalize_visual_blockers(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [raw_value.strip()] if raw_value.strip() else []
    if not isinstance(raw_value, list):
        raise ValueError("visualBlockers must be a string or array of strings")
    blockers: list[str] = []
    for index, item in enumerate(raw_value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"visualBlockers[{index}] must be a non-empty string")
        blockers.append(item.strip())
    return blockers


def load_candidates(path: Path) -> tuple[list[dict[str, Any]], str]:
    data = load_json(path)
    raw_candidates = data.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise SystemExit("candidates JSON must contain a non-empty candidates array")
    candidates: list[dict[str, Any]] = []
    for index, entry in enumerate(raw_candidates):
        if not isinstance(entry, dict):
            raise SystemExit(f"candidate {index + 1} must be a JSON object")
        candidates.append(entry)
    notes = data.get("notes")
    return candidates, notes if isinstance(notes, str) else ""


def analyze_candidate(
    *,
    run_dir: Path,
    source: Path,
    allow_synthetic_test_source: bool,
) -> dict[str, Any]:
    source_validation = record.validate_source_path(
        source=source,
        run_dir=run_dir,
        requested_provenance="built-in-imagegen",
        allow_synthetic_test_source=allow_synthetic_test_source,
    )
    if not source.exists():
        return {
            "sourceValidation": source_validation,
            "sourceSha256": None,
            "analysis": None,
            "deterministicWarningCodes": ["source_path_missing_on_disk"],
            "strictBlockingWarningCodes": ["source_path_missing_on_disk"],
            "warnings": [
                {
                    "code": "source_path_missing_on_disk",
                    "message": "Candidate source image does not exist on disk.",
                }
            ],
        }

    analysis = record.analyze_base_style(source, record.read_chroma_key_rgb(run_dir))
    strict_blockers = record.blocking_row_source_style_warnings(analysis)
    warnings = [warning for warning in analysis.get("warnings", []) if isinstance(warning, dict)]
    return {
        "sourceValidation": source_validation,
        "sourceSha256": record.file_sha256(source),
        "analysis": analysis,
        "deterministicWarningCodes": [str(warning.get("code")) for warning in warnings if warning.get("code")],
        "strictBlockingWarningCodes": [
            str(warning.get("code")) for warning in strict_blockers if warning.get("code")
        ],
        "warnings": warnings,
    }


def build_report(
    *,
    run_dir: Path,
    job_id: str,
    candidates_path: Path,
    built_in_repair_threshold: int = 3,
    allow_synthetic_test_source: bool = False,
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    candidates_path = candidates_path.expanduser().resolve()
    raw_candidates, notes = load_candidates(candidates_path)
    current = current_kept_row(run_dir, job_id)

    candidate_reports: list[dict[str, Any]] = []
    for index, raw_candidate in enumerate(raw_candidates, start=1):
        decision = str(raw_candidate.get("decision", "reject")).strip().lower()
        if decision != "reject":
            raise ValueError("candidate rejection reports may only contain decision='reject' entries")
        source = resolve_path(run_dir, raw_candidate.get("source") or raw_candidate.get("sourcePath"))
        if source is None:
            raise ValueError(f"candidate {index} is missing source")
        visual_blockers = normalize_visual_blockers(raw_candidate.get("visualBlockers"))
        source_report = analyze_candidate(
            run_dir=run_dir,
            source=source,
            allow_synthetic_test_source=allow_synthetic_test_source,
        )
        if not visual_blockers and not source_report["strictBlockingWarningCodes"]:
            raise ValueError(
                f"candidate {index} must include at least one visualBlocker or strict source blocker"
            )
        candidate_reports.append(
            {
                "index": index,
                "sourcePath": str(source),
                "sourceSha256": source_report["sourceSha256"],
                "sourceValidation": source_report["sourceValidation"],
                "promptStrategy": raw_candidate.get("promptStrategy", ""),
                "decision": "reject",
                "recorded": False,
                "visualBlockers": visual_blockers,
                "deterministicWarningCodes": source_report["deterministicWarningCodes"],
                "strictBlockingWarningCodes": source_report["strictBlockingWarningCodes"],
                "warnings": source_report["warnings"],
                "analysis": source_report["analysis"],
            }
        )

    rejected_count = sum(1 for candidate in candidate_reports if candidate["decision"] == "reject")
    exhausted = rejected_count >= max(1, built_in_repair_threshold)
    report = {
        "ok": True,
        "reportKind": "companion-candidate-rejection-report",
        "runDir": str(run_dir),
        "jobId": job_id,
        "candidatesInput": str(candidates_path),
        "currentKeptRow": current,
        "summary": {
            "candidateCount": len(candidate_reports),
            "rejectedCount": rejected_count,
            "recordedCount": 0,
            "builtInPromptRepairThreshold": built_in_repair_threshold,
            "builtInPromptRepairExhaustedForNow": exhausted,
        },
        "candidates": candidate_reports,
        "notes": notes,
        "conclusion": {
            "doNotRecordOrAssembleRejectedCandidates": True,
            "builtInPromptRepairExhaustedForNow": exhausted,
            "nextRecommendedAction": (
                "Stop retrying the same built-in prompt pattern; preserve the current accepted story/scale "
                "and regenerate through Codex app $imagegen with revised prompt/reference grounding."
                if exhausted
                else "Continue with a narrow grounded row repair only if it targets the recorded blockers without changing the accepted story or scale."
            ),
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--candidates-json", required=True, type=Path)
    parser.add_argument(
        "--built-in-repair-threshold",
        type=int,
        default=3,
        help="Number of rejected built-in candidates after which the report recommends stopping prompt churn.",
    )
    parser.add_argument(
        "--allow-synthetic-test-source",
        action="store_true",
        help="Allow non-$CODEX_HOME/generated_images sources for tests only.",
    )
    parser.add_argument("--out", type=Path, help="Output JSON; defaults to qa/<job-id>-candidate-rejection-report.json")
    args = parser.parse_args()

    report = build_report(
        run_dir=args.run_dir,
        job_id=args.job_id,
        candidates_path=args.candidates_json,
        built_in_repair_threshold=args.built_in_repair_threshold,
        allow_synthetic_test_source=args.allow_synthetic_test_source,
    )
    run_dir = args.run_dir.expanduser().resolve()
    out_path = args.out.expanduser().resolve() if args.out else run_dir / "qa" / f"{args.job_id}-candidate-rejection-report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "candidateRejectionReport": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
