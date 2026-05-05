import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_companion_manifest.py"

spec = importlib.util.spec_from_file_location("validate_companion_manifest", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def write_manifest(tmp_path: Path, enhancer: dict, style_extra: dict | None = None) -> Path:
    style = {"stateClarity": "semantic-enhancers"}
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


class ManifestValidatorTests(unittest.TestCase):
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
                    {"id": "left-fin", "kind": "fin", "count": 1, "placement": "left side"},
                    {"id": "right-fin", "kind": "fin", "count": 1, "placement": "right side"},
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


if __name__ == "__main__":
    unittest.main()
