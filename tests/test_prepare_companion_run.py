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
            self.assertIn("no slanted angry eyes", working_prompt)
            self.assertIn("V-shaped", working_prompt)
            self.assertIn("no held, near-hand", working_prompt)
            self.assertIn("purposeful processing", working_prompt)
            self.assertIn("remain visible after chroma-key cleanup", working_prompt)
            self.assertIn("tiny detached speck", working_prompt)
            self.assertIn("Reject a pretty motif-native effect when it does not communicate the state", working_prompt)
            self.assertIn("Do not place repeated leaf, oval, wing, mitten, paw, droplet", working_prompt)
            self.assertIn("inside the body core", working_prompt)

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
                    "--identity-prop",
                    "single chest screen",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Visible hands may point, present, hold, touch the face, type, or write", thinking_prompt)
            self.assertIn("friendly tiny helper robot", thinking_prompt)
            self.assertIn("Art direction floor", thinking_prompt)
            self.assertIn("polished mascot performance", thinking_prompt)
            self.assertIn("charming mascot-native acting beat", thinking_prompt)
            self.assertIn("Expression variation is mandatory", thinking_prompt)
            self.assertIn("Do not keep the same face in every frame", thinking_prompt)
            self.assertIn("visibly connected to its original shoulder/body anchor", thinking_prompt)
            self.assertIn("does not merge into a new cheek", thinking_prompt)
            self.assertIn("broad pixel-mitt", thinking_prompt)
            self.assertIn("Must-keep identity props/accessories: single chest screen", thinking_prompt)
            self.assertIn("Identity prop contract", thinking_prompt)
            self.assertIn("keep its count, side, scale, attachment, and basic silhouette stable", thinking_prompt)
            self.assertIn("Preserve signature props by default even when another cue is present", thinking_prompt)
            self.assertIn("Omit a must-keep prop only when the state card says", thinking_prompt)
            self.assertIn("Do not duplicate signature props", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(cue_plan["visualLanguage"]["motifs"], ["small panel glow"])
            self.assertEqual(cue_plan["visualLanguage"]["identityProps"], ["single chest screen"])
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
            self.assertIn("slanted angry eyes", working_prompt)
            self.assertIn("extra wings", working_prompt)
            self.assertIn("Cue colors and shapes must stay distinct", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("brace", manifest["states"]["working"]["enhancer"]["description"])

    def test_thinking_prompt_requires_visible_bubble_growth_arc(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Frame-by-frame acting arc", thinking_prompt)
            self.assertIn("small bubble", thinking_prompt)
            self.assertIn("medium bubble", thinking_prompt)
            self.assertIn("largest compact bubble", thinking_prompt)
            self.assertIn("neutral -> curious -> pondering -> recognition -> settle", thinking_prompt)
            self.assertIn("not the same face", thinking_prompt)
            self.assertIn("secondary to the mascot", thinking_prompt)
            self.assertIn("never larger than about one-third of the mascot body width", thinking_prompt)
            self.assertIn("do not let the thought cue become a second head/body-sized orb", thinking_prompt)
            self.assertIn("settle back into the loop", thinking_prompt)
            self.assertIn("not the same face or same bubble pasted in every frame", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("frameArc", cue_plan["states"]["thinking"])
            self.assertIn("small -> medium -> largest compact", cue_plan["states"]["thinking"]["frameArc"])

    def test_default_frame_counts_use_hatch_style_eight_frame_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "idle,thinking,working,answering",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["atlas"]["columns"], 8)
            self.assertEqual(manifest["states"]["idle"]["frames"], 8)
            self.assertEqual(manifest["states"]["thinking"]["frames"], 8)
            self.assertEqual(manifest["states"]["working"]["frames"], 8)
            self.assertEqual(manifest["states"]["answering"]["frames"], 8)

    def test_layout_guides_are_labeled_as_construction_not_output_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Guidey",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            request = json.loads((out_dir / "companion_request.json").read_text(encoding="utf-8"))
            usage = request["layoutGuides"][0]["usage"]
            self.assertIn("construction input only", usage)
            self.assertIn("intentionally empty", usage)
            self.assertIn("not a mascot preview", usage)

    def test_no_hand_working_prompt_allows_freestanding_work_props(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
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

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("freestanding or resting work prop", working_prompt)
            self.assertIn("small slate, tablet, blank card stack, token tray, chunky work tile", working_prompt)
            self.assertIn("beside or in front of the mascot", working_prompt)
            self.assertIn("the mascot works by looking, leaning, bobbing, and reacting", working_prompt)
            self.assertIn("not by holding, typing, writing, or inventing hands", working_prompt)
            self.assertIn("clear background gap", working_prompt)
            self.assertIn("no part of the prop or activity marks may touch", working_prompt)
            self.assertIn("inside or on the prop surface", working_prompt)
            self.assertIn("not in the empty gap", working_prompt)
            self.assertIn("merge the prop with the mascot body", working_prompt)
            self.assertIn("Frame-by-frame acting arc", working_prompt)
            self.assertIn("target wakes up", working_prompt)
            self.assertIn("sorting/checking/gathering", working_prompt)
            self.assertIn("chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens", working_prompt)
            self.assertIn("no readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, or list rows", working_prompt)
            self.assertIn("Working must show the mascot working on a concrete target", working_prompt)
            self.assertIn("visible before/during/after transformation", working_prompt)
            self.assertIn("not merely posing beside status icons", working_prompt)
            self.assertIn("Choose the work target from the mascot's visual language", working_prompt)
            self.assertIn("Place the work target in a believable interaction zone", working_prompt)
            self.assertIn("Avoid notebook, paper, page, or parchment-like surfaces", working_prompt)
            self.assertIn("fine stripes, wood-grain lines, plank lines, or parallel grooves", working_prompt)
            self.assertIn("Do not make the work surface read as a tiny document full of writing", working_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("freestandingPropPolicy", cue_plan["states"]["working"])

    def test_hands_working_prompt_keeps_prop_marks_non_text(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Handbot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("For any slate, tablet, blank card stack, token tray, panel, or work surface", working_prompt)
            self.assertIn("chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens", working_prompt)
            self.assertIn("solid and unruled", working_prompt)
            self.assertIn("no readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, or list rows", working_prompt)
            self.assertIn("Working must show the mascot working on a concrete target", working_prompt)
            self.assertIn("staff-tip glyph", working_prompt)
            self.assertIn("inactive or blank -> being operated/sorted/checked -> progress/result", working_prompt)
            self.assertIn("Tech/robot mascots can use panels, tablets, sliders, or status blocks", working_prompt)
            self.assertIn("Fantasy or magic mascots should use spell circles, rune tiles, charm tokens", working_prompt)
            self.assertIn("the mascot's gaze, hand, body, or identity prop must visibly cause the change", working_prompt)
            self.assertIn("near the active hand, paw, mouth, tool tip, staff tip", working_prompt)
            self.assertIn("prefer close-contact targets that touch, overlap, hover just above", working_prompt)
            self.assertIn("Avoid floor-level token rows and far-floating targets", working_prompt)
            self.assertIn("The viewer should understand what the mascot is acting on in every frame", working_prompt)
            self.assertIn("Use a theme-native result mark", working_prompt)
            self.assertIn("generic check marks only when the mascot's visual language supports product/tool UI", working_prompt)

    def test_answering_prompt_requires_mouth_origin_voice_cue(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Talky",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")
            self.assertIn("voice cue originating at the mouth", answering_prompt)
            self.assertIn("touch or overlap the mouth/lip edge", answering_prompt)
            self.assertIn("must not appear as a random bubble beside the head", answering_prompt)
            self.assertIn("Expression variation is mandatory", answering_prompt)
            self.assertIn("Mouth shapes and voice cues must change together", answering_prompt)
            self.assertIn("small attached cue -> clearer outward cue -> smaller returning cue", answering_prompt)

    def test_hands_thinking_prompt_tracks_hand_roles_for_face_touch_with_identity_prop(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Tridy",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single trident staff held on the left side",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Hand/appendage role continuity", thinking_prompt)
            self.assertIn(
                "account for every original hand, arm, paw, sleeve, fin, wing, or tentacle in every frame",
                thinking_prompt,
            )
            self.assertIn(
                "one hand may touch the chin only if the other original hand/arm remains accounted for",
                thinking_prompt,
            )
            self.assertIn(
                "no third hand, extra arm, duplicate sleeve, detached mitten, or new paw/finger cluster",
                thinking_prompt,
            )

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
