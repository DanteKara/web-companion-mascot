import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_companion_manifest.py"

spec = importlib.util.spec_from_file_location("validate_companion_manifest", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def write_manifest(tmp_path: Path, enhancer: dict, style_extra: dict | None = None) -> Path:
    style = {"stateClarity": "semantic-enhancers", "renderingStyle": "codex-pixel-art"}
    if style_extra:
        style.update(style_extra)
    manifest = {
        "id": "fixture",
        "displayName": "Fixture",
        "style": style,
        "atlas": {
            "path": "missing.png",
            "width": 3072,
            "height": 288,
            "columns": 12,
            "rows": 1,
            "cellWidth": 256,
            "cellHeight": 288,
        },
        "states": {
            "working": {
                "row": 0,
                "frames": 12,
                "durations": [120] * 12,
                "loop": True,
                "enhancer": enhancer,
            }
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def write_anatomy_review(tmp_path: Path, review_extra: dict | None = None) -> None:
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir(exist_ok=True)
    checks = {
        "frameByFrameAnatomyReviewed": True,
        "appendageCountStable": True,
        "noExtraAppendages": True,
        "noDuplicatedAppendages": True,
        "identityPropsStable": True,
        "stateCuesNotMisreadAsAnatomy": True,
        "contactAndOverlapBelievable": True,
    }
    review = {
        "status": "pass",
        "productionUse": True,
        "expectedAnatomy": (
            "Stable body core; two original hands/arms anchored at left and right sides; "
            "allowed side lift and small tilt only; no third hand, sleeve, paw, fin, or mitten."
        ),
        "expectedIdentityProps": "Single staff remains one staff on the same side.",
        "statesReviewed": ["working"],
        "reviewedFrames": {"working": list(range(1, 13))},
        "checks": checks,
        "blockers": [],
        "notes": "All used frames were inspected at enlarged size against the source reference.",
    }
    if review_extra:
        for key, value in review_extra.items():
            if key == "checks" and isinstance(value, dict):
                updated_checks = dict(checks)
                updated_checks.update(value)
                review[key] = updated_checks
            else:
                review[key] = value
    (qa_dir / "anatomy-review.json").write_text(json.dumps(review), encoding="utf-8")


def write_state_performance_review(tmp_path: Path, review_extra: dict | None = None) -> None:
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir(exist_ok=True)
    checks = {
        "frameByFrameStateReadReviewed": True,
        "intendedStateReadable": True,
        "noWrongStateRead": True,
        "expressionMatchesState": True,
        "cueMotionMatchesState": True,
        "coherentStateStoryArc": True,
        "mascotActingVariesAcrossFrames": True,
        "noTiredPantingUnlessStateRequiresIt": True,
        "noOffVibeGenericCue": True,
    }
    review = {
        "status": "pass",
        "productionUse": True,
        "statesReviewed": ["working"],
        "reviewedFrames": {"working": list(range(1, 13))},
        "expectedStateReads": {
            "working": "Active work with a concrete target and purposeful progress; not panting, sleeping, or answering.",
        },
        "checks": checks,
        "blockers": [],
        "notes": "All used frames were inspected for state readability, expression, and cue motion.",
    }
    if review_extra:
        for key, value in review_extra.items():
            if key == "checks" and isinstance(value, dict):
                updated_checks = dict(checks)
                updated_checks.update(value)
                review[key] = updated_checks
            else:
                review[key] = value
    (qa_dir / "state-performance-review.json").write_text(json.dumps(review), encoding="utf-8")


def write_eye_grammar_review(tmp_path: Path, review_extra: dict | None = None) -> None:
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir(exist_ok=True)
    checks = {
        "frameByFrameEyeGrammarReviewed": True,
        "eyeCountStable": True,
        "eyeShapeStable": True,
        "eyeFillAndHighlightStable": True,
        "eyePlacementStable": True,
        "noWhiteScleraOrCrescentSwap": True,
        "noMismatchedOrSymbolEyes": True,
        "blinkStyleMatchesSource": True,
    }
    review = {
        "status": "pass",
        "productionUse": True,
        "expectedEyeGrammar": (
            "Two source-matched oval eyes with stable fill, tiny highlights, matched spacing, "
            "and source-style blink lines only."
        ),
        "statesReviewed": ["working"],
        "reviewedFrames": {"working": list(range(1, 13))},
        "checks": checks,
        "blockers": [],
        "notes": "All used frames were inspected at enlarged size against the canonical base eye grammar.",
    }
    if review_extra:
        for key, value in review_extra.items():
            if key == "checks" and isinstance(value, dict):
                updated_checks = dict(checks)
                updated_checks.update(value)
                review[key] = updated_checks
            else:
                review[key] = value
    (qa_dir / "eye-grammar-review.json").write_text(json.dumps(review), encoding="utf-8")


class ManifestValidatorTests(unittest.TestCase):
    def test_validator_uses_manifest_chroma_key_for_halo_detection_without_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas_path = tmp_path / "atlas.png"
            atlas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            atlas.putpixel((16, 16), (0, 255, 0, 255))
            atlas.save(atlas_path)
            manifest = {
                "id": "fixture",
                "displayName": "Fixture",
                "style": {
                    "stateClarity": "pose-only",
                    "renderingStyle": "codex-pixel-art",
                    "chromaKey": {"hex": "#00FF00"},
                },
                "atlas": {
                    "path": "atlas.png",
                    "width": 32,
                    "height": 32,
                    "columns": 1,
                    "rows": 1,
                    "cellWidth": 32,
                    "cellHeight": 32,
                },
                "states": {
                    "idle": {
                        "row": 0,
                        "frames": 1,
                        "durations": [120],
                        "loop": True,
                    }
                },
            }
            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                max_outline_halo_pixels=0,
            )

            self.assertTrue(any("key-colored outline/halo pixels" in error for error in errors))

    def test_validator_uses_request_chroma_key_for_halo_detection_without_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            atlas_path = tmp_path / "atlas.png"
            atlas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            atlas.putpixel((16, 16), (0, 255, 0, 255))
            atlas.save(atlas_path)
            (tmp_path / "companion_request.json").write_text(
                json.dumps({"chromaKey": {"rgb": [0, 255, 0]}}),
                encoding="utf-8",
            )
            manifest = {
                "id": "fixture",
                "displayName": "Fixture",
                "style": {
                    "stateClarity": "pose-only",
                    "renderingStyle": "codex-pixel-art",
                },
                "atlas": {
                    "path": "atlas.png",
                    "width": 32,
                    "height": 32,
                    "columns": 1,
                    "rows": 1,
                    "cellWidth": 32,
                    "cellHeight": 32,
                },
                "states": {
                    "idle": {
                        "row": 0,
                        "frames": 1,
                        "durations": [120],
                        "loop": True,
                    }
                },
            }
            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                max_outline_halo_pixels=0,
            )

            self.assertTrue(any("key-colored outline/halo pixels" in error for error in errors))

    def test_rendering_style_is_required_when_requested(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            del data["style"]["renderingStyle"]
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
                require_rendering_style=True,
            )

            self.assertTrue(any("style.renderingStyle is required" in error for error in errors))

    def test_non_pixel_rendering_style_is_rejected(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(
                Path(raw_tmp),
                enhancer,
                {"anatomyClass": "no-limbs", "renderingStyle": "smooth-illustration"},
            )

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
                require_rendering_style=True,
            )

            self.assertTrue(any("style.renderingStyle must be codex-pixel-art" in error for error in errors))

    def test_art_direction_review_requires_pixel_art_style_check(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "no-limbs"})
            source_reference = tmp_path / "source.png"
            source_reference.write_bytes(b"not-really-an-image")
            qa_dir = tmp_path / "qa"
            qa_dir.mkdir()
            checks = {
                "referenceQualityMaintained": True,
                "identityPreserved": True,
                "eyeGrammarPreserved": True,
                "eyeGrammarStableEveryFrame": True,
                "stylePreserved": True,
                "cleanupReadyFlatChroma": True,
                "creativeStateReadability": True,
                "nativeEnhancers": True,
                "integratedEnhancers": True,
                "anatomyPreserved": True,
                "noExtraAnatomy": True,
                "believableOcclusion": True,
                "noPrototypeFlattening": True,
                "identityCleanupAndAnatomyOverrideStateRead": True,
            }
            (qa_dir / "art-direction-review.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "generationMethod": "imagegen-integrated-row-art",
                        "sourceReference": str(source_reference),
                        "productionUse": True,
                        "checks": checks,
                        "blockers": [],
                        "notes": "Visual review passed.",
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_art_direction_review=True,
            )

            self.assertTrue(any("checks.pixelArtStyle is required" in error for error in errors))

    def test_art_direction_review_requires_theme_native_state_cues_check(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "no-limbs"})
            source_reference = tmp_path / "source.png"
            source_reference.write_bytes(b"not-really-an-image")
            qa_dir = tmp_path / "qa"
            qa_dir.mkdir()
            checks = {
                "referenceQualityMaintained": True,
                "identityPreserved": True,
                "eyeGrammarPreserved": True,
                "eyeGrammarStableEveryFrame": True,
                "stylePreserved": True,
                "pixelArtStyle": True,
                "cleanupReadyFlatChroma": True,
                "creativeStateReadability": True,
                "nativeEnhancers": True,
                "integratedEnhancers": True,
                "anatomyPreserved": True,
                "noExtraAnatomy": True,
                "believableOcclusion": True,
                "noPrototypeFlattening": True,
                "identityCleanupAndAnatomyOverrideStateRead": True,
            }
            (qa_dir / "art-direction-review.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "generationMethod": "imagegen-integrated-row-art",
                        "sourceReference": str(source_reference),
                        "productionUse": True,
                        "checks": checks,
                        "blockers": [],
                        "notes": "Visual review passed.",
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_art_direction_review=True,
            )

            self.assertTrue(any("checks.themeNativeStateCues is required" in error for error in errors))

    def test_art_direction_review_requires_eye_grammar_check(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "no-limbs"})
            source_reference = tmp_path / "source.png"
            source_reference.write_bytes(b"not-really-an-image")
            qa_dir = tmp_path / "qa"
            qa_dir.mkdir()
            checks = {
                "referenceQualityMaintained": True,
                "identityPreserved": True,
                "eyeGrammarStableEveryFrame": True,
                "stylePreserved": True,
                "pixelArtStyle": True,
                "cleanupReadyFlatChroma": True,
                "creativeStateReadability": True,
                "themeNativeStateCues": True,
                "nativeEnhancers": True,
                "integratedEnhancers": True,
                "anatomyPreserved": True,
                "noExtraAnatomy": True,
                "believableOcclusion": True,
                "noPrototypeFlattening": True,
                "identityCleanupAndAnatomyOverrideStateRead": True,
            }
            (qa_dir / "art-direction-review.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "generationMethod": "imagegen-integrated-row-art",
                        "sourceReference": str(source_reference),
                        "productionUse": True,
                        "checks": checks,
                        "blockers": [],
                        "notes": "Visual review passed.",
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_art_direction_review=True,
            )

            self.assertTrue(any("checks.eyeGrammarPreserved is required" in error for error in errors))

    def test_art_direction_review_must_cover_every_used_frame(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "no-limbs"})
            source_reference = tmp_path / "source.png"
            source_reference.write_bytes(b"not-really-an-image")
            qa_dir = tmp_path / "qa"
            qa_dir.mkdir()
            checks = {
                "referenceQualityMaintained": True,
                "identityPreserved": True,
                "eyeGrammarPreserved": True,
                "eyeGrammarStableEveryFrame": True,
                "stylePreserved": True,
                "pixelArtStyle": True,
                "cleanupReadyFlatChroma": True,
                "creativeStateReadability": True,
                "themeNativeStateCues": True,
                "nativeEnhancers": True,
                "integratedEnhancers": True,
                "anatomyPreserved": True,
                "noExtraAnatomy": True,
                "believableOcclusion": True,
                "noPrototypeFlattening": True,
                "identityCleanupAndAnatomyOverrideStateRead": True,
            }
            (qa_dir / "art-direction-review.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "generationMethod": "imagegen-integrated-row-art",
                        "sourceReference": str(source_reference),
                        "productionUse": True,
                        "statesReviewed": ["working"],
                        "reviewedFrames": {"working": [1, 2, 3, 4, 5, 6]},
                        "checks": checks,
                        "blockers": [],
                        "notes": "Visual review passed.",
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_art_direction_review=True,
            )

            self.assertTrue(
                any("qa/art-direction-review.json reviewedFrames.working must include every used frame 1..12" in error for error in errors)
            )

    def test_completed_row_source_style_blockers_fail_validation(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "no-limbs"})
            (tmp_path / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "row_source_style_strict_blocking_warning_codes": [
                                    "non_uniform_chroma_key_background",
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("imagegen job thinking row source style failed: non_uniform_chroma_key_background" in error for error in errors)
            )
            self.assertEqual(
                qa["imagegenRowSourceStyleFailures"],
                [{"job": "thinking", "codes": ["non_uniform_chroma_key_background"]}],
            )

    def test_completed_generated_row_missing_source_style_evidence_fails_audition_validation(self) -> None:
        enhancer = {
            "kind": "thought-bubble",
            "attachment": "near-head",
            "description": "A compact thought puff painted into the row.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            (tmp_path / "imagegen-jobs.json").write_text(
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

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("imagegen job thinking is missing row_source_style_analysis" in error for error in errors)
            )
            self.assertEqual(
                qa["imagegenRowSourceStyleMissingEvidence"],
                [{"job": "thinking", "missing": ["row_source_style_analysis", "row_source_style_strict_blocking_warning_codes"]}],
            )

    def test_completed_artist_row_can_skip_generated_source_style_evidence(self) -> None:
        enhancer = {
            "kind": "thought-bubble",
            "attachment": "near-head",
            "description": "A compact thought puff painted into the row.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            (tmp_path / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "thinking",
                                "kind": "row-strip",
                                "status": "complete",
                                "source_provenance": "artist-provided-integrated-row-art",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertFalse(any("missing row_source_style_analysis" in error for error in errors))
            self.assertNotIn("imagegenRowSourceStyleMissingEvidence", qa)

    def test_completed_base_source_style_blockers_fail_validation(self) -> None:
        enhancer = {
            "kind": "thought-bubble",
            "attachment": "near-head",
            "description": "A compact thought puff painted into the row.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            (tmp_path / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "base",
                                "kind": "base-companion",
                                "status": "complete",
                                "base_style_analysis": {"ok": False},
                                "base_style_strict_blocking_warning_codes": [
                                    "non_uniform_chroma_key_background",
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("imagegen job base base source style failed: non_uniform_chroma_key_background" in error for error in errors)
            )
            self.assertEqual(
                qa["imagegenBaseSourceStyleFailures"],
                [{"job": "base", "codes": ["non_uniform_chroma_key_background"]}],
            )

    def test_completed_base_missing_source_style_evidence_fails_audition_validation(self) -> None:
        enhancer = {
            "kind": "thought-bubble",
            "attachment": "near-head",
            "description": "A compact thought puff painted into the row.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            (tmp_path / "imagegen-jobs.json").write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "base",
                                "kind": "base-companion",
                                "status": "complete",
                                "source_provenance": "built-in-imagegen",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("imagegen job base is missing base_style_analysis" in error for error in errors)
            )
            self.assertEqual(
                qa["imagegenBaseSourceStyleMissingEvidence"],
                [{"job": "base", "missing": ["base_style_analysis", "base_style_strict_blocking_warning_codes"]}],
            )

    def test_visual_language_is_required_when_requested(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_visual_language=True,
            )

            self.assertTrue(any("style.visualLanguage is required" in error for error in errors))
            self.assertTrue(any("enhancer.visualLanguageFit is required" in error for error in errors))

    def test_visual_language_contract_accepts_state_fit_note(self) -> None:
        enhancer = {
            "kind": "frost processing flakes",
            "attachment": "near-head",
            "description": "Small icy data flakes orbit near the head while the mascot focuses.",
            "visualLanguageFit": "Uses Glace-like frost puffs and pale blue crystals instead of generic gears or UI panels.",
        }
        style = {
            "anatomyClass": "fins-no-hands",
            "visualLanguage": {
                "sourceVibe": "soft round icy companion with a simple face and two side fins",
                "motifs": ["frost puffs", "snowflake dots", "pale blue rim"],
                "forbiddenGenericCues": ["gears", "circuit boards", "speech panels"],
                "stateCueRules": {
                    "working": "Use frost/data flakes or a soft processing aura, not generic tech symbols.",
                    "answering": "Use mouth shapes and icy breath puffs, not speech bubbles.",
                },
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, style)

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_visual_language=True,
            )

            self.assertFalse(any("style.visualLanguage" in error for error in errors))
            self.assertFalse(any("enhancer.visualLanguageFit" in error for error in errors))
            self.assertTrue(qa["stateClarity"]["hasVisualLanguage"])

    def test_near_head_overlap_component_policy_is_allowed(self) -> None:
        enhancer = {
            "kind": "partly occluded thought puff",
            "attachment": "near-head",
            "componentPolicy": "overlap-ok",
            "description": "A compact thought puff sits close enough to overlap the top of the hood.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_clarity=True,
            )

            self.assertFalse(any("componentPolicy" in error for error in errors))

    def test_unknown_component_policy_is_rejected(self) -> None:
        enhancer = {
            "kind": "thought puff",
            "attachment": "near-head",
            "componentPolicy": "maybe",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_clarity=True,
            )

            self.assertTrue(any("componentPolicy must be one of" in error for error in errors))

    def test_draft_enhancer_kind_warns_before_production_validation(self) -> None:
        enhancer = {
            "kind": "planned during row generation",
            "attachment": "body-pose",
            "description": "Prompt-planned visual aid that has not been updated after visual selection.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_clarity=True,
            )

            self.assertTrue(any("prompt-planning metadata" in warning for warning in warnings))

    def test_risky_working_prop_requires_anatomy_guard(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held by the mascot.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer)

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("anatomyGuard" in warning for warning in warnings))

    def test_risky_working_prop_accepts_explicit_anatomy_guard(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate braced against the mascot body.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["existing side fins only"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer)

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_fin_mascot_accepts_existing_fin_grip_with_anatomy_guard(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low by the mascot's existing side fins.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["existing side fins only"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("non-grip enhancer" in error for error in errors))
            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_vague_allowed_interactors_warn_for_risky_simple_appendage_prop(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low by the mascot.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["existing visible appendages only"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("allowedInteractors should name exact" in warning for warning in warnings))

    def test_risky_simple_appendage_prop_recommends_anatomy_contract(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low by the mascot's existing side fins.",
            "requiredAffordances": ["grip"],
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left side fin", "right side fin"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("style.anatomyContract" in warning for warning in warnings))

    def test_simple_appendage_enhanced_state_recommends_anatomy_contract(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff while one original fin may lift toward the chin.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left side fin", "right side fin"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("style.anatomyContract" in warning for warning in warnings))

    def test_anatomy_contract_total_appendages_must_match_appendage_counts(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low by the mascot's existing side fins.",
            "requiredAffordances": ["grip"],
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left side fin", "right side fin"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        style = {
            "anatomyClass": "fins-no-hands",
            "anatomyContract": {
                "source": "reference-audit",
                "bodyCore": "round icy body",
                "totalAppendages": 2,
                "appendages": [
                    {"id": "left-fin", "kind": "fin", "count": 1, "placement": "left side"}
                ],
                "forbiddenAdditions": ["extra fins", "hands", "fingers"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, style)

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("style.anatomyContract.totalAppendages" in error for error in errors))

    def test_risky_simple_appendage_prop_accepts_matching_anatomy_contract(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low by the mascot's existing side fins.",
            "requiredAffordances": ["grip"],
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left side fin", "right side fin"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        style = {
            "anatomyClass": "fins-no-hands",
            "anatomyContract": {
                "source": "reference-audit",
                "bodyCore": "round icy body",
                "totalAppendages": 2,
                "appendages": [
                    {
                        "id": "left-fin",
                        "kind": "fin",
                        "count": 1,
                        "placement": "left side",
                        "affordances": ["side-bob", "brace"],
                    },
                    {
                        "id": "right-fin",
                        "kind": "fin",
                        "count": 1,
                        "placement": "right side",
                        "affordances": ["side-bob", "brace"],
                    },
                ],
                "forbiddenAdditions": ["extra fins", "hands", "fingers"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, style)

            _data, errors, warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("style.anatomyContract" in error for error in errors))
            self.assertFalse(any("style.anatomyContract" in warning for warning in warnings))
            self.assertTrue(qa["stateClarity"]["hasAnatomyContract"])

    def test_face_touch_simple_appendage_warns_without_affordance(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff while the left side fin lifts toward the chin.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left side fin", "right side fin"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        style = {
            "anatomyClass": "fins-no-hands",
            "anatomyContract": {
                "source": "reference-audit",
                "bodyCore": "round icy body",
                "totalAppendages": 2,
                "appendages": [
                    {
                        "id": "left-fin",
                        "kind": "fin",
                        "count": 1,
                        "placement": "left side",
                        "affordances": ["side-bob", "small-wave", "tilt"],
                    },
                    {
                        "id": "right-fin",
                        "kind": "fin",
                        "count": 1,
                        "placement": "right side",
                        "affordances": ["side-bob", "small-wave", "tilt"],
                    },
                ],
                "forbiddenAdditions": ["extra fins", "hands", "fingers"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, style)

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("face-touch action" in warning for warning in warnings))

    def test_face_touch_hands_accepts_matching_affordance(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
            "requiredAffordances": ["face-touch"],
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["left hand", "right hand"],
                "forbidden": ["extra hands", "new fingers", "duplicate arms"],
            },
        }
        style = {
            "anatomyClass": "hands",
            "anatomyContract": {
                "source": "reference-audit",
                "bodyCore": "small chibi torso and head",
                "totalAppendages": 2,
                "appendages": [
                    {
                        "id": "left-hand",
                        "kind": "hand",
                        "count": 1,
                        "placement": "left side",
                        "affordances": ["wave", "point", "present", "face-touch", "grip"],
                    },
                    {
                        "id": "right-hand",
                        "kind": "hand",
                        "count": 1,
                        "placement": "right side",
                        "affordances": ["wave", "point", "present", "face-touch", "grip"],
                    },
                ],
                "forbiddenAdditions": ["extra hands", "duplicate arms"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, style)

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("face-touch action" in warning for warning in warnings))

    def test_required_affordance_unknown_term_warns(self) -> None:
        enhancer = {
            "kind": "custom expressive gesture",
            "attachment": "gesture",
            "description": "The mascot performs a special gesture.",
            "requiredAffordances": ["moonwalk"],
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("unknown affordance" in warning for warning in warnings))

    def test_no_limb_mascot_rejects_grip_prop_even_with_anatomy_guard(self) -> None:
        enhancer = {
            "kind": "glowing slate",
            "attachment": "held",
            "description": "A small work slate held low near the mascot.",
            "anatomyGuard": {
                "limbPolicy": "no-new-limbs",
                "allowedInteractors": ["body only"],
                "forbidden": ["extra hands", "new fingers", "duplicate fins"],
            },
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("non-grip enhancer" in error for error in errors))

    def test_no_limb_mascot_accepts_freestanding_resting_work_prop(self) -> None:
        enhancer = {
            "kind": "freestanding work slate",
            "attachment": "freestanding",
            "description": (
                "A small slate, tablet, blank card stack, token tray, chunky work tile, or solid work surface rests beside or in front "
                "of the mascot and animates on its own; not held, not typing, not writing, no grip, no hands, no fingers."
            ),
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("attachment must be one of" in error for error in errors))
            self.assertFalse(any("non-grip enhancer" in error for error in errors))
            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_no_limb_mascot_accepts_body_surface_work_glyph(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "A pulsing icy processing glyph painted on the mascot body surface.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("non-grip enhancer" in error for error in errors))
            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_negated_held_prop_language_does_not_create_anatomy_risk(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "Small processing glyphs painted on the body surface; no held object or tablet.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("non-grip enhancer" in error for error in errors))
            self.assertFalse(any("requiredAffordances" in warning for warning in warnings))
            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_negated_comma_separated_prop_list_does_not_create_anatomy_risk(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "Small processing glyphs painted on the body surface; no held object, tablet, slate, keyboard, paper, or pencil.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("non-grip enhancer" in error for error in errors))
            self.assertFalse(any("requiredAffordances" in warning for warning in warnings))
            self.assertFalse(any("anatomyGuard" in warning for warning in warnings))

    def test_negation_breaker_restores_anatomy_risk_detection(self) -> None:
        enhancer = {
            "kind": "body-surface-processing-glyph",
            "attachment": "attached",
            "description": "No held object, but a tablet appears near the mascot.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("non-grip enhancer" in error for error in errors))

    def test_no_text_visual_cue_is_not_text_dependent(self) -> None:
        enhancer = {
            "kind": "tiny no-text voice cue",
            "attachment": "near-face",
            "description": "Compact visual voice marks anchored close to the face.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("text-dependent" in warning for warning in warnings))

    def test_text_label_enhancer_warns_as_text_dependent(self) -> None:
        enhancer = {
            "kind": "text label",
            "attachment": "near-face",
            "description": "A label near the mascot.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "fins-no-hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("text-dependent" in warning for warning in warnings))

    def test_work_prop_text_like_marks_warn(self) -> None:
        enhancer = {
            "kind": "freestanding work notebook",
            "attachment": "freestanding",
            "description": "A small notebook beside the mascot with ruled notebook lines and tiny pseudo-writing.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("text-like work marks" in warning for warning in warnings))

    def test_work_prop_fine_surface_lines_warn(self) -> None:
        enhancer = {
            "kind": "freestanding work tray",
            "attachment": "freestanding",
            "description": "A small tray beside the mascot with wood-grain lines and parallel grooves.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("text-like work marks" in warning for warning in warnings))

    def test_negated_text_like_work_mark_language_does_not_warn(self) -> None:
        enhancer = {
            "kind": "freestanding work slate",
            "attachment": "freestanding",
            "description": "A small work slate with chunky progress blocks; no writing, no letters, no ruled lines.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("text-like work marks" in warning for warning in warnings))

    def test_audition_profile_allows_single_state_without_idle_warning(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_clarity=True,
            )

            self.assertFalse(any("manifest has no idle state" in warning for warning in warnings))
            self.assertFalse(any("chatbot profile" in warning for warning in warnings))
            self.assertFalse(any("recommends" in warning for warning in warnings))

    def test_chatbot_profile_recommends_eight_frame_baseline(self) -> None:
        enhancer = {
            "kind": "freestanding work slate",
            "attachment": "freestanding",
            "description": "A small work slate rests beside the mascot and animates on its own.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["atlas"]["columns"] = 6
            data["atlas"]["width"] = 1536
            data["states"]["working"]["frames"] = 6
            data["states"]["working"]["durations"] = [120] * 6
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertTrue(any("recommends 8+" in warning for warning in warnings))

    def test_chatbot_profile_does_not_require_optional_working_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest = {
                "id": "fixture",
                "displayName": "Fixture",
                "style": {
                    "stateClarity": "semantic-enhancers",
                    "renderingStyle": "codex-pixel-art",
                },
                "atlas": {
                    "path": "missing.png",
                    "width": 2048,
                    "height": 1600,
                    "columns": 8,
                    "rows": 5,
                    "cellWidth": 256,
                    "cellHeight": 320,
                },
                "states": {
                    "idle": {"row": 0, "frames": 8, "durations": [120] * 8, "loop": True},
                    "thinking": {"row": 1, "frames": 8, "durations": [120] * 8, "loop": True},
                    "answering": {"row": 2, "frames": 8, "durations": [120] * 8, "loop": True},
                    "success": {"row": 3, "frames": 8, "durations": [120] * 8, "loop": True},
                    "error": {"row": 4, "frames": 8, "durations": [120] * 8, "loop": True},
                },
            }
            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
                require_state_clarity=True,
            )

            self.assertFalse(any("missing core state: working" in warning for warning in warnings))

    def test_exact_present_affordance_does_not_canonicalize_to_point(self) -> None:
        self.assertEqual(validator.canonical_affordance_group("present"), "present")
        self.assertEqual(validator.canonical_affordance_group("point"), "point")

    def test_require_anatomy_review_warns_when_missing(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_anatomy_review=True,
            )

            self.assertTrue(any("qa/anatomy-review.json is missing or unreadable" in warning for warning in warnings))

    def test_audition_high_visibility_visible_appendage_state_warns_when_anatomy_review_is_missing(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head while existing hands make a small side gesture.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["states"]["thinking"] = data["states"].pop("working")
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("high-visibility state thinking is missing qa/anatomy-review.json" in warning for warning in warnings)
            )

    def test_audition_high_visibility_no_limb_state_does_not_warn_for_missing_anatomy_review_by_default(self) -> None:
        enhancer = {
            "kind": "body-surface thought shimmer",
            "attachment": "attached",
            "description": "A small body-surface processing cue with no appendage acting.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "no-limbs"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["states"]["thinking"] = data["states"].pop("working")
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertFalse(
                any("high-visibility state thinking is missing qa/anatomy-review.json" in warning for warning in warnings)
            )

    def test_anatomy_review_requires_frame_by_frame_check(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_anatomy_review(tmp_path, {"checks": {"frameByFrameAnatomyReviewed": False}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_anatomy_review=True,
            )

            self.assertTrue(any("checks.frameByFrameAnatomyReviewed must be true" in error for error in errors))

    def test_anatomy_review_requires_every_used_frame(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_anatomy_review(tmp_path, {"reviewedFrames": {"working": [1, 2, 3, 4, 7, 8, 9, 10, 11, 12]}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_anatomy_review=True,
            )

            self.assertTrue(
                any("reviewedFrames.working must include every used frame 1..12" in error for error in errors)
            )

    def test_anatomy_review_requires_specific_source_anatomy_details(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_anatomy_review(tmp_path, {"expectedAnatomy": "Anatomy looks good."})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_anatomy_review=True,
            )

            self.assertTrue(
                any(
                    "qa/anatomy-review.json expectedAnatomy must describe body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy"
                    in error
                    for error in errors
                )
            )

    def test_anatomy_review_passes_when_all_state_frames_are_reviewed(self) -> None:
        enhancer = {
            "kind": "hand-to-chin thought gesture",
            "attachment": "gesture",
            "description": "The left hand touches the chin while a small thought cue appears near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_anatomy_review(tmp_path)

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_anatomy_review=True,
            )

            self.assertFalse(any("qa/anatomy-review.json" in error for error in errors))
            self.assertEqual(qa["anatomyReview"]["status"], "pass")

    def test_require_state_performance_review_warns_when_missing(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json is missing or unreadable" in warning for warning in warnings)
            )

    def test_state_performance_review_requires_no_wrong_state_read_check(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path, {"checks": {"noWrongStateRead": False}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json checks.noWrongStateRead must be true" in error for error in errors)
            )

    def test_state_performance_review_requires_coherent_story_arc_check(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path, {"checks": {"coherentStateStoryArc": False}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json checks.coherentStateStoryArc must be true" in error for error in errors)
            )

    def test_state_performance_review_requires_mascot_acting_variation_check(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path, {"checks": {"mascotActingVariesAcrossFrames": False}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json checks.mascotActingVariesAcrossFrames must be true" in error for error in errors)
            )

    def test_audition_high_visibility_state_warns_when_state_performance_review_is_missing(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["states"]["thinking"] = data["states"].pop("working")
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("high-visibility state thinking is missing qa/state-performance-review.json" in warning for warning in warnings)
            )

    def test_state_performance_review_requires_every_used_frame(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path, {"reviewedFrames": {"working": [1, 2, 3, 6, 7, 8, 9, 10, 11, 12]}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json reviewedFrames.working must include every used frame 1..12" in error for error in errors)
            )

    def test_state_performance_review_requires_expected_state_read(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path, {"expectedStateReads": {}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertTrue(
                any("qa/state-performance-review.json expectedStateReads.working must be a non-empty string" in error for error in errors)
            )

    def test_state_performance_review_passes_when_all_state_frames_are_reviewed(self) -> None:
        enhancer = {
            "kind": "staff-tip work motes",
            "attachment": "near-hand",
            "description": "A small work target changes near the staff tip while the mascot focuses.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_state_performance_review(tmp_path)

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_state_performance_review=True,
            )

            self.assertFalse(any("qa/state-performance-review.json" in error for error in errors))
            self.assertEqual(qa["statePerformanceReview"]["status"], "pass")

    def test_require_eye_grammar_review_warns_when_missing(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertTrue(any("qa/eye-grammar-review.json is missing or unreadable" in warning for warning in warnings))

    def test_chatbot_high_visibility_state_warns_when_eye_grammar_review_is_missing(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["states"]["thinking"] = data["states"].pop("working")
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="chatbot",
            )

            self.assertTrue(
                any("high-visibility state thinking is missing qa/eye-grammar-review.json" in warning for warning in warnings)
            )

    def test_audition_high_visibility_state_warns_when_eye_grammar_review_is_missing(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            manifest_path = write_manifest(Path(raw_tmp), enhancer, {"anatomyClass": "hands"})
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["states"]["thinking"] = data["states"].pop("working")
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            _data, _errors, warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
            )

            self.assertTrue(
                any("high-visibility state thinking is missing qa/eye-grammar-review.json" in warning for warning in warnings)
            )

    def test_eye_grammar_review_requires_no_white_sclera_swap_check(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_eye_grammar_review(tmp_path, {"checks": {"noWhiteScleraOrCrescentSwap": False}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertTrue(
                any("qa/eye-grammar-review.json checks.noWhiteScleraOrCrescentSwap must be true" in error for error in errors)
            )

    def test_eye_grammar_review_requires_expected_eye_grammar(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_eye_grammar_review(tmp_path, {"expectedEyeGrammar": ""})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertTrue(any("qa/eye-grammar-review.json expectedEyeGrammar must be a non-empty string" in error for error in errors))

    def test_eye_grammar_review_requires_specific_source_eye_details(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_eye_grammar_review(tmp_path, {"expectedEyeGrammar": "Source eyes look good."})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertTrue(
                any(
                    "qa/eye-grammar-review.json expectedEyeGrammar must describe eye count/shape, fill or pupil color, highlight/catchlight logic, spacing/placement, and blink style"
                    in error
                    for error in errors
                )
            )

    def test_eye_grammar_review_requires_every_used_frame(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_eye_grammar_review(tmp_path, {"reviewedFrames": {"working": [1, 2, 3, 4, 7, 8, 9, 10, 11, 12]}})

            _data, errors, _warnings, _qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertTrue(
                any("qa/eye-grammar-review.json reviewedFrames.working must include every used frame 1..12" in error for error in errors)
            )

    def test_eye_grammar_review_passes_when_all_state_frames_are_reviewed(self) -> None:
        enhancer = {
            "kind": "side-origin thought puff",
            "attachment": "near-head",
            "description": "A compact thought puff near the head.",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            manifest_path = write_manifest(tmp_path, enhancer, {"anatomyClass": "hands"})
            write_eye_grammar_review(tmp_path)

            _data, errors, _warnings, qa = validator.validate_manifest(
                manifest_path,
                profile="audition",
                require_eye_grammar_review=True,
            )

            self.assertFalse(any("qa/eye-grammar-review.json" in error for error in errors))
            self.assertEqual(qa["eyeGrammarReview"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
