import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "scripts" / "create_companion_production_readiness_report.py"

spec = importlib.util.spec_from_file_location("create_companion_production_readiness_report", REPORT_PATH)
readiness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(readiness)


def write_manifest(run_dir: Path) -> Path:
    manifest = {
        "id": "fixture",
        "displayName": "Fixture",
        "style": {"stateClarity": "semantic-enhancers", "renderingStyle": "codex-pixel-art"},
        "atlas": {
            "path": "atlas.png",
            "width": 512,
            "height": 288,
            "columns": 2,
            "rows": 1,
            "cellWidth": 256,
            "cellHeight": 288,
        },
        "states": {
            "thinking": {"row": 0, "frames": 2, "durations": [120, 120], "loop": True},
        },
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def write_pass_review(run_dir: Path, filename: str) -> None:
    (run_dir / "qa").mkdir(exist_ok=True)
    checks = {check_name: True for check_name in readiness.REQUIRED_REVIEW_CHECKS_BY_FILE.get(filename, ())}
    (run_dir / "qa" / filename).write_text(
        json.dumps({"status": "pass", "productionUse": True, "blockers": [], "checks": checks}),
        encoding="utf-8",
    )


def set_mtime(path: Path, timestamp: float) -> None:
    os.utime(path, (timestamp, timestamp))


class CompanionProductionReadinessReportTests(unittest.TestCase):
    def test_report_blocks_good_story_rows_with_bad_source_cleanup_and_missing_visual_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": "source-thinking.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source_audit_path = run_dir / "qa" / "imagegen-source-style-audit-latest.json"
            source_audit_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "summary": {"completedRowJobs": 1, "blockingRowJobs": 1},
                        "rowJobs": [
                            {
                                "id": "thinking",
                                "strictBlockingWarningCodes": ["non_uniform_chroma_key_background"],
                                "sourcePath": "source-thinking.png",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "errors": [
                            "imagegen job thinking is missing row_source_style_analysis, row_source_style_strict_blocking_warning_codes"
                        ],
                        "warnings": ["qa/eye-grammar-review.json is missing or unreadable"],
                        "qa": {"qualityReport": {"ok": True}},
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            self.assertFalse(report["productionReady"])
            self.assertEqual(report["summary"]["blockerCount"], 6)
            blocker_text = "\n".join(blocker["message"] for blocker in report["blockers"])
            self.assertIn("non_uniform_chroma_key_background", blocker_text)
            self.assertIn("missing row_source_style_analysis", blocker_text)
            self.assertIn("qa/eye-grammar-review.json", blocker_text)
            self.assertIn("qa/art-direction-review.json", blocker_text)
            self.assertIn("good state read is not enough", report["verdict"])
            self.assertTrue(any("Codex app $imagegen" in action for action in report["nextActions"]))

    def test_report_can_pass_when_source_validation_quality_and_reviews_are_clean(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            self.assertTrue(report["productionReady"])
            self.assertEqual(report["blockers"], [])
            self.assertIn("production-ready", report["verdict"])

    def test_report_blocks_legacy_handoff_without_source_match_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-repair-handoff.json").write_text(
                json.dumps({"jobId": "thinking", "output": "old-output.png"}),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertFalse(report["productionReady"])
            self.assertTrue(any(blocker["kind"] == "fallback-handoff" for blocker in report["blockers"]))
            self.assertTrue(any("does not prove sourceMatchesRecordedJob" in blocker["message"] for blocker in report["blockers"]))

    def test_report_summarizes_story_preserving_repair_intent_for_repair_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-repair-handoff.json").write_text(
                json.dumps(
                    {
                        "jobId": "thinking",
                        "sourceMatchesRecordedJob": True,
                        "output": "thinking-transparent.png",
                        "repairIntent": {
                            "mode": "story-preserving-source-repair",
                            "preserve": ["current row state story", "apparent mascot body scale and padding"],
                            "repair": ["transparent or cleanup-ready background", "source eye grammar"],
                        },
                        "promptRepairContract": {
                            "ok": True,
                            "missingRequiredChecks": [],
                            "checks": {"preserve-story": True, "repair-eye-grammar": True},
                        },
                        "defaultPromptWritten": True,
                        "repairPromptSource": "generic-story-preserving-default",
                        "requiredEnvironment": ["MASCOT_REPAIR_TOOL_READY"],
                        "requiresExplicitUserApproval": True,
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                report = readiness.build_report(
                    manifest_path=manifest_path,
                    source_audit_path=run_dir / "qa" / "source-audit.json",
                    validation_report_path=run_dir / "qa" / "validation.json",
                )

            self.assertTrue(report["productionReady"])
            self.assertEqual(report["handoffs"][0]["repairIntentMode"], "story-preserving-source-repair")
            self.assertIn("current row state story", report["handoffs"][0]["repairIntentPreserve"])
            self.assertIn("source eye grammar", report["handoffs"][0]["repairIntentRepair"])
            self.assertTrue(report["handoffs"][0]["promptRepairContractOk"])
            self.assertTrue(report["handoffs"][0]["defaultPromptWritten"])
            self.assertEqual(report["handoffs"][0]["repairPromptSource"], "generic-story-preserving-default")
            self.assertEqual(report["handoffs"][0]["requiredEnvironment"], ["MASCOT_REPAIR_TOOL_READY"])
            self.assertEqual(report["handoffs"][0]["requiredEnvironmentStatus"], {"MASCOT_REPAIR_TOOL_READY": "missing"})
            self.assertTrue(report["handoffs"][0]["requiresExplicitUserApproval"])
            self.assertEqual(
                report["handoffs"][0]["executionBlockedBy"],
                ["explicit-user-approval-required", "missing-env:MASCOT_REPAIR_TOOL_READY"],
            )
            self.assertFalse(report["fallbackRepairReady"])
            self.assertEqual(report["summary"]["blockedHandoffCount"], 1)
            self.assertEqual(report["summary"]["runnableHandoffCount"], 0)
            self.assertTrue(
                any(
                    "MASCOT_REPAIR_TOOL_READY" in action and "explicit user approval" in action
                    for action in report["nextActions"]
                )
            )

    def test_report_treats_approved_handoff_with_present_environment_as_runnable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-repair-handoff.json").write_text(
                json.dumps(
                    {
                        "jobId": "thinking",
                        "sourceMatchesRecordedJob": True,
                        "output": "thinking-transparent.png",
                        "repairIntent": {"mode": "story-preserving-source-repair"},
                        "promptRepairContract": {
                            "ok": True,
                            "missingRequiredChecks": [],
                            "checks": {"preserve-story": True, "repair-eye-grammar": True},
                        },
                        "requiredEnvironment": ["MASCOT_REPAIR_TOOL_READY"],
                        "requiresExplicitUserApproval": True,
                        "explicitUserApprovalReceived": True,
                        "approvalNote": "User approved the narrow repair generation.",
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"MASCOT_REPAIR_TOOL_READY": "1"}, clear=True):
                report = readiness.build_report(
                    manifest_path=manifest_path,
                    source_audit_path=run_dir / "qa" / "source-audit.json",
                    validation_report_path=run_dir / "qa" / "validation.json",
                )

            self.assertTrue(report["productionReady"])
            self.assertTrue(report["handoffs"][0]["explicitUserApprovalReceived"])
            self.assertTrue(report["handoffs"][0]["promptRepairContractOk"])
            self.assertEqual(report["handoffs"][0]["requiredEnvironmentStatus"], {"MASCOT_REPAIR_TOOL_READY": "present"})
            self.assertEqual(report["handoffs"][0]["executionBlockedBy"], [])
            self.assertTrue(report["fallbackRepairReady"])
            self.assertEqual(report["summary"]["blockedHandoffCount"], 0)
            self.assertEqual(report["summary"]["runnableHandoffCount"], 1)
            self.assertFalse(any("not runnable yet" in action for action in report["nextActions"]))

    def test_report_allows_rejected_candidate_handoff_as_repair_plan(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            rejected_source = run_dir / "candidate.png"
            rejected_source.write_bytes(b"candidate")
            prompt_path = run_dir / "prompts" / "rows" / "thinking-true-transparency-fallback.md"
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text("preserve story and repair transparency", encoding="utf-8")
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps({"jobs": [{"id": "thinking", "kind": "row-strip", "status": "pending"}]}),
                encoding="utf-8",
            )
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-repair-handoff.json").write_text(
                json.dumps(
                    {
                        "jobId": "thinking",
                        "jobStatus": "pending",
                        "sourceMode": "rejected-candidate",
                        "source": str(rejected_source),
                        "recordedJobSource": None,
                        "sourceMatchesRecordedJob": None,
                        "promptFile": str(prompt_path),
                        "output": "thinking-transparent.png",
                        "repairIntent": {"mode": "story-preserving-source-repair"},
                        "promptRepairContract": {
                            "ok": True,
                            "missingRequiredChecks": [],
                            "checks": {"preserve-story": True, "repair-eye-grammar": True},
                        },
                        "requiredEnvironment": ["MASCOT_REPAIR_TOOL_READY"],
                        "requiresExplicitUserApproval": True,
                        "explicitUserApprovalReceived": True,
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"MASCOT_REPAIR_TOOL_READY": "1"}, clear=True):
                report = readiness.build_report(
                    manifest_path=manifest_path,
                    source_audit_path=run_dir / "qa" / "source-audit.json",
                    validation_report_path=run_dir / "qa" / "validation.json",
                )

            self.assertTrue(report["productionReady"])
            self.assertEqual(report["handoffs"][0]["sourceMode"], "rejected-candidate")
            self.assertIsNone(report["handoffs"][0]["sourceMatchesRecordedJob"])
            self.assertEqual(report["handoffs"][0]["executionBlockedBy"], [])
            self.assertTrue(report["fallbackRepairReady"])
            self.assertFalse(any(blocker["kind"] == "fallback-handoff" for blocker in report["blockers"]))

    def test_report_blocks_handoff_with_missing_prompt_repair_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-repair-handoff.json").write_text(
                json.dumps(
                    {
                        "jobId": "thinking",
                        "sourceMatchesRecordedJob": True,
                        "output": "thinking-transparent.png",
                        "repairIntent": {"mode": "story-preserving-source-repair"},
                        "promptRepairContract": {
                            "ok": False,
                            "missingRequiredChecks": ["preserve-story", "repair-eye-grammar"],
                        },
                        "requiredEnvironment": ["MASCOT_REPAIR_TOOL_READY"],
                        "requiresExplicitUserApproval": True,
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertFalse(report["productionReady"])
            self.assertFalse(report["handoffs"][0]["promptRepairContractOk"])
            self.assertIn("fallback-prompt-contract-missing", report["handoffs"][0]["executionBlockedBy"])
            blocker_text = "\n".join(blocker["message"] for blocker in report["blockers"])
            self.assertIn("thinking-repair-handoff.json promptRepairContract is incomplete", blocker_text)
            self.assertIn("preserve-story", blocker_text)
            self.assertTrue(any("repair prompt contract" in action for action in report["nextActions"]))

    def test_report_blocks_stale_fallback_handoff_after_job_prompt_or_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            (run_dir / "prompts" / "rows").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            source_path = run_dir / "current-source.png"
            source_path.write_bytes(b"source")
            prompt_path = run_dir / "prompts" / "rows" / "thinking-fallback.md"
            prompt_path.write_text("preserve story and repair eye grammar", encoding="utf-8")
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": str(source_path),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            handoff_path = run_dir / "qa" / "thinking-repair-handoff.json"
            handoff_path.write_text(
                json.dumps(
                    {
                        "jobId": "thinking",
                        "source": str(source_path),
                        "sourceMatchesRecordedJob": True,
                        "promptFile": str(prompt_path),
                        "output": "thinking-transparent.png",
                        "repairIntent": {"mode": "story-preserving-source-repair"},
                        "promptRepairContract": {
                            "ok": True,
                            "missingRequiredChecks": [],
                            "checks": {"preserve-story": True, "repair-eye-grammar": True},
                        },
                    }
                ),
                encoding="utf-8",
            )
            set_mtime(handoff_path, 100)
            set_mtime(manifest_path, 200)
            set_mtime(jobs_path, 210)
            set_mtime(source_path, 220)
            set_mtime(prompt_path, 230)

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertFalse(report["productionReady"])
            stale_handoff_blockers = [
                blocker for blocker in report["blockers"] if blocker["kind"] == "stale-fallback-handoff"
            ]
            self.assertEqual(1, len(stale_handoff_blockers))
            self.assertIn("newer than manifest.json", stale_handoff_blockers[0]["message"])
            self.assertIn("newer than imagegen-jobs.json", stale_handoff_blockers[0]["message"])
            self.assertIn("newer than current-source.png", stale_handoff_blockers[0]["message"])
            self.assertIn("newer than prompts\\rows\\thinking-fallback.md", stale_handoff_blockers[0]["message"])
            self.assertTrue(any("Regenerate stale repair handoffs" in action for action in report["nextActions"]))

    def test_report_summarizes_rejected_candidate_evidence_without_blocking_by_itself(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            current_source = str((run_dir / "generated-source.png").resolve())
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": current_source,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-candidate-rejection-report.json").write_text(
                json.dumps(
                    {
                        "reportKind": "companion-candidate-rejection-report",
                        "jobId": "thinking",
                        "currentKeptRow": {
                            "sourcePath": current_source,
                            "decision": "keep-current-for-now",
                        },
                        "summary": {
                            "candidateCount": 3,
                            "rejectedCount": 3,
                            "recordedCount": 0,
                            "builtInPromptRepairExhaustedForNow": True,
                        },
                        "candidates": [
                            {
                                "decision": "reject",
                                "recorded": False,
                                "strictBlockingWarningCodes": ["non_uniform_chroma_key_background"],
                                "visualBlockers": ["white crescent eye drift"],
                            }
                        ],
                        "conclusion": {
                            "nextRecommendedAction": "Stop retrying the same built-in prompt pattern; regenerate through Codex app $imagegen."
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertTrue(report["productionReady"])
            self.assertEqual(report["summary"]["candidateRejectionReportCount"], 1)
            self.assertEqual(report["summary"]["exhaustedCandidateRepairCount"], 1)
            self.assertEqual(report["candidateRejections"][0]["jobId"], "thinking")
            self.assertTrue(report["candidateRejections"][0]["sourceMatchesRecordedJob"])
            self.assertIn("non_uniform_chroma_key_background", report["candidateRejections"][0]["strictBlockingWarningCodes"])
            self.assertTrue(any("Rejected candidate evidence" in action for action in report["nextActions"]))

    def test_report_marks_stale_rejected_candidate_evidence_when_current_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": str((run_dir / "new-source.png").resolve()),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "thinking-candidate-rejection-report.json").write_text(
                json.dumps(
                    {
                        "reportKind": "companion-candidate-rejection-report",
                        "jobId": "thinking",
                        "currentKeptRow": {
                            "sourcePath": str((run_dir / "old-source.png").resolve()),
                            "decision": "keep-current-for-now",
                        },
                        "summary": {
                            "candidateCount": 2,
                            "rejectedCount": 2,
                            "recordedCount": 0,
                            "builtInPromptRepairExhaustedForNow": True,
                        },
                        "candidates": [],
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertTrue(report["productionReady"])
            self.assertFalse(report["candidateRejections"][0]["sourceMatchesRecordedJob"])
            self.assertTrue(report["candidateRejections"][0]["stale"])

    def test_report_blocks_strict_validation_warnings_that_are_not_duplicate_review_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "source-audit.json").write_text(
                json.dumps({"ok": True, "summary": {"blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            (run_dir / "qa" / "validation.json").write_text(
                json.dumps(
                    {
                        "ok": True,
                        "errors": [],
                        "warnings": ["chatbot profile recommends 8+ frames for high-visibility states"],
                        "qa": {"qualityReport": {"ok": True}},
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=run_dir / "qa" / "source-audit.json",
                validation_report_path=run_dir / "qa" / "validation.json",
            )

            self.assertFalse(report["productionReady"])
            self.assertTrue(any(blocker["kind"] == "validation-warning" for blocker in report["blockers"]))
            self.assertTrue(any("chatbot profile recommends 8+" in blocker["message"] for blocker in report["blockers"]))

    def test_report_deduplicates_visual_review_validation_errors_but_keeps_review_check_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
            ):
                write_pass_review(run_dir, filename)
            eye_review_path = run_dir / "qa" / "eye-grammar-review.json"
            eye_review_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "productionUse": False,
                        "blockers": ["white crescent side-glance eyes in thinking frame 3"],
                        "checks": {
                            "frameByFrameEyeGrammarReviewed": True,
                            "eyeCountStable": True,
                            "eyeShapeStable": False,
                            "noWhiteScleraOrCrescentSwap": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "errors": [
                            "qa/eye-grammar-review.json status must be 'pass' for production validation",
                            "qa/eye-grammar-review.json productionUse must be true for production validation",
                            "eye grammar review blocker: white crescent side-glance eyes in thinking frame 3",
                            "qa/eye-grammar-review.json checks.eyeShapeStable must be true",
                            "qa/eye-grammar-review.json expectedEyeGrammar must be a non-empty string",
                        ],
                        "warnings": [],
                        "qa": {"qualityReport": {"ok": True}},
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            blocker_text = "\n".join(blocker["message"] for blocker in report["blockers"])
            self.assertNotIn("production validation", blocker_text)
            self.assertNotIn("eye grammar review blocker:", blocker_text)
            self.assertNotIn("checks.eyeShapeStable", blocker_text)
            self.assertIn("qa/eye-grammar-review.json status must be pass", blocker_text)
            self.assertIn("qa/eye-grammar-review.json productionUse must be true", blocker_text)
            self.assertIn("qa/eye-grammar-review.json blocker: white crescent", blocker_text)
            self.assertIn("qa/eye-grammar-review.json check eyeShapeStable must be true", blocker_text)
            self.assertIn("qa/eye-grammar-review.json expectedEyeGrammar must be a non-empty string", blocker_text)
            self.assertTrue(
                any(
                    blocker["kind"] == "validation-error"
                    and "expectedEyeGrammar must be a non-empty string" in blocker["message"]
                    for blocker in report["blockers"]
                )
            )

    def test_report_blocks_missing_required_state_performance_review_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            (run_dir / "imagegen-jobs.json").write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            (run_dir / "qa" / "state-performance-review.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "productionUse": True,
                        "blockers": [],
                        "checks": {
                            "frameByFrameStateReadReviewed": True,
                            "intendedStateReadable": True,
                            "noWrongStateRead": True,
                            "expressionMatchesState": True,
                            "cueMotionMatchesState": True,
                            "noTiredPantingUnlessStateRequiresIt": True,
                            "noOffVibeGenericCue": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "errors": [
                            "qa/state-performance-review.json checks.coherentStateStoryArc is required",
                            "qa/state-performance-review.json checks.mascotActingVariesAcrossFrames is required",
                        ],
                        "warnings": [],
                        "qa": {"qualityReport": {"ok": True}},
                    }
                ),
                encoding="utf-8",
            )

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            blocker_text = "\n".join(blocker["message"] for blocker in report["blockers"])
            self.assertFalse(report["productionReady"])
            self.assertIn("qa/state-performance-review.json check coherentStateStoryArc is required", blocker_text)
            self.assertIn(
                "qa/state-performance-review.json check mascotActingVariesAcrossFrames is required",
                blocker_text,
            )

    def test_report_blocks_stale_source_audit_and_validation_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(json.dumps({"jobs": []}), encoding="utf-8")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            set_mtime(source_audit_path, 100)
            set_mtime(validation_path, 100)
            set_mtime(jobs_path, 200)
            set_mtime(manifest_path, 300)

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            self.assertFalse(report["productionReady"])
            self.assertTrue(any(blocker["kind"] == "stale-source-audit" for blocker in report["blockers"]))
            self.assertTrue(any(blocker["kind"] == "stale-validation" for blocker in report["blockers"]))
            blocker_text = "\n".join(blocker["message"] for blocker in report["blockers"])
            self.assertIn("newer than imagegen-jobs.json", blocker_text)
            self.assertIn("newer than manifest.json", blocker_text)

    def test_report_blocks_stale_manual_visual_reviews_after_atlas_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(json.dumps({"jobs": []}), encoding="utf-8")
            atlas_path = run_dir / "atlas.png"
            atlas_path.write_bytes(b"atlas")
            contact_sheet_path = run_dir / "qa" / "contact-sheet.png"
            contact_sheet_path.write_bytes(b"contact sheet")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            set_mtime(jobs_path, 100)
            set_mtime(manifest_path, 200)
            set_mtime(atlas_path, 300)
            set_mtime(contact_sheet_path, 300)
            set_mtime(source_audit_path, 400)
            set_mtime(validation_path, 400)
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
            ):
                set_mtime(run_dir / "qa" / filename, 500)
            set_mtime(run_dir / "qa" / "eye-grammar-review.json", 150)

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            self.assertFalse(report["productionReady"])
            stale_review_blockers = [
                blocker for blocker in report["blockers"] if blocker["kind"] == "stale-visual-review"
            ]
            self.assertEqual(1, len(stale_review_blockers))
            self.assertEqual("qa/eye-grammar-review.json", stale_review_blockers[0]["target"])
            self.assertIn("newer than manifest.json", stale_review_blockers[0]["message"])
            self.assertIn("newer than atlas.png", stale_review_blockers[0]["message"])
            self.assertIn("newer than qa/contact-sheet.png", stale_review_blockers[0]["message"])
            self.assertTrue(any("Regenerate stale manual visual reviews" in action for action in report["nextActions"]))

    def test_report_blocks_stale_manual_visual_reviews_after_visual_qa_sheet_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "qa").mkdir(parents=True)
            manifest_path = write_manifest(run_dir)
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(json.dumps({"jobs": []}), encoding="utf-8")
            atlas_path = run_dir / "atlas.png"
            atlas_path.write_bytes(b"atlas")
            for qa_filename in (
                "contact-sheet.png",
                "cutout-check.png",
                "state-readability-check.png",
                "semantic-anchor-check.png",
                "motion-quality-check.png",
            ):
                (run_dir / "qa" / qa_filename).write_bytes(qa_filename.encode("utf-8"))
            previews_dir = run_dir / "qa" / "previews"
            previews_dir.mkdir()
            preview_path = previews_dir / "thinking.gif"
            preview_path.write_bytes(b"preview")
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
            ):
                write_pass_review(run_dir, filename)
            source_audit_path = run_dir / "qa" / "source-audit.json"
            source_audit_path.write_text(
                json.dumps({"ok": True, "summary": {"blockingBaseJobs": 0, "blockingRowJobs": 0}, "rowJobs": []}),
                encoding="utf-8",
            )
            validation_path = run_dir / "qa" / "validation.json"
            validation_path.write_text(
                json.dumps({"ok": True, "errors": [], "warnings": [], "qa": {"qualityReport": {"ok": True}}}),
                encoding="utf-8",
            )
            set_mtime(jobs_path, 100)
            set_mtime(manifest_path, 200)
            set_mtime(atlas_path, 300)
            set_mtime(run_dir / "qa" / "contact-sheet.png", 300)
            set_mtime(run_dir / "qa" / "cutout-check.png", 400)
            set_mtime(run_dir / "qa" / "state-readability-check.png", 410)
            set_mtime(run_dir / "qa" / "semantic-anchor-check.png", 420)
            set_mtime(run_dir / "qa" / "motion-quality-check.png", 430)
            set_mtime(preview_path, 440)
            set_mtime(source_audit_path, 500)
            set_mtime(validation_path, 500)
            for filename in (
                "art-direction-review.json",
                "anatomy-review.json",
                "state-performance-review.json",
            ):
                set_mtime(run_dir / "qa" / filename, 500)
            set_mtime(run_dir / "qa" / "eye-grammar-review.json", 350)

            report = readiness.build_report(
                manifest_path=manifest_path,
                source_audit_path=source_audit_path,
                validation_report_path=validation_path,
            )

            self.assertFalse(report["productionReady"])
            stale_review_blockers = [
                blocker for blocker in report["blockers"] if blocker["kind"] == "stale-visual-review"
            ]
            self.assertEqual(1, len(stale_review_blockers))
            self.assertEqual("qa/eye-grammar-review.json", stale_review_blockers[0]["target"])
            self.assertIn("newer than qa/cutout-check.png", stale_review_blockers[0]["message"])
            self.assertIn("newer than qa/state-readability-check.png", stale_review_blockers[0]["message"])
            self.assertIn("newer than qa/semantic-anchor-check.png", stale_review_blockers[0]["message"])
            self.assertIn("newer than qa/motion-quality-check.png", stale_review_blockers[0]["message"])
            self.assertIn("newer than qa/previews/thinking.gif", stale_review_blockers[0]["message"])


if __name__ == "__main__":
    unittest.main()
