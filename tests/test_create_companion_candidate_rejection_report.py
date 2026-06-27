import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "create_companion_candidate_rejection_report.py"

spec = importlib.util.spec_from_file_location("create_companion_candidate_rejection_report", SCRIPT_PATH)
candidate_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate_report)


def write_manifest(run_dir: Path) -> None:
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "fixture",
                "displayName": "Fixture",
                "style": {"chromaKey": {"hex": "#FF00FF", "rgb": [255, 0, 255]}},
                "atlas": {
                    "path": "atlas.png",
                    "width": 512,
                    "height": 288,
                    "columns": 2,
                    "rows": 1,
                    "cellWidth": 256,
                    "cellHeight": 288,
                },
                "states": {
                    "thinking": {"row": 0, "frames": 2, "durations": [120, 120], "loop": True},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_flat_sprite(path: Path) -> None:
    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    draw.rectangle((41, 40, 44, 46), fill=(10, 24, 30, 255))
    draw.rectangle((52, 40, 55, 46), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_nonflat_sprite(path: Path) -> None:
    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    pixels = image.load()
    for y in range(96):
        for x in range(96):
            pixels[x, y] = (255, min(38, x // 4 + y // 5), 255, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_smooth_ramp_sprite(path: Path) -> None:
    image = Image.new("RGBA", (128, 128), (255, 0, 255, 255))
    pixels = image.load()
    for y in range(24, 104):
        for x in range(24, 104):
            if (x - 64) ** 2 + (y - 64) ** 2 <= 40 ** 2:
                shade = int((x - 24) * 120 / 79)
                pixels[x, y] = (40 + shade, 120 + shade // 2, 150 + shade // 3, 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


class CompanionCandidateRejectionReportTests(unittest.TestCase):
    def test_report_records_rejected_candidates_without_mutating_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            run_dir = tmp_path / "run"
            run_dir.mkdir()
            write_manifest(run_dir)
            kept = tmp_path / "kept.png"
            dirty = tmp_path / "dirty.png"
            clean_but_wrong = tmp_path / "clean-but-wrong.png"
            write_flat_sprite(kept)
            write_nonflat_sprite(dirty)
            write_flat_sprite(clean_but_wrong)

            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": str(kept),
                                "source_provenance": "built-in-imagegen",
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            before_jobs = jobs_path.read_text(encoding="utf-8")
            candidates_json = tmp_path / "candidates.json"
            candidates_json.write_text(
                json.dumps(
                    {
                        "notes": "Auditioned after the current row; neither candidate should be recorded.",
                        "candidates": [
                            {
                                "source": str(dirty),
                                "promptStrategy": "preserve story; repair eye grammar and flat key",
                                "visualBlockers": [
                                    "background is visibly non-flat",
                                    "expression reads worried instead of thinking",
                                ],
                            },
                            {
                                "source": str(clean_but_wrong),
                                "promptStrategy": "try simpler thinking performance prompt",
                                "visualBlockers": ["eye grammar drift in the peak frame"],
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            report = candidate_report.build_report(
                run_dir=run_dir,
                job_id="thinking",
                candidates_path=candidates_json,
                built_in_repair_threshold=2,
                allow_synthetic_test_source=True,
            )

            self.assertTrue(report["ok"])
            self.assertEqual(report["jobId"], "thinking")
            self.assertEqual(report["summary"]["candidateCount"], 2)
            self.assertEqual(report["summary"]["rejectedCount"], 2)
            self.assertTrue(report["summary"]["builtInPromptRepairExhaustedForNow"])
            self.assertEqual(report["currentKeptRow"]["sourcePath"], str(kept.resolve()))
            self.assertEqual(report["currentKeptRow"]["decision"], "keep-current-for-now")
            self.assertEqual(report["candidates"][0]["decision"], "reject")
            self.assertFalse(report["candidates"][0]["recorded"])
            self.assertIn("non_uniform_chroma_key_background", report["candidates"][0]["strictBlockingWarningCodes"])
            self.assertEqual(report["candidates"][1]["strictBlockingWarningCodes"], [])
            self.assertIn("eye grammar drift", report["candidates"][1]["visualBlockers"][0])
            self.assertTrue(report["conclusion"]["doNotRecordOrAssembleRejectedCandidates"])
            self.assertIn("Codex app $imagegen", report["conclusion"]["nextRecommendedAction"])
            self.assertEqual(jobs_path.read_text(encoding="utf-8"), before_jobs)

    def test_rejected_candidate_requires_a_reason(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            run_dir = tmp_path / "run"
            run_dir.mkdir()
            write_manifest(run_dir)
            candidate = tmp_path / "clean.png"
            write_flat_sprite(candidate)
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_path": str(candidate),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidates_json = tmp_path / "candidates.json"
            candidates_json.write_text(
                json.dumps({"candidates": [{"source": str(candidate), "visualBlockers": []}]}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "must include at least one visualBlocker or strict source blocker"):
                candidate_report.build_report(
                    run_dir=run_dir,
                    job_id="thinking",
                    candidates_path=candidates_json,
                    allow_synthetic_test_source=True,
                )

    def test_report_preserves_rejected_base_candidate_with_v3_metrics_without_completing_job(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            run_dir = tmp_path / "run"
            run_dir.mkdir()
            write_manifest(run_dir)
            smooth = tmp_path / "smooth-base.png"
            write_smooth_ramp_sprite(smooth)

            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "base",
                                "kind": "base-companion",
                                "status": "pending",
                                "output_path": "generated/base.png",
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            before_jobs = jobs_path.read_text(encoding="utf-8")
            candidates_json = tmp_path / "base-candidates.json"
            candidates_json.write_text(
                json.dumps(
                    {
                        "notes": "Base rejected after strict v3 recording failed.",
                        "candidates": [
                            {
                                "source": str(smooth),
                                "promptStrategy": "flatter indexed native-pixel base",
                                "visualBlockers": ["still reads as smooth/painterly instead of native pixel art"],
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            report = candidate_report.build_report(
                run_dir=run_dir,
                job_id="base",
                candidates_path=candidates_json,
                built_in_repair_threshold=1,
                allow_synthetic_test_source=True,
            )

            self.assertTrue(report["ok"])
            self.assertEqual(report["jobId"], "base")
            self.assertEqual(report["jobKind"], "base-companion")
            self.assertEqual(report["currentKeptSource"]["decision"], "none")
            self.assertEqual(report["candidates"][0]["decision"], "reject")
            self.assertFalse(report["candidates"][0]["recorded"])
            self.assertIn(
                "smooth_gradient_or_painterly_render_risk",
                report["candidates"][0]["sourceStyleAnalysisV3"]["blockingWarningCodes"],
            )
            foreground = report["candidates"][0]["sourceStyleAnalysisV3"]["foreground"]
            self.assertIn("rawUniqueRgbCount", foreground)
            self.assertIn("sameOrSmallDeltaRampRatio", foreground)
            self.assertIn("hardTransitionRatio", foreground)
            self.assertIn("not production-ready yet", report["conclusion"]["nextRecommendedAction"])
            self.assertEqual(jobs_path.read_text(encoding="utf-8"), before_jobs)


if __name__ == "__main__":
    unittest.main()
