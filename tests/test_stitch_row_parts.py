import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "stitch_row_parts.py"

spec = importlib.util.spec_from_file_location("stitch_row_parts", SCRIPT_PATH)
stitcher = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stitcher)


class StitchRowPartsTests(unittest.TestCase):
    def test_stitches_parts_left_to_right_on_key_background(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            left = Image.new("RGBA", (8, 6), (255, 0, 255, 255))
            right = Image.new("RGBA", (6, 4), (255, 0, 255, 255))
            ImageDraw.Draw(left).rectangle((1, 1, 3, 3), fill=(0, 0, 0, 255))
            ImageDraw.Draw(right).rectangle((2, 1, 4, 2), fill=(255, 255, 255, 255))
            left_path = tmp_path / "left.png"
            right_path = tmp_path / "right.png"
            out_path = tmp_path / "out.png"
            left.save(left_path)
            right.save(right_path)

            result = stitcher.stitch_parts([left_path, right_path], out_path)

            self.assertTrue(result["ok"])
            self.assertEqual(result["width"], 14)
            self.assertEqual(result["height"], 6)
            out = Image.open(out_path).convert("RGBA")
            self.assertEqual(out.size, (14, 6))
            self.assertEqual(out.getpixel((1, 1)), (0, 0, 0, 255))
            self.assertEqual(out.getpixel((10, 2)), (255, 255, 255, 255))
            self.assertEqual(out.getpixel((13, 5)), (255, 0, 255, 255))


if __name__ == "__main__":
    unittest.main()
