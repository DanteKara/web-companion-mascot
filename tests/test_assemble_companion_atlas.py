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


if __name__ == "__main__":
    unittest.main()
