#!/usr/bin/env python3
"""Prepare a web companion mascot run with state cue plans and row prompts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CANONICAL_BASE_PATH = "references/canonical-base.png"
BASE_OUTPUT_PATH = "generated/base.png"
LAYOUT_GUIDE_DIR = "references/layout-guides"
LAYOUT_GUIDE_SAFE_MARGIN_X = 24
LAYOUT_GUIDE_SAFE_MARGIN_Y = 22

DEFAULT_STATES = [
    "idle",
    "greeting",
    "listening",
    "thinking",
    "working",
    "answering",
    "success",
    "error",
    "confused",
    "sleeping",
]

SEMANTIC_STATES = {"listening", "thinking", "working", "answering", "success", "error", "confused"}
LONG_STATES = {"thinking", "working", "answering"}
STATE_PURPOSES = {
    "idle": "default calm presence",
    "greeting": "chat opens or first welcome",
    "listening": "user is typing or speaking",
    "thinking": "assistant is planning before output",
    "working": "assistant is using tools, retrieval, search, files, or backend work",
    "answering": "assistant is streaming a response",
    "success": "task or answer completed successfully",
    "error": "recoverable failure or warning",
    "confused": "input is unclear or needs clarification",
    "sleeping": "inactive, minimized, or offline",
}

STATE_ACTING = {
    "idle": "slow breathing, soft blink, tiny posture settle",
    "greeting": "friendly anticipation, small wave or body bounce, warm smile, return to rest",
    "listening": "attentive lean toward the user, eyes tracking, small blink hold",
    "thinking": "curious head tilt, eyes up or to the side, hand/appendage pondering pose when supported, changing thoughtful mouth and eye beats",
    "working": "busy-but-friendly concentration, attentive eye tracking toward the work target, lean-in, faster purposeful body/hand/prop motion; never angry, no slanted angry eyes, no V-shaped brow or eye marks",
    "answering": "speaking mouth shapes with voice cue originating at the mouth, bright eyes, rhythmic face/body beats",
    "success": "cheerful bounce, proud hold, bright face, return to loop",
    "error": "worried recognition, small recoil or slump, recovery beat",
    "confused": "squint, head tilt, uncertain mouth, small recovery",
    "sleeping": "closed eyes, slow breathing, sleepy settle",
}

STATE_VISUAL_AIDS = {
    "listening": "small attached sound rings or attentive pose only when needed",
    "thinking": "compact side-origin thought puff, idea orb, or hand-to-chin only when anatomy supports it; the largest cue stays secondary to the mascot",
    "working": "existing work prop when anatomy supports it; otherwise a freestanding/resting work prop or compact attached processing cue with purposeful cycling, sorting, checking, or gathering motion that clearly reads as active work, not random sparkle or tiny detached specks",
    "answering": "mouth shapes first; tiny no-text voice pixels or breath puffs close to the face when needed",
    "success": "small check/glint, proud pose, or raised existing prop",
    "error": "attached tear, warning charm, prop droop, or small attached smoke/stars",
    "confused": "tiny question cue only if expression and tilt are not enough",
}

STATE_REJECTS = {
    "working": "anger, hostile eyes, slanted angry eyes, V-shaped eyes, invented angry eyebrows or brow marks, decorative particles that do not read as work, unsupported held tools, static prop with no work motion, text-like prop marks, pseudo-writing, code lines, ruled notebook lines",
    "answering": "speech panels, text, punctuation, generic chat UI, mouthless talking cues",
    "thinking": "generic icon straight above the head, oversized second head/body-sized thought orb, static dots, face-touch by unsupported appendages",
    "listening": "microphone props for non-voice apps, detached sound clutter",
    "success": "large confetti, loose sparkles, text labels",
    "error": "red X labels, detached symbols, scenery",
    "confused": "text labels or large punctuation panels",
}

STATE_FRAME_ARCS = {
    "thinking": (
        "Frame-by-frame acting arc: 1 neutral-curious face and stable identity props, 2 eyes glance up/side "
        "and supported hand/appendage begins a pondering pose, 3 small thinking mouth and small bubble/tiny first puff, "
        "4 medium bubble with more curious eyes, 5 largest compact bubble/orb while eyes track it, "
        "6 small blink or pondering hold, 7 small smile/idea recognition, 8 settle back into the loop. "
        "Keep the thought cue secondary to the mascot: the largest bubble is never larger than about one-third "
        "of the mascot body width, and do not let the thought cue become a second head/body-sized orb. "
        "For shorter or longer rows, preserve the same expression-changing neutral -> curious -> pondering -> "
        "recognition -> settle arc and the same small -> medium -> largest compact cue growth; this is not the "
        "same face or same bubble pasted in every frame."
    ),
    "working": (
        "Frame-by-frame acting arc: 1 mascot notices a concrete work target, 2 leans in and the target wakes up while eyes focus on it, "
        "3 begins an action on the target, 4 active work peak with hand/prop/body follow-through, "
        "5 visible progress change on the target, 6 small blink/effort or satisfied beat, 7 result/check/sorted state, "
        "8 settle back while the target remains active. For shorter or longer rows, preserve the same notice -> "
        "operate/sort/check -> result -> settle arc with meaningful face, gaze, hand/prop, and target changes."
    ),
    "answering": (
        "Frame-by-frame acting arc: 1 neutral/listen face with closed or tiny smile mouth, 2 small open mouth, "
        "3 wider speaking mouth and first attached voice pixel at the mouth corner, 4 clearest speaking beat with "
        "voice cue growing outward from the mouth, 5 smile-open mouth or blink hold, 6 smaller mouth and cue retracts, "
        "7 closed-mouth smile, 8 settle back into the loop. The voice cue must originate from and overlap/touch the "
        "mouth or lip edge before drifting outward; it must not appear as a random bubble beside the head."
    ),
}

NO_HAND_WORK_PROP_POLICY = (
    "For simple/no-hand mascots, a freestanding or resting work prop is allowed when it sits beside or in "
    "front of the mascot and does not require grip anatomy. Use a mascot-native small slate, tablet, "
    "blank card stack, token tray, chunky work tile, or solid work surface with visible sorting/checking/gathering activity; the mascot "
    "works by looking, leaning, bobbing, and reacting, not by holding, typing, writing, or inventing hands. "
    "Keep a clear background gap between the mascot and prop; no part of the prop or activity marks may touch "
    "the body, appendages, outline, or effects. Keep sorting/checking/gathering motion inside or on the prop "
    "surface, not in the empty gap, because rising pips, sparkles, crystals, or motion marks can merge the "
    "prop with the mascot body during cleanup and QA."
)

WORK_PROP_MARK_POLICY = (
    "For any slate, tablet, blank card stack, token tray, panel, or work surface, use only chunky non-text progress "
    "blocks, dots, check marks, sliders, or sorting tokens. Use 1-4 large simple marks that can read at "
    "64-96 px; no readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, "
    "ruled notebook lines, or list rows. Avoid notebook, paper, page, or parchment-like surfaces unless the "
    "user specifically asked for them; if they are used, keep the surface blank except for chunky non-text tokens. "
    "Keep tray/tile/slate surfaces solid and unruled; avoid fine stripes, wood-grain lines, plank lines, or "
    "parallel grooves that can read as notebook rules or pseudo-writing at small sizes. "
    "If anatomy supports typing or writing, show that action through hand/body motion while the surface marks remain non-text. "
    "Do not make the work surface read as a tiny document full of writing."
)

WORK_TARGET_POLICY = (
    "Working must show the mascot working on a concrete target, not merely posing beside status icons. Choose one "
    "small mascot-native work target: slate, tablet, token tray, card stack, work tile, tool, staff-tip glyph, "
    "magical work circle, sorting tokens, or an existing identity prop used as a pointer/brace. The target needs a "
    "visible before/during/after transformation: inactive or blank -> being operated/sorted/checked -> progress/result. "
    "For mascots with a staff, wand, tool, or held identity prop, preserve that prop and place the work target near "
    "the prop tip or free hand so the action reads as deliberate work. Do not use random decorative squares, generic "
    "floating UI icons, loose sparkles, or a check mark with no preceding work action."
)

WORK_TARGET_FIT_POLICY = (
    "Choose the work target from the mascot's visual language. Tech/robot mascots can use panels, tablets, sliders, "
    "or status blocks. Fantasy or magic mascots should use spell circles, rune tiles, charm tokens, staff-tip glyphs, "
    "or glowing sorted motes rather than app-like UI blocks. Nature mascots can sort leaves, seeds, stones, or wooden "
    "tokens. Icy/water mascots can use frost tiles, droplets, or crystal tokens. Food/plush/toy mascots should use "
    "their own simple objects. The target must still communicate work through before/during/after transformation and "
    "the mascot's gaze, hand, body, or identity prop must visibly cause the change."
)

WORK_TARGET_INTERACTION_POLICY = (
    "Place the work target in a believable interaction zone: near the active hand, paw, mouth, tool tip, staff tip, "
    "or directly in front of the mascot's gaze. Do not let the target drift to the floor, far side, or empty space "
    "unless a visible gaze line, hand pose, tool/staff alignment, aura connection, or body lean makes the causal "
    "relationship obvious. For mascots with real hands, paws, staffs, wands, tools, or held identity props, prefer "
    "close-contact targets that touch, overlap, hover just above, or sit within a few pixels of the active hand/tool "
    "tip. Avoid floor-level token rows and far-floating targets unless the whole character design naturally works "
    "from the floor. The viewer should understand what the mascot is acting on in every frame."
)

BODY_SURFACE_CUE_POLICY = (
    "For body-surface, rim-touching, or compact attached processing cues on no-limb, fin, wing, paw, or other "
    "simple-appendage mascots, keep the cue inside the body core or as one small rim-touching mark. Do not place "
    "repeated leaf, oval, wing, mitten, paw, droplet, or appendage-colored tokens along the lower rim or side edges "
    "where they read as feet, extra limbs, extra wings, new paws, or detached appendages. Prefer one small central "
    "glyph/status band or 1-3 high-contrast square, dot, check, or token marks inside the silhouette. Cue colors and "
    "shapes must stay distinct from sprouts, ears, fins, wings, paws, sleeves, tails, or other real anatomy."
)

ARTISTIC_QUALITY_POLICY = (
    "Art direction floor: make the row feel like a polished mascot performance, not a checklist of constraints. "
    "Choose the most charming mascot-native acting beat that still preserves identity: expressive eyes, mouth shapes, "
    "head/body tilt, timing, appendage follow-through, and a tiny state cue only when it improves readability. "
    "The result should look like the referenced character naturally doing the state in Codex pixel-pet style, with "
    "confident simple shapes, tasteful asymmetry, and deliberate frame-to-frame acting. Reject bland, stiff, generic, "
    "or symbol-only rows even when the anatomy is technically correct."
)

FACE_TOUCH_SILHOUETTE_POLICY = (
    "For face-touch, chin-touch, cheek-touch, near-face thinking, presenting, or held-prop gestures, keep every "
    "interacting hand, paw, sleeve, tentacle, or arm visibly connected to its original shoulder/body anchor with a "
    "clear silhouette path. Leave a tiny readable gap or outline separation where the appendage nears the face or "
    "prop so it does not merge into a new cheek, nose, mitten, duplicated hand, or face patch. Use broad pixel-mitt "
    "or paw poses rather than tiny fingers unless the reference clearly has fingers."
)

IDENTITY_PROP_POLICY = (
    "Identity prop contract: preserve must-keep props, emblems, clothing silhouettes, and signature accessories as "
    "part of the mascot identity. Simplify ornate detail into a few readable pixel clusters, not noisy filigree. "
    "If a prop appears in a state row, keep its count, side, scale, attachment, and basic silhouette stable across "
    "the row; animate it with small pose/angle/follow-through changes instead of redesigning it. Preserve signature "
    "props by default even when another cue is present; place the cue in available space, near the mouth, near the "
    "head, or near the prop tip instead of dropping the prop. Omit a must-keep prop only when the state card says "
    "that exact prop is optional for that whole row, never because a thought bubble, voice puff, or work cue was added. "
    "Do not duplicate signature props, turn decorative trim into extra limbs, or mutate a staff/tool/emblem into a "
    "different object unless that row is explicitly auditioning a new design."
)

VOICE_CUE_POLICY = (
    "Answering voice cues must be mouth-origin cues. The first voice pixel, puff, breath mark, or sound ring must "
    "touch or overlap the mouth/lip edge, then travel only a short distance outward with the speaking mouth shapes. "
    "Keep it close enough that a viewer can tell it comes from the mascot speaking. Do not place speech puffs, chat "
    "bubbles, or loose orbs beside the cheek, hand, staff, or hood if they do not originate from the mouth."
)

EXPRESSION_VARIATION_POLICY = (
    "Expression variation is mandatory for high-visibility states. Across the row, change at least two of: eye "
    "direction, blink/closed-eye frame, pupil/highlight placement, mouth shape, smile/open-mouth size, cheek/body tilt, "
    "or hand/appendage pose. Do not keep the same face in every frame while only moving the visual aid."
)

ANATOMY_GUIDANCE = {
    "hands": (
        "Visible hands may point, present, hold, touch the face, type, or write when the reference supports it. "
        "Keep exactly the original hands/arms; no duplicates."
    ),
    "paws": (
        "Paws may gesture, brace chunky props, or present broadly. Avoid finger-dependent typing/writing unless "
        "the reference clearly has fingers."
    ),
    "fins-no-hands": (
        "Fins stay side-attached with side-bob, tilt, tuck, or tiny wave. Do not turn fins into hands, fingers, "
        "detached mitts, arms, or front-body appendage patches. Freestanding/resting props may sit beside or "
        "in front of the mascot; fins must not grip, type, write, or become hands unless a separate audition proves that exact design can safely brace a prop."
    ),
    "no-limbs": (
        "Use face, body posture, breathing, attached marks, aura, near-head effects, or freestanding/resting props. "
        "Do not use held, near-hand, typing, writing, grip, or hand-operated props. Tablets, slates, blank card stacks, "
        "token trays, chunky work tiles, and work surfaces are allowed only when they rest beside or in front of the mascot and animate on their own."
    ),
    "ambiguous-limbs": (
        "Treat appendages conservatively until the reference audit proves their affordances. Prefer face/body "
        "acting and small anchored aids over risky grip or face-touch poses."
    ),
}

CHROMA_KEY_CANDIDATES = [
    ("magenta", "#FF00FF"),
    ("cyan", "#00FFFF"),
    ("yellow", "#FFFF00"),
    ("blue", "#0000FF"),
    ("orange", "#FF7F00"),
    ("green", "#00FF00"),
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "companion"


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def frame_count_for(state: str, compact: bool) -> int:
    if compact:
        return 6 if state in LONG_STATES else 6
    return 8


def durations_for(state: str, frames: int) -> list[int]:
    if state in {"working", "answering"}:
        base = [110, 100, 110, 120]
    elif state in {"thinking", "listening"}:
        base = [140, 120, 140, 180]
    elif state == "sleeping":
        base = [260, 320, 420, 320]
    else:
        base = [150, 130, 150, 190]
    durations = [base[index % len(base)] for index in range(frames)]
    durations[-1] = max(durations[-1], 180)
    return durations


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise SystemExit(f"invalid chroma key color: {value}; expected #RRGGBB")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return sum((left[index] - right[index]) ** 2 for index in range(3)) ** 0.5


def image_metadata(path: Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image:
        return {
            "path": str(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def sampled_reference_pixels(paths: list[Path]) -> list[tuple[int, int, int]]:
    from PIL import Image

    pixels: list[tuple[int, int, int]] = []
    for path in paths:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
            image.thumbnail((128, 128), Image.Resampling.LANCZOS)
            data = image.tobytes()
            for index in range(0, len(data), 4):
                red, green, blue, alpha = data[index : index + 4]
                if alpha <= 16:
                    continue
                pixels.append((red, green, blue))

    non_background = [
        pixel
        for pixel in pixels
        if not (pixel[0] > 244 and pixel[1] > 244 and pixel[2] > 244)
    ]
    return non_background or pixels


def choose_chroma_key(reference_paths: list[Path], requested: str) -> dict[str, Any]:
    if requested.lower() != "auto":
        rgb = parse_hex_color(requested)
        return {
            "hex": rgb_to_hex(rgb),
            "rgb": list(rgb),
            "name": "user-selected",
            "selection": "manual",
        }

    pixels = sampled_reference_pixels(reference_paths) if reference_paths else []
    if not pixels:
        rgb = parse_hex_color("#FF00FF")
        return {
            "hex": "#FF00FF",
            "rgb": list(rgb),
            "name": "magenta",
            "selection": "fallback",
        }

    scored: list[tuple[float, int, str, tuple[int, int, int]]] = []
    for preference_index, (name, hex_color) in enumerate(CHROMA_KEY_CANDIDATES):
        rgb = parse_hex_color(hex_color)
        distances = sorted(color_distance(rgb, pixel) for pixel in pixels)
        percentile_index = max(0, min(len(distances) - 1, int(len(distances) * 0.01)))
        scored.append((distances[percentile_index], -preference_index, name, rgb))

    score, _preference, name, rgb = max(scored)
    return {
        "hex": rgb_to_hex(rgb),
        "rgb": list(rgb),
        "name": name,
        "selection": "auto",
        "score": round(score, 2),
    }


def visual_aid_mode_for(state: str, state_clarity: str) -> str:
    if state_clarity == "pose-only" or state not in SEMANTIC_STATES:
        return "pose-only"
    return "use only if acting alone would be unclear at 64-96 px"


def build_visual_language(args: argparse.Namespace) -> dict[str, Any]:
    motifs = args.motif or ["infer mascot-native motifs from the reference"]
    identity_props = args.identity_prop or []
    forbidden = args.forbid_cue or [
        "generic UI symbols that do not fit the reference",
        "text labels",
        "speech panels",
        "decorative particles that do not communicate the state",
    ]
    return {
        "sourceVibe": args.source_vibe or "Infer from the reference before choosing state cues.",
        "motifs": motifs,
        "identityProps": identity_props,
        "forbiddenGenericCues": forbidden,
    }


def build_state_plan(state: str, anatomy_class: str, state_clarity: str) -> dict[str, str]:
    visual_aid = STATE_VISUAL_AIDS.get(state, "none unless the pose is unclear")
    freestanding_prop_policy = ""
    body_surface_cue_policy = ""
    if state == "thinking" and anatomy_class in {"fins-no-hands", "no-limbs", "ambiguous-limbs"}:
        visual_aid = "compact side-origin thought puff or idea orb; use eyes, tilt, and blink timing, not hand-to-chin"
    if anatomy_class == "no-limbs" and state == "working":
        visual_aid = (
            "face/body acting plus a freestanding or resting work prop, compact attached processing cue, or "
            "body-surface processing cue with purposeful cycling, sorting, checking, or gathering motion; "
            "no held, near-hand, or tiny detached speck props"
        )
        freestanding_prop_policy = NO_HAND_WORK_PROP_POLICY
        body_surface_cue_policy = BODY_SURFACE_CUE_POLICY
    if anatomy_class in {"fins-no-hands", "ambiguous-limbs"} and state == "working":
        visual_aid = (
            "busy-but-friendly face/body acting plus a freestanding or resting work prop, compact attached cue, "
            "rim-touching cue, or body-surface processing cue; no held props or tiny detached specks in the draft plan"
        )
        freestanding_prop_policy = NO_HAND_WORK_PROP_POLICY
        body_surface_cue_policy = BODY_SURFACE_CUE_POLICY
    if state_clarity == "pose-only":
        visual_aid = "none; communicate through acting, timing, and existing identity props only"
        freestanding_prop_policy = ""
        body_surface_cue_policy = ""
    return {
        "state": state,
        "semanticRead": STATE_PURPOSES.get(state, state),
        "actingFirst": STATE_ACTING.get(state, "clear face, posture, and timing"),
        "visualAidDecision": visual_aid_mode_for(state, state_clarity),
        "suggestedVisualAid": visual_aid,
        "frameArc": STATE_FRAME_ARCS.get(
            state,
            "Frame-by-frame acting arc: each frame must change face, gaze, posture, appendage motion, prop motion, or cue position enough to read as animation.",
        ),
        "freestandingPropPolicy": freestanding_prop_policy,
        "workPropMarkPolicy": WORK_PROP_MARK_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetPolicy": WORK_TARGET_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetFitPolicy": WORK_TARGET_FIT_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetInteractionPolicy": WORK_TARGET_INTERACTION_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "bodySurfaceCuePolicy": body_surface_cue_policy,
        "voiceCuePolicy": VOICE_CUE_POLICY if state == "answering" and state_clarity != "pose-only" else "",
        "rejectIf": STATE_REJECTS.get(state, "unclear state read, off-vibe symbol, identity drift, extra anatomy"),
    }


def draw_dashed_line(
    draw: Any,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: str,
    dash: int = 8,
    gap: int = 6,
) -> None:
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        for y in range(min(y1, y2), max(y1, y2), dash + gap):
            draw.line((x1, y, x2, min(y + dash, max(y1, y2))), fill=fill)
        return
    if y1 == y2:
        for x in range(min(x1, x2), max(x1, x2), dash + gap):
            draw.line((x, y1, min(x + dash, max(x1, x2)), y2), fill=fill)
        return
    raise ValueError("draw_dashed_line only supports horizontal or vertical lines")


def create_layout_guide(
    path: Path,
    *,
    state: str,
    frames: int,
    cell_width: int,
    cell_height: int,
) -> dict[str, Any]:
    from PIL import Image, ImageDraw

    width = frames * cell_width
    height = cell_height
    image = Image.new("RGB", (width, height), "#f7f7f7")
    draw = ImageDraw.Draw(image)

    for index in range(frames):
        left = index * cell_width
        right = left + cell_width - 1
        draw.rectangle((left, 0, right, height - 1), outline="#111111", width=2)

        safe_left = left + LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_top = LAYOUT_GUIDE_SAFE_MARGIN_Y
        safe_right = right - LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_bottom = height - 1 - LAYOUT_GUIDE_SAFE_MARGIN_Y
        draw.rectangle((safe_left, safe_top, safe_right, safe_bottom), outline="#2f80ed", width=2)

        center_x = left + cell_width // 2
        center_y = height // 2
        draw_dashed_line(draw, (center_x, safe_top), (center_x, safe_bottom), fill="#b8b8b8")
        draw_dashed_line(draw, (safe_left, center_y), (safe_right, center_y), fill="#b8b8b8")

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return {
        "state": state,
        "path": str(path),
        "width": width,
        "height": height,
        "frames": frames,
        "cellWidth": cell_width,
        "cellHeight": cell_height,
        "safeMarginX": LAYOUT_GUIDE_SAFE_MARGIN_X,
        "safeMarginY": LAYOUT_GUIDE_SAFE_MARGIN_Y,
        "usage": (
            "construction input only; intentionally empty frame boxes for spacing and safe padding, "
            "not a mascot preview; do not copy visible guide lines into generated sprite strips"
        ),
    }


def create_layout_guides(
    run_dir: Path,
    states: list[str],
    frames_by_state: dict[str, int],
    cell_width: int,
    cell_height: int,
) -> list[dict[str, Any]]:
    guide_dir = run_dir / LAYOUT_GUIDE_DIR
    return [
        create_layout_guide(
            guide_dir / f"{state}.png",
            state=state,
            frames=frames_by_state[state],
            cell_width=cell_width,
            cell_height=cell_height,
        )
        for state in states
    ]


def build_base_prompt(
    *,
    name: str,
    description: str,
    visual_language: dict[str, Any],
    anatomy_class: str,
    chroma_key: dict[str, Any],
) -> str:
    source_vibe = visual_language["sourceVibe"]
    motifs = ", ".join(visual_language.get("motifs", []))
    identity_props = ", ".join(visual_language.get("identityProps", [])) or "infer must-keep props and signature accessories from the reference"
    forbidden = ", ".join(visual_language.get("forbiddenGenericCues", []))
    key_hex = chroma_key["hex"]
    key_name = chroma_key["name"]
    return f"""# {name} canonical base companion prompt

Create one centered full-body canonical base sprite for a React/chatbot companion mascot named {name}.

Reference and concept: {description or "Use the attached reference image(s) as the mascot identity source."}
Vibe read: {source_vibe}
Mascot-native motifs to preserve when useful: {motifs}
Must-keep identity props/accessories: {identity_props}
Generic cues to avoid: {forbidden}
Anatomy class: {anatomy_class}

Style lock: Codex digital-pet pixel art, compact chibi sprite, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, hard-edged sprite details, simple expressive face, readable silhouette at website sizes. No smooth illustration, glossy rendering, 3D, painterly gradients, vector-flat icon style, text, labels, scenery, shadows, UI panels, or marketing artwork.

Output one neutral full-body mascot sprite pose only on a perfectly flat pure {key_name} {key_hex} chroma-key background. Preserve the reference identity, silhouette cues, palette family, face, must-keep markings, appendage count, and charm. Do not include state props, speech bubbles, thought bubbles, detached particles, scenery, or extra anatomy. Do not use {key_hex}, pure {key_name}, or colors close to that chroma key in the mascot, outline, highlights, or effects.
"""


def build_prompt(
    *,
    name: str,
    state: str,
    state_plan: dict[str, str],
    anatomy_class: str,
    frame_count: int,
    cell_width: int,
    cell_height: int,
    source_vibe: str,
    identity_props: list[str] | None = None,
    chroma_key: dict[str, Any] | None = None,
) -> str:
    anatomy = ANATOMY_GUIDANCE.get(anatomy_class, ANATOMY_GUIDANCE["ambiguous-limbs"])
    key_hex = chroma_key["hex"] if chroma_key else "the chosen chroma-key color"
    key_name = chroma_key["name"] if chroma_key else "flat"
    props = ", ".join(identity_props or [])
    identity_prop_line = f"Must-keep identity props/accessories: {props}" if props else "Must-keep identity props/accessories: infer from the reference; keep signature props, emblems, and outfit silhouettes consistent when present."
    return f"""# {name} {state} row prompt

Use the attached reference image(s) for original identity, the attached canonical base sprite as the approved design, and the attached layout guide only for frame count, slot spacing, centering, and safe padding. The layout guide is a construction input only: it is intentionally empty and is not a mascot preview. Infer the mascot's vibe from the reference before choosing the pose or visual aid.

Create one horizontal sprite row strip with exactly {frame_count} separated frames on a perfectly flat pure {key_name} {key_hex} chroma-key background.

Style lock: Codex digital-pet pixel art, compact chibi sprite, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, hard-edged sprite effects. No smooth illustration, glossy rendering, 3D, painterly gradients, vector-flat icons, text, labels, scenery, shadows, or UI panels.

Identity lock: preserve the same mascot species/body type, face, palette, markings, outline weight, proportions, appendage count, and silhouette from the reference. Do not redesign the character.

Expression lock: preserve the source mascot's expression language. Do not invent angry brows, brow marks, slanted angry eyes, V-shaped eye/brow marks, teeth, sweat, blush, or dramatic emotion symbols unless they are already part of the source design or the state explicitly needs them and they remain character-appropriate. If the source is calm, cute, sleepy, plush, abstract, or browless, keep that same friendly face grammar while active. For working, show concentration through eye direction, blink timing, mouth shape, lean, pace, and approved props/effects; do not add eyebrows to a browless mascot.

State: {state}
Semantic read: {state_plan["semanticRead"]}
Acting first: {state_plan["actingFirst"]}
Visual aid decision: {state_plan["visualAidDecision"]}
Suggested visual aid when needed: {state_plan["suggestedVisualAid"]}
{state_plan["frameArc"]}
{state_plan["freestandingPropPolicy"]}
{state_plan["workPropMarkPolicy"]}
{state_plan["workTargetPolicy"]}
{state_plan["workTargetFitPolicy"]}
{state_plan["workTargetInteractionPolicy"]}
{state_plan["bodySurfaceCuePolicy"]}
{state_plan["voiceCuePolicy"]}
{ARTISTIC_QUALITY_POLICY}
{EXPRESSION_VARIATION_POLICY}
{FACE_TOUCH_SILHOUETTE_POLICY if anatomy_class in {"hands", "paws", "ambiguous-limbs"} else ""}
Vibe fit: {source_vibe}
{identity_prop_line}
{IDENTITY_PROP_POLICY}
Anatomy class: {anatomy_class}
Anatomy guidance: {anatomy}
Reject if: {state_plan["rejectIf"]}

Semantic ladder:
1. Make the face, eyes, mouth, posture, timing, and original appendages perform the state.
2. Use existing identity props or appendages only when the reference supports that action.
3. Add one tiny attached or anchored visual aid only if the state is still unclear at website size.
4. Reject a pretty motif-native effect when it does not communicate the state.

Visual aid rule: if a visual aid is used, make it a small visual verb with a state-specific motion path, not a decorative symbol. The cue must remain visible after chroma-key cleanup and readable at 64-96 px; do not rely on isolated tiny specks that cleanup may remove. For working, the cue should look like purposeful processing, sorting, checking, gathering, or tool activity while the face stays busy-but-friendly, character-appropriate, and never angry or hostile; for simple/no-limb mascots, use body-surface, rim-touching, compact attached, or freestanding/resting cues placed beside or in front of the mascot, never held or operated by invented hands. For answering, the cue should support mouth/voice motion rather than become a speech panel.

Layout guide rule: follow the attached guide's {frame_count} frame boxes and safe padding, but do not reproduce the guide itself. The guide is not output art. No visible boxes, borders, labels, guide colors, center marks, or guide background may appear in the output.

Frame layout: keep each pose fully inside an implied {cell_width}x{cell_height} cell with safe padding. Keep body center, top-of-head height, bottom edge, silhouette scale, and appendage count stable across the row. Every frame must have a meaningful change in face, pose, body motion, prop, or visual aid. Do not use {key_hex}, pure {key_name}, or colors close to that chroma key in the mascot, prop, outline, highlights, or effects.
"""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def make_jobs(
    *,
    run_dir: Path,
    states: list[str],
    frames_by_state: dict[str, int],
    copied_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reference_inputs = [
        {"path": rel(Path(str(ref["copiedPath"])), run_dir), "role": "original mascot reference"}
        for ref in copied_refs
    ]
    jobs: list[dict[str, Any]] = [
        {
            "id": "base",
            "kind": "base-companion",
            "status": "pending",
            "prompt_file": "prompts/base.md",
            "input_images": reference_inputs,
            "output_path": BASE_OUTPUT_PATH,
            "depends_on": [],
            "generation_skill": "$imagegen",
            "requires_grounded_generation": bool(reference_inputs),
            "allow_prompt_only_generation": not reference_inputs,
            "recording_owner": "parent",
        }
    ]

    identity_reference_paths = [CANONICAL_BASE_PATH, BASE_OUTPUT_PATH]
    for state in states:
        frames = frames_by_state[state]
        jobs.append(
            {
                "id": state,
                "kind": "row-strip",
                "status": "pending",
                "state": state,
                "frames": frames,
                "prompt_file": f"prompts/rows/{state}.md",
                "input_images": [
                    *reference_inputs,
                    {
                        "path": f"{LAYOUT_GUIDE_DIR}/{state}.png",
                        "role": (
                            f"construction layout guide for {frames} frame slots; intentionally empty spacing input, "
                            "not a mascot preview, do not copy guide lines"
                        ),
                    },
                    {"path": CANONICAL_BASE_PATH, "role": "canonical identity reference"},
                    {"path": BASE_OUTPUT_PATH, "role": "approved base companion sprite"},
                ],
                "output_path": f"generated/{state}.png",
                "depends_on": ["base"],
                "generation_skill": "$imagegen",
                "requires_grounded_generation": True,
                "allow_prompt_only_generation": False,
                "identity_reference_paths": identity_reference_paths,
                "parallelizable_after": ["base"],
                "recording_owner": "parent",
            }
        )
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companion-name", required=True, help="Mascot display name")
    parser.add_argument("--description", default="", help="One-sentence companion description")
    parser.add_argument("--reference", action="append", default=[], help="Reference image path used for grounding")
    parser.add_argument("--output-dir", required=True, help="Run directory to create")
    parser.add_argument("--states", default=",".join(DEFAULT_STATES), help="Comma-separated state list")
    parser.add_argument("--state-clarity", choices=["pose-only", "semantic-enhancers"], default="semantic-enhancers")
    parser.add_argument("--anatomy-class", choices=sorted(ANATOMY_GUIDANCE), default="ambiguous-limbs")
    parser.add_argument("--source-vibe", help="Optional inferred vibe note; omit to make prompts infer from reference")
    parser.add_argument("--motif", action="append", default=[], help="Mascot-native motif; can be repeated")
    parser.add_argument("--identity-prop", action="append", default=[], help="Must-keep identity prop, emblem, clothing shape, or signature accessory; can be repeated")
    parser.add_argument("--forbid-cue", action="append", default=[], help="Generic/off-vibe cue to avoid; can be repeated")
    parser.add_argument("--cell-width", type=int, default=256)
    parser.add_argument("--cell-height", type=int, default=288)
    parser.add_argument("--columns", type=int, help="Atlas columns; defaults to max generated frame count")
    parser.add_argument(
        "--chroma-key",
        default="auto",
        help="Chroma key as #RRGGBB, or auto to choose a safe key from reference colors",
    )
    parser.add_argument("--compact", action="store_true", help="Use 6-frame audition rows")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing run directory")
    parser.add_argument("--quiet", action="store_true", help="Do not print the output summary")
    args = parser.parse_args(argv)

    states = parse_csv(args.states)
    unknown_states = [state for state in states if state not in DEFAULT_STATES]
    if unknown_states:
        parser.error("unknown states: " + ", ".join(unknown_states))

    out_dir = Path(args.output_dir).expanduser().resolve()
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        parser.error(f"output directory is not empty; use --force to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompts").mkdir(exist_ok=True)
    (out_dir / "prompts" / "rows").mkdir(parents=True, exist_ok=True)
    (out_dir / "generated").mkdir(exist_ok=True)
    (out_dir / "qa").mkdir(exist_ok=True)
    (out_dir / "references").mkdir(exist_ok=True)

    copied_refs: list[dict[str, Any]] = []
    copied_ref_paths: list[Path] = []
    for index, raw_reference in enumerate(args.reference, start=1):
        source = Path(raw_reference).expanduser().resolve()
        if not source.is_file():
            parser.error(f"reference not found: {source}")
        suffix = source.suffix.lower() or ".png"
        copied = out_dir / "references" / f"reference-{index:02d}{suffix}"
        shutil.copy2(source, copied)
        meta = image_metadata(copied)
        meta["sourcePath"] = str(source)
        meta["copiedPath"] = str(copied)
        copied_refs.append(meta)
        copied_ref_paths.append(copied)

    visual_language = build_visual_language(args)
    frames_by_state = {state: frame_count_for(state, args.compact) for state in states}
    columns = max(args.columns or 0, max(frames_by_state.values()))
    chroma_key = choose_chroma_key(copied_ref_paths, args.chroma_key)
    layout_guides = create_layout_guides(out_dir, states, frames_by_state, args.cell_width, args.cell_height)

    manifest: dict[str, Any] = {
        "id": slugify(args.companion_name),
        "displayName": args.companion_name,
        "description": args.description,
        "references": [rel(Path(str(ref["copiedPath"])), out_dir) for ref in copied_refs],
        "style": {
            "renderingStyle": "codex-pixel-art",
            "stateClarity": args.state_clarity,
            "anatomyClass": args.anatomy_class,
            "visualLanguage": visual_language,
            "chromaKey": chroma_key,
        },
        "atlas": {
            "path": "atlas.webp",
            "width": columns * args.cell_width,
            "height": len(states) * args.cell_height,
            "columns": columns,
            "rows": len(states),
            "cellWidth": args.cell_width,
            "cellHeight": args.cell_height,
        },
        "states": {},
    }

    request = {
        "id": manifest["id"],
        "displayName": args.companion_name,
        "description": args.description,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "primaryGenerationSkill": "$imagegen",
        "renderingStyle": "codex-pixel-art",
        "stateClarity": args.state_clarity,
        "anatomyClass": args.anatomy_class,
        "visualLanguage": visual_language,
        "chromaKey": chroma_key,
        "states": states,
        "framesByState": frames_by_state,
        "references": [
            {
                **ref,
                "copiedPath": rel(Path(str(ref["copiedPath"])), out_dir),
            }
            for ref in copied_refs
        ],
        "layoutGuides": [
            {**guide, "path": rel(Path(str(guide["path"])), out_dir)}
            for guide in layout_guides
        ],
    }

    plan: dict[str, Any] = {
        "companionName": args.companion_name,
        "stateClarity": args.state_clarity,
        "anatomyClass": args.anatomy_class,
        "visualLanguage": visual_language,
        "states": {},
        "notes": [
            "This is a prompt/state-cue plan, not final art acceptance.",
            "Layout guide PNGs are intentionally empty construction inputs, not mascot previews or QA output.",
            "After row generation, update enhancer metadata to match the actual accepted visual aid.",
            "Reject rows where the state read is unclear even if the effect matches the mascot vibe.",
        ],
    }

    write_text(
        out_dir / "prompts" / "base.md",
        build_base_prompt(
            name=args.companion_name,
            description=args.description,
            visual_language=visual_language,
            anatomy_class=args.anatomy_class,
            chroma_key=chroma_key,
        ),
    )

    for row, state in enumerate(states):
        frames = frames_by_state[state]
        state_plan = build_state_plan(state, args.anatomy_class, args.state_clarity)
        manifest_state: dict[str, Any] = {
            "row": row,
            "frames": frames,
            "durations": durations_for(state, frames),
            "loop": True,
        }
        if args.state_clarity == "semantic-enhancers" and state in SEMANTIC_STATES:
            manifest_state["enhancer"] = {
                "kind": "planned during row generation",
                "attachment": "body-pose",
                "description": state_plan["suggestedVisualAid"],
                "visualLanguageFit": "Prompt requires the row to infer a mascot-native cue and reject decorative ambiguity.",
            }
        manifest["states"][state] = manifest_state
        plan["states"][state] = state_plan
        prompt_text = build_prompt(
            name=args.companion_name,
            state=state,
            state_plan=state_plan,
            anatomy_class=args.anatomy_class,
            frame_count=frames,
            cell_width=args.cell_width,
            cell_height=args.cell_height,
            source_vibe=visual_language["sourceVibe"],
            identity_props=visual_language.get("identityProps", []),
            chroma_key=chroma_key,
        )
        write_text(out_dir / "prompts" / f"{state}.md", prompt_text)
        write_text(out_dir / "prompts" / "rows" / f"{state}.md", prompt_text)

    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "companion_request.json", request)
    write_json(out_dir / "qa" / "state-cue-plan.json", plan)
    write_json(
        out_dir / "imagegen-jobs.json",
        {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "run_dir": str(out_dir),
            "primary_generation_skill": "$imagegen",
            "request": "companion_request.json",
            "canonical_identity_reference": None,
            "jobs": make_jobs(
                run_dir=out_dir,
                states=states,
                frames_by_state=frames_by_state,
                copied_refs=copied_refs,
            ),
        },
    )
    if not args.quiet:
        print(
            json.dumps(
                {
                    "ok": True,
                    "runDir": str(out_dir),
                    "manifest": str(out_dir / "manifest.json"),
                    "request": str(out_dir / "companion_request.json"),
                    "jobs": str(out_dir / "imagegen-jobs.json"),
                    "stateCuePlan": str(out_dir / "qa" / "state-cue-plan.json"),
                    "promptsDir": str(out_dir / "prompts"),
                    "readyJobs": ["base"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
