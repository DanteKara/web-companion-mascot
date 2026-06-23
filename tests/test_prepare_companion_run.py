import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_companion_run.py"
STATUS_PATH = ROOT / "scripts" / "companion_job_status.py"
RECORD_PATH = ROOT / "scripts" / "record_companion_imagegen_result.py"

spec = importlib.util.spec_from_file_location("prepare_companion_run", PREPARE_PATH)
prepare = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare)

status_spec = importlib.util.spec_from_file_location("companion_job_status", STATUS_PATH)
job_status = importlib.util.module_from_spec(status_spec)
assert status_spec.loader is not None
status_spec.loader.exec_module(job_status)

record_spec = importlib.util.spec_from_file_location("record_companion_imagegen_result", RECORD_PATH)
record = importlib.util.module_from_spec(record_spec)
assert record_spec.loader is not None
record_spec.loader.exec_module(record)


def write_fixture_png(path: Path, color: tuple[int, int, int, int] = (240, 250, 255, 255)) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=color, outline=(40, 100, 160, 255), width=3)
    draw.ellipse((24, 27, 29, 33), fill=(20, 30, 40, 255))
    draw.ellipse((36, 27, 41, 33), fill=(20, 30, 40, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_flat_pixel_base(path: Path, key: tuple[int, int, int, int] = (255, 0, 255, 255)) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (96, 96), key)
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    draw.rectangle((34, 24, 48, 28), fill=(104, 222, 216, 255))
    draw.rectangle((35, 36, 61, 52), fill=(255, 241, 178, 255))
    draw.rectangle((41, 40, 44, 46), fill=(10, 24, 30, 255))
    draw.rectangle((52, 40, 55, 46), fill=(10, 24, 30, 255))
    draw.point((42, 41), fill=(255, 255, 255, 255))
    draw.point((53, 41), fill=(255, 255, 255, 255))
    draw.rectangle((39, 56, 58, 64), fill=(32, 160, 154, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_nonuniform_key_base(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    pixels = image.load()
    for y in range(96):
        for x in range(96):
            pixels[x, y] = (255, min(28, x // 4 + y // 6), 255, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    draw.rectangle((35, 36, 61, 52), fill=(255, 241, 178, 255))
    draw.rectangle((41, 40, 44, 46), fill=(10, 24, 30, 255))
    draw.rectangle((52, 40, 55, 46), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_inner_falloff_key_base(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (96, 96), (255, 0, 255, 255))
    pixels = image.load()
    for y in range(10, 86):
        for x in range(10, 86):
            distance = abs(x - 48) + abs(y - 48)
            green = max(0, 34 - distance // 3)
            pixels[x, y] = (255, green, 255, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 18, 68, 70), fill=(20, 36, 44, 255))
    draw.rectangle((32, 22, 64, 66), fill=(38, 184, 180, 255))
    draw.rectangle((35, 36, 61, 52), fill=(255, 241, 178, 255))
    draw.rectangle((41, 40, 44, 46), fill=(10, 24, 30, 255))
    draw.rectangle((52, 40, 55, 46), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_smooth_gradient_base(path: Path, key: tuple[int, int, int, int] = (255, 0, 255, 255)) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (128, 128), key)
    pixels = image.load()
    for y in range(24, 104):
        for x in range(24, 104):
            dx = x - 64
            dy = y - 64
            if dx * dx + dy * dy <= 40 * 40:
                shade = int((x - 24) * 80 / 79)
                pixels[x, y] = (25 + shade, 150 + shade // 2, 160 + shade // 3, 255)
    draw = ImageDraw.Draw(image)
    draw.ellipse((34, 42, 54, 62), fill=(255, 244, 190, 255))
    draw.ellipse((74, 42, 94, 62), fill=(255, 244, 190, 255))
    draw.rectangle((42, 48, 49, 58), fill=(10, 24, 30, 255))
    draw.rectangle((82, 48, 89, 58), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_fake_checkerboard_base(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (128, 128), (255, 255, 255, 255))
    pixels = image.load()
    for y in range(128):
        for x in range(128):
            shade = 255 if ((x // 8) + (y // 8)) % 2 == 0 else 236
            pixels[x, y] = (shade, shade, shade, 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((42, 28, 86, 84), fill=(20, 36, 44, 255))
    draw.rectangle((46, 32, 82, 80), fill=(38, 184, 180, 255))
    draw.rectangle((52, 46, 57, 54), fill=(10, 24, 30, 255))
    draw.rectangle((70, 46, 75, 54), fill=(10, 24, 30, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


class PrepareCompanionRunTests(unittest.TestCase):
    def assert_compact_row_prompt(self, prompt: str, *, state: str) -> None:
        self.assertIn(f"{state} row prompt - compact", prompt)
        self.assertIn("Create one horizontal sprite row strip", prompt)
        self.assertIn("Identity lock:", prompt)
        self.assertIn("Style lock:", prompt)
        self.assertIn("State performance story arc", prompt)
        self.assertIn("coherent mini-story", prompt)
        self.assertIn("Frame plan:", prompt)
        self.assertIn("Scale and layout rules:", prompt)
        self.assertIn("Reject if:", prompt)
        self.assertIn("wide empty", prompt)
        self.assertIn("outer row image border", prompt)
        self.assertIn("No action rays", prompt)
        self.assertIn("sound rays", prompt)
        self.assertIn("emphasis strokes", prompt)
        self.assertIn("wave lines", prompt)
        self.assertIn("alert marks", prompt)

    def assert_no_verbose_policy_dump(self, prompt: str) -> None:
        for old_section in (
            "Hard native-pixel rendering lock",
            "Canonical base row lock",
            "Reference palette fidelity lock",
            "HatchPet-style sprite artifact rules",
            "Semantic ladder:",
            "Anatomy guidance:",
            "Professional state acting choreography",
            "Visible appendage acting policy",
            "Identity prop contract",
        ):
            self.assertNotIn(old_section, prompt)

    def test_prompt_policies_do_not_leak_audition_specific_identity(self) -> None:
        policy_text = "\n".join(
            str(value)
            for name, value in vars(prepare).items()
            if name.isupper() and isinstance(value, str)
        ).lower()

        for forbidden in ("tridy", "trident", "teal face", "red robe", "hood robe"):
            self.assertNotIn(forbidden, policy_text)

    def test_default_states_omit_working_and_fold_processing_into_thinking(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Defaulty",
                    "--output-dir",
                    str(out_dir),
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("working", manifest["states"])
            self.assertNotIn("confused", manifest["states"])
            self.assertIn("hover", manifest["states"])
            self.assertIn("dragging", manifest["states"])
            self.assertIn("thinking", manifest["states"])
            self.assertIn("answering", manifest["states"])

            request = json.loads((out_dir / "companion_request.json").read_text(encoding="utf-8"))
            self.assertNotIn("working", request["states"])
            self.assertNotIn("confused", request["states"])
            self.assertIn("hover", request["states"])
            self.assertIn("dragging", request["states"])

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            job_ids = [job["id"] for job in jobs["jobs"]]
            self.assertNotIn("working", job_ids)
            self.assertNotIn("confused", job_ids)
            self.assertIn("hover", job_ids)
            self.assertIn("dragging", job_ids)
            self.assertIn("thinking", job_ids)

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("assistant is thinking, processing, retrieving, using tools, or waiting on backend progress", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Do not create a separate working state unless the user explicitly requests one", cue_plan["states"]["thinking"]["frameArc"])

    def test_default_interaction_states_have_pointer_specific_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "PointerPal",
                    "--output-dir",
                    str(out_dir),
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("pointer hover over the companion", cue_plan["states"]["hover"]["semanticRead"])
            self.assertIn("user is dragging the companion around the app", cue_plan["states"]["dragging"]["semanticRead"])
            self.assertIn("cursor icons", cue_plan["states"]["hover"]["rejectIf"])
            self.assertIn("external hands", cue_plan["states"]["dragging"]["rejectIf"])

            hover_prompt = (out_dir / "prompts" / "hover.md").read_text(encoding="utf-8")
            dragging_prompt = (out_dir / "prompts" / "dragging.md").read_text(encoding="utf-8")
            self.assertIn("Communicate the state through the canonical mascot's expression", hover_prompt)
            self.assertIn("cursor-follow movement", dragging_prompt)
            self.assertIn("cursor icons", dragging_prompt.lower())

    def test_base_prompt_requires_native_pixel_art_and_no_unrequested_identity_marks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Helper",
                    "--description",
                    "A friendly tiny teal helper robot mascot with two simple mitten hands and a small antenna.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single top antenna",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Base production lock", base_prompt)
            self.assertIn("native pixel-art sprite, not a scaled-down smooth illustration", base_prompt)
            self.assertIn("flat cel-shaded pixel clusters", base_prompt)
            self.assertIn("no glossy gradients", base_prompt)
            self.assertIn("no soft airbrush", base_prompt)
            self.assertIn("Text-only concept anatomy lock", base_prompt)
            self.assertIn("only add anatomy and identity props named in the concept", base_prompt)
            self.assertIn("Do not add unrequested body markings, lights, badges, emblems, display details", base_prompt)
            self.assertIn("Keep the body compact with exactly the named anatomy and identity features", base_prompt)
            self.assertIn("When the concept only names upper appendages, do not infer visible legs or feet", base_prompt)
            self.assertIn("Keep plain body areas plain unless a mark is named", base_prompt)

    def test_base_prompt_requires_row_compatible_base_and_locked_eye_grammar(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "EyeBot",
                    "--description",
                    "A teal helper robot with a cream face panel, dark oval eyes, tiny highlights, two mitten hands, and one antenna.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Canonical base acceptance gate", base_prompt)
            self.assertIn("final atlas-frame source of truth", base_prompt)
            self.assertIn("not concept art, a preview illustration, a pose-sheet sample, an app icon, or a softened style target", base_prompt)
            self.assertIn("simple enough to reproduce across eight row frames without redesign", base_prompt)
            self.assertIn("Reject and regenerate the base before any row prompt if it is smoother, glossier, more detailed, or less pixel-native than the intended row art", base_prompt)
            self.assertIn("Rows must preserve the accepted base, not fix it by changing eye style, body shape, colors, outline weight, props, or anatomy", base_prompt)
            self.assertIn("Base eye grammar lock", base_prompt)
            self.assertIn("The canonical base sets the eye count, eye shape, spacing, fill or pupil color, outline color, catchlight/highlight count, and blink style", base_prompt)
            self.assertIn("For dark oval eyes, keep the open eyes mostly dark with at most one tiny blocked highlight per eye", base_prompt)
            self.assertIn("Avoid oversized glossy highlights, white sclera crescents, rimmed white eyes, UI-screen eyes, square pixel-display eyes, mismatched eyes, and decorative extra catchlights unless the source reference already uses them", base_prompt)

    def test_base_prompt_forbids_soft_pixel_styled_gloss_and_nonuniform_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "FlatBot",
                    "--description",
                    "A charming teal robot mascot with dark oval eyes and simple mitten hands.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--source-vibe",
                    "soft friendly product helper",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Hard native-pixel rendering lock", base_prompt)
            self.assertIn("Use hard-edged square pixel clusters and 2-3 flat tone steps per material", base_prompt)
            self.assertIn("softness must come from shape language and expression, not blurred rendering", base_prompt)
            self.assertIn("No blurred or feathered transitions, no transparent or semi-transparent shine, no airbrushed lighting, no smooth diagonal antialias fringe", base_prompt)
            self.assertIn("Highlights must be tiny rectangular pixel blocks", base_prompt)
            self.assertIn("no broad glossy shine patches on large surfaces, accessories, appendages, or face areas", base_prompt)
            self.assertIn("Flat chroma-key lock", base_prompt)
            self.assertIn("The background must be one perfectly uniform solid chroma-key color from corner to corner", base_prompt)
            self.assertIn("no vignette, lighting falloff, texture, noise, shadow, ground plane, or background glow", base_prompt)

    def test_base_prompt_uses_small_source_pixel_grid_to_avoid_app_icon_shading(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "GridBot",
                    "--description",
                    "A friendly teal robot mascot.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Source-pixel grid lock", base_prompt)
            self.assertIn("Draw the mascot as if it was first made on a tiny 64x72 or 80x90 pixel grid and then enlarged with nearest-neighbor scaling", base_prompt)
            self.assertIn("Every visible edge and highlight should snap to that coarse pixel grid", base_prompt)
            self.assertIn("Large body regions should be flat color clusters with one darker stepped shadow band at most", base_prompt)
            self.assertIn("Do not use smooth radial gradients, soft cylindrical shading, pillow shading, or app-icon material lighting", base_prompt)
            self.assertIn("If a surface needs dimension, use one or two chunky stair-step shadow clusters, not continuous tone ramps", base_prompt)

    def test_base_prompt_matches_hatch_pet_compact_192x208_style_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Hatchy",
                    "--description",
                    "A friendly teal robot mascot.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Compact web companion source target", base_prompt)
            self.assertIn("The base should be fully visible, readable as a small website companion", base_prompt)
            self.assertIn("simple enough to animate without redesign", base_prompt)
            self.assertIn("pixel-art-adjacent low-resolution mascot sprite", base_prompt)
            self.assertIn("flat cel shading with hard blocked highlights/shadows", base_prompt)
            self.assertIn("no detail that disappears at companion-widget sizes", base_prompt)
            self.assertIn("Do not compose it as a large glossy product mascot, large hero character, app icon, or high-resolution sticker", base_prompt)
            self.assertIn("leave generous chroma-key padding and keep the sprite compact", base_prompt)

    def test_base_prompt_uses_indexed_sprite_cell_and_simplifies_named_parts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "IndexedBot",
                    "--description",
                    "A friendly teal helper robot with a cream face panel, dark oval eyes, two simple side mitten hands, and one short top antenna.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single short top antenna",
                    "--identity-prop",
                    "two simple side mitten hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            self.assertIn("Indexed-color sprite discipline", base_prompt)
            self.assertIn("Use a controlled sprite palette that preserves identity and charm", base_prompt)
            self.assertIn("Avoid per-pixel color ramps", base_prompt)
            self.assertIn("smooth shade bands", base_prompt)
            self.assertIn("gradient-filled body areas", base_prompt)
            self.assertIn("keep signature costume, magic, material, and character color relationships when they matter", base_prompt)
            self.assertIn("Part simplification lock", base_prompt)
            self.assertIn("Do not invent parts from these instructions", base_prompt)
            self.assertIn("Small accessories should become plain readable silhouettes", base_prompt)
            self.assertIn("simple side appendages should keep one outline and one flat fill", base_prompt)
            self.assertIn("long held props should remain one continuous readable object", base_prompt)
            self.assertIn("Reference-native style lock", base_prompt)
            self.assertIn("If an attached reference already looks like a HatchPet or Codex digital-pet sprite", base_prompt)
            self.assertIn("Reference-aware palette guide", base_prompt)
            self.assertIn("Build a compact per-mascot palette from the attached reference or the text concept", base_prompt)
            self.assertIn("Never impose a preselected color palette", base_prompt)
            self.assertIn("Avoid unnecessary intermediate blends", base_prompt)
            self.assertIn("do not erase important reference color personality", base_prompt)
            self.assertIn("Reference character direction lock", base_prompt)
            self.assertIn("Keep the strongest character decisions from the provided reference or text concept", base_prompt)
            self.assertIn("Do not substitute a stock assistant mascot", base_prompt)
            self.assertIn("do not redesign the mascot while making it more pixel-native", base_prompt)
            self.assertIn("Pixel-reference audition loop", base_prompt)
            self.assertIn("When the attached reference is photographic, realistic, smooth, high-detail, or otherwise non-pixel", base_prompt)
            self.assertIn("generate a simplified native pixel-art base candidate first", base_prompt)
            self.assertIn("use that inspected pixel candidate as the next grounding reference", base_prompt)
            self.assertIn("Only record the final canonical base after the pixel reference itself passes source and visual QA", base_prompt)
            self.assertNotIn("Keep the strong v9-style character read", base_prompt)

    def test_row_prompts_inherit_hard_native_pixel_rendering_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "FlatRows",
                    "--description",
                    "A teal robot mascot with a cream face panel.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            for state in ("thinking", "answering"):
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                self.assertIn("row prompt - compact", prompt)
                self.assertIn("Native Codex digital-pet pixel-art sprite", prompt)
                self.assertIn("hard square pixels", prompt)
                self.assertIn("Perfectly uniform", prompt)
                self.assertIn("No smooth illustration", prompt)
                self.assertIn("non-native pixel-art rendering", prompt)

    def test_all_state_prompts_require_coherent_looping_story_arcs(self) -> None:
        states = [
            "idle",
            "greeting",
            "listening",
            "thinking",
            "answering",
            "success",
            "error",
            "confused",
            "sleeping",
        ]
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "StoryBot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    ",".join(states),
                    "--anatomy-class",
                    "no-limbs",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))

            for state in states:
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                if state == "thinking":
                    self.assertIn("thinking row prompt - compact", prompt)
                    self.assertIn("neutral-curious -> focused processing -> compact cue/prop beat -> idea lands -> pleased settle", prompt)
                    self.assertIn("Expressions are adjacent state-caused beats", prompt)
                    self.assertIn("Every frame changes face, posture, body/appendage timing, prop timing, or cue", prompt)
                    self.assertIn("no one-frame expression-style outliers", prompt)
                    self.assertIn("loop cleanly back to the first frame", prompt)
                else:
                    self.assert_compact_row_prompt(prompt, state=state)
                    self.assert_no_verbose_policy_dump(prompt)
                self.assertIn("statePerformanceStoryPolicy", cue_plan["states"][state])
                self.assertIn("stateStoryBeats", cue_plan["states"][state])

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn(
                "neutral-curious -> focused processing -> compact cue/prop beat -> idea lands -> pleased settle",
                thinking_prompt,
            )
            self.assertIn("not random sad, serious, sleepy, angry, blank, or unrelated faces", thinking_prompt)

    def test_row_prompts_are_compact_and_do_not_dump_full_policy_docs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Compacty",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "idle,thinking,answering,working",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            for state in ("idle", "thinking", "answering", "working"):
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                self.assertLess(len(prompt), 6500)
                self.assertIn("row prompt - compact", prompt)

            for state in ("idle", "answering", "working"):
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                self.assert_no_verbose_policy_dump(prompt)

    def test_simple_appendage_thinking_prompt_stays_compact(self) -> None:
        for anatomy_class in ("fins-no-hands", "ambiguous-limbs"):
            with self.subTest(anatomy_class=anatomy_class):
                with tempfile.TemporaryDirectory() as raw_tmp:
                    out_dir = Path(raw_tmp) / "run"

                    result = prepare.main(
                        [
                            "--companion-name",
                            "CompactThinker",
                            "--output-dir",
                            str(out_dir),
                            "--states",
                            "thinking",
                            "--anatomy-class",
                            anatomy_class,
                            "--compact",
                            "--quiet",
                        ]
                    )

                    self.assertEqual(result, 0)
                    thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
                    self.assertLess(len(thinking_prompt), 6200)
                    self.assertLess(len(thinking_prompt.splitlines()), 55)
                    self.assert_no_verbose_policy_dump(thinking_prompt)
                    self.assertIn("neutral-curious -> focused processing -> compact cue/prop beat -> idea lands -> pleased settle", thinking_prompt)
                    self.assertIn("Keep simple side appendages outside the body", thinking_prompt)
                    self.assertIn("face-touch beat is acceptable only if it clearly remains the original connected appendage", thinking_prompt)
                    self.assertIn("same source-colored eye masses", thinking_prompt)
                    self.assertIn("wide empty", thinking_prompt)
                    self.assertIn("outer row image border", thinking_prompt)
                    self.assertIn("accepted rows define apparent body size/padding", thinking_prompt)
                    self.assertIn("Match canonical base and accepted rows for body size", thinking_prompt)
                    self.assertIn("action rays", thinking_prompt)
                    self.assertIn("sound rays", thinking_prompt)
                    self.assertIn("emphasis strokes", thinking_prompt)
                    self.assertIn("wave lines", thinking_prompt)
                    self.assertIn("alert marks", thinking_prompt)
                    self.assertIn("non-flat magenta #FF00FF background", thinking_prompt)

    def test_generated_prompts_do_not_inject_unsupplied_mascot_specific_examples(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Generic",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering,working",
                    "--anatomy-class",
                    "ambiguous-limbs",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            joined_prompts = "\n".join(
                (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8").lower()
                for state in ("thinking", "answering", "working")
            )
            for forbidden in ("tridy", "trident", "teal", "cream", "antenna", "mitten", "staff", "wand", "robe", "hood"):
                self.assertNotIn(forbidden, joined_prompts)

    def test_no_limb_working_prompt_forbids_held_work_props(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Orb",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working,answering",
                    "--anatomy-class",
                    "no-limbs",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assert_no_verbose_policy_dump(working_prompt)
            self.assertIn("busy-but-friendly", working_prompt)
            self.assertIn("no slanted angry eyes", working_prompt)
            self.assertIn("V-shaped", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["style"]["renderingStyle"], "codex-pixel-art")
            self.assertEqual(manifest["style"]["stateClarity"], "semantic-enhancers")
            self.assertEqual(manifest["states"]["working"]["frames"], 6)
            self.assertIn("visualLanguageFit", manifest["states"]["working"]["enhancer"])
            self.assertIn("no held, near-hand", cue_plan["states"]["working"]["suggestedVisualAid"])
            self.assertIn("tiny detached speck", cue_plan["states"]["working"]["suggestedVisualAid"])
            self.assertIn("inside the body core", cue_plan["states"]["working"]["bodySurfaceCuePolicy"])

    def test_hand_mascot_prompt_allows_supported_expressive_actions(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Handbot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "hands",
                    "--source-vibe",
                    "friendly tiny helper robot with real hands",
                    "--motif",
                    "small panel glow",
                    "--identity-prop",
                    "single chest screen",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("thinking row prompt - compact", thinking_prompt)
            self.assertIn("friendly tiny helper robot", thinking_prompt)
            self.assertIn("Must-keep identity props/accessories: single chest screen", thinking_prompt)
            self.assertIn("Use only existing appendages", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(cue_plan["visualLanguage"]["motifs"], ["small panel glow"])
            self.assertEqual(cue_plan["visualLanguage"]["identityProps"], ["single chest screen"])
            self.assertEqual(cue_plan["states"]["working"]["visualAidDecision"], "use only if acting alone would be unclear at 64-96 px")
            self.assertIn("Visible appendage acting policy", cue_plan["states"]["thinking"]["appendageActingPolicy"])
            self.assertIn("Identity prop contract", prepare.IDENTITY_PROP_POLICY)

    def test_visible_hand_mascot_prompts_require_small_hand_acting_for_waiting_states(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Staffy",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single staff held in the left hand",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")

            self.assertIn("thinking row prompt - compact", thinking_prompt)
            self.assert_compact_row_prompt(answering_prompt, state="answering")
            self.assert_no_verbose_policy_dump(answering_prompt)
            self.assertIn("Must-keep identity props/accessories: single staff held in the left hand", thinking_prompt)
            self.assertIn("Must-keep identity props/accessories: single staff held in the left hand", answering_prompt)
            self.assertIn("prop-holding appendage attached", thinking_prompt)
            self.assertIn("Use only appendages and props visible in the canonical base/reference", answering_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("appendageActingPolicy", cue_plan["states"]["thinking"])
            self.assertIn("appendageActingPolicy", cue_plan["states"]["answering"])
            self.assertIn("Visible appendage acting policy", cue_plan["states"]["thinking"]["appendageActingPolicy"])
            self.assertIn("State-specific appendage acting", cue_plan["states"]["answering"]["appendageActingPolicy"])

    def test_high_visibility_states_include_positive_acting_choreography(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Performer",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering,success,error",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "small side satchel",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))

            for state in ("thinking", "answering", "success", "error"):
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                self.assertIn(f"{state} row prompt - compact", prompt)
                self.assertIn("Use a plain digital solid-color canvas", prompt)
                self.assertIn("recordable by a strict cleanup gate", prompt)
                self.assertIn("No white crescent side-glance eyes", prompt)
                if state == "thinking":
                    self.assertIn("Every frame changes face, posture, body/appendage timing, prop timing, or cue", prompt)
                    self.assertIn("Thinking should read curious processing", prompt)
                else:
                    self.assertIn("Do not let all motion live in a cue while the mascot face and body stay frozen", prompt)
                self.assertIn("stateActingChoreography", cue_plan["states"][state])

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("compact source-bound cue", thinking_prompt)
            self.assertIn("primary cue element is only slightly larger, never oversized", thinking_prompt)
            self.assertIn("recognition smile", thinking_prompt)

            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")
            self.assertIn("Mouth shapes must visibly cycle", answering_prompt)
            self.assertIn("Match the canonical base and accepted rows", answering_prompt)
            self.assertIn("do not shrink or enlarge the mascot body", answering_prompt)

            success_prompt = (out_dir / "prompts" / "success.md").read_text(encoding="utf-8")
            self.assertIn("clearest read", success_prompt)

            error_prompt = (out_dir / "prompts" / "error.md").read_text(encoding="utf-8")
            self.assertIn("clearest read", error_prompt)
            self.assertIn("Do not include happy/success/answering frames", error_prompt)

    def test_non_thinking_prompts_include_neighboring_state_guards(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Bounded",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "listening,error,confused,sleeping",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            listening_prompt = (out_dir / "prompts" / "listening.md").read_text(encoding="utf-8")
            error_prompt = (out_dir / "prompts" / "error.md").read_text(encoding="utf-8")
            confused_prompt = (out_dir / "prompts" / "confused.md").read_text(encoding="utf-8")
            sleeping_prompt = (out_dir / "prompts" / "sleeping.md").read_text(encoding="utf-8")

            self.assertIn("Listening should read attentive and ready, not thinking, surprised", listening_prompt)
            self.assertIn("Avoid open shocked mouths, hand-to-chin poses", listening_prompt)
            self.assertIn("Error should remain a gentle recoverable failure loop", error_prompt)
            self.assertIn("no white-eye stress rewrites", error_prompt)
            self.assertIn("Confused should read curious-uncertain rather than sad/error", confused_prompt)
            self.assertIn("avoid hand-to-chin/under-face clusters", confused_prompt)
            self.assertIn("Sleeping should be quiet breathing and closed-eye settle", sleeping_prompt)
            self.assertIn("avoid hand-to-mouth clusters and sleep symbols", sleeping_prompt)

    def test_simple_fin_draft_plan_stays_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Finny",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("A near-face or face-touch beat is acceptable only if it clearly remains the original connected appendage", thinking_prompt)
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assertIn("invented angry eyebrows", working_prompt)
            self.assertIn("slanted angry eyes", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertNotIn("brace", manifest["states"]["working"]["enhancer"]["description"])
            self.assertIn("no held props or tiny detached specks in the draft plan", cue_plan["states"]["working"]["suggestedVisualAid"])
            self.assertIn("rim-touching", cue_plan["states"]["working"]["suggestedVisualAid"])
            self.assertIn("Cue colors and shapes must stay distinct", cue_plan["states"]["working"]["bodySurfaceCuePolicy"])

    def test_thinking_prompt_requires_generic_compact_cue_growth_arc(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("exactly 6 separated frames", thinking_prompt)
            self.assertIn("Frame-by-frame acting arc", thinking_prompt)
            self.assertIn("Six-frame acting story", thinking_prompt)
            self.assertIn("one tiny compact cue appears near the inferred thought-cue source", thinking_prompt)
            self.assertIn("the cue grows slightly while staying close and secondary", thinking_prompt)
            self.assertIn("compact cue peak beside the inferred source", thinking_prompt)
            self.assertIn("primary cue element is only slightly larger, never oversized", thinking_prompt)
            self.assertIn("cue shrinks to one tiny close remnant or resolves cleanly", thinking_prompt)
            self.assertIn("neutral-curious -> focused processing -> compact cue/prop beat -> idea lands -> pleased settle", thinking_prompt)
            self.assertIn("Every frame changes face, posture, body/appendage timing, prop timing, or cue", thinking_prompt)
            self.assertIn("no stale same-face holds", thinking_prompt)
            self.assertIn("no one-frame expression-style outliers", thinking_prompt)
            self.assertIn("sad/serious/downturned expression", thinking_prompt)
            self.assertIn("Face/body/appendage timing should sell thinking before the cue is noticed", thinking_prompt)
            self.assertIn("Do not make a tall vertical stack", thinking_prompt)
            self.assertIn("Do not let the cue force the mascot smaller", thinking_prompt)
            self.assertIn("non-flat magenta #FF00FF background", thinking_prompt)
            self.assertIn("darker/lighter key-color variations", thinking_prompt)
            self.assertNotIn("darker/lighter green variations", thinking_prompt)
            self.assertIn("Keep simple side appendages outside the body", thinking_prompt)
            self.assertIn("face-touch beat is acceptable only if it clearly remains the original connected appendage", thinking_prompt)
            self.assertIn("If unclear, leave it resting", thinking_prompt)
            self.assertIn("no white side-glance or new sclera", thinking_prompt)
            self.assertIn("same source-colored eye masses", thinking_prompt)
            self.assertIn("new white sclera", thinking_prompt)
            self.assertIn("Use closed/thoughtful mouths only: closed smile, tiny pleased smile, or gently upturned one-pixel smile", thinking_prompt)
            self.assertIn("Expression and eye rules", thinking_prompt)
            self.assertIn("focused open-eye or tiny mouth beat", thinking_prompt)
            self.assertIn("source-matched open eyes stay forward or nearly forward", thinking_prompt)
            self.assertIn("one-frame dramatic side glances", thinking_prompt)
            self.assertIn("stale same-face row", thinking_prompt)
            self.assertIn("does not become a new hand, finger, lower-face patch, or detached blob", thinking_prompt)
            self.assertNotIn("open black eyes", thinking_prompt)
            self.assertNotIn("eyes glance up or aside", thinking_prompt)
            self.assertNotIn("one hand makes", thinking_prompt)
            self.assertNotIn("side attention shift", thinking_prompt)
            self.assertNotIn("hood/head/face", thinking_prompt)
            self.assertNotIn("white puff", thinking_prompt)
            self.assertNotIn("exactly three visible puffs", thinking_prompt)
            self.assertNotIn("main puff", thinking_prompt)
            self.assertNotIn("free hand or hand-like appendage", thinking_prompt)
            self.assertNotIn("non-flat green background", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("frameArc", cue_plan["states"]["thinking"])
            self.assertIn("small -> slightly larger -> medium -> smaller -> tiny/settle", cue_plan["states"]["thinking"]["frameArc"])

    def test_thinking_prompt_stays_hatchpet_style_compact_and_nonduplicative(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "CompactThinker",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertLessEqual(len(thinking_prompt), 5000)
            self.assertEqual(thinking_prompt.count("Frame-by-frame acting arc"), 1)
            self.assertEqual(thinking_prompt.count("Thought cue rules"), 1)
            self.assertEqual(thinking_prompt.count("Expression and eye rules"), 1)
            self.assertEqual(thinking_prompt.count("State performance story arc"), 0)
            self.assertEqual(thinking_prompt.count("Reject if any frame has"), 1)
            self.assertNotIn("random emotion collage", thinking_prompt)
            self.assertNotIn("Mouth pixels must be", thinking_prompt)
            self.assertNotIn("No single-dot mouth", thinking_prompt)
            self.assertIn("Good state read is not enough if identity, cleanup, eye grammar, anatomy, or scale drifts", thinking_prompt)

    def test_thinking_prompt_rejects_speck_sparkle_cues_as_primary_read(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "CueLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Thinking cue solidity lock", thinking_prompt)
            self.assertIn("use deliberate compact cue shapes, not loose specks", thinking_prompt)
            self.assertIn("no lightbulb, star, ray, sparkle, diamond, rune, punctuation, UI icon, or glow", thinking_prompt)
            self.assertIn("random symbol", thinking_prompt)
            self.assertIn("The peak should be a compact cue beat, not a mandated symbol or puff count", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("do not use loose sparkles", cue_plan["states"]["thinking"]["thinkingCueVocabularyPolicy"])
            self.assertIn("The final frame must not leave a stray dot", cue_plan["states"]["thinking"]["thinkingCueVocabularyPolicy"])

    def test_thinking_prompt_makes_idea_peak_deliberate_without_mandating_puffs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "IdeaPeak",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "ambiguous-limbs",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("idea lands", thinking_prompt)
            self.assertIn("primary cue element is only slightly larger, never oversized", thinking_prompt)
            self.assertIn("cue vocabulary", thinking_prompt)
            self.assertIn("do not enlarge the cue to prove the idea landed", thinking_prompt)
            self.assertIn("stable source-to-peak trail", thinking_prompt)
            self.assertIn("smallest element stays closest to the inferred source", thinking_prompt)
            self.assertIn("Do not let intermediate cue elements drift downward", thinking_prompt)
            self.assertNotIn("exactly three visible puffs", thinking_prompt)
            self.assertNotIn("main puff", thinking_prompt)

    def test_near_head_thinking_cues_do_not_merge_into_body_core(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "CoreLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("keep the cue close, low, compact, and secondary", thinking_prompt)
            self.assertIn("keep the cue close, low, compact, and secondary", thinking_prompt)
            self.assertIn("or high peak", thinking_prompt)
            self.assertIn("Do not make a tall vertical stack", thinking_prompt)
            self.assertIn("Do not let the cue force the mascot smaller", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            policy = cue_plan["states"]["thinking"]["thinkingCueContinuityPolicy"]
            self.assertIn("Near-head cue core-separation lock", policy)
            self.assertIn("keep a 2-4 px chroma-key gap", policy)
            self.assertIn("Near-head cue footprint lock", policy)
            self.assertIn("stable source-to-peak trail", policy)
            self.assertIn("smallest element stays closest to the inferred source", policy)
            self.assertIn("Do not let intermediate cue elements drift downward", policy)

    def test_no_limb_thinking_prompt_forbids_chin_marks_and_worried_faces(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "PebbleDot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "no-limbs",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("not surprised, answering, worried, sleepy, or confused", thinking_prompt)
            self.assertIn("No appendage acting", thinking_prompt)
            self.assertIn("Do not invent hands, hand-to-chin poses, or face-touching appendages", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingStateReadPolicy", cue_plan["states"]["thinking"])
            self.assertIn("faceArtifactPolicy", cue_plan["states"]["thinking"])
            self.assertIn("No-limb thinking face artifact guard", cue_plan["states"]["thinking"]["faceArtifactPolicy"])
            self.assertIn("worried squiggles", cue_plan["states"]["thinking"]["thinkingStateReadPolicy"])

    def test_thinking_processing_blink_must_not_read_as_sleepy(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "BlinkBot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "ambiguous-limbs",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("quick active processing blink", thinking_prompt)
            self.assertIn("round open o-mouth, exclamation mouth, speaking syllable mouth", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            policy = cue_plan["states"]["thinking"]["thinkingStateReadPolicy"]
            self.assertIn("quick active processing blink, not sleep", policy)
            self.assertIn("Processing blinks should use simple closed curved or short horizontal eyes", policy)

    def test_hands_thinking_prompt_prefers_safe_hand_acting_over_face_patch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Helper",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Use only existing appendages", thinking_prompt)
            self.assertIn("make one polished thinking face-touch beat", thinking_prompt)
            self.assertIn("Face-touch is acceptable only when the appendage stays connected", thinking_prompt)
            self.assertIn("does not read as a face patch, duplicate appendage, or lower-face blob", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingCueStrategy", cue_plan["states"]["thinking"])
            self.assertIn("Hands/paws thinking", cue_plan["states"]["thinking"]["thinkingCueStrategy"])
            self.assertIn("Face-touch quality gate", cue_plan["states"]["thinking"]["thinkingCueStrategy"])

    def test_thinking_prompt_blocks_mood_jumps_and_cue_pop_dropout(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "LoopBot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "ambiguous-limbs",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("not surprised, answering, worried, sleepy, or confused", thinking_prompt)
            self.assertIn("Story arc: neutral-curious", thinking_prompt)
            self.assertIn("no lightbulb, star, ray, sparkle, diamond, rune, punctuation, UI icon", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingMoodContinuityPolicy", cue_plan["states"]["thinking"])
            self.assertIn("thinkingCueContinuityPolicy", cue_plan["states"]["thinking"])
            self.assertIn("Thinking mood continuity lock", cue_plan["states"]["thinking"]["thinkingMoodContinuityPolicy"])
            self.assertIn("Cue continuity lock", cue_plan["states"]["thinking"]["thinkingCueContinuityPolicy"])
            self.assertIn("must not pop in for one frame", cue_plan["states"]["thinking"]["thinkingCueContinuityPolicy"])

    def test_thinking_prompt_uses_one_cue_vocabulary_and_bans_icon_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "CueBot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Use one compact source-appropriate non-chroma-key cue vocabulary only", thinking_prompt)
            self.assertIn("no lightbulb, star, ray, sparkle, diamond, rune, punctuation, UI icon", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingCueVocabularyPolicy", cue_plan["states"]["thinking"])
            self.assertIn("Thinking cue vocabulary lock", cue_plan["states"]["thinking"]["thinkingCueVocabularyPolicy"])

    def test_row_prompt_locks_canonical_base_features_against_redesign(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "BaseLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single top antenna",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("thinking row prompt - compact", thinking_prompt)
            self.assertIn("Preserve the same mascot body, palette, outline weight, appendage count", thinking_prompt)
            self.assertIn("Must-keep identity props/accessories: single top antenna", thinking_prompt)
            self.assertIn("Do not skew, stretch, rotate, squash, or warp", thinking_prompt)
            self.assertIn("extra/missing held prop", thinking_prompt)
            self.assertIn("Canonical base row lock", prepare.CANONICAL_BASE_ROW_LOCK)
            self.assertNotIn("same antenna count", prepare.CANONICAL_BASE_ROW_LOCK)
            self.assertNotIn("robot UI detail", prepare.CANONICAL_BASE_ROW_LOCK)

    def test_row_prompt_locks_simple_face_panels_against_skew_and_warp(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "PanelLock",
                    "--description",
                    "A rounded robot mascot with a simple cream face panel and plain rounded body.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Do not skew, stretch, rotate, squash, or warp the body core or face-bearing area", thinking_prompt)
            self.assertIn("Show motion through tiny bob, side shift, mouth/blink change", prepare.CANONICAL_BASE_ROW_LOCK)
            self.assertNotIn("cream fill", prepare.CANONICAL_BASE_ROW_LOCK)

    def test_row_prompt_forbids_floor_shadows_as_motion_cues(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "ShadowLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("No smooth illustration", thinking_prompt)
            self.assertIn("shadows", thinking_prompt)
            self.assertIn("Perfectly uniform", thinking_prompt)
            self.assertIn("exact flat flood-fill", thinking_prompt)
            self.assertIn("non-native pixel-art rendering", thinking_prompt)

    def test_row_prompt_locks_eye_grammar_against_hollow_or_inverted_eyes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "EyeLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")

            for prompt in (thinking_prompt, answering_prompt):
                self.assertIn("Eye grammar to preserve", prompt)
                self.assertIn("Closed", prompt)
                self.assertIn("wrong eye grammar", prompt)
            self.assertIn("No white crescent side-glance eyes, hollow/mismatched eyes", thinking_prompt)
            self.assertIn("No hollow or inverted eyes, mismatched eyes, extra catchlights, symbol eyes", answering_prompt)

    def test_inferred_eye_grammar_hint_is_recorded_and_inherited(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"
            eye_grammar = (
                "large matched black oval eyes with one blocky white upper highlight each; "
                "keep highlight count, size relationship, spacing, and dark fill stable"
            )

            result = prepare.main(
                [
                    "--companion-name",
                    "EyeHint",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--eye-grammar",
                    eye_grammar,
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            request = json.loads((out_dir / "companion_request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["visualLanguage"]["eyeGrammar"], eye_grammar)
            base_prompt = (out_dir / "prompts" / "base.md").read_text(encoding="utf-8")
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn(f"Eye grammar to preserve: {eye_grammar}", base_prompt)
            self.assertIn(f"Eye grammar to preserve: {eye_grammar}", thinking_prompt)

    def test_solid_dark_eye_mascots_keep_dark_open_eyes_dominant(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "DarkEyes",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Open eyes preserve source-matched fill/outline/highlights", thinking_prompt)
            self.assertIn("No white crescent side-glance eyes", thinking_prompt)
            self.assertIn("hollow/mismatched eyes, extra catchlights, symbol eyes", thinking_prompt)
            self.assertIn("For solid dark base eyes", prepare.EYE_IDENTITY_CONTINUITY_POLICY)

    def test_row_prompt_uses_stable_eye_acting_when_gaze_would_break_eye_style(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "StableEyes",
                    "--description",
                    "A small robot with a cream face panel and two dark oval eyes.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")

            for prompt in (thinking_prompt, answering_prompt):
                self.assertIn("Eye grammar to preserve", prompt)
                self.assertIn("Closed", prompt)
            self.assertIn("No white crescent side-glance eyes", thinking_prompt)
            self.assertIn("No hollow or inverted eyes", answering_prompt)
            self.assertIn("Eye acting stability rule", prepare.EYE_IDENTITY_CONTINUITY_POLICY)
            self.assertIn("No eye-to-symbol swaps", prepare.EYE_IDENTITY_CONTINUITY_POLICY)

    def test_closed_eye_blinks_preserve_eye_positions_without_symbol_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "BlinkLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "idle,thinking,answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            for state in ("idle", "thinking", "answering"):
                prompt = (out_dir / "prompts" / f"{state}.md").read_text(encoding="utf-8")
                self.assertIn("Closed", prompt)
                self.assertIn("same eye positions and spacing", prompt)
                if state == "thinking":
                    self.assertIn("simple short curved lines", prompt)
                    self.assertIn("symbol eyes", prompt)
                else:
                    self.assertIn("not symbols or a new eye style", prompt)

    def test_thinking_prompt_defines_face_panel_exclusion_zone_for_hand_mascots(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "ClearFace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("make one polished thinking face-touch beat", thinking_prompt)
            self.assertIn("leaves eyes and mouth readable", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Face-touch quality gate", cue_plan["states"]["thinking"]["thinkingCueStrategy"])
            self.assertIn("under-chin presenting poses", cue_plan["states"]["thinking"]["thinkingCueStrategy"])

    def test_default_thinking_hand_motion_is_side_anchored_for_generic_mittens(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "MittenBot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("make one polished thinking face-touch beat", thinking_prompt)
            self.assertIn("If unclear, use a side-anchored lift/tilt/tuck", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            strategy = cue_plan["states"]["thinking"]["thinkingCueStrategy"]
            self.assertIn("Default generic mitten-hand thinking motion remains conservative", strategy)
            self.assertIn("one clean face-touch audition", strategy)

    def test_simple_mittens_do_not_inherit_articulated_hand_actions_in_thinking(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "MittenBot",
                    "--description",
                    "A friendly tiny helper robot with two rounded side mittens and no fingers.",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Use only existing appendages", thinking_prompt)
            self.assertIn("make one polished thinking face-touch beat", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            strategy = cue_plan["states"]["thinking"]["thinkingCueStrategy"]
            self.assertIn("Face-touch quality gate", strategy)
            self.assertIn("If it reads as a new cheek, nose, lower-face patch", strategy)

    def test_thinking_prompt_keeps_recognition_from_becoming_answering_mouth(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "MouthLock",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("tiny closed-mouth recognition smile", thinking_prompt)
            self.assertIn("round open o-mouth, exclamation mouth, speaking syllable mouth", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Recognition in thinking should be a closed or tiny pixel smile", cue_plan["states"]["thinking"]["thinkingStateReadPolicy"])

    def test_default_frame_counts_use_hatch_style_eight_frame_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "idle,thinking,working,answering",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["atlas"]["columns"], 8)
            self.assertEqual(manifest["states"]["idle"]["frames"], 8)
            self.assertEqual(manifest["states"]["thinking"]["frames"], 8)
            self.assertEqual(manifest["states"]["working"]["frames"], 8)
            self.assertEqual(manifest["states"]["answering"]["frames"], 8)

    def test_layout_guides_are_labeled_as_construction_not_output_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Guidey",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            request = json.loads((out_dir / "companion_request.json").read_text(encoding="utf-8"))
            usage = request["layoutGuides"][0]["usage"]
            self.assertIn("construction input only", usage)
            self.assertIn("intentionally empty", usage)
            self.assertIn("not a mascot preview", usage)

    def test_no_hand_working_prompt_allows_freestanding_work_props(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assert_no_verbose_policy_dump(working_prompt)
            self.assertIn("Show a concrete before/during/after work action", working_prompt)
            self.assertIn("No text, pseudo-writing, generic UI panel", working_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("freestandingPropPolicy", cue_plan["states"]["working"])
            self.assertIn("Freestanding props are a last resort", cue_plan["states"]["working"]["freestandingPropPolicy"])
            self.assertIn("chunky non-text progress blocks", cue_plan["states"]["working"]["workPropMarkPolicy"])
            self.assertIn("Working must show the mascot working through a concrete action", cue_plan["states"]["working"]["workTargetPolicy"])

    def test_hands_working_prompt_keeps_prop_marks_non_text(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Handbot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assertIn("No text, pseudo-writing, generic UI panel", working_prompt)
            self.assertIn("duplicate identity prop", working_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("chunky non-text progress blocks", cue_plan["states"]["working"]["workPropMarkPolicy"])
            self.assertIn("inactive or blank -> being operated/sorted/checked -> progress/result", cue_plan["states"]["working"]["workTargetPolicy"])
            self.assertIn("Choose the work target from the mascot's visual language", cue_plan["states"]["working"]["workTargetFitPolicy"])
            self.assertIn("Do not shape the work cue like a duplicate of the mascot's identity prop", cue_plan["states"]["working"]["workIdentityPropEffectPolicy"])

    def test_working_prompt_forbids_cloned_identity_prop_effects(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "PropMage",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single trident staff held on the left side",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assertIn("Must-keep identity props/accessories: single trident staff held on the left side", working_prompt)
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assertIn("duplicate identity prop", working_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Use the existing held prop as the source of the action", cue_plan["states"]["working"]["workIdentityPropEffectPolicy"])
            self.assertIn("Keep long-prop working motion small and active-end-focused", cue_plan["states"]["working"]["workLongHeldPropPolicy"])
            self.assertIn("no copied mascot-specific prop, logo, badge, emblem, or identity symbol inside the target", cue_plan["states"]["working"]["workIdentityPropEffectPolicy"])

    def test_working_prompt_locks_reference_palette_friendly_face_bloom_and_acting(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "BrightStaff",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single glowing staff held on the left side",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            working_prompt = (out_dir / "prompts" / "working.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(working_prompt, state="working")
            self.assertIn("Preserve the same mascot body, silhouette, palette", working_prompt)
            self.assertIn("busy-but-friendly", working_prompt)
            self.assertIn("Show a concrete before/during/after work action", working_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Reference palette fidelity lock", prepare.REFERENCE_PALETTE_FIDELITY_POLICY)
            self.assertIn("Every working frame must stay busy-friendly or cute-focused", cue_plan["states"]["working"]["workStateReadPolicy"])
            self.assertIn("Active-end bloom animation must change frame by frame", cue_plan["states"]["working"]["workLongHeldPropPolicy"])
            self.assertIn("Every frame must include a visible mascot acting change", cue_plan["states"]["working"]["workMascotActingPolicy"])

    def test_answering_prompt_prioritizes_talking_performance_over_required_voice_cue(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Talky",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "answering",
                    "--anatomy-class",
                    "hands",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(answering_prompt, state="answering")
            self.assertIn("Mouth shapes must visibly cycle", answering_prompt)
            self.assertIn("Mouth-led talking is primary", answering_prompt)
            self.assertIn("Optional voice pixels or pips", answering_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Talking performance is primary", cue_plan["states"]["answering"]["voiceCuePolicy"])
            self.assertIn("Answering must look like engaged talking/streaming", cue_plan["states"]["answering"]["answeringStateReadPolicy"])

    def test_no_limb_answering_prompt_prefers_mouth_only_over_detached_voice_cues(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "PebbleDot",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "answering",
                    "--anatomy-class",
                    "no-limbs",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")
            self.assert_compact_row_prompt(answering_prompt, state="answering")
            self.assertIn("Mouth-led talking is primary", answering_prompt)
            self.assertIn("omit them if they look like cheek marks", answering_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn(
                "For no-limb, fins-no-hands, and ambiguous-limb mascots, prefer mouth-only answering",
                cue_plan["states"]["answering"]["voiceCuePolicy"],
            )

    def test_hands_thinking_prompt_tracks_hand_roles_without_near_face_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out_dir = Path(raw_tmp) / "run"

            result = prepare.main(
                [
                    "--companion-name",
                    "Tridy",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--anatomy-class",
                    "hands",
                    "--identity-prop",
                    "single trident staff held on the left side",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Must-keep identity props/accessories: single trident staff held on the left side", thinking_prompt)
            self.assertIn("Keep any prop-holding appendage attached", thinking_prompt)
            self.assertIn("Face-touch is acceptable only when the appendage stays connected", thinking_prompt)
            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("Hand/appendage role continuity", prepare.HAND_ROLE_CONTINUITY_POLICY)
            self.assertIn("appendageActingPolicy", cue_plan["states"]["thinking"])

    def test_preparer_writes_hatch_style_imagegen_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            reference = tmp_path / "reference.png"
            write_fixture_png(reference)

            result = prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--reference",
                    str(reference),
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking,working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            self.assertEqual(result, 0)
            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            self.assertEqual(jobs["primary_generation_skill"], "$imagegen")
            self.assertEqual([job["id"] for job in jobs["jobs"]], ["base", "thinking", "working"])
            self.assertEqual(
                jobs["row_generation_policy"]["after_base_recorded"],
                "subagents-preferred-when-user-authorized",
            )
            self.assertTrue(jobs["row_generation_policy"]["requires_explicit_user_authorization"])
            self.assertIn("record-result", jobs["row_generation_policy"]["parent_owned_actions"])
            self.assertEqual(jobs["row_generation_policy"]["subagent_return_contract"], ["selected_source", "qa_note"])

            base_job = jobs["jobs"][0]
            thinking_job = jobs["jobs"][1]
            self.assertTrue(base_job["requires_grounded_generation"])
            self.assertFalse(base_job["allow_prompt_only_generation"])
            self.assertFalse(base_job["subagent_eligible"])
            self.assertEqual(base_job["generation_owner"], "parent")
            self.assertIn("original mascot reference and style source", base_job["input_images"][0]["role"])
            self.assertIn("do not copy noisy or non-flat preview background", base_job["input_images"][0]["role"])
            self.assertEqual(thinking_job["depends_on"], ["base"])
            self.assertFalse(thinking_job["allow_prompt_only_generation"])
            self.assertTrue(thinking_job["subagent_eligible"])
            self.assertEqual(thinking_job["generation_owner"], "subagent-default-when-available")
            self.assertEqual(thinking_job["recording_owner"], "parent")
            self.assertEqual(thinking_job["subagent_handoff"]["return_only"], ["selected_source", "qa_note"])
            self.assertIn("edit imagegen-jobs.json", thinking_job["subagent_handoff"]["forbidden_actions"])
            self.assertIn("exact requested frame count", thinking_job["subagent_handoff"]["visual_checks"])
            self.assertIn("recordable cleanup-ready background", thinking_job["subagent_handoff"]["visual_checks"][2])
            self.assertIn("white-sclera or crescent", thinking_job["subagent_handoff"]["visual_checks"][4])
            self.assertIn("coherent state story", thinking_job["subagent_handoff"]["visual_checks"][5])
            self.assertIn("visible chroma-key falloff", thinking_job["subagent_handoff"]["qa_note_must_call_out"][0])
            self.assertIn("original mascot reference and style source", thinking_job["input_images"][0]["role"])
            self.assertIn("references/canonical-base.png", thinking_job["identity_reference_paths"])
            self.assertTrue((out_dir / "references" / "reference-01.png").is_file())
            self.assertTrue((out_dir / "references" / "layout-guides" / "thinking.png").is_file())
            self.assertTrue((out_dir / "prompts" / "base.md").is_file())
            self.assertTrue((out_dir / "prompts" / "rows" / "thinking.md").is_file())

            first_status = job_status.status(out_dir)
            self.assertEqual(first_status["counts"]["ready"], 1)
            self.assertEqual(first_status["ready_jobs"][0]["id"], "base")
            self.assertEqual(first_status["ready_jobs"][0]["generation_owner"], "parent")
            self.assertFalse(first_status["ready_jobs"][0]["subagent_eligible"])
            self.assertEqual(first_status["counts"]["blocked"], 2)

    def test_recording_base_creates_canonical_reference_and_unblocks_rows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            reference = tmp_path / "reference.png"
            base_source = source_dir / "ig_base.png"
            row_source = source_dir / "ig_working.png"
            write_fixture_png(reference)
            write_fixture_png(base_source, (245, 252, 255, 255))
            write_fixture_png(row_source, (235, 248, 255, 255))

            prepare.main(
                [
                    "--companion-name",
                    "Glace",
                    "--reference",
                    str(reference),
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--anatomy-class",
                    "fins-no-hands",
                    "--compact",
                    "--quiet",
                ]
            )

            with self.assertRaises(SystemExit):
                record.record_result(
                    run_dir=out_dir,
                    job_id="working",
                    source=row_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                )

            base_result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
            )
            self.assertTrue(base_result["ok"])
            self.assertTrue((out_dir / "references" / "canonical-base.png").is_file())

            ready_after_base = job_status.status(out_dir)
            self.assertEqual(ready_after_base["counts"]["ready"], 1)
            self.assertEqual(ready_after_base["ready_jobs"][0]["id"], "working")
            self.assertEqual(ready_after_base["ready_jobs"][0]["generation_owner"], "subagent-default-when-available")
            self.assertTrue(ready_after_base["ready_jobs"][0]["subagent_eligible"])
            self.assertEqual(ready_after_base["ready_jobs"][0]["subagent_handoff"]["return_only"], ["selected_source", "qa_note"])

            row_result = record.record_result(
                run_dir=out_dir,
                job_id="working",
                source=row_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
            )
            self.assertTrue(row_result["ok"])
            self.assertTrue((out_dir / "generated" / "working.png").is_file())

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            completed = {job["id"]: job for job in jobs["jobs"]}
            self.assertEqual(completed["base"]["status"], "complete")
            self.assertEqual(completed["working"]["status"], "complete")
            self.assertEqual(completed["base"]["source_provenance"], "synthetic-test")
            self.assertIn("canonical_identity_reference", jobs)

    def test_recording_flat_pixel_base_records_clean_style_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            write_flat_pixel_base(base_source)

            prepare.main(
                [
                    "--companion-name",
                    "FlatBase",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )

            self.assertTrue(result["ok"])
            self.assertIn("base_style_analysis", result)
            self.assertTrue(result["base_style_analysis"]["ok"])
            self.assertEqual(result["base_style_analysis"]["warnings"], [])

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            base_job = jobs["jobs"][0]
            self.assertTrue(base_job["base_style_analysis"]["ok"])
            self.assertEqual(base_job["base_style_analysis"]["warnings"], [])
            self.assertEqual(base_job["base_style_analysis"]["background"]["expectedRgb"], [255, 0, 255])

    def test_recording_reads_manifest_style_chroma_key_when_request_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            (run_dir / "manifest.json").write_text(
                json.dumps({"style": {"chromaKey": {"hex": "#00FF00"}}}),
                encoding="utf-8",
            )

            self.assertEqual(record.read_chroma_key_rgb(run_dir), (0, 255, 0))

    def test_recording_strict_base_accepts_transparent_user_art_with_palette_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "artist_base.png"
            write_smooth_gradient_base(base_source, key=(0, 0, 0, 0))

            prepare.main(
                [
                    "--companion-name",
                    "TransparentArtistBase",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="user-provided-integrated-row-art",
                force=False,
                allow_synthetic_test_source=False,
                strict_base_style=True,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["base_style_strict_blocking_warning_codes"], [])
            self.assertTrue(result["base_style_analysis"]["background"]["transparentBackground"])
            warning_codes = {warning["code"] for warning in result["base_style_analysis"]["warnings"]}
            self.assertEqual(warning_codes, {"smooth_or_overdetailed_foreground_palette"})

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            base_job = jobs["jobs"][0]
            self.assertEqual(base_job["source_provenance"], "user-provided-integrated-row-art")
            self.assertEqual(base_job["base_style_strict_blocking_warning_codes"], [])

    def test_recording_base_flags_nonuniform_chroma_key_background(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            write_nonuniform_key_base(base_source)

            prepare.main(
                [
                    "--companion-name",
                    "GlowKey",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            with self.assertRaisesRegex(SystemExit, "base style analysis failed"):
                record.record_result(
                    run_dir=out_dir,
                    job_id="base",
                    source=base_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                    strict_base_style=True,
                )

            self.assertFalse((out_dir / "generated" / "base.png").exists())

            result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=False,
            )
            warning_codes = {warning["code"] for warning in result["base_style_analysis"]["warnings"]}
            self.assertIn("non_uniform_chroma_key_background", warning_codes)

    def test_recording_base_flags_inner_chroma_key_falloff_with_flat_border(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            write_inner_falloff_key_base(base_source)

            prepare.main(
                [
                    "--companion-name",
                    "InnerGlow",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            with self.assertRaisesRegex(SystemExit, "base style analysis failed"):
                record.record_result(
                    run_dir=out_dir,
                    job_id="base",
                    source=base_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                    strict_base_style=True,
                )

            result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=False,
            )
            warning_codes = {warning["code"] for warning in result["base_style_analysis"]["warnings"]}
            self.assertIn("non_uniform_chroma_key_background", warning_codes)
            self.assertEqual(result["base_style_analysis"]["background"]["exactKeyRatio"], 1.0)
            self.assertLess(result["base_style_analysis"]["background"]["backgroundLikeExactKeyRatio"], 1.0)

    def test_recording_base_flags_smooth_gradient_foreground(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            write_smooth_gradient_base(base_source)

            prepare.main(
                [
                    "--companion-name",
                    "GlossyBase",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            result = record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )
            warning_codes = {warning["code"] for warning in result["base_style_analysis"]["warnings"]}
            self.assertIn("smooth_or_overdetailed_foreground_palette", warning_codes)
            self.assertEqual(result["base_style_strict_blocking_warning_codes"], [])

    def test_recording_strict_row_style_blocks_nonuniform_chroma_key_background(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            row_source = source_dir / "ig_working.png"
            write_flat_pixel_base(base_source)
            write_nonuniform_key_base(row_source)

            prepare.main(
                [
                    "--companion-name",
                    "RowGlow",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--quiet",
                ]
            )

            record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )

            with self.assertRaisesRegex(SystemExit, "row source style analysis failed"):
                record.record_result(
                    run_dir=out_dir,
                    job_id="working",
                    source=row_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                    strict_row_style=True,
                )

            self.assertFalse((out_dir / "generated" / "working.png").exists())

            result = record.record_result(
                run_dir=out_dir,
                job_id="working",
                source=row_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_row_style=False,
            )
            warning_codes = {warning["code"] for warning in result["row_source_style_analysis"]["warnings"]}
            self.assertIn("non_uniform_chroma_key_background", warning_codes)
            self.assertEqual(
                result["row_source_style_strict_blocking_warning_codes"],
                ["non_uniform_chroma_key_background"],
            )

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            working_job = next(job for job in jobs["jobs"] if job["id"] == "working")
            self.assertIn("row_source_style_analysis", working_job)
            self.assertEqual(
                working_job["row_source_style_strict_blocking_warning_codes"],
                ["non_uniform_chroma_key_background"],
            )

    def test_recording_strict_row_style_blocks_fake_checkerboard_transparency(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            row_source = source_dir / "ig_working.png"
            write_flat_pixel_base(base_source)
            write_fake_checkerboard_base(row_source)

            prepare.main(
                [
                    "--companion-name",
                    "FakeAlpha",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "working",
                    "--quiet",
                ]
            )

            record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )

            with self.assertRaisesRegex(SystemExit, "fake_checkerboard_transparency_background"):
                record.record_result(
                    run_dir=out_dir,
                    job_id="working",
                    source=row_source,
                    source_provenance="auto",
                    force=False,
                    allow_synthetic_test_source=True,
                    strict_row_style=True,
                )

            result = record.record_result(
                run_dir=out_dir,
                job_id="working",
                source=row_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_row_style=False,
            )
            warning_codes = {warning["code"] for warning in result["row_source_style_analysis"]["warnings"]}
            self.assertIn("fake_checkerboard_transparency_background", warning_codes)
            self.assertIn(
                "fake_checkerboard_transparency_background",
                result["row_source_style_strict_blocking_warning_codes"],
            )

    def test_recording_accepts_built_in_chroma_cleanup_with_original_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            codex_home = tmp_path / "codex-home"
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            generated_dir = codex_home / "generated_images" / "session"
            original_source = generated_dir / "ig_original-thinking.png"
            cleaned_source = tmp_path / "cleaned" / "thinking-alpha.png"
            base_source = source_dir / "ig_base.png"
            write_flat_pixel_base(base_source)
            write_nonuniform_key_base(original_source)
            write_flat_pixel_base(cleaned_source, key=(0, 0, 0, 0))

            prepare.main(
                [
                    "--companion-name",
                    "CleanupPath",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                result = record.record_result(
                    run_dir=out_dir,
                    job_id="thinking",
                    source=cleaned_source,
                    source_provenance="built-in-imagegen-chroma-cleanup",
                    force=False,
                    allow_synthetic_test_source=False,
                    strict_row_style=True,
                    chroma_cleanup_source=original_source,
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source_provenance"], "built-in-imagegen-chroma-cleanup")
            self.assertEqual(result["row_source_style_strict_blocking_warning_codes"], [])
            self.assertEqual(result["chroma_cleanup"]["originalSourcePath"], str(original_source.resolve()))
            self.assertEqual(result["chroma_cleanup"]["originalSourceProvenance"], "built-in-imagegen")
            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            thinking_job = next(job for job in jobs["jobs"] if job["id"] == "thinking")
            self.assertEqual(thinking_job["source_provenance"], "built-in-imagegen-chroma-cleanup")
            self.assertEqual(thinking_job["chroma_cleanup"], result["chroma_cleanup"])

    def test_recording_accepts_codex_app_imagegen_capture_with_sidecar_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "codex-app-imagegen"
            base_source = source_dir / "base.png"
            row_source = source_dir / "thinking.png"
            write_flat_pixel_base(base_source)
            write_flat_pixel_base(row_source)
            metadata_path = row_source.with_name(row_source.name + ".codex-imagegen.json")

            prepare.main(
                [
                    "--companion-name",
                    "CodexAppCapture",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="user-provided-integrated-row-art",
                force=False,
                allow_synthetic_test_source=False,
                strict_base_style=True,
            )

            metadata_path.write_text(
                json.dumps(
                    {
                        "source": "codex-app-imagegen",
                        "sessionPath": str(tmp_path / "rollout-test.jsonl"),
                        "callId": "ig_thinking",
                        "outputPath": str(row_source.resolve()),
                        "sha256": record.file_sha256(row_source),
                    }
                ),
                encoding="utf-8",
            )

            result = record.record_result(
                run_dir=out_dir,
                job_id="thinking",
                source=row_source,
                source_provenance="codex-app-imagegen",
                force=False,
                allow_synthetic_test_source=False,
                strict_row_style=True,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source_provenance"], "codex-app-imagegen")
            self.assertEqual(result["codex_app_imagegen"]["callId"], "ig_thinking")
            self.assertEqual(result["codex_app_imagegen"]["sha256"], record.file_sha256(row_source))
            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            thinking_job = next(job for job in jobs["jobs"] if job["id"] == "thinking")
            self.assertEqual(thinking_job["source_provenance"], "codex-app-imagegen")
            self.assertEqual(thinking_job["codex_app_imagegen"]["callId"], "ig_thinking")

    def test_recording_rejects_chroma_cleanup_without_builtin_original_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp_path = Path(raw_tmp)
            out_dir = tmp_path / "run"
            source_dir = tmp_path / "source"
            base_source = source_dir / "ig_base.png"
            cleaned_source = tmp_path / "cleaned" / "thinking-alpha.png"
            write_flat_pixel_base(base_source)
            write_flat_pixel_base(cleaned_source, key=(0, 0, 0, 0))

            prepare.main(
                [
                    "--companion-name",
                    "CleanupNeedsSource",
                    "--output-dir",
                    str(out_dir),
                    "--states",
                    "thinking",
                    "--quiet",
                ]
            )

            record.record_result(
                run_dir=out_dir,
                job_id="base",
                source=base_source,
                source_provenance="auto",
                force=False,
                allow_synthetic_test_source=True,
                strict_base_style=True,
            )

            with self.assertRaisesRegex(SystemExit, "--chroma-cleanup-source"):
                record.record_result(
                    run_dir=out_dir,
                    job_id="thinking",
                    source=cleaned_source,
                    source_provenance="built-in-imagegen-chroma-cleanup",
                    force=False,
                    allow_synthetic_test_source=False,
                    strict_row_style=True,
                )

if __name__ == "__main__":
    unittest.main()
