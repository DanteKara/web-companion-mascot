import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillDocumentTests(unittest.TestCase):
    def test_scope_resolver_prevents_full_mascot_static_image_confusion(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")

        self.assertIn("## Scope Resolver", text)
        self.assertIn("full mascot", text)
        self.assertIn("ready mascot", text)
        self.assertIn("make me a full mascot 16-bit pixel art from this reference", text)
        self.assertIn("make me a React chatbot companion from this character", text)
        self.assertIn("dog, robot, logo, plush, animal, object, character, avatar", text)
        self.assertIn("Full body", text)
        self.assertIn("does not narrow scope to a single static image", text)
        self.assertIn("full-body mascot image only", text)
        self.assertIn("explicitly narrows scope", text)
        self.assertIn("Incorrect: generate one full-body transparent PNG and call it done", text)
        self.assertIn('`readyJobs: ["base"]`', text)
        self.assertIn("only an internal stage", text)
        self.assertIn("mascot from this reference", workflow_text)
        self.assertIn("full mascot 16-bit pixel art from this reference", workflow_text)

    def test_prototype_escape_hatch_never_weakens_default_production_route(self) -> None:
        top_level_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        combined = top_level_text + "\n" + workflow_text

        self.assertIn("Prototype Escape Hatch", combined)
        self.assertIn("not production-v3 validated", combined)
        self.assertIn("production-v3 path is blocked", combined)
        self.assertIn("Never default to this path", combined)
        self.assertIn("explicitly chooses", combined)
        self.assertIn("does not satisfy production acceptance criteria", combined)
        self.assertIn("productionReady: true", combined)
        self.assertIn("Do not use prototype mode to bypass", combined)

    def test_public_skill_files_do_not_embed_local_windows_paths(self) -> None:
        forbidden = "C:" + "\\Users"
        checked_paths = [ROOT / "SKILL.md"]
        checked_paths.extend((ROOT / "references").glob("*.md"))
        checked_paths.extend((ROOT / "scripts").glob("*.py"))
        checked_paths.extend((ROOT / "tests").glob("*.py"))

        for path in checked_paths:
            self.assertNotIn(forbidden, path.read_text(encoding="utf-8-sig"), str(path.relative_to(ROOT)))

    def test_normal_production_docs_use_v3_command_path(self) -> None:
        docs = [
            ROOT / "SKILL.md",
            ROOT / "README.md",
            ROOT / "references" / "production-workflow.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
            ROOT / "references" / "quality-pipeline-v3.md",
        ]
        forbidden = {
            "scripts/prepare_companion_run.py": "scripts/prepare_production_companion_run.py",
            "scripts/record_companion_imagegen_result.py": "scripts/record_companion_imagegen_result_v3.py",
            "scripts/audit_companion_imagegen_sources.py": "scripts/audit_companion_imagegen_sources_v3.py",
            "smooth_or_overdetailed_foreground_palette": "smooth_gradient_or_painterly_render_risk",
        }

        for path in docs:
            text = path.read_text(encoding="utf-8-sig")
            for old, new in forbidden.items():
                self.assertNotIn(old, text, f"{path.name} should use {new} in production-v3 docs")

    def test_character_bible_example_documents_v3_identity_schema(self) -> None:
        example_path = ROOT / "references" / "character-bible.example.json"
        self.assertTrue(example_path.exists())
        data = json.loads(example_path.read_text(encoding="utf-8"))

        self.assertEqual(data["schemaVersion"], 3)
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["pixelArtProfile"], "16-bit-console")
        for key in (
            "sourceVibe",
            "speciesOrForm",
            "bodyCore",
            "speciesAnchors",
            "silhouetteAnchors",
            "proportionRules",
            "faceGrammar",
            "paletteRoles",
            "appendages",
            "forbiddenMutations",
            "personalityTraits",
            "motionVocabulary",
            "stateCueRules",
            "qualityProfile",
        ):
            self.assertIn(key, data)
        self.assertTrue(all(isinstance(item, dict) and {"role", "color"} <= set(item) for item in data["paletteRoles"]))
        self.assertTrue(
            all({"id", "kind", "count", "placement", "affordances"} <= set(item) for item in data["appendages"])
        )
        for state in (
            "idle",
            "hover",
            "dragging",
            "greeting",
            "listening",
            "thinking",
            "answering",
            "success",
            "error",
            "sleeping",
        ):
            self.assertIn(state, data["stateCueRules"])
        self.assertEqual(data["qualityProfile"], {"profile": "production-v3", "stateAllowances": {}})

    def test_top_level_skill_stays_compact_and_routes_to_references(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")

        self.assertLess(len(text.encode("utf-8")), 20000)
        self.assertIn("## Reference Routing", text)
        self.assertIn("references/production-workflow.md", text)
        self.assertIn("full production workflow", text)
        self.assertIn("references/companion-contract.md", text)
        self.assertIn("references/state-enhancers.md", text)
        self.assertIn("references/react-integration.md", text)
        self.assertIn("Use `$imagegen` for all production visual generation.", text)
        self.assertNotIn("## Generation Delegation", text)

    def test_skill_uses_hatchpet_style_workflow_sections(self) -> None:
        text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")

        expected_order = [
            "## Overview",
            "## Generation Delegation",
            "## Output Model",
            "## Scope And Completion Gate",
            "## Recordable Source Preflight",
            "## Prompt Boundary",
            "## Codex Pixel Companion Style",
            "## Transparency And Effects",
            "## Default Workflow",
            "## Subagent Row Generation",
            "## Repair Workflow",
            "## Secondary Image Generation Fallback",
            "## Visual Rules",
            "## React Integration",
            "## Scripts",
            "## Rules",
            "## Acceptance Criteria",
        ]
        positions = [text.index(heading) for heading in expected_order]

        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("## Generation Workflow", text)
        self.assertIn("Use `$imagegen` for all normal visual generation.", text)
        self.assertIn("Only the base job may be prompt-only", text)
        self.assertIn("The parent agent must own manifest writes, result recording, atlas assembly, QA, validation, and packaging.", text)
        self.assertIn("Return only:", text)
        self.assertIn("selected_source=/absolute/path/to/codex-app-imagegen/ig_*.png", text)
        self.assertIn("selected_source_metadata=/absolute/path/to/codex-app-imagegen/ig_*.png.codex-imagegen.json", text)
        self.assertIn("No silent sequential fallback", text)

    def test_skill_blocks_base_only_completion_for_normal_react_companion_requests(self) -> None:
        top_level_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")

        self.assertIn("sprite sheets", top_level_text)
        self.assertIn("Base-only or single-image outputs are incomplete", top_level_text)
        self.assertIn("full companion package", top_level_text)
        self.assertIn("## Scope And Completion Gate", workflow_text)
        self.assertIn("normal React/chatbot companion request means a full companion package", workflow_text)
        self.assertIn("do not stop after the canonical base", workflow_text)
        self.assertIn("base-only or single-image output as a concept/audition", workflow_text)
        self.assertIn("Base-only or single-image deliverables are incomplete", contract_text)
        self.assertIn("atlas and React assets", contract_text)

    def test_skill_documents_hover_and_dragging_interactions(self) -> None:
        top_level_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        react_text = (ROOT / "references" / "react-integration.md").read_text(encoding="utf-8")

        self.assertIn("hover, dragging", top_level_text)
        self.assertIn("include `hover` and `dragging` row prompts", workflow_text)
        self.assertIn("| hover | 8 | Pointer hover over the mascot |", contract_text)
        self.assertIn("| dragging | 8 | User is dragging the mascot around the app |", contract_text)
        self.assertIn("Pointer Interaction Priority", react_text)
        self.assertIn("Do not require a separate `dropped` row", react_text)
        self.assertIn("draggable?: boolean", react_text)
        self.assertIn("unclear input", contract_text)
        self.assertIn("Add `working` or `confused` only when the user explicitly asks", contract_text)
        self.assertIn('case "unclear":', react_text)
        self.assertIn('return "error";', react_text)

    def test_skill_has_codex_app_imagegen_capture_preflight(self) -> None:
        top_level_text = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")

        self.assertIn("Codex app image capture preflight", top_level_text)
        self.assertIn("capture_codex_app_imagegen_result.py", top_level_text)
        self.assertIn("## Recordable Source Preflight", workflow_text)
        self.assertIn("## Codex App Image Capture", workflow_text)
        self.assertIn("before treating any generated image as production source", workflow_text)
        self.assertIn("capture_codex_app_imagegen_result.py", workflow_text)
        self.assertIn("codex-app-imagegen", workflow_text)
        self.assertIn("image_generation_call", workflow_text)
        self.assertIn("Do not screenshot", workflow_text)
        self.assertIn("Recordable-source evidence", contract_text)
        self.assertIn("codex-app-imagegen", contract_text)
        self.assertIn("capture_codex_app_imagegen_result.py", contract_text)

    def test_user_facing_skill_docs_do_not_require_local_api_key(self) -> None:
        forbidden_api_key = "OPENAI" + "_API_KEY"
        paths = [
            ROOT / "SKILL.md",
            ROOT / "references" / "production-workflow.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
        ]

        for path in paths:
            text = path.read_text(encoding="utf-8-sig")
            self.assertNotIn(forbidden_api_key, text)
            self.assertNotIn("api" + " key", text.lower())

    def test_realistic_references_use_pixel_reference_audition_before_rows(self) -> None:
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        enhancer_text = (ROOT / "references" / "state-enhancers.md").read_text(encoding="utf-8")

        for text in (workflow_text, contract_text, enhancer_text):
            self.assertIn("pixel-reference audition loop", text)
            self.assertIn("photographic, realistic, smooth, high-detail, or otherwise non-pixel", text)
            self.assertIn("generate a simplified native pixel-art base candidate first", text)
            self.assertIn("use that inspected pixel candidate as the next grounding reference", text)
            self.assertIn("Do not generate state rows from the original non-pixel reference alone", text)
            self.assertIn("Only record the final canonical base after the pixel reference itself passes source and visual QA", text)

    def test_top_level_skill_does_not_seed_specific_mascot_examples(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        workflow_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig").lower()

        for forbidden in (
            "tridy",
            "trident",
            "teal",
            "cream",
            "robe",
            "hood",
            "antenna",
            "laptop",
            "tablet",
            "parchment",
            "quill",
        ):
            self.assertNotIn(forbidden, text)

        self.assertIn("row prompts must not hard-code", workflow_text)
        self.assertIn("do not let examples in this skill become default mascot identity", workflow_text)

    def test_generic_skill_references_do_not_leak_audition_specific_identity(self) -> None:
        paths = [
            ROOT / "SKILL.md",
            ROOT / "references" / "production-workflow.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
            ROOT / "scripts" / "prepare_companion_run.py",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()

        for forbidden in ("tridy", "trident", "teal face", "red robe", "hood robe"):
            self.assertNotIn(forbidden, text)

    def test_repeated_flat_key_failure_escalates_instead_of_normalizing_sources(self) -> None:
        skill_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        enhancer_text = (ROOT / "references" / "state-enhancers.md").read_text(encoding="utf-8")

        for text in (skill_text, contract_text, enhancer_text):
            self.assertIn("non_uniform_chroma_key_background", text)
            self.assertIn("fake_checkerboard_transparency_background", text)
            self.assertIn("source_style_analysis_v3", text)
            self.assertIn("source_style_strict_blocking_warning_codes_v3", text)
            self.assertIn("capture_codex_app_imagegen_result.py", text)
            self.assertIn("codex-app-imagegen", text)

        self.assertIn("Do not record a locally flood-filled", skill_text)
        self.assertIn("green-looking-but-non-uniform backgrounds", skill_text)
        self.assertIn("recordable cleanup-ready background", skill_text)
        self.assertIn("A visual note of \"flat green\" is not enough", enhancer_text)
        self.assertIn("merely looks green but has visible or measured falloff", contract_text)
        self.assertIn("Do not accept locally flood-filled", contract_text)
        self.assertIn("do not locally normalize the source background", enhancer_text)
        self.assertIn("audit_companion_imagegen_sources_v3.py", skill_text)
        self.assertIn("without copying files, recording jobs, or mutating", skill_text)
        self.assertIn("create_companion_candidate_rejection_report.py", skill_text)
        self.assertIn("candidate rejection report", skill_text)
        self.assertIn("recorded: false", skill_text)
        self.assertIn("leaves `imagegen-jobs.json` untouched", skill_text)
        self.assertIn("create_companion_production_readiness_report_v3.py", skill_text)
        self.assertIn("production-readiness report", skill_text)
        self.assertIn("candidate rejection reports", skill_text)
        self.assertIn("do not block production by themselves", skill_text)
        self.assertIn("built-in-imagegen-chroma-cleanup", skill_text)
        self.assertIn("--chroma-cleanup-source", skill_text)
        self.assertIn("remove_chroma_key.py", skill_text)
        self.assertIn("accepted cue vocabulary", skill_text)
        self.assertIn("strict validation warnings", skill_text)
        self.assertIn("stale QA evidence", skill_text)
        self.assertIn("stale manual visual reviews", skill_text)
        for evidence_name in (
            "qa/cutout-check.png",
            "qa/state-readability-check.png",
            "qa/semantic-anchor-check.png",
            "qa/motion-quality-check.png",
            "qa/previews/",
        ):
            self.assertIn(evidence_name, skill_text)
        self.assertIn("non-mutating QA report", contract_text)
        self.assertIn("create_companion_candidate_rejection_report.py", contract_text)
        self.assertIn("visually inspected and rejected", contract_text)
        self.assertIn("recorded: false", contract_text)
        self.assertIn("production-readiness report", contract_text)
        self.assertIn("candidate rejection reports", contract_text)
        self.assertIn("do not block production by themselves", contract_text)
        self.assertIn("built-in-imagegen-chroma-cleanup", contract_text)
        self.assertIn("--chroma-cleanup-source", contract_text)
        self.assertIn("remove_chroma_key.py", contract_text)
        self.assertIn("accepted cue vocabulary", contract_text)
        self.assertIn("strict validation warnings", contract_text)
        self.assertIn("stale QA evidence", contract_text)
        self.assertIn("manual visual reviews must be newer", contract_text)
        for evidence_name in (
            "qa/cutout-check.png",
            "qa/state-readability-check.png",
            "qa/semantic-anchor-check.png",
            "qa/motion-quality-check.png",
            "qa/previews/",
        ):
            self.assertIn(evidence_name, contract_text)
        self.assertIn("candidate rejection report", enhancer_text)
        self.assertIn("Do not record or assemble rejected candidates", enhancer_text)

    def test_art_direction_review_requires_frame_covered_eye_grammar_review(self) -> None:
        skill_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        enhancer_text = (ROOT / "references" / "state-enhancers.md").read_text(encoding="utf-8")

        self.assertIn("create_art_direction_review.py", skill_text)
        self.assertIn("create_eye_grammar_review.py", skill_text)
        self.assertIn("--require-eye-grammar-review", skill_text)
        self.assertIn("noWhiteScleraOrCrescentSwap", skill_text)
        self.assertIn("source eye count/shape, fill or pupil color", skill_text)
        self.assertIn("--review-all-frames", skill_text)
        self.assertIn("every used frame", skill_text)
        self.assertIn("coherentStateStoryArc", skill_text)
        self.assertIn("mascotActingVariesAcrossFrames", skill_text)
        self.assertIn("every-frame eye grammar", contract_text)
        self.assertIn("qa/eye-grammar-review.json", contract_text)
        self.assertIn("source eye count/shape, fill or pupil color", contract_text)
        self.assertIn("reviewedFrames", contract_text)
        self.assertIn("coherentStateStoryArc", contract_text)
        self.assertIn("mascotActingVariesAcrossFrames", contract_text)
        self.assertIn("reviewedFrames", enhancer_text)
        self.assertIn("coherentStateStoryArc", enhancer_text)
        self.assertIn("mascotActingVariesAcrossFrames", enhancer_text)

    def test_high_visibility_auditions_require_eye_grammar_gate(self) -> None:
        skill_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (skill_text, contract_text, readme_text):
            self.assertIn("high-visibility audition rows", text)
            self.assertIn("thinking, working, and answering", text)
            self.assertIn("anatomy review", text)
            self.assertIn("state-performance review", text)
            self.assertIn("eye-grammar review", text)
            self.assertIn("without anatomy review, state-performance review, and eye-grammar review", text)

        self.assertIn("--profile audition --strict", skill_text)
        self.assertIn("--require-anatomy-review", skill_text)
        self.assertIn("--require-state-performance-review", skill_text)
        self.assertIn("--require-eye-grammar-review", skill_text)
        self.assertIn("--require-anatomy-review", readme_text)
        self.assertIn("--require-state-performance-review", readme_text)
        self.assertIn("--require-eye-grammar-review", readme_text)

    def test_anatomy_review_requires_specific_source_anatomy_details(self) -> None:
        skill_text = (ROOT / "references" / "production-workflow.md").read_text(encoding="utf-8-sig")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        enhancer_text = (ROOT / "references" / "state-enhancers.md").read_text(encoding="utf-8")

        for text in (skill_text, contract_text, readme_text, enhancer_text):
            self.assertIn("body core", text)
            self.assertIn("appendage count", text)
            self.assertIn("placement/anchors", text)
            self.assertIn("allowed motion/interactors", text)
            self.assertIn("forbidden extra anatomy", text)

        self.assertIn("specific `expectedAnatomy`", skill_text)
        self.assertIn("expectedAnatomy` must specifically describe", contract_text)

    def test_thinking_idea_peak_stays_deliberate_without_mandating_puffs(self) -> None:
        paths = [
            ROOT / "README.md",
            ROOT / "references" / "production-workflow.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
        ]

        for path in paths:
            text = path.read_text(encoding="utf-8-sig")
            self.assertIn("primary cue element is only slightly larger, never oversized", text)
            self.assertIn("do not enlarge the cue to prove the idea landed", text)
            self.assertIn("accepted cue vocabulary", text)
            self.assertIn("stable source-to-peak trail", text)
            self.assertIn("smallest element stays closest to the inferred source", text)
            self.assertIn("Do not let intermediate cue elements drift downward", text)
            self.assertNotIn("main puff is never oversized", text)


if __name__ == "__main__":
    unittest.main()
