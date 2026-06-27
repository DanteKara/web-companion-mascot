import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]

README_REFERENCED_PATHS = [
    "scripts/prepare_production_companion_run.py",
    "scripts/approve_companion_identity.py",
    "scripts/record_companion_imagegen_result_v3.py",
    "scripts/create_canonical_base_review.py",
    "scripts/audit_companion_imagegen_sources_v3.py",
    "scripts/analyze_companion_quality_v3.py",
    "scripts/create_companion_review_bundle.py",
    "scripts/validate_production_contract_v3.py",
    "scripts/create_companion_production_readiness_report_v3.py",
    "references/quality-pipeline-v3.md",
]


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_v3_modules():
    return {
        "prepare_v3": load_module("prepare_production_companion_run", "scripts/prepare_production_companion_run.py"),
        "approve": load_module("approve_companion_identity", "scripts/approve_companion_identity.py"),
        "base_review": load_module("create_canonical_base_review", "scripts/create_canonical_base_review.py"),
        "record_v3": load_module("record_companion_imagegen_result_v3", "scripts/record_companion_imagegen_result_v3.py"),
        "audit_v3": load_module("audit_companion_imagegen_sources_v3", "scripts/audit_companion_imagegen_sources_v3.py"),
        "quality_v3": load_module("analyze_companion_quality_v3", "scripts/analyze_companion_quality_v3.py"),
        "review_bundle": load_module("create_companion_review_bundle", "scripts/create_companion_review_bundle.py"),
        "contract_v3": load_module("validate_production_contract_v3", "scripts/validate_production_contract_v3.py"),
        "readiness_v3": load_module(
            "create_companion_production_readiness_report_v3",
            "scripts/create_companion_production_readiness_report_v3.py",
        ),
        "helpers": load_module("quality_pipeline_v3", "scripts/quality_pipeline_v3.py"),
    }


def write_native_sprite(path: Path, *, chroma=(255, 0, 255, 255), transparent=False, frames: int = 1) -> None:
    width = 96 * frames
    image = Image.new("RGBA", (width, 96), (0, 0, 0, 0) if transparent else chroma)
    draw = ImageDraw.Draw(image)
    for frame in range(frames):
        ox = frame * 96
        draw.rectangle((ox + 28, 20, ox + 68, 72), fill=(16, 24, 40, 255))
        draw.rectangle((ox + 32, 24, ox + 64, 68), fill=(46, 168, 176, 255))
        draw.rectangle((ox + 34, 30, ox + 62, 52), fill=(244, 220, 150, 255))
        draw.rectangle((ox + 40, 38, ox + 44, 45), fill=(5, 12, 20, 255))
        draw.rectangle((ox + 52, 38, ox + 56, 45), fill=(5, 12, 20, 255))
        draw.rectangle((ox + 41, 39, ox + 42, 40), fill=(255, 255, 255, 255))
        draw.rectangle((ox + 53, 39, ox + 54, 40), fill=(255, 255, 255, 255))
        draw.rectangle((ox + 39, 58, ox + 58, 64), fill=(36, 128, 140, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_high_color_flat_sprite(path: Path, *, chroma=(255, 0, 255, 255)) -> None:
    image = Image.new("RGBA", (96, 96), chroma)
    pixels = image.load()
    for y in range(20, 72):
        for x in range(28, 68):
            if (x - 48) ** 2 + (y - 46) ** 2 <= 24 ** 2:
                pixels[x, y] = ((x * 17 + y * 11) % 256, (x * 7 + y * 13) % 256, (x * 5 + y * 3) % 256, 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_smooth_ramp_sprite(path: Path, *, chroma=(255, 0, 255, 255)) -> None:
    image = Image.new("RGBA", (128, 128), chroma)
    pixels = image.load()
    for y in range(24, 104):
        for x in range(24, 104):
            if (x - 64) ** 2 + (y - 64) ** 2 <= 40 ** 2:
                shade = int((x - 24) * 120 / 79)
                pixels[x, y] = (40 + shade, 120 + shade // 2, 150 + shade // 3, 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_identity(path: Path, states: list[str], allowances: dict | None = None) -> None:
    identity = {
        "schemaVersion": 3,
        "status": "approved",
        "pixelArtProfile": "16-bit-console",
        "sourceVibe": "stern tiny console sprite companion",
        "speciesOrForm": "single teal console robot",
        "bodyCore": "rounded rectangular teal body with cream face panel",
        "speciesAnchors": ["teal body", "cream face panel", "two dark oval eyes"],
        "silhouetteAnchors": ["single compact body", "small antenna", "two mitten hands"],
        "proportionRules": ["head/body stays compact", "face panel remains centered"],
        "faceGrammar": ["two dark oval eyes", "tiny blocked white highlights"],
        "paletteRoles": [
            {"role": "outline", "color": "#101828"},
            {"role": "body", "color": "#2EA8B0"},
            {"role": "face", "color": "#F4DC96"},
        ],
        "appendages": [
            {
                "id": "hands",
                "kind": "mitten hands",
                "count": 2,
                "placement": "left and right sides",
                "affordances": ["small side bob"],
            }
        ],
        "forbiddenMutations": ["extra limbs", "glossy render", "white crescent eyes"],
        "personalityTraits": ["stern", "focused", "precise"],
        "motionVocabulary": ["blink", "tiny bob", "prop pulse"],
        "stateCueRules": {
            state: {"attachment": "body-pose", "componentPolicy": "separate", "approvedAllowances": []}
            for state in states
        },
        "qualityProfile": {"profile": "production-v3", "stateAllowances": allowances or {}},
    }
    path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")


class QualityPipelineV3Tests(unittest.TestCase):
    def test_readme_references_exist_as_real_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        missing = [path for path in README_REFERENCED_PATHS if path in readme and not (ROOT / path).exists()]
        self.assertEqual(missing, [])

    def test_prepare_v3_creates_character_bible_and_locked_metadata(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            result = modules["prepare_v3"].main(
                [
                    "--companion-name",
                    "Vela",
                    "--output-dir",
                    str(run_dir),
                    "--states",
                    "thinking,success",
                    "--quiet",
                ]
            )
            self.assertEqual(result, 0)
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            jobs = json.loads((run_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["qualityPipelineVersion"], 3)
            self.assertEqual(manifest["style"]["pixelArtProfile"], "16-bit-console")
            self.assertEqual(manifest["style"]["qualityProfile"], "production-v3")
            self.assertEqual(manifest["style"]["qualityProfileV3"]["profile"], "production-v3")
            self.assertTrue((run_dir / "references" / "character-bible.json").exists())
            self.assertTrue((run_dir / "references" / "qa-profiles-v3.json").exists())
            self.assertIn("native 16-bit console sprite art", (run_dir / "prompts" / "base.md").read_text(encoding="utf-8"))
            for job in jobs["jobs"]:
                required = job["quality_gates"]["requires"]
                self.assertIn("approved_identity_contract", required)
                if job["id"] != "base":
                    self.assertIn("current_canonical_base_review", required)

    def test_approve_identity_refuses_after_any_job_complete_and_then_approves_hash_bindings(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            modules["prepare_v3"].main(
                ["--companion-name", "Vela", "--output-dir", str(run_dir), "--states", "thinking", "--quiet"]
            )
            states = ["thinking"]
            identity_path = Path(raw_tmp) / "identity.json"
            write_identity(identity_path, states)

            jobs_path = run_dir / "imagegen-jobs.json"
            jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
            jobs["jobs"][0]["status"] = "complete"
            jobs_path.write_text(json.dumps(jobs, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "already complete"):
                modules["approve"].approve_identity(run_dir / "manifest.json", from_json=identity_path)

            jobs["jobs"][0]["status"] = "pending"
            jobs_path.write_text(json.dumps(jobs, indent=2) + "\n", encoding="utf-8")
            result = modules["approve"].approve_identity(run_dir / "manifest.json", from_json=identity_path)
            self.assertTrue(result["ok"])

            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            approved = json.loads((run_dir / "references" / "character-bible.json").read_text(encoding="utf-8"))
            jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
            identity_sha = manifest["style"]["identityContract"]["sha256"]
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(jobs["quality_gate_bindings"]["identityContractSha256"], identity_sha)
            self.assertEqual(jobs["jobs"][0]["quality_gate_bindings"]["identityContractSha256"], identity_sha)

    def test_record_v3_refuses_row_before_base_review_then_base_review_updates_bindings(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            run_dir = root / "run"
            source_dir = root / "source"
            base = source_dir / "base.png"
            row = source_dir / "thinking.png"
            write_native_sprite(base)
            write_native_sprite(row)
            modules["prepare_v3"].main(
                ["--companion-name", "Vela", "--output-dir", str(run_dir), "--states", "thinking", "--quiet"]
            )
            identity_path = root / "identity.json"
            write_identity(identity_path, ["thinking"])
            modules["approve"].approve_identity(run_dir / "manifest.json", from_json=identity_path)
            modules["record_v3"].record_result_v3(
                run_dir=run_dir,
                job_id="base",
                source=base,
                source_provenance="user-provided-integrated-row-art",
                force=False,
                allow_synthetic_test_source=False,
                strict_base_style=True,
            )

            with self.assertRaisesRegex(SystemExit, "canonical base review"):
                modules["record_v3"].record_result_v3(
                    run_dir=run_dir,
                    job_id="thinking",
                    source=row,
                    source_provenance="user-provided-integrated-row-art",
                    force=False,
                    allow_synthetic_test_source=False,
                    strict_row_style=True,
                )

            modules["base_review"].create_review(
                manifest_path=run_dir / "manifest.json",
                candidates=[base, row],
                status="pass",
                production_use=True,
                checks={name: True for name in modules["base_review"].REQUIRED_CHECKS},
                observations={name: "specific reviewed evidence" for name in modules["base_review"].REQUIRED_OBSERVATIONS},
                notes="Base chosen after comparing two native sprite candidates.",
            )
            jobs = json.loads((run_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            thinking = next(job for job in jobs["jobs"] if job["id"] == "thinking")
            self.assertIn("canonicalBaseReviewSha256", thinking["quality_gate_bindings"])

    def test_record_v3_rejects_foreground_quantization_disguised_as_chroma_cleanup(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            original = root / "original.png"
            cleaned = root / "cleaned.png"
            write_native_sprite(original)
            with Image.open(original) as image:
                changed = image.convert("RGBA")
            pixels = changed.load()
            for y in range(changed.height):
                for x in range(changed.width):
                    r, g, b, a = pixels[x, y]
                    if a and (r, g, b) != (255, 0, 255):
                        pixels[x, y] = (r // 32 * 32, g // 32 * 32, b // 32 * 32, a)
            changed.save(cleaned)

            result = modules["helpers"].verify_background_only_cleanup(original, cleaned, (255, 0, 255))
            self.assertFalse(result["ok"])
            self.assertIn("cleanup_changed_foreground_palette", result["blockingWarningCodes"])

    def test_source_style_v3_advises_on_high_raw_rgb_but_blocks_smooth_ramp(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            noisy = root / "flat-high-color.png"
            smooth = root / "smooth.png"
            write_high_color_flat_sprite(noisy)
            write_smooth_ramp_sprite(smooth)

            noisy_result = modules["helpers"].analyze_source_style(noisy, (255, 0, 255))
            smooth_result = modules["helpers"].analyze_source_style(smooth, (255, 0, 255))

            self.assertEqual(noisy_result["blockingWarningCodes"], [])
            self.assertGreater(noisy_result["foreground"]["rawUniqueRgbCount"], 64)
            self.assertIn("high_raw_unique_rgb_count", noisy_result["advisoryWarningCodes"])
            self.assertIn("smooth_gradient_or_painterly_render_risk", smooth_result["blockingWarningCodes"])

    def test_analyze_quality_v3_exposes_no_production_threshold_override_flags(self) -> None:
        module = load_module("analyze_companion_quality_v3", "scripts/analyze_companion_quality_v3.py")
        parser = module.build_parser()
        actions = {option for action in parser._actions for option in action.option_strings}
        self.assertIn("--profile", actions)
        self.assertNotIn("--max-core-scale-range-ratio", actions)
        self.assertNotIn("--max-body-jump-ratio", actions)

    def test_review_bundle_requires_per_frame_observations_and_generates_compat_reviews(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            (run_dir / "frames" / "thinking").mkdir(parents=True)
            frame = run_dir / "frames" / "thinking" / "000.png"
            write_native_sprite(frame)
            (run_dir / "qa").mkdir(parents=True)
            for artifact in (
                "contact-sheet.png",
                "cutout-check.png",
                "state-readability-check.png",
                "semantic-anchor-check.png",
                "motion-quality-check.png",
            ):
                (run_dir / "qa" / artifact).write_bytes(artifact.encode("utf-8"))
            (run_dir / "atlas.png").write_bytes(b"atlas")
            manifest = {
                "atlas": {"path": "atlas.png"},
                "states": {"thinking": {"frames": 1, "row": 0}},
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            template_path = run_dir / "qa" / "review-template.json"
            template = modules["review_bundle"].write_template(run_dir / "manifest.json", template_path)
            bad = run_dir / "qa" / "bad-observations.json"
            bad.write_text(json.dumps({"observations": []}), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "missing observation"):
                modules["review_bundle"].consume_observations(run_dir / "manifest.json", bad)

            observations = template
            for item in observations["observations"]:
                for key in modules["review_bundle"].RESULT_FIELDS:
                    item[key] = "pass"
                item["notes"] = "Frame keeps identity, anatomy, cue, eye grammar, and native pixel-art read."
            good = run_dir / "qa" / "good-observations.json"
            good.write_text(json.dumps(observations), encoding="utf-8")
            result = modules["review_bundle"].consume_observations(run_dir / "manifest.json", good)
            self.assertTrue(result["ok"])
            evidence = json.loads((run_dir / "qa" / "review-evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(len(evidence["observations"]), 1)
            for filename in (
                "anatomy-review.json",
                "state-performance-review.json",
                "eye-grammar-review.json",
                "art-direction-review.json",
            ):
                review = json.loads((run_dir / "qa" / filename).read_text(encoding="utf-8"))
                self.assertEqual(review["evidenceSource"], "qa/review-evidence.json")
                self.assertTrue(review["checks"])

    def test_validate_contract_rejects_post_hoc_component_policy_changes(self) -> None:
        modules = load_v3_modules()
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "run"
            modules["prepare_v3"].main(
                ["--companion-name", "Vela", "--output-dir", str(run_dir), "--states", "thinking", "--quiet"]
            )
            identity_path = Path(raw_tmp) / "identity.json"
            write_identity(identity_path, ["thinking"])
            modules["approve"].approve_identity(run_dir / "manifest.json", from_json=identity_path)
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            manifest["states"]["thinking"]["enhancer"]["componentPolicy"] = "overlap-ok"
            (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            report = modules["contract_v3"].validate_contract(run_dir / "manifest.json")
            self.assertFalse(report["ok"])
            self.assertTrue(any("componentPolicy" in blocker for blocker in report["blockers"]))

    def test_readiness_report_statuses(self) -> None:
        module = load_module(
            "create_companion_production_readiness_report_v3",
            "scripts/create_companion_production_readiness_report_v3.py",
        )
        no = module.build_readiness({"ok": False, "blockers": ["missing audit"], "approvedExceptions": []})
        with_ex = module.build_readiness({"ok": True, "blockers": [], "approvedExceptions": ["curled-pose-compression"]})
        ready = module.build_readiness({"ok": True, "blockers": [], "approvedExceptions": []})

        self.assertEqual(no["status"], "notProductionReady")
        self.assertEqual(with_ex["status"], "productionReadyWithApprovedExceptions")
        self.assertEqual(ready["status"], "productionReady")


if __name__ == "__main__":
    unittest.main()
