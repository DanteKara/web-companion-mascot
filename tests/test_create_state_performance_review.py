import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_state_performance_review.py"


def write_manifest(tmp_path: Path) -> Path:
    atlas_path = tmp_path / "atlas.png"
    atlas = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for index in range(4):
        x = index * 32 + 10
        for dx in range(12):
            for dy in range(14):
                atlas.putpixel((x + dx, 9 + dy), (20, 24, 31, 255))
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


def production_pass_args(manifest_path: Path) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--manifest",
        str(manifest_path),
        "--status",
        "pass",
        "--production-use",
        "--review-all-frames",
        "--expected-state-read",
        "thinking=Coherent source-vibe processing arc with expression, body timing, and compact thought cue.",
        "--check",
        "frameByFrameStateReadReviewed=true",
        "--check",
        "intendedStateReadable=true",
        "--check",
        "noWrongStateRead=true",
        "--check",
        "expressionMatchesState=true",
        "--check",
        "cueMotionMatchesState=true",
        "--check",
        "noTiredPantingUnlessStateRequiresIt=true",
        "--check",
        "noOffVibeGenericCue=true",
    ]


class CreateStatePerformanceReviewTests(unittest.TestCase):
    def test_production_pass_requires_story_arc_and_mascot_acting_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp))

            result = subprocess.run(
                production_pass_args(manifest_path),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("coherentStateStoryArc", result.stderr)
            self.assertIn("mascotActingVariesAcrossFrames", result.stderr)

    def test_writes_story_arc_and_mascot_acting_checks_for_production_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path)
            args = production_pass_args(manifest_path) + [
                "--check",
                "coherentStateStoryArc=true",
                "--check",
                "mascotActingVariesAcrossFrames=true",
                "--notes",
                "Every used frame was inspected for coherent story arc and mascot acting, not cue-only motion.",
            ]

            result = subprocess.run(
                args,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            review = json.loads((tmp_path / "qa" / "state-performance-review.json").read_text(encoding="utf-8"))
            self.assertTrue(review["checks"]["coherentStateStoryArc"])
            self.assertTrue(review["checks"]["mascotActingVariesAcrossFrames"])


if __name__ == "__main__":
    unittest.main()
