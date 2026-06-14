import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = ROOT / "scripts" / "create_imagegen_cli_fallback_handoff.py"

spec = importlib.util.spec_from_file_location("create_imagegen_cli_fallback_handoff", HANDOFF_PATH)
handoff = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(handoff)


class ImagegenCliFallbackHandoffTests(unittest.TestCase):
    def write_run(
        self,
        tmp_path: Path,
        prompt_text: str = "Fallback prompt",
        *,
        job_status: str = "complete",
        include_source_path: bool = True,
    ) -> dict[str, Path]:
        run_dir = tmp_path / "run"
        (run_dir / "references" / "layout-guides").mkdir(parents=True)
        (run_dir / "references" / "canonical-base.png").write_bytes(b"base")
        (run_dir / "references" / "reference-01.png").write_bytes(b"reference")
        (run_dir / "references" / "layout-guides" / "thinking.png").write_bytes(b"guide")
        (run_dir / "generated").mkdir()
        (run_dir / "generated" / "base.png").write_bytes(b"generated-base")
        (run_dir / "prompts" / "rows").mkdir(parents=True)
        prompt_file = run_dir / "prompts" / "rows" / "thinking-fallback.md"
        prompt_file.write_text(prompt_text, encoding="utf-8")
        source = tmp_path / "source-thinking.png"
        source.write_bytes(b"source")
        output = tmp_path / "output" / "thinking-transparent.png"
        job = {
            "id": "thinking",
            "kind": "row-strip",
            "status": job_status,
            "state": "thinking",
            "frames": 6,
            "input_images": [
                {"path": "references\\reference-01.png", "role": "original reference"},
                {"path": "references\\layout-guides\\thinking.png", "role": "layout guide"},
                {"path": "references\\canonical-base.png", "role": "canonical base"},
                {"path": "generated\\base.png", "role": "generated base"},
            ],
        }
        if include_source_path:
            job["source_path"] = str(source)
        jobs = {"jobs": [job]}
        (run_dir / "imagegen-jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
        return {"run_dir": run_dir, "prompt_file": prompt_file, "source": source, "output": output}

    def test_builds_dry_run_real_run_and_record_commands_without_api_call(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["jobId"], "thinking")
            self.assertEqual(result["sourceMode"], "recorded-row")
            self.assertTrue(result["sourceMatchesRecordedJob"])
            self.assertEqual(result["output"], str(paths["output"]))
            self.assertIn("--dry-run", result["dryRunCommand"])
            self.assertNotIn("--dry-run", result["runCommand"])
            self.assertIn(" edit ", result["runCommand"])
            self.assertLess(result["runCommand"].index(str(paths["source"])), result["runCommand"].index("reference-01.png"))
            self.assertIn("--background transparent", result["runCommand"])
            self.assertIn("--output-format png", result["runCommand"])
            self.assertIn("--source-provenance imagegen-cli-fallback", result["recordCommand"])
            self.assertIn("--cli-fallback-approved", result["recordCommand"])
            self.assertIn("--cli-fallback-model gpt-image-1.5", result["recordCommand"])
            self.assertIn("--cli-fallback-background transparent", result["recordCommand"])
            self.assertIn("--cli-fallback-output-format png", result["recordCommand"])
            self.assertIn("--strict-row-style", result["recordCommand"])

    def test_handoff_records_narrow_story_preserving_repair_intent(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            intent = result["repairIntent"]
            self.assertEqual(intent["mode"], "story-preserving-source-repair")
            self.assertIn("current row state story", intent["preserve"])
            self.assertIn("accepted expression, blink, mouth, and appendage performance", intent["preserve"])
            self.assertIn("apparent mascot body scale and padding", intent["preserve"])
            self.assertIn("source eye grammar", intent["repair"])
            self.assertIn("transparent or cleanup-ready background", intent["repair"])
            self.assertIn("do not redesign the mascot", intent["forbidden"])

    def test_can_write_generic_story_preserving_repair_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))
            default_prompt = paths["run_dir"] / "prompts" / "rows" / "thinking-true-transparency-fallback.md"
            self.assertFalse(default_prompt.exists())

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=None,
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
                write_default_prompt=True,
            )

            prompt_text = default_prompt.read_text(encoding="utf-8")
            self.assertTrue(result["defaultPromptWritten"])
            self.assertEqual(result["repairPromptSource"], "generic-story-preserving-default")
            self.assertEqual(result["promptFile"], str(default_prompt))
            self.assertTrue(result["promptRepairContract"]["ok"])
            self.assertIn("narrow story-preserving source repair", prompt_text)
            self.assertIn("current row state story", prompt_text)
            self.assertIn("neutral curiosity -> thought forming -> compact idea lands", prompt_text)
            self.assertIn("exactly 6 separated frames", prompt_text)
            self.assertIn("restore source eye grammar", prompt_text)
            self.assertIn("output true transparency with alpha 0", prompt_text)
            self.assertIn("accepted compact cue vocabulary", prompt_text)
            self.assertIn("Do not redesign the mascot", prompt_text)
            self.assertNotIn("Tridy", prompt_text)
            self.assertNotIn("trident", prompt_text.lower())
            self.assertNotIn("teal", prompt_text.lower())
            self.assertNotIn("red hood", prompt_text.lower())

    def test_missing_default_prompt_requires_explicit_write_flag(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))
            with self.assertRaisesRegex(SystemExit, "--write-default-prompt"):
                handoff.build_handoff(
                    run_dir=paths["run_dir"],
                    job_id="thinking",
                    source=paths["source"],
                    prompt_file=None,
                    output=paths["output"],
                    imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                    record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                    python_exe=Path("C:/Python/python.exe"),
                )

    def test_handoff_records_prompt_repair_contract_evidence(self) -> None:
        prompt_text = """
        Preserve the current row state story, body scale, spacing, and padding.
        Preserve the accepted expression, blink, mouth, appendage rhythm, and state-cue timing.
        Keep the same mascot identity and do not redesign the mascot.
        Repair source eye grammar and output true transparency with alpha 0 outside sprite pixels.
        For thinking, preserve the idea lands beat. The main puff is never oversized;
        use round/blocky puff silhouettes and do not make the cue bigger to prove the idea landed.
        Do not add generic UI symbols, detached icons, random symbols, or new props.
        """
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp), prompt_text=prompt_text)

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            contract = result["promptRepairContract"]
            self.assertTrue(contract["ok"])
            self.assertEqual(contract["missingRequiredChecks"], [])
            self.assertTrue(contract["checks"]["preserve-story"])
            self.assertTrue(contract["checks"]["preserve-scale"])
            self.assertTrue(contract["checks"]["repair-eye-grammar"])
            self.assertTrue(contract["checks"]["repair-transparency"])
            self.assertTrue(contract["checks"]["thinking-cue-compactness"])
            self.assertTrue(contract["checks"]["thinking-do-not-enlarge-cue"])

    def test_thinking_handoff_accepts_generic_compact_cue_contract_without_puff_terms(self) -> None:
        prompt_text = """
        Preserve the current row state story, body scale, spacing, and padding.
        Preserve the accepted expression, blink, mouth, appendage rhythm, and state-cue timing.
        Keep the same mascot identity and do not redesign the mascot.
        Repair source eye grammar and output true transparency with alpha 0 outside sprite pixels.
        For thinking, keep the accepted state cue compact, close to its source, and secondary to the mascot.
        Do not enlarge the cue, switch cue vocabulary, add generic UI symbols, add detached icons,
        add random symbols, or introduce new props.
        """
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp), prompt_text=prompt_text)

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            contract = result["promptRepairContract"]
            self.assertTrue(contract["ok"])
            self.assertEqual(contract["missingRequiredChecks"], [])
            self.assertTrue(contract["checks"]["thinking-cue-compactness"])
            self.assertTrue(contract["checks"]["thinking-do-not-enlarge-cue"])
            self.assertTrue(contract["checks"]["thinking-no-new-cue-vocabulary"])
            self.assertNotIn("thinking-idea-lands-story", contract["checks"])
            self.assertNotIn("thinking-idea-peak-not-oversized", contract["checks"])

    def test_handoff_exposes_missing_prompt_repair_contract_for_vague_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp), prompt_text="Fallback prompt")

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            contract = result["promptRepairContract"]
            self.assertFalse(contract["ok"])
            self.assertIn("preserve-story", contract["missingRequiredChecks"])
            self.assertIn("repair-eye-grammar", contract["missingRequiredChecks"])
            self.assertIn("repair-transparency", contract["missingRequiredChecks"])

    def test_handoff_records_required_cli_environment(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
            )

            self.assertEqual(result["requiredEnvironment"], ["OPENAI_API_KEY"])
            self.assertTrue(result["requiresExplicitUserApproval"])
            self.assertFalse(result["explicitUserApprovalReceived"])
            self.assertTrue(any("OPENAI_API_KEY" in note for note in result["notes"]))

    def test_handoff_can_use_unrecorded_rejected_candidate_without_recording_job(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(
                Path(raw_tmp),
                job_status="pending",
                include_source_path=False,
            )

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=None,
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
                write_default_prompt=True,
                allow_rejected_candidate_source=True,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["jobStatus"], "pending")
            self.assertEqual(result["sourceMode"], "rejected-candidate")
            self.assertIsNone(result["recordedJobSource"])
            self.assertIsNone(result["sourceMatchesRecordedJob"])
            self.assertIn(str(paths["source"]), result["runCommand"])
            self.assertLess(result["runCommand"].index(str(paths["source"])), result["runCommand"].index("reference-01.png"))
            self.assertIn("--source-provenance imagegen-cli-fallback", result["recordCommand"])
            self.assertTrue(any("do not record that candidate" in note for note in result["notes"]))

    def test_pending_candidate_source_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(
                Path(raw_tmp),
                job_status="pending",
                include_source_path=False,
            )

            with self.assertRaisesRegex(SystemExit, "--allow-rejected-candidate-source"):
                handoff.build_handoff(
                    run_dir=paths["run_dir"],
                    job_id="thinking",
                    source=paths["source"],
                    prompt_file=paths["prompt_file"],
                    output=paths["output"],
                    imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                    record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                    python_exe=Path("C:/Python/python.exe"),
                )

    def test_recorded_job_can_use_rejected_candidate_repair_branch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))
            rejected_candidate = Path(raw_tmp) / "rejected-candidate.png"
            rejected_candidate.write_bytes(b"candidate")

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=rejected_candidate,
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
                allow_rejected_candidate_source=True,
            )

            self.assertEqual(result["sourceMode"], "rejected-candidate")
            self.assertEqual(result["recordedJobSource"], str(paths["source"]))
            self.assertFalse(result["sourceMatchesRecordedJob"])
            self.assertTrue(any("rejected or unrecorded candidate" in note for note in result["notes"]))

    def test_handoff_can_record_explicit_user_approval_with_note(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))

            result = handoff.build_handoff(
                run_dir=paths["run_dir"],
                job_id="thinking",
                source=paths["source"],
                prompt_file=paths["prompt_file"],
                output=paths["output"],
                imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                python_exe=Path("C:/Python/python.exe"),
                user_approved=True,
                approval_note="User approved true-transparency CLI fallback for thinking on 2026-06-12.",
            )

            self.assertTrue(result["requiresExplicitUserApproval"])
            self.assertTrue(result["explicitUserApprovalReceived"])
            self.assertEqual(
                result["approvalNote"],
                "User approved true-transparency CLI fallback for thinking on 2026-06-12.",
            )
            self.assertTrue(any("Approval has been recorded" in note for note in result["notes"]))

    def test_handoff_requires_note_when_recording_explicit_user_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))

            with self.assertRaisesRegex(SystemExit, "--approval-note is required"):
                handoff.build_handoff(
                    run_dir=paths["run_dir"],
                    job_id="thinking",
                    source=paths["source"],
                    prompt_file=paths["prompt_file"],
                    output=paths["output"],
                    imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                    record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                    python_exe=Path("C:/Python/python.exe"),
                    user_approved=True,
                )

    def test_rejects_non_row_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            paths = self.write_run(tmp_path)
            jobs = {"jobs": [{"id": "base", "kind": "base-companion", "status": "complete"}]}
            (paths["run_dir"] / "imagegen-jobs.json").write_text(json.dumps(jobs), encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "must be a row-strip job"):
                handoff.build_handoff(
                    run_dir=paths["run_dir"],
                    job_id="base",
                    source=paths["source"],
                    prompt_file=paths["prompt_file"],
                    output=paths["output"],
                    imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                    record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                    python_exe=Path("C:/Python/python.exe"),
                )

    def test_rejects_stale_source_that_does_not_match_recorded_job_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            paths = self.write_run(Path(raw_tmp))
            stale_source = Path(raw_tmp) / "stale-thinking.png"
            stale_source.write_bytes(b"stale")

            with self.assertRaisesRegex(SystemExit, "does not match recorded job source_path"):
                handoff.build_handoff(
                    run_dir=paths["run_dir"],
                    job_id="thinking",
                    source=stale_source,
                    prompt_file=paths["prompt_file"],
                    output=paths["output"],
                    imagegen_script=Path("C:/Users/dante/.codex/skills/.system/imagegen/scripts/image_gen.py"),
                    record_script=ROOT / "scripts" / "record_companion_imagegen_result.py",
                    python_exe=Path("C:/Python/python.exe"),
                )


if __name__ == "__main__":
    unittest.main()
