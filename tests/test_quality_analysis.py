import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.analyze_companion_quality import analyze_manifest_quality
from scripts.assemble_companion_atlas import normalize_manifest
from scripts.validate_companion_manifest import validate_manifest


def make_cell(
    size: tuple[int, int],
    body_center: tuple[int, int] = (50, 68),
    enhancer_center: tuple[int, int] | None = None,
) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    bx, by = body_center
    draw.ellipse((bx - 20, by - 20, bx + 20, by + 20), fill=(220, 245, 255, 255), outline=(0, 20, 35, 255), width=3)
    if enhancer_center:
        ex, ey = enhancer_center
        draw.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=(230, 250, 255, 255), outline=(0, 20, 35, 255), width=2)
    return image


def write_package(
    root: Path,
    state: str,
    frames: list[Image.Image],
    enhancer: dict[str, str] | None = None,
) -> Path:
    cell_width, cell_height = frames[0].size
    atlas = Image.new("RGBA", (cell_width * len(frames), cell_height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        atlas.alpha_composite(frame, (index * cell_width, 0))
    atlas.save(root / "atlas.png")
    (root / "qa").mkdir()
    (root / "qa" / "assembly-report.json").write_text(
        json.dumps({"ok": True, "warnings": [], "outlineImprover": {"enabled": True, "totalOutlineHaloPixels": 0}}),
        encoding="utf-8",
    )
    manifest = {
        "id": "test",
        "displayName": "Test",
        "style": {"stateClarity": "semantic-enhancers", "enhancerTheme": "test"},
        "atlas": {
            "path": "atlas.png",
            "width": atlas.width,
            "height": atlas.height,
            "columns": len(frames),
            "rows": 1,
            "cellWidth": cell_width,
            "cellHeight": cell_height,
        },
        "states": {
            state: {
                "row": 0,
                "frames": len(frames),
                "durations": [120] * len(frames),
                "loop": True,
            }
        },
    }
    if enhancer:
        manifest["states"][state]["enhancer"] = enhancer
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


class QualityAnalysisTests(unittest.TestCase):
    def test_warns_when_semantic_enhancer_anchor_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = [
                make_cell((100, 100), enhancer_center=(50, 25)),
                make_cell((100, 100), enhancer_center=(78, 24)),
                make_cell((100, 100), enhancer_center=(22, 25)),
                make_cell((100, 100), enhancer_center=(88, 25)),
            ]
            manifest = write_package(
                root,
                "thinking",
                frames,
                {"kind": "thought-bubble", "attachment": "near-head", "description": "bubble above the head"},
            )

            result = analyze_manifest_quality(manifest, max_semantic_drift_ratio=0.25)

            self.assertFalse(result["ok"])
            self.assertTrue(any("semantic enhancer anchor drifts" in warning for warning in result["warnings"]))
            self.assertTrue((root / "qa" / "quality-report.json").exists())
            self.assertTrue((root / "qa" / "semantic-anchor-check.png").exists())
            self.assertTrue((root / "qa" / "motion-quality-check.png").exists())

    def test_warns_when_animation_uses_near_duplicate_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = [make_cell((100, 100)) for _ in range(6)]
            manifest = write_package(root, "idle", frames)

            result = analyze_manifest_quality(manifest, max_duplicate_ratio=0.2)

            self.assertFalse(result["ok"])
            self.assertTrue(any("near-duplicate" in warning for warning in result["warnings"]))

    def test_strict_validation_can_require_quality_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = [make_cell((100, 100)) for _ in range(4)]
            manifest = write_package(root, "idle", frames)

            _data, _errors, warnings, _qa = validate_manifest(
                manifest,
                require_quality_report=True,
            )

            self.assertIn("qa/quality-report.json is missing or unreadable", warnings)

    def test_chatbot_profile_recommends_smooth_waiting_state_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = [make_cell((100, 100)) for _ in range(10)]
            manifest = write_package(root, "thinking", frames)

            _data, _errors, warnings, _qa = validate_manifest(
                manifest,
                profile="chatbot",
            )

            self.assertTrue(any("thinking" in warning and "12+" in warning for warning in warnings))

    def test_assembler_fills_smooth_frame_durations_with_varied_timing(self) -> None:
        manifest = {
            "states": {
                "answering": {
                    "row": 0,
                    "frames": 12,
                    "durations": [],
                }
            }
        }

        result = normalize_manifest(manifest, columns=12, rows=1, cell_width=100, cell_height=100, atlas_path="atlas.webp")
        durations = result["states"]["answering"]["durations"]

        self.assertEqual(len(durations), 12)
        self.assertGreater(len(set(durations)), 1)


if __name__ == "__main__":
    unittest.main()
