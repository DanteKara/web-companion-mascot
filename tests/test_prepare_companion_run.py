import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


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


class PrepareCompanionRunTests(unittest.TestCase):
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
            self.assertIn("thinking", manifest["states"])
            self.assertIn("answering", manifest["states"])

            request = json.loads((out_dir / "companion_request.json").read_text(encoding="utf-8"))
            self.assertNotIn("working", request["states"])

            jobs = json.loads((out_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            job_ids = [job["id"] for job in jobs["jobs"]]
            self.assertNotIn("working", job_ids)
            self.assertIn("thinking", job_ids)

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Thinking also covers processing, retrieval, tool-use waiting, and backend progress", thinking_prompt)
            self.assertIn("Do not create a separate working state unless the user explicitly requests one", thinking_prompt)

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
            self.assertIn("Do not add unrequested chest lights, badges, emblems, screens, buttons, feet, legs, tails, tools, or extra props", base_prompt)
            self.assertIn("For hand-only text concepts, use a rounded lower body with no visible legs or feet", base_prompt)
            self.assertIn("Keep the body front plain unless a chest mark is named", base_prompt)
            self.assertIn("no chest dot, belly light, button, badge, screen, or emblem", base_prompt)

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
            self.assertIn("no broad glossy shine patches on the forehead, body, antenna, mittens, or face panel", base_prompt)
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
            self.assertIn("HatchPet compact source target", base_prompt)
            self.assertIn("The base should read like a Codex app digital pet first and a website mascot second", base_prompt)
            self.assertIn("fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite cell", base_prompt)
            self.assertIn("pixel-art-adjacent low-resolution mascot sprite", base_prompt)
            self.assertIn("flat cel shading with at most one small highlight and one shadow step", base_prompt)
            self.assertIn("no detail that disappears at 192x208", base_prompt)
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
            self.assertIn("Indexed-color sprite cell lock", base_prompt)
            self.assertIn("Use the fewest colors that preserve identity", base_prompt)
            self.assertIn("roughly 8-16 total non-background colors", base_prompt)
            self.assertIn("No per-pixel color ramps", base_prompt)
            self.assertIn("no smooth shade bands", base_prompt)
            self.assertIn("no gradient-filled body, face panel, clothing, props, antenna, or mittens", base_prompt)
            self.assertIn("Favor simpler and flatter over prettier", base_prompt)
            self.assertIn("Part simplification lock", base_prompt)
            self.assertIn("When an antenna is present, simplify it as a tiny plain stem and small cap or nub", base_prompt)
            self.assertIn("not a jewel, gem, crystal, screen, lantern, badge, or glowing ornament", base_prompt)
            self.assertIn("When side mittens or sleeve nubs are present, keep them as simple rounded side blobs", base_prompt)
            self.assertIn("no cuff bands, finger ticks, segmented gloves, dark wrist gadgets, or extra mitten details unless they are visible identity marks in the source", base_prompt)
            self.assertIn("Reference-native style lock", base_prompt)
            self.assertIn("If an attached reference already looks like a HatchPet or Codex digital-pet sprite", base_prompt)
            self.assertIn("Reference-aware palette guide", base_prompt)
            self.assertIn("Build a tiny per-mascot palette from the attached reference or the text concept", base_prompt)
            self.assertIn("Never impose a teal/cream/white-eye palette", base_prompt)
            self.assertIn("Do not blend between palette colors", base_prompt)
            self.assertIn("Reference character direction lock", base_prompt)
            self.assertIn("Keep the strongest character decisions from the provided reference or text concept", base_prompt)
            self.assertIn("Do not substitute a stock robot", base_prompt)
            self.assertIn("do not redesign the mascot while making it more pixel-native", base_prompt)
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
                self.assertIn("Hard native-pixel rendering lock", prompt)
                self.assertIn("Use hard-edged square pixel clusters and 2-3 flat tone steps per material", prompt)
                self.assertIn("No blurred or feathered transitions", prompt)
                self.assertIn("Highlights must be tiny rectangular pixel blocks", prompt)
                self.assertIn("Flat chroma-key lock", prompt)
                self.assertIn("one perfectly uniform solid chroma-key color from corner to corner", prompt)

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
                self.assertIn("State performance story arc", prompt)
                self.assertIn("coherent mini-story", prompt)
                self.assertIn("not a random emotion collage", prompt)
                self.assertIn("Expressions must be adjacent beats", prompt)
                self.assertIn("caused by the state action", prompt)
                self.assertIn("Avoid abrupt mood jumps", prompt)
                self.assertIn("loop cleanly back to the first frame", prompt)
                self.assertIn("State story beats:", prompt)
                self.assertIn("statePerformanceStoryPolicy", cue_plan["states"][state])
                self.assertIn("stateStoryBeats", cue_plan["states"][state])

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn(
                "neutral-curious -> noticing -> pondering -> idea lands -> pleased settle",
                thinking_prompt,
            )
            self.assertIn("not random sad, sleepy, angry, blank, or unrelated faces", thinking_prompt)

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
            self.assertIn("Semantic ladder", working_prompt)
            self.assertIn("busy-but-friendly", working_prompt)
            self.assertIn("Expression lock", working_prompt)
            self.assertIn("do not add eyebrows to a browless mascot", working_prompt)
            self.assertIn("no slanted angry eyes", working_prompt)
            self.assertIn("V-shaped", working_prompt)
            self.assertIn("no held, near-hand", working_prompt)
            self.assertIn("purposeful processing", working_prompt)
            self.assertIn("remain visible after chroma-key cleanup", working_prompt)
            self.assertIn("tiny detached speck", working_prompt)
            self.assertIn("Reject a pretty motif-native effect when it does not communicate the state", working_prompt)
            self.assertIn("Do not place repeated leaf, oval, wing, mitten, paw, droplet", working_prompt)
            self.assertIn("inside the body core", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["style"]["renderingStyle"], "codex-pixel-art")
            self.assertEqual(manifest["style"]["stateClarity"], "semantic-enhancers")
            self.assertEqual(manifest["states"]["working"]["frames"], 6)
            self.assertIn("visualLanguageFit", manifest["states"]["working"]["enhancer"])

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
            self.assertIn("Visible hands may point, present, hold, type, or write", thinking_prompt)
            self.assertIn("Default thinking rows keep hands away from the", thinking_prompt)
            self.assertIn("friendly tiny helper robot", thinking_prompt)
            self.assertIn("Art direction floor", thinking_prompt)
            self.assertIn("polished mascot performance", thinking_prompt)
            self.assertIn("charming mascot-native acting beat", thinking_prompt)
            self.assertIn("Expression variation is mandatory", thinking_prompt)
            self.assertIn("Do not keep the same face in every frame", thinking_prompt)
            self.assertIn("default thinking prompts must keep the mouth, chin, cheek", thinking_prompt)
            self.assertIn("lower face, and face panel unobscured", thinking_prompt)
            self.assertIn("Must-keep identity props/accessories: single chest screen", thinking_prompt)
            self.assertIn("Identity prop contract", thinking_prompt)
            self.assertIn("keep its count, side, scale, attachment, and basic silhouette stable", thinking_prompt)
            self.assertIn("Preserve signature props by default even when another cue is present", thinking_prompt)
            self.assertIn("State cues must not cover, replace, recolor, merge with, or grow out of identity props", thinking_prompt)
            self.assertIn("antenna bulbs, ears, horns, hats, badges, emblems, staffs, or wands", thinking_prompt)
            self.assertIn("Omit a must-keep prop only when the state card says", thinking_prompt)
            self.assertIn("Do not duplicate signature props", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(cue_plan["visualLanguage"]["motifs"], ["small panel glow"])
            self.assertEqual(cue_plan["visualLanguage"]["identityProps"], ["single chest screen"])
            self.assertEqual(cue_plan["states"]["working"]["visualAidDecision"], "use only if acting alone would be unclear at 64-96 px")

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

            for prompt in (thinking_prompt, answering_prompt):
                self.assertIn("Visible appendage acting policy", prompt)
                self.assertIn("Do not leave hands, paws, sleeves, or held props frozen across the whole row", prompt)
                self.assertIn("include at least two small safe appendage acting beats", prompt)
                self.assertIn("prop-holding hand remains attached while the free hand can lift, present, tuck, point, or settle", prompt)
                self.assertIn("no extra hands, duplicate arms, detached mittens, finger clusters, or new grip anatomy", prompt)

            self.assertIn("thinking rows can use a side-anchored low free-hand lift, side bob", thinking_prompt)
            self.assertIn("tiny outward side tilt", thinking_prompt)
            self.assertIn("low outer-body tuck beside the body, or staff-hand grip shift", thinking_prompt)
            self.assertIn("default thinking prompts must keep the mouth, chin, cheek", thinking_prompt)
            self.assertIn("avoid under-chin hand poses", thinking_prompt)
            self.assertIn("staff-hand grip shift", thinking_prompt)
            self.assertIn("answering rows can use a small presenting beat, conversational hand bounce, palm-up gesture, or free-hand settle", answering_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("appendageActingPolicy", cue_plan["states"]["thinking"])
            self.assertIn("appendageActingPolicy", cue_plan["states"]["answering"])

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
                self.assertIn("Professional state acting choreography", prompt)
                self.assertIn("Coordinate three synchronized tracks", prompt)
                self.assertIn("expression track", prompt)
                self.assertIn("body/appendage track", prompt)
                self.assertIn("cue/prop track", prompt)
                self.assertIn("Do not let all motion live in the prop, bubble, sparkle, or cue", prompt)
                self.assertIn("parked hands", prompt)
                self.assertIn("stateActingChoreography", cue_plan["states"][state])

            thinking_prompt = (out_dir / "prompts" / "thinking.md").read_text(encoding="utf-8")
            self.assertIn("Frame 2: eyes glance up or aside while the hands stay side-anchored", thinking_prompt)
            self.assertIn("Frame 4: cue grows to slightly larger while one hand makes a side-anchored low side", thinking_prompt)
            self.assertIn("Frame 7: recognition smile; hands start returning to rest", thinking_prompt)

            answering_prompt = (out_dir / "prompts" / "answering.md").read_text(encoding="utf-8")
            self.assertIn("Frame 3: wider mouth; free hand begins a small presenting gesture if anatomy supports it", answering_prompt)
            self.assertIn("Frame 5: quick speaking blink or smile-open beat with a tiny conversational hand bounce", answering_prompt)
            self.assertIn("Frame 7: closed smile while the hand settles", answering_prompt)
            self.assertIn("also match any already accepted state row in this run", answering_prompt)
            self.assertIn("Do not zoom the mascot in to fill the cell", answering_prompt)

            success_prompt = (out_dir / "prompts" / "success.md").read_text(encoding="utf-8")
            self.assertIn("Frame 4: proud peak with hands/paws/appendages lifted only if they already exist", success_prompt)

            error_prompt = (out_dir / "prompts" / "error.md").read_text(encoding="utf-8")
            self.assertIn("Frame 4: small recoil or tuck; appendages pull inward only if that preserves the original count", error_prompt)

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
            self.assertIn("not hand-to-chin", thinking_prompt)
            self.assertIn("no held props or tiny detached specks in the draft plan", working_prompt)
            self.assertIn("rim-touching", working_prompt)
            self.assertIn("invented angry eyebrows", working_prompt)
            self.assertIn("slanted angry eyes", working_prompt)
            self.assertIn("extra wings", working_prompt)
            self.assertIn("Cue colors and shapes must stay distinct", working_prompt)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("brace", manifest["states"]["working"]["enhancer"]["description"])

    def test_thinking_prompt_requires_visible_bubble_growth_arc(self) -> None:
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
            self.assertIn("Frame-by-frame acting arc", thinking_prompt)
            self.assertIn("Six-frame acting story", thinking_prompt)
            self.assertIn("two small close puffs sit low beside the upper head/hat/hood/face edge", thinking_prompt)
            self.assertIn("two puffs plus a very small third puff form a compact cluster", thinking_prompt)
            self.assertIn("compact three-puff thought bubble", thinking_prompt)
            self.assertIn("one slightly larger main puff and two smaller close support puffs", thinking_prompt)
            self.assertIn("thought cue shrinks to one tiny close remnant or resolves cleanly", thinking_prompt)
            self.assertIn("neutral-curious -> noticing -> pondering -> idea lands -> pleased settle", thinking_prompt)
            self.assertIn("The face, body timing, and any side appendage should sell thinking even before the bubble is noticed", thinking_prompt)
            self.assertIn("Do not make a tall vertical stack", thinking_prompt)
            self.assertIn("Do not let the cue force the mascot smaller", thinking_prompt)
            self.assertIn("non-flat magenta #FF00FF background", thinking_prompt)
            self.assertIn("Use only existing side appendages as subtle side-attached bobs", thinking_prompt)
            self.assertIn("Do not turn fins, sleeves, mitts, or ambiguous side shapes into hands", thinking_prompt)
            self.assertNotIn("open black eyes", thinking_prompt)
            self.assertNotIn("white puff", thinking_prompt)
            self.assertNotIn("free hand or hand-like appendage", thinking_prompt)
            self.assertNotIn("non-flat green background", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("frameArc", cue_plan["states"]["thinking"])
            self.assertIn("small -> slightly larger -> medium -> smaller -> tiny/settle", cue_plan["states"]["thinking"]["frameArc"])

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
            self.assertIn("do not use loose sparkles, isolated white specks, star glints, diamond flecks, or single-pixel dust", thinking_prompt)
            self.assertIn("The cue must read as one deliberate compact thought puff, bubble cluster, idea orb, or processing aura", thinking_prompt)
            self.assertIn("The final frame must not leave a stray dot", thinking_prompt)
            self.assertIn("either resolve cleanly to no cue or keep a tiny settled cue still visibly associated with the same state source", thinking_prompt)

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
            self.assertIn("Near-head cue core-separation lock", thinking_prompt)
            self.assertIn("do not alpha-connect the thought cue to the head, antenna, hood, face panel, body core, or outline when it grows", thinking_prompt)
            self.assertIn("keep a 2-4 px chroma-key gap between the growing cue and the mascot core", thinking_prompt)
            self.assertIn("Use proximity, eye tracking, timing, or one tiny separated tail dot", thinking_prompt)
            self.assertIn("without making QA measure the cue as body size", thinking_prompt)
            self.assertIn("Near-head cue footprint lock", thinking_prompt)
            self.assertIn("does not become the tallest or widest row element and force atlas assembly to shrink the mascot body", thinking_prompt)
            self.assertIn("tuck it closer to the upper head/hat/hood/face edge instead of changing mascot scale", thinking_prompt)

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
            self.assertIn("Thinking must read as curious pondering and processing, not worry, confusion, sadness, anger, sleepiness, or error", thinking_prompt)
            self.assertIn("Use neutral-curious, tiny closed pondering mouths, one-pixel thoughtful line mouths, blink/hold, and small recognition-smile beats", thinking_prompt)
            self.assertIn("avoid downturned frowns, curled lower-lip marks, worried squiggles, and confused/error mouth shapes", thinking_prompt)
            self.assertIn("No-limb thinking face artifact guard", thinking_prompt)
            self.assertIn("do not add chin-touch, cheek-touch, hand-to-chin, lower-face squiggles, extra mouth ticks, chin marks", thinking_prompt)
            self.assertIn("moustache-like pixels, or small appendage-colored marks on the lower face or chin", thinking_prompt)
            self.assertIn("If the mascot has no appendages, thinking must come from eyes, blink timing, mouth shape, body tilt, and the thought cue", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingStateReadPolicy", cue_plan["states"]["thinking"])
            self.assertIn("faceArtifactPolicy", cue_plan["states"]["thinking"])

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
            self.assertIn("Any closed-eye thinking frame must read as a quick active processing blink, not sleep, idle rest, fatigue, or meditation", thinking_prompt)
            self.assertIn("Keep the thought cue active during that blink", thinking_prompt)
            self.assertIn("place open-eye curious or recognition frames immediately before and after it", thinking_prompt)
            self.assertIn("Do not use long closed-eye holds, droopy eyelids, sleepy breathing, or relaxed sleeping mouths in thinking", thinking_prompt)
            self.assertIn("Processing blinks should use simple closed curved or short horizontal eyes", thinking_prompt)
            self.assertIn("not squeezed shut X-eyes, chevron eyes, scrunched effort eyes, or strain grimaces", thinking_prompt)

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
            self.assertIn("Hands/paws thinking strategy", thinking_prompt)
            self.assertIn("keep the face panel and lower face completely clear in every frame", thinking_prompt)
            self.assertIn("Default generic mitten-hand thinking motion is side-anchored", thinking_prompt)
            self.assertIn("use a side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck only", thinking_prompt)
            self.assertIn("with a visible gap below the face", thinking_prompt)
            self.assertIn("Do not touch, cover, underline, or frame the mouth, chin, cheek", thinking_prompt)
            self.assertIn("hand-to-chin, hand-to-mouth, clasped hands under the mouth", thinking_prompt)
            self.assertIn("scalloped mitten/bib cluster below the face", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingCueStrategy", cue_plan["states"]["thinking"])
            self.assertIn("Hands/paws thinking", cue_plan["states"]["thinking"]["thinkingCueStrategy"])

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
            self.assertIn("Thinking mood continuity lock", thinking_prompt)
            self.assertIn("no worried frown frames", thinking_prompt)
            self.assertIn("no sleepy closed-eye smile frames", thinking_prompt)
            self.assertIn("no open exclamation or speaking-mouth frames", thinking_prompt)
            self.assertIn("Cue continuity lock", thinking_prompt)
            self.assertIn("Keep the cue separate from identity props", thinking_prompt)
            self.assertIn("do not use an antenna tip, ear, horn", thinking_prompt)
            self.assertIn("must not cover, replace, recolor, or merge with an antenna bulb", thinking_prompt)
            self.assertIn("mascot body footprint stays stable", thinking_prompt)
            self.assertIn("close 2-4 px chroma-key gap or tiny separated tail dot", thinking_prompt)
            self.assertIn("must not pop in for one frame, jump upward into a giant peak, or drop out abruptly", thinking_prompt)
            self.assertIn("final frame should either keep a tiny settled cue or clearly resolve back to frame 1 without a visual snap", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingMoodContinuityPolicy", cue_plan["states"]["thinking"])
            self.assertIn("thinkingCueContinuityPolicy", cue_plan["states"]["thinking"])

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
            self.assertIn("Thinking cue vocabulary lock", thinking_prompt)
            self.assertIn("Use one cue family across the whole row", thinking_prompt)
            self.assertIn("do not switch between thought bubble, data cloud, lightbulb, exclamation, sparkle, or icon", thinking_prompt)
            self.assertIn("no detached lightbulb", thinking_prompt)
            self.assertIn("no one-frame idea icon", thinking_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("thinkingCueVocabularyPolicy", cue_plan["states"]["thinking"])

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
            self.assertIn("Canonical base row lock", thinking_prompt)
            self.assertIn("copy the canonical base's main silhouette and design language", thinking_prompt)
            self.assertIn("same antenna count and basic antenna shape", thinking_prompt)
            self.assertIn("same face screen or face panel shape", thinking_prompt)
            self.assertIn("same eye style", thinking_prompt)
            self.assertIn("same chest mark or emblem when present", thinking_prompt)
            self.assertIn("If the canonical base has a plain body with no chest mark", thinking_prompt)
            self.assertIn("no new chest panel, status light, belly screen, button, badge", thinking_prompt)
            self.assertIn("dot cluster, readout, emblem, or robot UI detail", thinking_prompt)
            self.assertIn("If the canonical base has a rounded lower body with no feet", thinking_prompt)
            self.assertIn("no foot nubs, shoes, base tabs, toe pixels, shadow feet, or lower protrusions", thinking_prompt)
            self.assertIn("Do not upgrade the face into a different eye style", thinking_prompt)
            self.assertIn("do not bend, add, remove, or duplicate the antenna", thinking_prompt)

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
            self.assertIn("Simple face/body stability lock", thinking_prompt)
            self.assertIn("do not skew, stretch, rotate, squash, or turn a face panel into a trapezoid", thinking_prompt)
            self.assertIn("keep face-panel corners, outline thickness, and cream fill shape consistent", thinking_prompt)
            self.assertIn("show motion through 1-2 px bob, tiny side shift, mouth/blink change, appendage beat, or cue timing", thinking_prompt)

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
            self.assertIn("No floor-motion artifacts", thinking_prompt)
            self.assertIn("do not show bobbing, jumping, thinking, or emphasis with floor shadows, contact shadows, ground lines, baseline marks, landing marks, or dark under-body strokes", thinking_prompt)
            self.assertIn("the sprite must be only the mascot and approved state cue on chroma key", thinking_prompt)

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
                self.assertIn("Eye identity continuity lock", prompt)
                self.assertIn("preserve the canonical base eye grammar", prompt)
                self.assertIn("same eye count, shape, size, spacing, outline color, pupil or fill color", prompt)
                self.assertIn("same catchlight/highlight count and placement logic", prompt)
                self.assertIn("Do not invert dark pupils into hollow white eyes", prompt)
                self.assertIn("do not turn solid dark eyes into white oval eyes with dark rims", prompt)
                self.assertIn("do not add extra catchlights", prompt)
                self.assertIn("no glossy anime eyes, vertical slit pupils, square UI eyes", prompt)
                self.assertIn("no one-frame eye-style swaps", prompt)
                self.assertIn("both eyes must stay matched and anchored to the same face-panel positions", prompt)

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
            self.assertIn("For solid dark base eyes", thinking_prompt)
            self.assertIn("open eyes must remain mostly dark with the original tiny highlight", thinking_prompt)
            self.assertIn("do not expose white sclera crescents", thinking_prompt)
            self.assertIn("do not make a white crescent or white cutout the dominant eye shape", thinking_prompt)
            self.assertIn("Gaze can be shown by moving the dark eye oval or tiny highlight only a pixel or two", thinking_prompt)
            self.assertIn("do not show side glances by carving white crescent gaps into dark eyes", thinking_prompt)

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
                self.assertIn("Eye acting stability rule", prompt)
                self.assertIn("If a requested up-glance, side-glance, blink, or speaking beat would require changing the eye style, keep the eyes forward or nearly forward", prompt)
                self.assertIn("carry the acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead", prompt)
                self.assertIn("Keep eye centers inside the original eye boxes", prompt)
                self.assertIn("never slide eyes onto cheeks, panel edges, the mouth line, or outside the face panel", prompt)
                self.assertIn("No eye-to-symbol swaps", prompt)
                self.assertIn("do not replace eyes with loading dots, LEDs, status bars, diagonal slashes, crosses, punctuation, or reaction icons", prompt)

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
                self.assertIn("Closed-eye blinks", prompt)
                self.assertIn("replace each open eye with a simple short closed curve or horizontal pixel line", prompt)
                self.assertIn("same eye positions and spacing", prompt)
                self.assertIn("not X-eyes, chevrons, eyebrows, reaction glyphs", prompt)
                self.assertIn("not mouth-like lower-face squiggles", prompt)

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
            self.assertIn("Face-panel exclusion zone", thinking_prompt)
            self.assertIn("no hand, paw, sleeve, mitten, finger, or prop may enter the face panel", thinking_prompt)
            self.assertIn("or sit centered directly below the mouth/chin", thinking_prompt)
            self.assertIn("Keep thinking hand beats outside the face-panel horizontal span when possible", thinking_prompt)
            self.assertIn("beside the body, shoulder-side, or low outer-body zones", thinking_prompt)
            self.assertIn("Do not use hand-to-body beats under the face panel", thinking_prompt)
            self.assertIn("no lower-face/chin-adjacent hand poses", thinking_prompt)
            self.assertIn("no under-chin presenting pose", thinking_prompt)

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
            self.assertIn("Default generic mitten-hand thinking motion is side-anchored", thinking_prompt)
            self.assertIn("side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck only", thinking_prompt)
            self.assertIn("Do not move one hand inward toward the face", thinking_prompt)
            self.assertIn("do not point toward the head", thinking_prompt)
            self.assertIn("do not cross the body front", thinking_prompt)
            self.assertIn("keep hands attached to the side mid-body", thinking_prompt)
            self.assertIn("not the bottom edge where they read as feet, legs, or lower tabs", thinking_prompt)

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
            self.assertIn("Simple mitten safeguard", thinking_prompt)
            self.assertIn("simple mittens, sleeve nubs, rounded side hands, or fingerless blobs", thinking_prompt)
            self.assertIn("side-bob, side-tilt, tiny outward tilt, low side lift, or side tuck only", thinking_prompt)
            self.assertIn("do not use pointing, presenting across the body, typing, writing, gripping, or face-touch acting", thinking_prompt)

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
            self.assertIn("Recognition in thinking should be a closed or tiny pixel smile", thinking_prompt)
            self.assertIn("not a wide open speaking mouth", thinking_prompt)
            self.assertIn("not an exclamation mouth", thinking_prompt)
            self.assertIn("not a syllable mouth from answering", thinking_prompt)

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
            self.assertIn("HatchPet-style sprite artifact rules", working_prompt)
            self.assertIn("Prefer pose, expression, and silhouette changes over decorative effects", working_prompt)
            self.assertIn("Effects are allowed only when they are state-relevant, opaque, hard-edged, pixel-style", working_prompt)
            self.assertIn("source-bound to the mascot silhouette, mouth edge, hand, tool, worn prop, or state source", working_prompt)
            self.assertIn("Freestanding props are a last resort", working_prompt)
            self.assertIn("Prefer body-surface, rim-touching, attached, or overlapping processing cues", working_prompt)
            self.assertIn("freestanding or resting work prop", working_prompt)
            self.assertIn("small slate, tablet, blank card stack, token tray, chunky work tile", working_prompt)
            self.assertIn("beside or in front of the mascot", working_prompt)
            self.assertIn("the mascot works by looking, leaning, bobbing, and reacting", working_prompt)
            self.assertIn("not by holding, typing, writing, or inventing hands", working_prompt)
            self.assertIn("clear background gap", working_prompt)
            self.assertIn("no part of the prop or activity marks may touch", working_prompt)
            self.assertIn("inside or on the prop surface", working_prompt)
            self.assertIn("not in the empty gap", working_prompt)
            self.assertIn("merge the prop with the mascot body", working_prompt)
            self.assertIn("Frame-by-frame acting arc", working_prompt)
            self.assertIn("target wakes up", working_prompt)
            self.assertIn("sorting/checking/gathering", working_prompt)
            self.assertIn("chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens", working_prompt)
            self.assertIn("no readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, or list rows", working_prompt)
            self.assertIn("Working must show the mascot working through a concrete action", working_prompt)
            self.assertIn("visible before/during/after transformation", working_prompt)
            self.assertIn("not a decorative detached prop or status icon", working_prompt)
            self.assertIn("Choose the work target from the mascot's visual language", working_prompt)
            self.assertIn("Place the work target in a believable interaction zone", working_prompt)
            self.assertIn("Avoid notebook, paper, page, or parchment-like surfaces", working_prompt)
            self.assertIn("fine stripes, wood-grain lines, plank lines, or parallel grooves", working_prompt)
            self.assertIn("Do not make the work surface read as a tiny document full of writing", working_prompt)
            self.assertIn(
                "Do not use breath puffs, speech beads, panting clouds, sleepy exhale cues, or tired closed-eye holds to show working",
                working_prompt,
            )
            self.assertIn("A closed-eye frame in working may only be a quick blink", working_prompt)
            self.assertIn("working cues must stay at the work target or tool tip, not at the mouth", working_prompt)

            cue_plan = json.loads((out_dir / "qa" / "state-cue-plan.json").read_text(encoding="utf-8"))
            self.assertIn("freestandingPropPolicy", cue_plan["states"]["working"])

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
            self.assertIn("Use this prompt as an authoritative sprite-production spec", working_prompt)
            self.assertIn("HatchPet-style sprite artifact rules", working_prompt)
            self.assertIn("first through face, gaze, body lean, timing, and existing hands or identity props", working_prompt)
            self.assertIn("For any slate, tablet, blank card stack, token tray, panel, or work surface", working_prompt)
            self.assertIn("chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens", working_prompt)
            self.assertIn("solid and unruled", working_prompt)
            self.assertIn("no readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, or list rows", working_prompt)
            self.assertIn("Working must show the mascot working through a concrete action, not a decorative detached prop", working_prompt)
            self.assertIn("staff-tip glyph", working_prompt)
            self.assertIn("inactive or blank -> being operated/sorted/checked -> progress/result", working_prompt)
            self.assertIn("Tech/robot mascots can use panels, tablets, sliders, or status blocks", working_prompt)
            self.assertIn("Fantasy or magic mascots should use spell circles, rune tiles, charm tokens", working_prompt)
            self.assertIn("the mascot's gaze, hand, body, or identity prop must visibly cause the change", working_prompt)
            self.assertIn("near the active hand, paw, mouth, active tool end, staff head, wand tip", working_prompt)
            self.assertIn("For long props, the active end is the wand tip, staff head, tool bit, pointer tip, brush tip, blade tip, or nozzle", working_prompt)
            self.assertIn("prefer close-contact targets that touch, overlap, hover just above", working_prompt)
            self.assertIn("Avoid floor-level token rows and far-floating targets", working_prompt)
            self.assertIn("The viewer should understand what the mascot is acting on in every frame", working_prompt)
            self.assertIn("Use a theme-native result mark", working_prompt)
            self.assertIn("generic check marks only when the mascot's visual language supports product/tool UI", working_prompt)
            self.assertIn("Do not shape the work cue like a duplicate of the mascot's identity prop", working_prompt)
            self.assertIn("no second staff, wand, tool, weapon, badge, emblem, or prop-shaped glyph", working_prompt)
            self.assertIn("Do not echo identity emblems, logos, badges, weapon silhouettes, or signature markings inside the work target", working_prompt)
            self.assertIn("Use plain abstract dots, squares, diamonds, bars, or motes instead", working_prompt)

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
            self.assertIn("Use the existing held prop as the source of the action", working_prompt)
            self.assertIn("do not summon, draw, or echo a second copy of that prop", working_prompt)
            self.assertIn("active pose replaces the resting pose", working_prompt)
            self.assertIn("do not show the resting prop and a second active copy in the same frame", working_prompt)
            self.assertIn("active end is the wand tip, staff head, tool bit, pointer tip, brush tip, blade tip, or nozzle", working_prompt)
            self.assertIn("not the floor, base, butt end, handle end, or lower shaft", working_prompt)
            self.assertIn("Keep long-prop working motion small and active-end-focused", working_prompt)
            self.assertIn("prefer an attached active-end bloom, aura, pulse, or contact mark over a separate rune/tile/object", working_prompt)
            self.assertIn("Do not use a detached diamond, object, emblem, badge, floor target, or prop-shaped echo", working_prompt)
            self.assertIn("The bloom must wrap around, touch, or overlap the active end", working_prompt)
            self.assertIn("Avoid large full-body leans, big cross-body swings, diagonal staff sweeps", working_prompt)
            self.assertIn("same top-of-head height, bottom edge, body core width, and prop count", working_prompt)
            self.assertIn("target should be a distinct small rune, tile, mote, orb, tray, panel, or token", working_prompt)
            self.assertIn("no copied trident, logo, badge, emblem, or identity symbol inside the target", working_prompt)

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
            self.assertIn("Reference palette fidelity lock", working_prompt)
            self.assertIn("Preserve the actual reference colors for eye whites/highlights, pupils, eye outlines, face base color, cheek marks, outfit, props, and signature markings", working_prompt)
            self.assertIn("Do not force white eyes or white highlights when the reference uses another color", working_prompt)
            self.assertIn("only keep whites white when the source uses white", working_prompt)
            self.assertIn("Do not let a glow, aura, bloom, prop color, or gold effect tint or recolor the mascot identity palette", working_prompt)
            self.assertIn("Every working frame must stay busy-friendly or cute-focused", working_prompt)
            self.assertIn("reject even a single frame with angry, hostile, slanted, narrowed, or V-shaped eyes", working_prompt)
            self.assertIn("Active-end bloom animation must change frame by frame", working_prompt)
            self.assertIn("dim seed -> small bloom -> brighter wrap -> peak cluster -> shrinking settle", working_prompt)
            self.assertIn("Do not paste the same static glow in every frame", working_prompt)
            self.assertIn("Small sparkle pixels are allowed only when they belong to the active-end bloom cluster", working_prompt)
            self.assertIn("touching, overlapping, or within a few pixels of the active prop end", working_prompt)
            self.assertIn("Every frame must include a visible mascot acting change", working_prompt)
            self.assertIn("not only bloom or cue animation", working_prompt)
            self.assertIn("body bob, head tilt, robe/clothing settle, hand grip shift, subtle prop follow-through, eye direction, blink, mouth shape, or cheek/body tilt", working_prompt)
            self.assertIn("emotion arc should read as notice -> focus -> effort -> progress -> pleased settle", working_prompt)

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
            self.assertIn("Talking performance is primary", answering_prompt)
            self.assertIn("speech pips, sound ticks, tiny rings, breath marks, or voice pixels are optional", answering_prompt)
            self.assertIn("closed smile -> small open -> wider open -> syllable hold -> smile", answering_prompt)
            self.assertIn("tiny conversational bob", answering_prompt)
            self.assertIn("If a voice cue is used", answering_prompt)
            self.assertIn("near the mouth/lip edge", answering_prompt)
            self.assertIn("not as a random bubble beside the head", answering_prompt)
            self.assertIn("Voice cues are optional and should be omitted when they cannot stay clearly attached to the mouth", answering_prompt)
            self.assertIn("touch or overlap the mouth/lip edge or begin within 1-2 pixels of it", answering_prompt)
            self.assertIn("short 2-3 frame outward trail", answering_prompt)
            self.assertIn("not a single isolated speck in only one frame", answering_prompt)
            self.assertIn("not one-frame voice ticks or one-frame sound marks", answering_prompt)
            self.assertIn("If a cue cannot appear in at least two adjacent frames with a mouth-origin progression, omit it", answering_prompt)
            self.assertIn("not a cheek mark, face marking, or detached fleck", answering_prompt)
            self.assertIn("Use breath, frost, smoke, or cloud puffs only when they belong to the source mascot", answering_prompt)
            self.assertIn("Expression variation is mandatory", answering_prompt)
            self.assertIn("Mouth shapes must change clearly even when no voice cue is used", answering_prompt)
            self.assertIn("voice cue should support the speaking impression instead of carrying the whole state", answering_prompt)
            self.assertIn("Answering must look like engaged talking/streaming, not tired panting or exhaling", answering_prompt)
            self.assertIn("avoid sleepy closed-eye holds unless it is a quick speaking blink", answering_prompt)
            self.assertIn("Do not over-police tiny cue geometry when the mascot already reads as talking", answering_prompt)

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
            self.assertIn(
                "For no-limb, fins-no-hands, and ambiguous-limb mascots, prefer mouth-only answering",
                answering_prompt,
            )
            self.assertIn("mouth shapes, eye engagement, blink timing, and body rhythm", answering_prompt)
            self.assertIn("omit voice pixels instead of creating a cheek mark or detached fleck", answering_prompt)

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
            self.assertIn("Hand/appendage role continuity", thinking_prompt)
            self.assertIn(
                "account for every original hand, arm, paw, sleeve, fin, wing, or tentacle in every frame",
                thinking_prompt,
            )
            self.assertIn(
                "If the mascot holds an identity prop, keep the prop-holding appendage attached and identifiable",
                thinking_prompt,
            )
            self.assertIn("Default thinking hand acting leaves the face clear", thinking_prompt)
            self.assertIn("low outer-body beats beside the body instead of near-mouth, under-chin, or centered-below-face poses", thinking_prompt)
            self.assertIn(
                "no third hand, extra arm, duplicate sleeve, detached mitten, or new paw/finger cluster",
                thinking_prompt,
            )

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

            base_job = jobs["jobs"][0]
            thinking_job = jobs["jobs"][1]
            self.assertTrue(base_job["requires_grounded_generation"])
            self.assertFalse(base_job["allow_prompt_only_generation"])
            self.assertIn("original mascot reference and style source", base_job["input_images"][0]["role"])
            self.assertIn("do not copy noisy or non-flat preview background", base_job["input_images"][0]["role"])
            self.assertEqual(thinking_job["depends_on"], ["base"])
            self.assertFalse(thinking_job["allow_prompt_only_generation"])
            self.assertIn("original mascot reference and style source", thinking_job["input_images"][0]["role"])
            self.assertIn("references/canonical-base.png", thinking_job["identity_reference_paths"])
            self.assertTrue((out_dir / "references" / "reference-01.png").is_file())
            self.assertTrue((out_dir / "references" / "layout-guides" / "thinking.png").is_file())
            self.assertTrue((out_dir / "prompts" / "base.md").is_file())
            self.assertTrue((out_dir / "prompts" / "rows" / "thinking.md").is_file())

            first_status = job_status.status(out_dir)
            self.assertEqual(first_status["counts"]["ready"], 1)
            self.assertEqual(first_status["ready_jobs"][0]["id"], "base")
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
            self.assertIn("smooth_or_overdetailed_foreground_palette", warning_codes)


if __name__ == "__main__":
    unittest.main()
