import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_eye_grammar_review.py"


def write_manifest(tmp_path: Path) -> Path:
    atlas_path = tmp_path / "atlas.png"
    atlas = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for index in range(4):
        x = index * 32 + 10
        for dx in range(12):
            for dy in range(14):
                atlas.putpixel((x + dx, 9 + dy), (20, 24, 31, 255))
        atlas.putpixel((x + 3, 12), (255, 255, 255, 255))
    atlas.save(atlas_path)

    manifest = {
        "id": "fixture",
        "displayName": "Fixture",
        "atlas": {
            "path": "atlas.png",
            "width": 128,
            "height": 32,
            "columns": 4,
            "rows": 1,
            "cellWidth": 32,
            "cellHeight": 32,
        },
        "states": {
            "thinking": {
                "row": 0,
                "frames": 4,
                "durations": [120, 120, 120, 120],
                "loop": True,
            }
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


class CreateEyeGrammarReviewTests(unittest.TestCase):
    def test_production_pass_requires_expected_eye_grammar(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp))

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--status",
                    "pass",
                    "--production-use",
                    "--review-all-frames",
                    "--check",
                    "frameByFrameEyeGrammarReviewed=true",
                    "--check",
                    "eyeCountStable=true",
                    "--check",
                    "eyeShapeStable=true",
                    "--check",
                    "eyeFillAndHighlightStable=true",
                    "--check",
                    "eyePlacementStable=true",
                    "--check",
                    "noWhiteScleraOrCrescentSwap=true",
                    "--check",
                    "noMismatchedOrSymbolEyes=true",
                    "--check",
                    "blinkStyleMatchesSource=true",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--expected-eye-grammar is required", result.stderr)

    def test_writes_review_and_sheet_for_production_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--status",
                    "pass",
                    "--production-use",
                    "--review-all-frames",
                    "--expected-eye-grammar",
                    "Two stable dark oval eyes with tiny matched highlights and source-style blink lines.",
                    "--check",
                    "frameByFrameEyeGrammarReviewed=true",
                    "--check",
                    "eyeCountStable=true",
                    "--check",
                    "eyeShapeStable=true",
                    "--check",
                    "eyeFillAndHighlightStable=true",
                    "--check",
                    "eyePlacementStable=true",
                    "--check",
                    "noWhiteScleraOrCrescentSwap=true",
                    "--check",
                    "noMismatchedOrSymbolEyes=true",
                    "--check",
                    "blinkStyleMatchesSource=true",
                    "--notes",
                    "Every used frame preserves the canonical eye grammar.",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            review_path = tmp_path / "qa" / "eye-grammar-review.json"
            sheet_path = tmp_path / "qa" / "eye-grammar-review.png"
            review = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual(review["status"], "pass")
            self.assertTrue(review["productionUse"])
            self.assertEqual(review["statesReviewed"], ["thinking"])
            self.assertEqual(review["reviewedFrames"], {"thinking": [1, 2, 3, 4]})
            self.assertTrue(review["checks"]["noWhiteScleraOrCrescentSwap"])
            self.assertTrue(sheet_path.exists())


if __name__ == "__main__":
    unittest.main()
