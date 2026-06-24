import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "assemble_companion_atlas.py"

spec = importlib.util.spec_from_file_location("assemble_companion_atlas", SCRIPT_PATH)
assembler = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(assembler)


class AssembleCompanionAtlasTests(unittest.TestCase):
    def test_resolve_key_color_uses_manifest_chroma_key_before_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = Path(raw_tmp) / "manifest.json"
            manifest = {"style": {"chromaKey": {"hex": "#00FF00"}}}

            self.assertEqual(assembler.resolve_key_color(manifest, manifest_path, None), "#00FF00")

    def test_resolve_key_color_uses_companion_request_when_manifest_lacks_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = tmp_path / "manifest.json"
            (tmp_path / "companion_request.json").write_text(
                json.dumps({"chromaKey": {"hex": "#00FFFF"}}),
                encoding="utf-8",
            )

            self.assertEqual(assembler.resolve_key_color({}, manifest_path, None), "#00FFFF")

    def test_resolve_key_color_allows_explicit_override(self) -> None:
        manifest = {"style": {"chromaKey": {"hex": "#00FF00"}}}

        self.assertEqual(assembler.resolve_key_color(manifest, Path("manifest.json"), "#FF00FF"), "#FF00FF")

    def test_component_mode_uses_largest_expected_components_as_bodies(self) -> None:
        strip = Image.new("RGBA", (360, 120), (0, 0, 0, 0))
        draw = ImageDraw.Draw(strip)
        for offset in [20, 140, 260]:
            draw.rectangle((offset, 40, offset + 48, 88), fill=(20, 40, 60, 255))
            draw.rectangle((offset + 58, 10, offset + 72, 24), fill=(230, 245, 255, 255))

        _slots, metadata = assembler.component_frame_slots(
            strip,
            expected=3,
            body_min_area=100,
            component_min_area=20,
        )

        self.assertEqual(len(metadata), 3)
        self.assertEqual([entry["components"] for entry in metadata], [2, 2, 2])
        for entry in metadata:
            self.assertGreater(entry["componentAreas"][0], entry["componentAreas"][1])

    def test_state_fit_scale_uses_largest_frame_footprint(self) -> None:
        body_only = Image.new("RGBA", (40, 40), (20, 40, 60, 255))
        body_with_effect = Image.new("RGBA", (40, 80), (0, 0, 0, 0))
        ImageDraw.Draw(body_with_effect).rectangle((0, 40, 39, 79), fill=(20, 40, 60, 255))
        ImageDraw.Draw(body_with_effect).ellipse((10, 0, 29, 19), fill=(230, 245, 255, 255))

        scale = assembler.fit_scale_for_sprites([body_only, body_with_effect], 100, 60, 0)

        self.assertAlmostEqual(scale, 0.75)

    def test_body_anchor_fit_ignores_tall_detached_cue_for_body_scale(self) -> None:
        body_only = {
            "sprite": Image.new("RGBA", (40, 40), (20, 40, 60, 255)),
            "body_bbox": (0, 0, 40, 40),
        }
        body_with_tall_cue = {
            "sprite": Image.new("RGBA", (40, 80), (0, 0, 0, 0)),
            "body_bbox": (0, 40, 40, 80),
        }
        draw = ImageDraw.Draw(body_with_tall_cue["sprite"])
        draw.rectangle((0, 40, 39, 79), fill=(20, 40, 60, 255))
        draw.ellipse((10, 0, 29, 19), fill=(230, 245, 255, 255))

        scale = assembler.fit_scale_for_body_anchored_sprites(
            [body_only, body_with_tall_cue],
            cell_width=100,
            cell_height=60,
            padding=0,
        )

        self.assertAlmostEqual(scale, 1.0)

    def test_body_anchor_target_keeps_detached_cue_from_shrinking_body(self) -> None:
        body_with_tall_cue = {
            "sprite": Image.new("RGBA", (40, 90), (0, 0, 0, 0)),
            "body_bbox": (0, 50, 40, 90),
            "fit_bbox": (0, 50, 40, 90),
        }
        draw = ImageDraw.Draw(body_with_tall_cue["sprite"])
        draw.rectangle((0, 50, 39, 89), fill=(20, 40, 60, 255))
        draw.ellipse((10, 0, 29, 19), fill=(230, 245, 255, 255))

        scale = assembler.fit_scale_for_body_anchored_sprites(
            [body_with_tall_cue],
            cell_width=100,
            cell_height=60,
            padding=0,
            target_body_fit_size=(40, 40),
        )

        self.assertAlmostEqual(scale, 1.0)

    def test_body_anchor_fit_uses_core_bbox_when_connected_prop_extends_frame(self) -> None:
        body_with_connected_prop = {
            "sprite": Image.new("RGBA", (40, 80), (0, 0, 0, 0)),
            "body_bbox": (0, 0, 40, 80),
            "fit_bbox": (0, 40, 40, 80),
        }
        draw = ImageDraw.Draw(body_with_connected_prop["sprite"])
        draw.rectangle((0, 40, 39, 79), fill=(20, 40, 60, 255))
        draw.rectangle((18, 0, 21, 40), fill=(230, 185, 40, 255))

        scale = assembler.fit_scale_for_body_anchored_sprites(
            [body_with_connected_prop],
            cell_width=100,
            cell_height=60,
            padding=0,
        )

        self.assertAlmostEqual(scale, 1.0)

    def test_body_anchor_target_scales_large_source_row_to_shared_body_size(self) -> None:
        larger_generated_body = {
            "sprite": Image.new("RGBA", (50, 50), (20, 40, 60, 255)),
            "body_bbox": (0, 0, 50, 50),
            "fit_bbox": (0, 0, 50, 50),
        }

        scale = assembler.fit_scale_for_body_anchored_sprites(
            [larger_generated_body],
            cell_width=100,
            cell_height=80,
            padding=0,
            target_body_fit_size=(40, 40),
        )

        self.assertAlmostEqual(scale, 0.8)

    def test_body_anchor_y_offset_uses_bottom_slack_for_tall_cue(self) -> None:
        body_with_tall_cue = {
            "sprite": Image.new("RGBA", (40, 70), (0, 0, 0, 0)),
            "body_bbox": (0, 30, 40, 70),
            "fit_bbox": (0, 30, 40, 70),
        }
        draw = ImageDraw.Draw(body_with_tall_cue["sprite"])
        draw.ellipse((10, 0, 29, 19), fill=(230, 245, 255, 255))
        draw.rectangle((0, 30, 39, 69), fill=(20, 40, 60, 255))

        y_offset = assembler.body_anchor_state_y_offset(
            [body_with_tall_cue],
            scale=1.0,
            cell_height=80,
            padding=10,
        )
        cell = assembler.fit_body_anchored_to_cell(
            body_with_tall_cue["sprite"],
            body_with_tall_cue["body_bbox"],
            cell_width=100,
            cell_height=80,
            padding=10,
            key=(0, 255, 0),
            spill_threshold=45,
            scale=1.0,
            y_offset=y_offset,
        )

        self.assertEqual(y_offset, 1)
        self.assertEqual(cell.getchannel("A").getbbox()[1], 1)

    def test_body_anchor_edge_scale_reduces_only_when_slack_is_exhausted(self) -> None:
        body_with_too_tall_cue = {
            "sprite": Image.new("RGBA", (40, 90), (0, 0, 0, 0)),
            "body_bbox": (0, 50, 40, 90),
            "fit_bbox": (0, 50, 40, 90),
        }
        draw = ImageDraw.Draw(body_with_too_tall_cue["sprite"])
        draw.ellipse((10, 0, 29, 19), fill=(230, 245, 255, 255))
        draw.rectangle((0, 50, 39, 89), fill=(20, 40, 60, 255))

        scale = assembler.body_anchor_scale_for_edge_clearance(
            [body_with_too_tall_cue],
            scale=1.0,
            cell_width=100,
            cell_height=80,
            padding=10,
        )
        y_offset = assembler.body_anchor_state_y_offset(
            [body_with_too_tall_cue],
            scale=scale,
            cell_height=80,
            padding=10,
        )
        cell = assembler.fit_body_anchored_to_cell(
            body_with_too_tall_cue["sprite"],
            body_with_too_tall_cue["body_bbox"],
            cell_width=100,
            cell_height=80,
            padding=10,
            key=(0, 255, 0),
            spill_threshold=45,
            scale=scale,
            y_offset=y_offset,
        )
        bbox = cell.getchannel("A").getbbox()

        self.assertLess(scale, 1.0)
        self.assertGreaterEqual(bbox[1], 1)
        self.assertLessEqual(bbox[3], 79)


if __name__ == "__main__":
    unittest.main()
