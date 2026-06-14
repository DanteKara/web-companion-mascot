import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillDocumentTests(unittest.TestCase):
    def test_skill_uses_hatchpet_style_workflow_sections(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        expected_order = [
            "## Overview",
            "## Generation Delegation",
            "## Output Model",
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
        self.assertIn("selected_source=/absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png", text)
        self.assertIn("No silent sequential fallback", text)

    def test_top_level_skill_does_not_seed_specific_mascot_examples(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()

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

        self.assertIn("row prompts must not hard-code", text)
        self.assertIn("do not let examples in this skill become default mascot identity", text)

    def test_generic_skill_references_do_not_leak_audition_specific_identity(self) -> None:
        paths = [
            ROOT / "SKILL.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
            ROOT / "scripts" / "prepare_companion_run.py",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()

        for forbidden in ("tridy", "trident", "teal face", "red robe", "hood robe"):
            self.assertNotIn(forbidden, text)

    def test_repeated_flat_key_failure_escalates_instead_of_normalizing_sources(self) -> None:
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (ROOT / "references" / "companion-contract.md").read_text(encoding="utf-8")
        enhancer_text = (ROOT / "references" / "state-enhancers.md").read_text(encoding="utf-8")

        for text in (skill_text, contract_text, enhancer_text):
            self.assertIn("non_uniform_chroma_key_background", text)
            self.assertIn("fake_checkerboard_transparency_background", text)
            self.assertIn("base_style_analysis", text)
            self.assertIn("base_style_strict_blocking_warning_codes", text)
            self.assertIn("row_source_style_analysis", text)
            self.assertIn("row_source_style_strict_blocking_warning_codes", text)
            self.assertIn("true-transparency fallback", text)
            self.assertIn("explicit user confirmation", text)

        self.assertIn("Do not record a locally flood-filled", skill_text)
        self.assertIn("green-looking-but-non-uniform backgrounds", skill_text)
        self.assertIn("recordable cleanup-ready background", skill_text)
        self.assertIn("A visual note of \"flat green\" is not enough", enhancer_text)
        self.assertIn("merely looks green but has visible or measured falloff", contract_text)
        self.assertIn("Do not accept locally flood-filled", contract_text)
        self.assertIn("do not locally normalize the source background", enhancer_text)
        self.assertIn("audit_companion_imagegen_sources.py", skill_text)
        self.assertIn("without copying files, recording jobs, or mutating", skill_text)
        self.assertIn("create_companion_candidate_rejection_report.py", skill_text)
        self.assertIn("candidate rejection report", skill_text)
        self.assertIn("recorded: false", skill_text)
        self.assertIn("leaves `imagegen-jobs.json` untouched", skill_text)
        self.assertIn("create_imagegen_cli_fallback_handoff.py", skill_text)
        self.assertIn("does not call the API", skill_text)
        self.assertIn("current recorded row `source_path` by default", skill_text)
        self.assertIn("--allow-rejected-candidate-source", skill_text)
        self.assertIn("sourceMode: \"rejected-candidate\"", skill_text)
        self.assertIn("narrow source repair", skill_text)
        self.assertIn("requiredEnvironment", skill_text)
        self.assertIn("OPENAI_API_KEY", skill_text)
        self.assertIn("requiredEnvironmentStatus", skill_text)
        self.assertIn("executionBlockedBy", skill_text)
        self.assertIn("explicitUserApprovalReceived", skill_text)
        self.assertIn("approvalNote", skill_text)
        self.assertIn("promptRepairContract", skill_text)
        self.assertIn("promptRepairContractOk", skill_text)
        self.assertIn("--write-default-prompt", skill_text)
        self.assertIn("compact generic story-preserving repair prompt", skill_text)
        self.assertIn("defaultPromptWritten", skill_text)
        self.assertIn("repairPromptSource", skill_text)
        self.assertIn("generic-story-preserving-default", skill_text)
        self.assertIn("fallbackRepairReady", skill_text)
        self.assertIn("blockedHandoffCount", skill_text)
        self.assertIn("runnableHandoffCount", skill_text)
        self.assertIn("preserve the current row story and scale", skill_text)
        self.assertIn("create_companion_production_readiness_report.py", skill_text)
        self.assertIn("production-readiness report", skill_text)
        self.assertIn("candidate rejection reports", skill_text)
        self.assertIn("do not block production by themselves", skill_text)
        self.assertIn("built-in-imagegen-chroma-cleanup", skill_text)
        self.assertIn("--chroma-cleanup-source", skill_text)
        self.assertIn("remove_chroma_key.py", skill_text)
        self.assertIn("fallback repair intent", skill_text)
        self.assertIn("cue-agnostic", skill_text)
        self.assertIn("accepted cue vocabulary", skill_text)
        self.assertIn("strict validation warnings", skill_text)
        self.assertIn("stale QA evidence", skill_text)
        self.assertIn("stale manual visual reviews", skill_text)
        self.assertIn("stale fallback handoffs", skill_text)
        self.assertIn("current manifest", skill_text)
        self.assertIn("current imagegen-jobs.json", skill_text)
        self.assertIn("current row source", skill_text)
        self.assertIn("current fallback prompt", skill_text)
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
        self.assertIn("handoff generator only", contract_text)
        self.assertIn("current recorded row `source_path` by default", contract_text)
        self.assertIn("--allow-rejected-candidate-source", contract_text)
        self.assertIn("sourceMode: \"rejected-candidate\"", contract_text)
        self.assertIn("story-preserving source repair", contract_text)
        self.assertIn("requiredEnvironment", contract_text)
        self.assertIn("OPENAI_API_KEY", contract_text)
        self.assertIn("requiredEnvironmentStatus", contract_text)
        self.assertIn("executionBlockedBy", contract_text)
        self.assertIn("explicitUserApprovalReceived", contract_text)
        self.assertIn("approvalNote", contract_text)
        self.assertIn("promptRepairContract", contract_text)
        self.assertIn("promptRepairContractOk", contract_text)
        self.assertIn("--write-default-prompt", contract_text)
        self.assertIn("compact generic repair prompt", contract_text)
        self.assertIn("defaultPromptWritten", contract_text)
        self.assertIn("repairPromptSource", contract_text)
        self.assertIn("generic-story-preserving-default", contract_text)
        self.assertIn("fallbackRepairReady", contract_text)
        self.assertIn("blockedHandoffCount", contract_text)
        self.assertIn("runnableHandoffCount", contract_text)
        self.assertIn("production-readiness report", contract_text)
        self.assertIn("candidate rejection reports", contract_text)
        self.assertIn("do not block production by themselves", contract_text)
        self.assertIn("built-in-imagegen-chroma-cleanup", contract_text)
        self.assertIn("--chroma-cleanup-source", contract_text)
        self.assertIn("remove_chroma_key.py", contract_text)
        self.assertIn("fallback repair intent", contract_text)
        self.assertIn("cue-agnostic", contract_text)
        self.assertIn("accepted cue vocabulary", contract_text)
        self.assertIn("strict validation warnings", contract_text)
        self.assertIn("stale QA evidence", contract_text)
        self.assertIn("manual visual reviews must be newer", contract_text)
        self.assertIn("stale fallback handoffs", contract_text)
        self.assertIn("current manifest", contract_text)
        self.assertIn("current imagegen-jobs.json", contract_text)
        self.assertIn("current row source", contract_text)
        self.assertIn("current fallback prompt", contract_text)
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
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
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
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
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
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
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
            ROOT / "SKILL.md",
            ROOT / "references" / "companion-contract.md",
            ROOT / "references" / "state-enhancers.md",
        ]

        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("primary cue element is only slightly larger, never oversized", text)
            self.assertIn("do not enlarge the cue to prove the idea landed", text)
            self.assertIn("accepted cue vocabulary", text)
            self.assertIn("stable source-to-peak trail", text)
            self.assertIn("smallest element stays closest to the inferred source", text)
            self.assertIn("Do not let intermediate cue elements drift downward", text)
            self.assertNotIn("main puff is never oversized", text)


if __name__ == "__main__":
    unittest.main()
