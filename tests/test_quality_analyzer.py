import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "scripts" / "analyze_companion_quality.py"

spec = importlib.util.spec_from_file_location("analyze_companion_quality", ANALYZER_PATH)
analyzer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(analyzer)


def write_manifest(tmp_path: Path, atlas_name: str = "atlas.png") -> Path:
    manifest = {
        "id": "fixture",
        "displayName": "Fixture",
        "style": {"stateClarity": "pose-only"},
        "atlas": {
            "path": atlas_name,
            "width": 1024,
            "height": 288,
            "columns": 4,
            "rows": 1,
            "cellWidth": 256,
            "cellHeight": 288,
        },
        "states": {
            "idle": {
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


def paste_body(
    atlas: Image.Image,
    column: int,
    radius: int,
    center: tuple[int, int] = (128, 160),
    row: int = 0,
) -> None:
    frame = Image.new("RGBA", (256, 288), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    cx, cy = center
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(230, 245, 255, 255))
    draw.ellipse((cx - 10, cy - 6, cx - 4, cy), fill=(0, 0, 0, 255))
    draw.ellipse((cx + 4, cy - 6, cx + 10, cy), fill=(0, 0, 0, 255))
    atlas.alpha_composite(frame, (column * 256, row * 288))


class QualityAnalyzerTests(unittest.TestCase):
    def test_flags_silhouette_scale_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column, radius in enumerate([52, 53, 74, 52]):
                paste_body(atlas, column, radius)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("silhouette core scale drifts" in warning for warning in result["warnings"]))

    def test_accepts_small_breathing_silhouette_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column, radius in enumerate([52, 54, 53, 52]):
                paste_body(atlas, column, radius)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(any("silhouette core scale drifts" in warning for warning in result["warnings"]))

    def test_flags_silhouette_center_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column, center in enumerate([(128, 160), (128, 160), (128, 183), (128, 160)]):
                paste_body(atlas, column, 52, center=center)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("silhouette core center drifts" in warning for warning in result["warnings"]))

    def test_flags_silhouette_scale_range_even_when_median_drift_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1536, 288), (0, 0, 0, 0))
            for column, radius in enumerate([52, 54, 56, 58, 60, 62]):
                paste_body(atlas, column, radius)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["atlas"]["width"] = 1536
            manifest["atlas"]["columns"] = 6
            manifest["states"]["idle"]["frames"] = 6
            manifest["states"]["idle"]["durations"] = [120, 120, 120, 120, 120, 120]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("silhouette core scale range" in warning for warning in result["warnings"]))

    def test_accepts_moderate_core_scale_range_for_expressive_rows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column, radius in enumerate([52, 52, 55, 52]):
                paste_body(atlas, column, radius)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertTrue(result["ok"], result["warnings"])
            self.assertGreater(result["qa"]["idle"]["bodyCoreScaleRangeRatio"], 0.05)
            self.assertLess(
                result["qa"]["idle"]["bodyCoreScaleRangeRatio"],
                analyzer.DEFAULT_MAX_CORE_SCALE_RANGE_RATIO,
            )
            self.assertFalse(any("silhouette core scale range" in warning for warning in result["warnings"]))

    def test_flags_core_scale_range_above_production_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column, radius in enumerate([52, 52, 57, 52]):
                paste_body(atlas, column, radius)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertGreater(
                result["qa"]["idle"]["bodyCoreScaleRangeRatio"],
                analyzer.DEFAULT_MAX_CORE_SCALE_RANGE_RATIO,
            )
            self.assertFalse(result["ok"])
            self.assertTrue(any("silhouette core scale range" in warning for warning in result["warnings"]))

    def test_flags_cross_state_core_scale_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 576), (0, 0, 0, 0))
            for column in range(4):
                paste_body(atlas, column, 52, row=0)
                paste_body(atlas, column, 70, row=1)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["atlas"]["height"] = 576
            manifest["atlas"]["rows"] = 2
            manifest["states"]["answering"] = {
                "row": 1,
                "frames": 4,
                "durations": [120, 120, 120, 120],
                "loop": True,
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("cross-state median core scale range" in warning for warning in result["warnings"]))
            self.assertIn("crossState", result["qa"])

    def test_near_face_attached_voice_cue_does_not_require_separate_component(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column in range(4):
                paste_body(atlas, column, 52)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["style"] = {"stateClarity": "semantic-enhancers", "renderingStyle": "codex-pixel-art"}
            manifest["states"]["idle"]["enhancer"] = {
                "kind": "no-text pixel voice cue",
                "attachment": "near-face",
                "description": "Tiny voice pixels anchored on or close to the mouth.",
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(any("semantic enhancer appears" in warning for warning in result["warnings"]))

    def test_near_head_enhancer_still_requires_separate_component(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column in range(4):
                paste_body(atlas, column, 52)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["style"] = {"stateClarity": "semantic-enhancers", "renderingStyle": "codex-pixel-art"}
            manifest["states"]["idle"]["enhancer"] = {
                "kind": "thought puff",
                "attachment": "near-head",
                "description": "A compact thought puff near the head.",
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertTrue(any("semantic enhancer appears" in warning for warning in result["warnings"]))

    def test_near_head_overlap_policy_does_not_require_separate_component(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas = Image.new("RGBA", (1024, 288), (0, 0, 0, 0))
            for column in range(4):
                paste_body(atlas, column, 52)
            atlas.save(tmp_path / "atlas.png")
            manifest_path = write_manifest(tmp_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["style"] = {"stateClarity": "semantic-enhancers", "renderingStyle": "codex-pixel-art"}
            manifest["states"]["idle"]["enhancer"] = {
                "kind": "partly occluded thought puff",
                "attachment": "near-head",
                "componentPolicy": "overlap-ok",
                "description": "A compact thought puff sits close enough to overlap the top of the hood.",
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = analyzer.analyze_manifest_quality(manifest_path)

            self.assertFalse(any("semantic enhancer appears" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
