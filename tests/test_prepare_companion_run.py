import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_companion_run.py"

spec = importlib.util.spec_from_file_location("prepare_companion_run", PREPARE_PATH)
prepare = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare)


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
            self.assertIn("focused-but-friendly", working_prompt)
            self.assertIn("no held or near-hand props", working_prompt)
            self.assertIn("purposeful processing", working_prompt)
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
            self.assertIn("no held props in the draft plan", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("brace", manifest["states"]["working"]["enhancer"]["description"])


if __name__ == "__main__":
    unittest.main()
