import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_companion_run.py"
STATUS_PATH = ROOT / "scripts" / "companion_job_status.py"
RECORD_PATH = ROOT / "scripts" / "record_companion_imagegen_result.py"

spec = importlib.util.spec_from_file_location("prepare_companion_run", PREPARE_PATH)
prepare = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare)

status_spec = importlib.util.spec_from_file_location("companion_job_status", STATUS_PATH)
job_status = importlib.util.module_from_spec(status_spec)
assert status_spec.loader is not None
status_spec.loader.exec_module(job_status)

record_spec = importlib.util.spec_from_file_location("record_companion_imagegen_result", RECORD_PATH)
record = importlib.util.module_from_spec(record_spec)
assert record_spec.loader is not None
record_spec.loader.exec_module(record)


def write_fixture_png(path: Path, color: tuple[int, int, int, int] = (240, 250, 255, 255)) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=color, outline=(40, 100, 160, 255), width=3)
    draw.ellipse((24, 27, 29, 33), fill=(20, 30, 40, 255))
    draw.ellipse((36, 27, 41, 33), fill=(20, 30, 40, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


class PrepareCompanionRunTests(unittest.TestCase):
    def test_no_limb_working_prompt_forbids_held_work_props(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Orb",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working,answering",
                    "--anatomy-class",
                    "no-limbs",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("Semantic ladder", working_prompt)
            self.assertIn("busy-but-friendly", working_prompt)
            self.assertIn("Expression lock", working_prompt)
            self.assertIn("do not add eyebrows to a browless mascot", working_prompt)
            self.assertIn("no held, near-hand", working_prompt)
            self.assertIn("purposeful processing", working_prompt)
            self.assertIn("remain visible after chroma-key cleanup", working_prompt)
            self.assertIn("tiny detached speck", working_prompt)
            self.assertIn("Reject a pretty motif-native effect when it does not communicate the state", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["style"]["renderingStyle"], "codex-pixel-art")
            self.assertEqual(manifest["style"]["stateClarity"], "semantic-enhancers")
            self.assertEqual(manifest["states"]["working"]["frames"], 6)
            self.assertIn("visualLanguageFit", manifest["states"]["working"]["enhancer"])

    def test_hand_mascot_prompt_allows_supported_expressive_actions(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Handbot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "hands",
                    "--source-vibe",
                    "friendly tiny helper robot with real hands",
                    "--motif",
                    "small panel glow",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Visible hands may point, present, hold, touch the face, type, or write", thinking_prompt)
            self.assertIn("friendly tiny helper robot", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(cue_plan["visualLanguage"]["motifs"], ["small panel glow"])
            self.assertEqual(cue_plan["states"]["working"]["visualAidDecision"], "use only if acting alone would be unclear at 64-96 px")

    def test_simple_fin_draft_plan_stays_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Finny",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("not hand-to-chin", thinking_prompt)
            self.assertIn("no held props or tiny detached specks in the draft plan", working_prompt)
            self.assertIn("rim-touching", working_prompt)
            self.assertIn("invented angry eyebrows", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("brace", manifest["states"]["working"]["enhancer"]["description"])

    def test_preparer_writes_hatch_style_imagegen_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            reference = tmp_path / "reference.png"
            write_fixture_png(reference)

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--reference",
                    str(reference),
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            self.assertEqual(jobs["primary_generation_skill"], "$imagegen")
            self.assertEqual([job["id"] for job in jobs["jobs"]], ["base", "thinking", "working"])

            base_job = jobs["jobs"][0]
            thinking_job = jobs["jobs"][1]
            self.assertTrue(base_job["requires_grounded_generation"])
            self.assertFalse(base_job["allow_prompt_only_generation"])
            self.assertEqual(thinking_job["depends_on"], ["base"])
            self.assertFalse(thinking_job["allow_prompt_only_generation"])
            self.assertIn("references/canonical-base.png", thinking_job["identity_reference_paths"])
            self.assertTrue((out_dir / "references" / "reference-01.png").is_file())
            self.assertTrue((out_dir / "references" / "layout-guides" / "thinking.png").is_file())
            self.assertTrue((out_dir / "prompts" / "base.md").is_file())
            self.assertTrue((out_dir / "prompts" / "rows" / "thinking.md").is_file())

            first_status = job_status.status(out_dir)
            self.assertEqual(first_status["counts"]["ready"], 1)
            self.assertEqual(first_status["ready_jobs"][0]["id"], "base")
            self.assertEqual(first_status["counts"]["blocked"], 2)

    def test_recording_base_creates_canonical_reference_and_unblocks_rows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            reference = tmp_path / "reference.png"
            base_source = source_dir / "ig_base.png"
            row_source = source_dir / "ig_working.png"
            write_fixture_png(reference)
            write_fixture_png(base_source, (245, 252, 255, 255))
            write_fixture_png(row_source, (235, 248, 255, 255))

            prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--reference",
                    str(reference),
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            with self.assertRaises(SystemExit):
                record.record_result(
                    run_dir=out_dir,
                    job_id="working",
                    source=row_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                )

            base_result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
            )
            self.assertTrue(base_result["ok"])
            self.assertTrue((out_dir / "references" / "canonical-base.png").is_file())

            ready_after_base = job_status.status(out_dir)
            self.assertEqual(ready_after_base["counts"]["ready"], 1)
            self.assertEqual(ready_after_base["ready_jobs"][0]["id"], "working")

            row_result = record.record_result(
                run_dir=out_dir,
                job_id="working",
                source=row_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
            )
            self.assertTrue(row_result["ok"])
            self.assertTrue((out_dir / "generated" / "working.png").is_file())

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            completed = {job["id"]: job for job in jobs["jobs"]}
            self.assertEqual(completed["base"]["status"], "complete")
            self.assertEqual(completed["working"]["status"], "complete")
            self.assertEqual(completed["base"]["source_provenance"], "synthetic-test")
            self.assertIn("canonical_identity_reference", jobs)


if __name__ == "__main__":
    unittest.main()
