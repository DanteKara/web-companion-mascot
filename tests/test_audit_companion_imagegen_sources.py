import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_companion_imagegen_sources.py"

spec = importlib.util.spec_from_file_location("audit_companion_imagegen_sources", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)


def write_flat_row(path: Path) -> None:
    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    draw.rectangle((41, 40, 44, 46), fill=(10, 24, 30, 255))
    draw.rectangle((52, 40, 55, 46), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_nonflat_row(path: Path) -> None:
    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    pixels = image.load()
    for y in range(96):
        for x in range(96):
            pixels[x, y] = (255, min(32, x // 4 + y // 5), 255, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


class AuditCompanionImagegenSourcesTests(unittest.TestCase):
    def test_audits_completed_base_source_without_mutating_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            run_dir = tmp_path / "run"
            run_dir.mkdir()
            dirty = tmp_path / "dirty-base.png"
            write_nonflat_row(dirty)
            jobs = {
                "jobs": [
                    {
                        "id": "base",
                        "kind": "base-companion",
                        "status": "complete",
                        "source_path": str(dirty),
                        "source_provenance": "built-in-imagegen",
                    }
                ]
            }
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
            before = jobs_path.read_text(encoding="utf-8")

            report = audit.audit_sources(run_dir)

            self.assertFalse(report["ok"])
            self.assertEqual(report["summary"]["completedBaseJobs"], 1)
            self.assertEqual(report["summary"]["blockingBaseJobs"], 1)
            self.assertIn("baseJobs", report)
            base = report["baseJobs"][0]
            self.assertEqual(base["id"], "base")
            self.assertIn("non_uniform_chroma_key_background", base["strictBlockingWarningCodes"])
            self.assertEqual(jobs_path.read_text(encoding="utf-8"), before)

    def test_audits_completed_generated_row_sources_without_mutating_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            run_dir = tmp_path / "run"
            run_dir.mkdir()
            clean = tmp_path / "clean.png"
            dirty = tmp_path / "dirty.png"
            write_flat_row(clean)
            write_nonflat_row(dirty)
            jobs = {
                "jobs": [
                    {
                        "id": "thinking",
                        "kind": "row-strip",
                        "status": "complete",
                        "source_path": str(dirty),
                        "source_provenance": "built-in-imagegen",
                    },
                    {
                        "id": "answering",
                        "kind": "row-strip",
                        "status": "complete",
                        "source_path": str(clean),
                        "source_provenance": "built-in-imagegen",
                    },
                    {
                        "id": "base",
                        "kind": "base-companion",
                        "status": "complete",
                        "source_path": str(clean),
                    },
                ]
            }
            jobs_path = run_dir / "imagegen-jobs.json"
            jobs_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
            before = jobs_path.read_text(encoding="utf-8")

            report = audit.audit_sources(run_dir)

            self.assertFalse(report["ok"])
            self.assertEqual(report["summary"]["completedRowJobs"], 2)
            self.assertEqual(report["summary"]["blockingRowJobs"], 1)
            thinking = next(row for row in report["rowJobs"] if row["id"] == "thinking")
            self.assertIn("non_uniform_chroma_key_background", thinking["strictBlockingWarningCodes"])
            answering = next(row for row in report["rowJobs"] if row["id"] == "answering")
            self.assertEqual(answering["strictBlockingWarningCodes"], [])
            self.assertEqual(jobs_path.read_text(encoding="utf-8"), before)

    def test_reports_missing_source_path_as_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            run_dir.mkdir()
            (run_dir / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_provenance": "built-in-imagegen",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = audit.audit_sources(run_dir)

            self.assertFalse(report["ok"])
            self.assertEqual(report["rowJobs"][0]["strictBlockingWarningCodes"], ["missing_source_path"])


if __name__ == "__main__":
    unittest.main()
