#!/usr/bin/env python3
"""Create a production-readiness summary from companion QA evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REQUIRED_VISUAL_REVIEWS = (
    "art-direction-review.json",
    "anatomy-review.json",
    "state-performance-review.json",
    "eye-grammar-review.json",
)

REQUIRED_REVIEW_CHECKS_BY_FILE = {
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


VISUAL_REVIEW_BLOCKER_PREFIXES = (
    "art direction blocker:",
    "anatomy review blocker:",
    "state performance review blocker:",
    "eye grammar review blocker:",
)


def is_duplicate_visual_review_warning(message: str) -> bool:
    return any(f"qa/{filename} is missing or unreadable" in message for filename in REQUIRED_VISUAL_REVIEWS)


def is_duplicate_visual_review_error(message: str) -> bool:
    if any(message.startswith(prefix) for prefix in VISUAL_REVIEW_BLOCKER_PREFIXES):
        return True
    for filename in REQUIRED_VISUAL_REVIEWS:
        review_prefix = f"qa/{filename} "
        if message.startswith(review_prefix) and (
            " status must be " in message
            or " productionUse must be " in message
            or " checks." in message
        ):
            return True
    return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise SystemExit(f"could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return load_json(path)


def add_blocker(
    blockers: list[dict[str, Any]],
    *,
    kind: str,
    message: str,
    target: str | None = None,
    code: str | None = None,
    source: str | None = None,
) -> None:
    blocker: dict[str, Any] = {"kind": kind, "message": message}
    if target:
        blocker["target"] = target
    if code:
        blocker["code"] = code
    if source:
        blocker["source"] = source
    blockers.append(blocker)


def is_older_than(path: Path, dependency: Path) -> bool:
    if not path.exists() or not dependency.exists():
        return False
    return path.stat().st_mtime < dependency.stat().st_mtime


def stale_dependency_labels(path: Path, dependencies: list[tuple[Path, str]]) -> list[str]:
    return [label for dependency, label in dependencies if is_older_than(path, dependency)]


def dependency_label(run_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(run_dir.resolve()))
    except ValueError:
        return str(path)


def report_freshness(
    blockers: list[dict[str, Any]],
    *,
    manifest_path: Path,
    imagegen_jobs_path: Path,
    source_audit_path: Path,
    validation_report_path: Path,
) -> None:
    if is_older_than(source_audit_path, imagegen_jobs_path):
        add_blocker(
            blockers,
            kind="stale-source-audit",
            target=str(source_audit_path),
            message="source audit must be newer than imagegen-jobs.json; rerun audit_companion_imagegen_sources.py after job/source changes.",
        )
    for dependency, label in ((manifest_path, "manifest.json"), (imagegen_jobs_path, "imagegen-jobs.json")):
        if is_older_than(validation_report_path, dependency):
            add_blocker(
                blockers,
                kind="stale-validation",
                target=str(validation_report_path),
                message=f"validation report must be newer than {label}; rerun validate_companion_manifest.py after manifest or job changes.",
            )


def report_source_audit(blockers: list[dict[str, Any]], source_audit: dict[str, Any] | None) -> None:
    if source_audit is None:
        add_blocker(
            blockers,
            kind="missing-source-audit",
            message="qa imagegen source-style audit is missing; run audit_companion_imagegen_sources.py first.",
        )
        return
    for group_name, kind in (("baseJobs", "base-source-style"), ("rowJobs", "row-source-style")):
        jobs = source_audit.get(group_name, [])
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            if not isinstance(job, dict):
                continue
            job_id = str(job.get("id", "<unknown>"))
            codes = job.get("strictBlockingWarningCodes", [])
            if not isinstance(codes, list):
                continue
            for code in codes:
                if not code:
                    continue
                add_blocker(
                    blockers,
                    kind=kind,
                    target=job_id,
                    code=str(code),
                    source=str(job.get("sourcePath") or ""),
                    message=f"{job_id} source audit blocks production with {code}.",
                )


def report_validation(blockers: list[dict[str, Any]], validation: dict[str, Any] | None) -> None:
    if validation is None:
        add_blocker(
            blockers,
            kind="missing-validation",
            message="strict validation report is missing; run validate_companion_manifest.py with production/audition gates.",
        )
        return
    for error in validation.get("errors", []):
        if isinstance(error, str) and error and not is_duplicate_visual_review_error(error):
            add_blocker(blockers, kind="validation-error", message=error)
    for warning in validation.get("warnings", []):
        if isinstance(warning, str) and warning and not is_duplicate_visual_review_warning(warning):
            add_blocker(blockers, kind="validation-warning", message=warning)
    qa = validation.get("qa")
    if isinstance(qa, dict):
        quality = qa.get("qualityReport")
        if isinstance(quality, dict) and quality.get("ok") is False:
            add_blocker(
                blockers,
                kind="quality-report",
                message="qa/quality-report.json is not OK; resolve scale, motion, anchor, or cutout warnings first.",
            )


def report_visual_reviews(
    blockers: list[dict[str, Any]],
    *,
    run_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> None:
    qa_dir = run_dir / "qa"
    visual_review_dependencies = [(manifest_path, "manifest.json")]
    atlas = manifest.get("atlas")
    if isinstance(atlas, dict) and atlas.get("path"):
        visual_review_dependencies.append((run_dir / str(atlas["path"]), str(atlas["path"])))
    for qa_filename in (
        "contact-sheet.png",
        "cutout-check.png",
        "state-readability-check.png",
        "semantic-anchor-check.png",
        "motion-quality-check.png",
    ):
        qa_path = qa_dir / qa_filename
        if qa_path.exists():
            visual_review_dependencies.append((qa_path, f"qa/{qa_filename}"))
    previews_dir = qa_dir / "previews"
    if previews_dir.exists():
        for preview_path in sorted(path for path in previews_dir.iterdir() if path.is_file()):
            visual_review_dependencies.append((preview_path, f"qa/previews/{preview_path.name}"))
    for filename in REQUIRED_VISUAL_REVIEWS:
        path = qa_dir / filename
        review = optional_json(path)
        if review is None:
            add_blocker(
                blockers,
                kind="missing-visual-review",
                target=f"qa/{filename}",
                message=f"qa/{filename} is missing; good state read is not enough without visual identity/cleanup/anatomy review.",
            )
            continue
        stale_labels = stale_dependency_labels(path, visual_review_dependencies)
        if stale_labels:
            requirements = "; ".join(f"newer than {label}" for label in stale_labels)
            add_blocker(
                blockers,
                kind="stale-visual-review",
                target=f"qa/{filename}",
                message=f"qa/{filename} must be {requirements}; regenerate manual visual reviews after manifest, atlas, or visual QA changes.",
            )
        if review.get("status") != "pass":
            add_blocker(
                blockers,
                kind="visual-review",
                target=f"qa/{filename}",
                message=f"qa/{filename} status must be pass for production readiness.",
            )
        if review.get("productionUse") is not True:
            add_blocker(
                blockers,
                kind="visual-review",
                target=f"qa/{filename}",
                message=f"qa/{filename} productionUse must be true for production readiness.",
            )
        checks = review.get("checks", {})
        required_checks = REQUIRED_REVIEW_CHECKS_BY_FILE.get(filename, ())
        if not isinstance(checks, dict):
            add_blocker(
                blockers,
                kind="visual-review",
                target=f"qa/{filename}",
                message=f"qa/{filename} checks must be an object for production readiness.",
            )
        else:
            reported_checks: set[str] = set()
            for check_name in required_checks:
                reported_checks.add(check_name)
                if check_name not in checks:
                    add_blocker(
                        blockers,
                        kind="visual-review",
                        target=f"qa/{filename}",
                        message=f"qa/{filename} check {check_name} is required for production readiness.",
                    )
                elif checks.get(check_name) is not True:
                    add_blocker(
                        blockers,
                        kind="visual-review",
                        target=f"qa/{filename}",
                        message=f"qa/{filename} check {check_name} must be true for production readiness.",
                    )
            for check_name, value in sorted(checks.items()):
                if check_name in reported_checks:
                    continue
                if value is not True:
                    add_blocker(
                        blockers,
                        kind="visual-review",
                        target=f"qa/{filename}",
                        message=f"qa/{filename} check {check_name} must be true for production readiness.",
                    )
        review_blockers = review.get("blockers", [])
        if isinstance(review_blockers, list):
            for blocker in review_blockers:
                if blocker:
                    add_blocker(
                        blockers,
                        kind="visual-review",
                        target=f"qa/{filename}",
                        message=f"qa/{filename} blocker: {blocker}",
                    )


def report_handoffs(blockers: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    handoff_summaries: list[dict[str, Any]] = []
    manifest_path = run_dir / "manifest.json"
    imagegen_jobs_path = run_dir / "imagegen-jobs.json"
    for path in sorted((run_dir / "qa").glob("*cli-fallback-handoff*.json")):
        handoff = optional_json(path)
        if not handoff:
            continue
        required_environment = [
            str(name)
            for name in (handoff.get("requiredEnvironment") or [])
            if isinstance(name, str) and name.strip()
        ]
        required_environment_status = {
            name: "present" if os.environ.get(name) else "missing"
            for name in required_environment
        }
        execution_blocked_by: list[str] = []
        explicit_user_approval_received = bool(handoff.get("explicitUserApprovalReceived"))
        if handoff.get("requiresExplicitUserApproval") and not explicit_user_approval_received:
            execution_blocked_by.append("explicit-user-approval-required")
        for name, status in required_environment_status.items():
            if status == "missing":
                execution_blocked_by.append(f"missing-env:{name}")
        prompt_repair_contract = handoff.get("promptRepairContract")
        prompt_repair_contract_ok = False
        prompt_repair_contract_missing: list[str] = ["promptRepairContract"]
        if isinstance(prompt_repair_contract, dict):
            prompt_repair_contract_ok = prompt_repair_contract.get("ok") is True
            raw_missing = prompt_repair_contract.get("missingRequiredChecks")
            if isinstance(raw_missing, list):
                prompt_repair_contract_missing = [
                    str(item) for item in raw_missing if isinstance(item, str) and item.strip()
                ]
            else:
                prompt_repair_contract_missing = []
        if not prompt_repair_contract_ok:
            execution_blocked_by.append("fallback-prompt-contract-missing")
        freshness_dependencies: list[tuple[Path, str]] = []
        for dependency in (manifest_path, imagegen_jobs_path):
            if dependency.exists():
                freshness_dependencies.append((dependency, dependency.name))
        for raw_dependency in (handoff.get("source"), handoff.get("sourcePath"), handoff.get("promptFile")):
            normalized = normalize_path_value(run_dir, raw_dependency)
            if not normalized:
                continue
            dependency_path = Path(normalized)
            if dependency_path.exists():
                freshness_dependencies.append((dependency_path, dependency_label(run_dir, dependency_path)))
        stale_labels = stale_dependency_labels(path, freshness_dependencies)
        if stale_labels:
            execution_blocked_by.append("stale-handoff")
        source_mode = str(handoff.get("sourceMode") or "recorded-row")
        summary = {
            "path": str(path),
            "jobId": handoff.get("jobId"),
            "jobStatus": handoff.get("jobStatus") or "",
            "sourceMode": source_mode,
            "recordedJobSource": handoff.get("recordedJobSource"),
            "sourceMatchesRecordedJob": handoff.get("sourceMatchesRecordedJob"),
            "output": handoff.get("output"),
            "requiredEnvironment": required_environment,
            "requiredEnvironmentStatus": required_environment_status,
            "requiresExplicitUserApproval": bool(handoff.get("requiresExplicitUserApproval")),
            "explicitUserApprovalReceived": explicit_user_approval_received,
            "approvalNote": handoff.get("approvalNote") or "",
            "promptRepairContractOk": prompt_repair_contract_ok,
            "promptRepairContractMissing": prompt_repair_contract_missing,
            "defaultPromptWritten": bool(handoff.get("defaultPromptWritten")),
            "repairPromptSource": handoff.get("repairPromptSource") or "",
            "stale": bool(stale_labels),
            "staleDependencies": stale_labels,
            "executionBlockedBy": execution_blocked_by,
        }
        repair_intent = handoff.get("repairIntent")
        if isinstance(repair_intent, dict):
            summary["repairIntentMode"] = repair_intent.get("mode")
            summary["repairIntentPreserve"] = repair_intent.get("preserve") or []
            summary["repairIntentRepair"] = repair_intent.get("repair") or []
        handoff_summaries.append(summary)
        if not prompt_repair_contract_ok:
            missing_text = ", ".join(prompt_repair_contract_missing) if prompt_repair_contract_missing else "unknown"
            add_blocker(
                blockers,
                kind="fallback-handoff-prompt",
                target=str(handoff.get("jobId") or path.name),
                message=(
                    f"{path.name} promptRepairContract is incomplete; regenerate the handoff from a "
                    f"story-preserving fallback prompt before any real CLI/API generation: {missing_text}."
                ),
            )
        if stale_labels:
            requirements = "; ".join(f"newer than {label}" for label in stale_labels)
            add_blocker(
                blockers,
                kind="stale-fallback-handoff",
                target=str(handoff.get("jobId") or path.name),
                message=(
                    f"{path.name} must be {requirements}; regenerate the fallback handoff from the "
                    "current job source and fallback prompt before any real CLI/API generation."
                ),
            )
        if source_mode == "rejected-candidate":
            continue
        if handoff.get("sourceMatchesRecordedJob") is False:
            add_blocker(
                blockers,
                kind="fallback-handoff",
                target=str(handoff.get("jobId") or path.name),
                message=f"{path.name} uses a source that does not match the current recorded row source_path.",
            )
            continue
        if handoff.get("sourceMatchesRecordedJob") is not True:
            add_blocker(
                blockers,
                kind="fallback-handoff",
                target=str(handoff.get("jobId") or path.name),
                message=f"{path.name} does not prove sourceMatchesRecordedJob: true; regenerate it from the current imagegen-jobs.json source_path.",
            )
    return handoff_summaries


def normalize_path_value(run_dir: Path, raw_path: Any) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return str(path.resolve())


def completed_row_sources(run_dir: Path) -> dict[str, str]:
    jobs_path = run_dir / "imagegen-jobs.json"
    if not jobs_path.exists():
        return {}
    jobs_data = optional_json(jobs_path)
    if not jobs_data:
        return {}
    jobs = jobs_data.get("jobs")
    if not isinstance(jobs, list):
        return {}
    sources: dict[str, str] = {}
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if job.get("kind") != "row-strip" or job.get("status") != "complete":
            continue
        job_id = job.get("id")
        if not isinstance(job_id, str) or not job_id:
            continue
        source = normalize_path_value(run_dir, job.get("source_path") or job.get("source"))
        if source:
            sources[job_id] = source
    return sources


def report_candidate_rejections(run_dir: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    row_sources = completed_row_sources(run_dir)
    for path in sorted((run_dir / "qa").glob("*candidate-rejection-report*.json")):
        report = optional_json(path)
        if not report:
            continue
        job_id = report.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            job_id = path.stem
        summary_data = report.get("summary")
        if not isinstance(summary_data, dict):
            summary_data = {}
        current = report.get("currentKeptRow")
        if not isinstance(current, dict):
            current = {}
        current_source = normalize_path_value(run_dir, current.get("sourcePath") or current.get("source_path"))
        recorded_source = row_sources.get(job_id)
        source_matches = bool(current_source and recorded_source and current_source == recorded_source)
        candidates = report.get("candidates")
        strict_codes: set[str] = set()
        visual_blockers: list[str] = []
        if isinstance(candidates, list):
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                codes = candidate.get("strictBlockingWarningCodes", [])
                if isinstance(codes, list):
                    strict_codes.update(str(code) for code in codes if code)
                blockers = candidate.get("visualBlockers", [])
                if isinstance(blockers, list):
                    visual_blockers.extend(str(blocker) for blocker in blockers if blocker)
        summaries.append(
            {
                "path": str(path),
                "jobId": job_id,
                "candidateCount": int(summary_data.get("candidateCount") or 0),
                "rejectedCount": int(summary_data.get("rejectedCount") or 0),
                "recordedCount": int(summary_data.get("recordedCount") or 0),
                "builtInPromptRepairExhaustedForNow": bool(
                    summary_data.get("builtInPromptRepairExhaustedForNow")
                ),
                "currentKeptRowSource": current_source,
                "recordedJobSource": recorded_source,
                "sourceMatchesRecordedJob": source_matches,
                "stale": bool(current_source and recorded_source and current_source != recorded_source),
                "strictBlockingWarningCodes": sorted(strict_codes),
                "visualBlockers": visual_blockers[:12],
                "nextRecommendedAction": (
                    report.get("conclusion", {}).get("nextRecommendedAction")
                    if isinstance(report.get("conclusion"), dict)
                    else None
                ),
            }
        )
    return summaries


def infer_next_actions(
    blockers: list[dict[str, Any]],
    candidate_rejections: list[dict[str, Any]] | None = None,
    handoffs: list[dict[str, Any]] | None = None,
) -> list[str]:
    actions: list[str] = []
    if any(blocker.get("code") in {"non_uniform_chroma_key_background", "fake_checkerboard_transparency_background"} for blocker in blockers):
        actions.append(
            "Use the approved $imagegen true-transparency fallback for promising rows with non-flat or fake backgrounds; do not locally normalize the source."
        )
    if any(blocker.get("kind") == "validation-error" and "row_source_style" in blocker.get("message", "") for blocker in blockers):
        actions.append("Re-record repaired row sources with --strict-row-style so row-source evidence is stored in imagegen-jobs.json.")
    if any(blocker.get("kind") == "missing-visual-review" for blocker in blockers):
        actions.append("After repaired sources are selected and assembled, create frame-covered anatomy, state-performance, eye-grammar, and art-direction reviews.")
    if any(blocker.get("kind") == "fallback-handoff" for blocker in blockers):
        actions.append("Regenerate fallback handoffs from the current imagegen-jobs.json source_path before using any real run command.")
    if any(blocker.get("kind") == "fallback-handoff-prompt" for blocker in blockers):
        actions.append("Regenerate any fallback prompt repair contract before running real CLI/API generation; preserve story/scale while repairing eye grammar and transparency.")
    if any(blocker.get("kind") == "stale-fallback-handoff" for blocker in blockers):
        actions.append(
            "Regenerate stale fallback handoffs from the current manifest, imagegen-jobs.json, row source, and fallback prompt before any true-transparency repair."
        )
    if any(blocker.get("kind") == "stale-visual-review" for blocker in blockers):
        actions.append("Regenerate stale manual visual reviews after the latest atlas, contact sheet, and manifest changes.")
    if any(str(blocker.get("kind", "")).startswith("stale-") for blocker in blockers):
        actions.append("Regenerate stale QA evidence after the latest manifest and imagegen-jobs.json changes, then rerun this readiness report.")
    handoffs = handoffs or []
    blocked_handoffs = [handoff for handoff in handoffs if handoff.get("executionBlockedBy")]
    if blocked_handoffs:
        blocked_jobs = ", ".join(str(handoff.get("jobId")) for handoff in blocked_handoffs if handoff.get("jobId"))
        missing_env_names = sorted(
            {
                blocker.split("missing-env:", 1)[1]
                for handoff in blocked_handoffs
                for blocker in handoff.get("executionBlockedBy", [])
                if isinstance(blocker, str) and blocker.startswith("missing-env:")
            }
        )
        approval_needed = any(
            "explicit-user-approval-required" in handoff.get("executionBlockedBy", [])
            for handoff in blocked_handoffs
        )
        pieces: list[str] = []
        if approval_needed:
            pieces.append("explicit user approval")
        if missing_env_names:
            pieces.append("environment " + ", ".join(missing_env_names))
        if pieces:
            actions.append(
                f"Fallback handoffs for {blocked_jobs} are not runnable yet; resolve "
                + " and ".join(pieces)
                + " before any real CLI/API generation."
            )
    candidate_rejections = candidate_rejections or []
    exhausted_current = [
        item
        for item in candidate_rejections
        if item.get("builtInPromptRepairExhaustedForNow") and item.get("sourceMatchesRecordedJob")
    ]
    if exhausted_current:
        jobs = ", ".join(str(item.get("jobId")) for item in exhausted_current if item.get("jobId"))
        actions.append(
            f"Rejected candidate evidence for {jobs} says repeated built-in repairs are exhausted for the current recorded row; preserve story/scale and move only through a narrow approved repair or true-transparency fallback."
        )
    if not actions and blockers:
        actions.append("Resolve listed blockers, then rerun strict validation and this readiness report.")
    if not actions:
        actions.append("Ready for final human visual approval before any GitHub push.")
    return actions


def default_source_audit(run_dir: Path) -> Path:
    return run_dir / "qa" / "imagegen-source-style-audit-latest.json"


def default_validation_report(run_dir: Path) -> Path:
    preferred = run_dir / "qa" / "validation-with-eye-base-gates.json"
    if preferred.exists():
        return preferred
    return run_dir / "qa" / "validation.json"


def build_report(
    *,
    manifest_path: Path,
    source_audit_path: Path | None = None,
    validation_report_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    run_dir = manifest_path.parent
    manifest = load_json(manifest_path)
    source_audit_path = source_audit_path.expanduser().resolve() if source_audit_path else default_source_audit(run_dir)
    validation_report_path = (
        validation_report_path.expanduser().resolve() if validation_report_path else default_validation_report(run_dir)
    )
    source_audit = optional_json(source_audit_path)
    validation = optional_json(validation_report_path)

    blockers: list[dict[str, Any]] = []
    report_freshness(
        blockers,
        manifest_path=manifest_path,
        imagegen_jobs_path=run_dir / "imagegen-jobs.json",
        source_audit_path=source_audit_path,
        validation_report_path=validation_report_path,
    )
    report_source_audit(blockers, source_audit)
    report_validation(blockers, validation)
    report_visual_reviews(blockers, run_dir=run_dir, manifest_path=manifest_path, manifest=manifest)
    handoffs = report_handoffs(blockers, run_dir)
    candidate_rejections = report_candidate_rejections(run_dir)

    blocked_handoff_count = sum(1 for handoff in handoffs if handoff.get("executionBlockedBy"))
    runnable_handoff_count = sum(1 for handoff in handoffs if not handoff.get("executionBlockedBy"))
    fallback_repair_ready = bool(handoffs) and blocked_handoff_count == 0
    production_ready = not blockers
    state_names = sorted((manifest.get("states") or {}).keys()) if isinstance(manifest.get("states"), dict) else []
    verdict = (
        "production-ready after deterministic gates and visual-review evidence; await final human visual approval before any GitHub push."
        if production_ready
        else "not production-ready: good state read is not enough if identity, cleanup, source evidence, or anatomy/eye review is missing."
    )
    return {
        "ok": production_ready,
        "productionReady": production_ready,
        "manifest": str(manifest_path),
        "sourceAudit": str(source_audit_path),
        "validationReport": str(validation_report_path),
        "states": state_names,
        "fallbackRepairReady": fallback_repair_ready,
        "summary": {
            "stateCount": len(state_names),
            "blockerCount": len(blockers),
            "handoffCount": len(handoffs),
            "blockedHandoffCount": blocked_handoff_count,
            "runnableHandoffCount": runnable_handoff_count,
            "candidateRejectionReportCount": len(candidate_rejections),
            "exhaustedCandidateRepairCount": sum(
                1
                for item in candidate_rejections
                if item.get("builtInPromptRepairExhaustedForNow") and item.get("sourceMatchesRecordedJob")
            ),
        },
        "verdict": verdict,
        "blockers": blockers,
        "handoffs": handoffs,
        "candidateRejections": candidate_rejections,
        "nextActions": infer_next_actions(blockers, candidate_rejections, handoffs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-audit", type=Path)
    parser.add_argument("--validation-report", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = build_report(
        manifest_path=args.manifest,
        source_audit_path=args.source_audit,
        validation_report_path=args.validation_report,
    )
    if args.json_out:
        out_path = args.json_out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["productionReady"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
