import base64
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_PATH = ROOT / "scripts" / "capture_codex_app_imagegen_result.py"

spec = importlib.util.spec_from_file_location("capture_codex_app_imagegen_result", CAPTURE_PATH)
capture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(capture)


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class CaptureCodexAppImagegenResultTests(unittest.TestCase):
    def test_captures_matching_image_generation_call_to_png_and_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            session_path = tmp_path / "rollout-test.jsonl"
            session_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-06-17T00:00:00.000Z",
                                "type": "response_item",
                                "payload": {
                                    "type": "image_generation_call",
                                    "id": "ig_old",
                                    "status": "completed",
                                    "result": base64.b64encode(b"not-a-png").decode("ascii"),
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-06-17T00:01:00.000Z",
                                "type": "response_item",
                                "payload": {
                                    "type": "image_generation_call",
                                    "id": "ig_target",
                                    "status": "generating",
                                    "revised_prompt": "pixel mascot row",
                                    "result": base64.b64encode(PNG_BYTES).decode("ascii"),
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            out_path = tmp_path / "captured" / "thinking.png"
            result = capture.capture_result(
                session=session_path,
                out=out_path,
                call_id="ig_target",
                json_out=None,
            )

            self.assertEqual(out_path.read_bytes(), PNG_BYTES)
            self.assertEqual(result["callId"], "ig_target")
            self.assertEqual(result["source"], "codex-app-imagegen")
            self.assertEqual(result["outputPath"], str(out_path.resolve()))
            self.assertEqual(result["sha256"], capture.sha256_bytes(PNG_BYTES))
            sidecar = out_path.with_name(out_path.name + ".codex-imagegen.json")
            self.assertTrue(sidecar.is_file())
            sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(sidecar_data["callId"], "ig_target")
            self.assertNotIn("result", sidecar_data)


if __name__ == "__main__":
    unittest.main()
