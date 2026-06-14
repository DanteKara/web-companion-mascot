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
ROW_GENERATION_POLICY = {
    "after_base_recorded": "subagents-preferred-when-user-authorized",
    "requires_explicit_user_authorization": True,
    "parent_owned_actions": [
        "record-result",
        "manifest-writes",
        "atlas-assembly",
        "qa-generation",
        "validation",
        "react-packaging",
    ],
    "subagent_return_contract": ["selected_source", "qa_note"],
}
ROW_SUBAGENT_HANDOFF = {
    "return_only": ["selected_source", "qa_note"],
    "forbidden_actions": [
        "edit imagegen-jobs.json",
        "copy files into generated",
        "run record_companion_imagegen_result.py",
        "assemble atlas",
        "run validation",
        "package React assets",
    ],
    "visual_checks": [
        "exact requested frame count",
        "same mascot identity as canonical base",
        "recordable cleanup-ready background: true transparency or exact flat chroma key, not a green-looking vignette",
        "complete separated unclipped poses",
        "stable source eye grammar with no white-sclera or crescent side-glance swaps",
        "coherent state story that does not drift into a neighboring state",
        "no forbidden detached effects or slot-crossing artifacts",
    ],
    "qa_note_must_call_out": [
        "visible chroma-key falloff, vignette, or non-uniform background",
        "white-eye/crescent swaps or mismatched highlights",
        "wrong-state frames, stale acting, extra anatomy, or face-touch drift",
    ],
}

DEFAULT_STATES = [
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
OPTIONAL_STATES = ["working"]
SUPPORTED_STATES = DEFAULT_STATES + OPTIONAL_STATES

SEMANTIC_STATES = {"listening", "thinking", "working", "answering", "success", "error", "confused"}
LONG_STATES = {"thinking", "working", "answering"}
STATE_PURPOSES = {
    "idle": "default calm presence",
    "greeting": "chat opens or first welcome",
    "listening": "user is typing or speaking",
    "thinking": "assistant is thinking, processing, retrieving, using tools, or waiting on backend progress before output",
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
    "thinking": "clear-face thinking performance with curious head/body tilt, source-matched eyes mostly forward with only tiny in-eye shifts, changing tiny closed smile or gently upturned thoughtful mouth, low side-anchored appendage beats when supported, and readable processing/idea beats",
    "working": "busy-but-friendly concentration, attentive eye tracking toward the work target, lean-in, faster purposeful body/hand/prop motion; never angry, no slanted angry eyes, no V-shaped brow or eye marks",
    "answering": "talking performance through clear speaking mouth shapes, bright eyes, blink timing, and rhythmic face/body beats; voice cues are optional",
    "success": "cheerful bounce, proud hold, bright face, return to loop",
    "error": "worried recognition, small recoil or slump, recovery beat",
    "confused": "squint, head tilt, uncertain mouth, small recovery",
    "sleeping": "closed eyes, slow breathing, sleepy settle",
}

BACKGROUND_SOURCE_LOCK = (
    "Perfectly uniform exact flat flood-fill background: Use a plain digital solid-color canvas, "
    "recordable by a strict cleanup gate: true transparency if supported, else exact key RGB in every pixel. "
    "No gradients, shadows, texture, darker/lighter key-color variations, glow/matte."
)

SOURCE_EYE_LOCK = (
    "Open eyes preserve the source-matched fill, outline, and highlight/catchlight logic. Open eyes must remain "
    "the same source-colored eye masses in the same eye boxes. No hollow or inverted eyes, mismatched eyes, "
    "extra catchlights, symbol eyes. No white crescent side-glance eyes, hollow eyes, mismatched eyes, "
    "extra catchlights, or symbol eyes; no new white sclera or one-frame eye-style swaps. If gaze would break "
    "eye style, keep eyes forward and use mouth/blink/body/appendage/cue timing."
)

THINKING_EYE_LOCK = (
    "Open eyes preserve the source-matched fill, outline, and highlight/catchlight logic. Open eyes must remain "
    "the same source-colored eye masses in the same eye boxes. No white crescent side-glance eyes, hollow eyes, "
    "mismatched eyes, extra catchlights, or symbol eyes; no new white sclera. If gaze breaks eye style, keep eyes "
    "forward/nearly forward and use mouth/blink/body/cue timing; do not carve white eye gaps or crescent cutouts."
)

STATE_SPECIFIC_GUARDS = {
    "idle": (
        "Idle stays calm and present. Do not turn it into greeting, speaking, sleeping, error, or thinking; "
        "avoid wide open mouths, semantic cues, and dramatic mood changes."
    ),
    "greeting": (
        "Greeting should stay warm and welcoming. Use a small wave, bounce, or smile peak only if the mascot anatomy "
        "supports it; do not add detached marks, text, confetti, or a second prop."
    ),
    "listening": (
        "Listening should read attentive and ready, not thinking, surprised, sleepy, worried, confused, or answering. "
        "Avoid open shocked mouths, hand-to-chin poses, question/thought cues, and side-glance eye rewrites."
    ),
    "thinking": (
        "Thinking should read curious processing, not surprise/sad/sleep/confused/answering; cue compact."
    ),
    "answering": (
        "Answering should stay engaged and mouth-led. Do not let the row become greeting, panting, exhaling, idle, "
        "or thinking; omit voice pixels if they become detached flecks or cheek marks."
    ),
    "success": (
        "Success should read as a proud completion beat. Keep any glint/check tiny, attached or source-bound, and "
        "secondary; do not use loose sparkle fields, confetti, text, or a generic UI badge."
    ),
    "error": (
        "Error should remain a gentle recoverable failure loop. Do not include happy/success/answering frames in the "
        "same row, no harsh anger, no red X labels, no generic warning panels, and no white-eye stress rewrites."
    ),
    "confused": (
        "Confused should read curious-uncertain rather than sad/error. Use mild squint, tilt, or uncertain mouth only; "
        "avoid hand-to-chin/under-face clusters, large punctuation, and white crescent side-glance eyes."
    ),
    "sleeping": (
        "Sleeping should be quiet breathing and closed-eye settle, not thinking or tired speaking. Keep appendages "
        "resting unless the source has clear articulated hands; avoid hand-to-mouth clusters and sleep symbols."
    ),
    "working": (
        "Working should read purposeful progress, not error, anger, answering, or generic busy icons. Keep the work "
        "cue source-bound and do not invent tools, hands, screens, or text."
    ),
}

STATE_STORY_BEATS = {
    "idle": "calm rest -> soft blink -> tiny breath lift -> relaxed settle",
    "greeting": "notice user -> warm smile -> peak greeting gesture/bounce -> friendly settle",
    "listening": "attentive start -> eyes track input -> focused hold/blink -> ready settle",
    "thinking": "neutral-curious -> noticing -> curious pondering -> idea lands -> pleased settle",
    "working": "notice -> focus -> effort -> progress -> pleased settle",
    "answering": "ready/listening -> first syllable -> clearer speech -> conversational blink/smile -> settled speaking loop",
    "success": "anticipation -> bright success peak -> proud hold -> warm settle",
    "error": "notice problem -> worried dip/recoil -> soft recovery -> stable retry-ready settle",
    "confused": "notice mismatch -> squint/tilt -> uncertain hold -> softened recovery",
    "sleeping": "drowsy settle -> closed-eye breath -> deeper sleepy hold -> gentle loop reset",
}

STATE_ACTING_CHOREOGRAPHY_POLICY = (
    "Professional state acting choreography: direct the row like a tiny looped character performance. "
    "Coordinate three synchronized tracks in every frame: expression track, body/appendage track, and "
    "cue/prop track. The face, body, existing appendages, surface details, held props, and optional state cue should "
    "take turns carrying the motion so the row feels alive. Do not let all motion live in the prop, bubble, "
    "sparkle, or cue while the mascot stays static. Reject parked hands, frozen appendages, unchanged faces, "
    "and symbol-only rows unless the reference truly has no movable anatomy; in that case use eyes, mouth, "
    "body tilt, breathing, and cue timing as the acting tracks."
)

STATE_ACTING_CHOREOGRAPHY = {
    "idle": (
        "Frame 1: calm resting face and stable silhouette. Frame 2: soft eye shift or blink begins. "
        "Frame 3: tiny breath lift or body rise. Frame 4: relaxed hold with appendages still accounted for. "
        "Frame 5: small gaze or mouth micro-change. Frame 6: breath lowers. Frame 7: second soft blink or "
        "settle beat. Frame 8: return cleanly to the first resting pose."
    ),
    "greeting": (
        "Frame 1: notices the user. Frame 2: eyes brighten and smile starts. Frame 3: an existing appendage "
        "or whole body begins a greeting lift/bounce if anatomy supports it. Frame 4: peak warm greeting. "
        "Frame 5: smile hold with tiny follow-through. Frame 6: gesture lowers. Frame 7: friendly settle. "
        "Frame 8: return to ready rest without a mood jump."
    ),
    "listening": (
        "Frame 1: attentive neutral. Frame 2: eyes track toward the user/input. Frame 3: head/body leans or "
        "one existing appendage cups/lifts if anatomy supports it. Frame 4: focused hold or blink. Frame 5: "
        "eyes open ready, small mouth or posture change. Frame 6: appendage/body eases back. Frame 7: alert "
        "settle. Frame 8: loop back to attentive neutral."
    ),
    "thinking": (
        "Frame 1: neutral-curious face with stable identity props. Frame 2: source-matched eyes stay mostly forward while "
        "appendages stay side-anchored or start a tiny side bob if anatomy supports it. Frame 3: tiny closed pondering "
        "smile or gently upturned one-pixel smile; tiny first thought cue appears only if needed. Frame 4: cue grows to slightly larger "
        "while the face stays curious and any supported appendage motion remains side-anchored, low, and outside the body centerline. "
        "Frame 5: medium compact cue peak with one slightly larger primary cue element when the chosen vocabulary supports it, still secondary "
        "to the mascot and with the face unobscured. Frame 6: cue shrinks with a quick active processing blink or thoughtful "
        "hold while the mouth stays smile-like and appendages remain separated from the mouth and chin. "
        "Frame 7: recognition smile; appendages start returning to rest. Frame 8: settled curious "
        "face ready to loop."
    ),
    "working": (
        "Frame 1: notices the work target or active prop end. Frame 2: eyes focus and body leans in slightly. "
        "Frame 3: existing hand, prop tip, tool end, or body cue begins the operation. Frame 4: purposeful work "
        "peak with small follow-through. Frame 5: visible progress change. Frame 6: quick blink or pleased "
        "effort beat. Frame 7: result or resolved work mark. Frame 8: busy-friendly settle with identity and "
        "scale intact."
    ),
    "answering": (
        "Frame 1: attentive ready face with closed or small smile. Frame 2: small open mouth begins speech. "
        "Frame 3: wider mouth; free hand begins a small presenting gesture if anatomy supports it. Frame 4: "
        "clearest syllable hold with bright eyes and slight body bob. Frame 5: quick speaking blink or "
        "smile-open beat with a tiny conversational hand bounce. Frame 6: smaller mouth and hand/body "
        "follow-through. Frame 7: closed smile while the body or appendage settles. Frame 8: ready speaking-rest pose that "
        "loops naturally back to frame 1."
    ),
    "success": (
        "Frame 1: anticipation or completion notice. Frame 2: smile grows. Frame 3: tiny upward bounce or proud "
        "lift. Frame 4: proud peak with existing appendages lifted only if the reference supports it. Frame 5: "
        "attached check/glint or mascot-native success cue appears only if needed. Frame 6: pleased hold. "
        "Frame 7: appendages/body lower. Frame 8: warm settled success face ready to loop."
    ),
    "error": (
        "Frame 1: notices something is wrong. Frame 2: small worried mouth or eye change. Frame 3: tiny dip, "
        "slump, or recoil without anger. Frame 4: small recoil or tuck; appendages pull inward only if that "
        "preserves the original count. Frame 5: quick recovery blink. Frame 6: softer retry-ready expression. "
        "Frame 7: body/appendages settle. Frame 8: stable gentle error face that can loop without looking hostile."
    ),
    "confused": (
        "Frame 1: notices mismatch. Frame 2: eyes shift or pupils search. Frame 3: head/body tilts. Frame 4: "
        "uncertain mouth or small squint within the source expression language. Frame 5: optional tiny attached "
        "question cue only if needed. Frame 6: soft realization or ask-ready face. Frame 7: tilt eases back. "
        "Frame 8: gentle confused settle."
    ),
    "sleeping": (
        "Frame 1: drowsy settle. Frame 2: eyelids lower. Frame 3: closed-eye breath lift. Frame 4: sleepy hold. "
        "Frame 5: slower breath lower. Frame 6: tiny relaxed mouth or posture change. Frame 7: quiet hold. "
        "Frame 8: returns to the first sleepy pose without waking."
    ),
}

STATE_VISUAL_AIDS = {
    "listening": "small attached sound rings or attentive pose only when needed",
    "thinking": "face/eye/mouth/body acting first with one compact source-bound thought cue when needed, such as a thought bubble, thought puff, idea orb, or mascot-native processing aura; it should grow small -> slightly larger -> medium -> smaller -> tiny/settle from the inferred thought-cue source near the expression area, not from an unrelated identity prop, stay close without inflating the mascot body footprint, and make the thinking read unmistakable at 64-96 px",
    "working": "existing hands, body lean, gaze, and identity prop motion first; for long held props prefer a compact attached active-end bloom, aura, pulse, or contact mark with purposeful cycling, sorting, checking, charging, or gathering motion when needed",
    "answering": "mouth shapes first; speech pips, sound ticks, tiny rings, breath marks, or voice pixels are optional and should stay secondary when used; omit them if they cannot stay clearly attached to the mouth",
    "success": "small check/glint, proud pose, or raised existing prop",
    "error": "attached tear, warning charm, prop droop, or small attached smoke/stars",
    "confused": "tiny question cue only if expression and tilt are not enough",
}

STATE_REJECTS = {
    "working": "anger, hostile eyes, slanted angry eyes, V-shaped eyes, invented angry eyebrows or brow marks, decorative particles that do not read as work, unsupported held tools, duplicate identity props, prop-shaped glyph copies, static prop with no work motion, text-like prop marks, pseudo-writing, code lines, ruled notebook lines",
    "answering": "speech panels, text, punctuation, generic chat UI, mouthless talking cues, single isolated voice speck, one-frame voice ticks, one-frame sound marks, detached fleck, cheek-mark-like voice cue",
    "thinking": "detached icon floating above the mascot, oversized second head/body-sized thought orb, giant bubble peak, thought cue fused into the body core causing body growth, static dots, loose sparkles, isolated white specks, star glints, stray final-frame dot, expression-panel skew or body warp, unsupported or poorly connected face-touch that reads as extra anatomy, a lower-face patch, detached mitten, duplicated hand, or covered expression, appendage-like cluster below the face, lower-face marks, worried frowns, sad/serious/downturned expressions, stale same-face row, confused/error mouth shapes, cue too subtle to read as thinking",
    "listening": "microphone props for non-voice apps, detached sound clutter",
    "success": "large confetti, loose sparkles, text labels",
    "error": "red X labels, detached symbols, scenery",
    "confused": "text labels or large punctuation panels",
}

STATE_FRAME_ARCS = {
    "thinking": (
        "Frame-by-frame acting arc for expressive thinking performance: 1 neutral-curious face and stable identity "
        "props, 2 source-matched eyes stay mostly forward while appendages stay side-anchored or begin a tiny side bob when anatomy supports it, "
        "3 tiny closed pondering smile or gently upturned one-pixel smile and one tiny compact cue kept close to the inferred thought-cue source, 4 slightly larger compact cue with more curious eyes and a tiny closed thoughtful smile, "
        "5 compact cue peak beside the inferred source with one slightly larger primary cue element only when the accepted cue vocabulary supports it while the face remains unobscured without changing the body footprint, 6 cue starts smaller with a quick active processing blink or pondering hold, "
        "7 small smile/idea recognition as the cue shrinks, 8 settle back into the loop. Use one compact thought bubble, thought puff, "
        "or idea orb when acting alone is unclear; make the thinking read unmistakable at 64-96 px without turning "
        "the cue into the main character. Thinking also covers processing, retrieval, tool-use waiting, and backend "
        "progress for chatbot companions. Do not create a separate working state unless the user explicitly requests one. "
        "Keep the thought cue secondary to the mascot: medium is the maximum thought cue size, it is never larger "
        "than about one-quarter of the mascot body width, and do not let the thought cue become a second "
        "head/body-sized orb. Do not use a giant bubble peak; shrink back down before the loop settles. "
        "For shorter or longer rows, preserve the same expression-changing neutral-curious -> noticing -> curious pondering -> "
        "idea lands -> settle arc and the same small -> slightly larger -> medium -> smaller -> tiny/settle cue growth; this is not the "
        "same face or same cue pasted in every frame. Keep the thinking expression story adjacent and character-appropriate, "
        "not random sad, sleepy, angry, blank, or unrelated faces."
    ),
    "working": (
        "Frame-by-frame acting arc: 1 mascot notices a concrete work target, 2 leans in and the target wakes up while eyes focus on it, "
        "3 begins an action on the target, 4 active work peak with hand/prop/body follow-through, "
        "5 visible progress change on the target, 6 small blink/effort or satisfied beat, 7 result/check/sorted state, "
        "8 settle back while the target remains active. For shorter or longer rows, preserve the same notice -> "
        "operate/sort/check -> result -> settle arc with meaningful face, gaze, hand/prop, and target changes."
    ),
    "answering": (
        "Frame-by-frame acting arc: Talking performance is primary. 1 neutral/listen face with closed smile, "
        "2 small open mouth, 3 wider open mouth, 4 syllable hold with the clearest speaking beat, "
        "5 smile-open mouth or quick speaking blink, 6 smaller mouth, 7 closed smile, 8 settle back into the loop. "
        "Use a readable mouth cycle such as closed smile -> small open -> wider open -> syllable hold -> smile, "
        "plus bright eyes, tiny conversational bob, and subtle head/body timing. If a voice cue is used, keep it "
        "near the mouth/lip edge and secondary to the mouth animation, not as a detached cue away from the mouth. "
        "Voice cues are optional and should be omitted when they cannot stay clearly attached to the mouth; when used, "
        "make a short 2-3 frame outward trail, not a single isolated speck in only one frame and not one-frame voice ticks."
    ),
}

HATCHPET_SPRITE_ARTIFACT_POLICY = (
    "HatchPet-style sprite artifact rules: Prefer pose, expression, and silhouette changes over decorative effects. "
    "Effects are allowed only when they are state-relevant, opaque, hard-edged, pixel-style, fully inside the same "
    "frame slot, and source-bound to the mascot silhouette, mouth edge, hand, tool, worn prop, or state source. "
    "Do not draw loose detached effects: floating stars, loose sparkles, floating punctuation, floating icons, "
    "separated smoke clouds, disconnected outline bits, stray pixels, generic UI panels, chat panels, scenery, "
    "shadows, glows, smears, dust, speed lines, motion trails, visible grids, guide marks, labels, or text. "
    "No floor-motion artifacts: do not show bobbing, jumping, thinking, or emphasis with floor shadows, contact "
    "shadows, ground lines, baseline marks, landing marks, or dark under-body strokes; the sprite must be only the "
    "mascot and approved state cue on chroma key. "
    "Near-head thought cues may use proximity or a tiny separated tail dot instead of touching when overlap would "
    "merge into the body core; keep them tiny, close to their source, and secondary to the mascot. Never let a "
    "state cue become a separate prop component that competes with the mascot."
)

REFERENCE_PALETTE_FIDELITY_POLICY = (
    "Reference palette fidelity lock: Preserve the actual reference colors for eye whites/highlights, pupils, eye "
    "outlines, face base color, cheek marks, outfit, props, and signature markings. Do not force white eyes or white "
    "highlights when the reference uses another color; only keep whites white when the source uses white. Translate "
    "colors into a limited pixel-art palette, but keep hue relationships and identity colors faithful to the reference. "
    "Do not let a glow, aura, bloom, prop color, or gold effect tint or recolor the mascot identity palette. Any "
    "prop-end light may touch the prop end, but it must not recolor eyes, face, clothing, markings, or must-keep props."
)

EYE_IDENTITY_CONTINUITY_POLICY = (
    "Eye identity continuity lock: preserve the canonical base eye grammar across every row frame: same eye count, "
    "shape, size, spacing, outline color, pupil or fill color, and same catchlight/highlight count and placement "
    "logic. Eye direction and tiny highlight/pupil shifts may change only as a deliberate gaze beat, while both "
    "eyes must stay matched and anchored to the same face-panel positions. Do not invert dark pupils into hollow "
    "white eyes, do not turn solid dark eyes into white oval eyes with dark rims, do not add extra catchlights, "
    "no glossy anime eyes, vertical slit pupils, square UI eyes, mismatched eyes, and no one-frame eye-style swaps. "
    "For solid dark base eyes, open eyes must remain mostly dark with the original tiny highlight; do not expose "
    "white sclera crescents, and do not make a white crescent or white cutout the dominant eye shape. Gaze can be "
    "shown by moving the dark eye oval or tiny highlight only a pixel or two; do not show side glances by carving "
    "white crescent gaps into dark eyes. Eye acting stability rule: If a requested up-glance, side-glance, blink, "
    "or speaking beat would require changing the eye style, keep the eyes forward or nearly forward and carry the "
    "acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead. "
    "Keep eye centers inside the original eye boxes; never slide eyes onto cheeks, panel edges, the mouth line, or "
    "outside the face panel. No eye-to-symbol swaps: do not replace eyes with loading dots, LEDs, status bars, "
    "diagonal slashes, crosses, punctuation, or reaction icons. "
    "Closed-eye blinks should replace each open eye with a simple short closed curve or horizontal pixel line in "
    "the same eye positions and spacing, not X-eyes, chevrons, eyebrows, reaction glyphs, and not mouth-like "
    "lower-face squiggles."
)

BASE_PRODUCTION_LOCK = (
    "Base production lock: create a native pixel-art sprite, not a scaled-down smooth illustration. Use flat "
    "cel-shaded pixel clusters, a limited palette, hard stepped edges, chunky readable silhouette, and an intentional "
    "1-2 px dark outline. Use simple blocked highlights only where needed. Use no glossy gradients, no soft airbrush, "
    "no bloom, no rim glow, no 3D lighting, no high-detail specular shine, and no smooth vector curves."
)

HARD_NATIVE_PIXEL_RENDERING_LOCK = (
    "Hard native-pixel rendering lock: Use hard-edged square pixel clusters and 2-3 flat tone steps per material. "
    "If the mascot's personality is soft or friendly, softness must come from shape language and expression, not "
    "blurred rendering. No blurred or feathered transitions, no transparent or semi-transparent shine, no airbrushed "
    "lighting, no smooth diagonal antialias fringe, no bevel, no glassy overlay, and no painterly texture. Highlights "
    "must be tiny rectangular pixel blocks; no broad glossy shine patches on large surfaces, accessories, appendages, "
    "or face areas."
)

SOURCE_PIXEL_GRID_LOCK = (
    "Source-pixel grid lock: Draw the mascot as if it was first made on a tiny 64x72 or 80x90 pixel grid and then "
    "enlarged with nearest-neighbor scaling. Every visible edge and highlight should snap to that coarse pixel grid. "
    "Large body regions should be flat color clusters with one darker stepped shadow band at most. Do not use smooth "
    "radial gradients, soft cylindrical shading, pillow shading, or app-icon material lighting. If a surface needs "
    "dimension, use one or two chunky stair-step shadow clusters, not continuous tone ramps."
)

INDEXED_COLOR_SPRITE_CELL_LOCK = (
    "Indexed-color sprite cell lock: Use the fewest colors that preserve identity, roughly 8-16 total non-background "
    "colors for the base sprite. Think indexed-color sprite, not digital painting. No per-pixel color ramps, no "
    "smooth shade bands, no gradient-filled body areas, face areas, clothing, props, accessories, or appendages, and no dozens "
    "of near-identical source-color, outline, shadow, or highlight colors. Favor simpler and flatter over prettier: one flat base color, one "
    "hard stepped shadow, and one tiny blocked highlight per material is enough."
)

REFERENCE_AWARE_PALETTE_GUIDE = (
    "Reference-aware palette guide: Build a tiny per-mascot palette from the attached reference or the text concept, "
    "not from a stock assistant-mascot palette. Preserve the source hue relationships for body, face areas, eye fills "
    "or highlights, pupils, cheek marks, clothing, trim, emblems, and held props. Never impose a preselected color "
    "palette on a mascot whose reference uses different identity colors. Use flat fills only: one base, one hard "
    "shadow, and one small blocked highlight per material is usually enough. Do not blend between palette colors, "
    "do not create intermediate shades, and do not anti-alias edges with many in-between colors."
)

REFERENCE_NATIVE_STYLE_LOCK = (
    "Reference-native style lock: If an attached reference already looks like a HatchPet or Codex digital-pet sprite, "
    "treat it as the visual style floor. Preserve its chunky outline weight, low-resolution pixel density, hard block "
    "shading, compact chibi proportions, eye and catchlight grammar, cheek/mouth pixel language, outfit simplification, "
    "and held-prop simplification. Do not improve it into glossy sticker art, a smooth app icon, anime key art, vector "
    "mascot art, or a higher-detail illustration. If the reference has a noisy or gradient preview background, use the "
    "character design and style only; output a perfectly flat production chroma-key background."
)

HATCHPET_COMPACT_SOURCE_TARGET = (
    "HatchPet compact source target: The base should read like a Codex app digital pet first and a website mascot "
    "second. Make it fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite "
    "cell even if the final web atlas later uses larger cells. Use pixel-art-adjacent low-resolution mascot sprite "
    "rendering: compact chibi proportions, chunky whole-body silhouette, thick dark 1-2 px outline, visible "
    "stepped/pixel edges, limited palette, flat cel shading with at most one small highlight and one shadow step, "
    "simple readable face, tiny limbs, and no detail that disappears at 192x208. Do not compose it as a large glossy "
    "product mascot, large hero character, app icon, or high-resolution sticker; leave generous chroma-key padding "
    "and keep the sprite compact."
)

FLAT_CHROMA_KEY_LOCK = (
    "Flat chroma-key lock: The background must be one perfectly uniform solid chroma-key color from corner to corner; "
    "no vignette, lighting falloff, texture, noise, shadow, ground plane, or background glow. The sprite may have "
    "hard opaque pixels only; do not rely on soft transparency, fuzzy shadows, or key-colored edge glow."
)

BASE_ACCEPTANCE_GATE = (
    "Canonical base acceptance gate: the base must look like a final atlas-frame source of truth, not concept art, "
    "a preview illustration, a pose-sheet sample, an app icon, or a softened style target. It must be simple enough "
    "to reproduce across eight row frames without redesign: stable silhouette, stable top-of-head height, stable "
    "bottom edge, stable face-bearing area, stable appendage count, stable prop count, and no tiny high-detail marks "
    "that will flicker in rows. Reject and regenerate the base before any row prompt if it is smoother, glossier, "
    "more detailed, or less pixel-native than the intended row art. Rows must preserve the accepted base, not fix it "
    "by changing eye style, body shape, colors, outline weight, props, or anatomy."
)

BASE_EYE_GRAMMAR_LOCK = (
    "Base eye grammar lock: The canonical base sets the eye count, eye shape, spacing, fill or pupil color, "
    "outline color, catchlight/highlight count, and blink style for every later row. Use simple readable eyes that "
    "can animate through tiny gaze shifts and blinks without changing style. For dark oval eyes, keep the open eyes "
    "mostly dark with at most one tiny blocked highlight per eye. Avoid oversized glossy highlights, white sclera "
    "crescents, rimmed white eyes, UI-screen eyes, square pixel-display eyes, mismatched eyes, and decorative extra "
    "catchlights unless the source reference already uses them."
)

TEXT_CONCEPT_ANATOMY_LOCK = (
    "Text-only concept anatomy lock: when there is no original reference image, only add anatomy and identity props "
    "named in the concept or command. Do not add unrequested body markings, lights, badges, emblems, display details, "
    "buttons, feet, legs, tails, tools, or extra props. Keep the body compact with exactly the named anatomy and "
    "identity features; avoid adding unrelated limb systems or new identity marks. When the concept only names upper "
    "appendages, do not infer visible legs or feet. Keep plain body areas plain unless a mark is named."
)

PART_SIMPLIFICATION_LOCK = (
    "Part simplification lock: Preserve source or named parts by simplifying them into stable sprite shapes. Do not "
    "invent parts from these instructions. Small accessories should become plain readable silhouettes, simple side "
    "appendages should keep one outline and one flat fill, long held props should remain one continuous readable "
    "object with stable side, scale, and attachment, and ornate detail should collapse into a few chunky pixel "
    "clusters instead of many tiny flickering details. Keep clothing trim, emblems, badges, and markings readable "
    "enough for identity but plain enough that later row frames will not mutate them."
)

CHARACTER_DIRECTION_LOCK = (
    "Reference character direction lock: Keep the strongest character decisions from the provided reference or text "
    "concept while flattening the rendering: body/head silhouette, outfit shape, prop count and side, appendage count, "
    "face/eye/cheek/mouth grammar, palette relationships, and overall personality. Do not substitute a stock assistant "
    "mascot, a previous run's look, or any unrelated mascot template. Only simplify color/material treatment and tiny "
    "unstable detail; do not redesign the mascot while making it more pixel-native."
)

NO_HAND_WORK_PROP_POLICY = (
    "For simple/no-hand mascots, first show work through face, gaze, body lean, timing, and body-surface or "
    "rim-touching cues. Prefer body-surface, rim-touching, attached, or overlapping processing cues before adding "
    "a separate object. Freestanding props are a last resort when attached/body acting cannot read at 64-96 px. "
    "If a freestanding or resting work prop is used, it must sit beside or in front of the mascot and must not "
    "require grip anatomy. Use a mascot-native small slate, tablet, "
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
    "Working must show the mascot working through a concrete action, not a decorative detached prop or status icon. "
    "Perform the state first through face, gaze, body lean, timing, and existing hands or identity props. Choose at most "
    "one small mascot-native work cue when acting alone is unclear: an attached active-end bloom, staff-tip glow, "
    "body-surface glyph, rim-touching "
    "processing mark, tiny slate, tablet, token tray, card stack, work tile, small rune tile, magical work circle, "
    "sorting tokens, or an existing identity prop used only as a pointer/brace. The target needs a "
    "visible before/during/after transformation: inactive or blank -> being operated/sorted/checked -> progress/result. "
    "For mascots with a staff, wand, tool, or held identity prop, preserve that prop and place the work target near "
    "or touching/overlapping the active end of the existing prop or free hand so the action reads as deliberate work "
    "and remains in the same frame slot. Do not use random decorative squares, generic "
    "floating UI icons, loose sparkles, or a check mark with no preceding work action."
)

WORK_IDENTITY_PROP_EFFECT_POLICY = (
    "Use the existing held prop as the source of the action when the mascot already has a staff, wand, weapon, tool, "
    "badge, emblem, or other signature prop; do not summon, draw, or echo a second copy of that prop as the work cue. "
    "If the held prop aims, taps, charges, points, or moves, that active pose replaces the resting pose; do not show "
    "the resting prop and a second active copy in the same frame. Keep it one continuous physical object with the "
    "original hand-to-prop attachment visible, even when the prop rotates or tilts. "
    "Do not shape the work cue like a duplicate of the mascot's identity prop: no second staff, wand, tool, weapon, "
    "badge, emblem, or prop-shaped glyph. Do not echo identity emblems, logos, badges, weapon silhouettes, or "
    "signature markings inside the work target; no copied mascot-specific prop, logo, badge, emblem, or identity symbol inside "
    "the target. Use plain abstract dots, squares, diamonds, bars, or motes instead. The target should be a distinct "
    "small rune, tile, mote, orb, tray, panel, or token that the existing prop/hand/gaze affects."
)

WORK_LONG_HELD_PROP_POLICY = (
    "Keep long-prop working motion small and active-end-focused. For long held identity props such as staffs, wands, "
    "weapons, tools, brushes, pens, pointers, blades, or nozzles, prefer an attached active-end bloom, aura, pulse, "
    "or contact mark over a separate rune/tile/object. The bloom must wrap around, touch, or overlap the active end "
    "and stay there across the row: staff head, wand tip, tool bit, brush tip, pen tip, pointer tip, blade tip, or "
    "nozzle. Communicate work through bloom intensity/shape changes, eye tracking, mouth changes, and subtle "
    "staff-hand/body motion. Active-end bloom animation must change frame by frame: dim seed -> small bloom -> "
    "brighter wrap -> peak cluster -> shrinking settle, then loop cleanly. Do not paste the same static glow in "
    "every frame. Small sparkle pixels are allowed only when they belong to the active-end bloom cluster and remain "
    "touching, overlapping, or within a few pixels of the active prop end; they must not become loose decorative "
    "sparkles or a separate object. Do not use a detached diamond, object, emblem, badge, floor target, or prop-shaped echo. "
    "If a separate target is explicitly intended, it must touch or overlap the active end and must not drift away. "
    "Avoid large full-body leans, big cross-body swings, diagonal staff sweeps, or full-body scale shifts; keep the "
    "same top-of-head height, bottom edge, body core width, and prop count. Keep the original hand-to-prop attachment "
    "visible in every frame."
)

WORK_MASCOT_ACTING_POLICY = (
    "Every frame must include a visible mascot acting change, not only bloom or cue animation. Add small but readable "
    "body bob, head tilt, surface/detail settle, appendage grip shift, subtle prop follow-through, eye direction, blink, "
    "mouth shape, or cheek/body tilt changes while preserving identity and stable scale. The emotion arc should read "
    "as notice -> focus -> effort -> progress -> pleased settle, with friendly concentration throughout."
)

WORK_TARGET_FIT_POLICY = (
    "Choose the work target from the mascot's visual language. Tech/robot mascots can use panels, tablets, sliders, "
    "or status blocks. Fantasy or magic mascots should use spell circles, rune tiles, charm tokens, staff-tip glyphs, "
    "or glowing sorted motes rather than app-like UI blocks; when they have long held props, prefer attached "
    "active-end blooms, staff-tip glyphs, or glowing sorted motes over separate floating target objects, and use "
    "rune tiles, charm tokens, or spell circles only when they touch or overlap the active end. "
    "Nature mascots can sort leaves, seeds, stones, or wooden "
    "tokens. Icy/water mascots can use frost tiles, droplets, or crystal tokens. Food/plush/toy mascots should use "
    "their own simple objects. The target must still communicate work through before/during/after transformation and "
    "the mascot's gaze, hand, body, or identity prop must visibly cause the change."
)

WORK_TARGET_INTERACTION_POLICY = (
    "Place the work target in a believable interaction zone: near the active hand, paw, mouth, active tool end, staff "
    "head, wand tip, or directly in front of the mascot's gaze. For long props, the active end is the wand tip, staff "
    "head, tool bit, pointer tip, brush tip, blade tip, or nozzle, not the floor, base, butt end, handle end, or lower "
    "shaft unless the source design clearly uses that end. Do not let the target drift to the floor, far side, or "
    "empty space unless a visible gaze line, hand pose, active-end alignment, aura connection, or body lean makes the "
    "causal relationship obvious. For mascots with real hands, paws, staffs, wands, tools, or held identity props, "
    "prefer close-contact targets that touch, overlap, hover just above, or sit within a few pixels of the active "
    "hand/tool end. Avoid floor-level token rows and far-floating targets unless the whole character design naturally "
    "works from the floor. The viewer should understand what the mascot is acting on in every frame."
)

WORK_RESULT_CUE_POLICY = (
    "Use a theme-native result mark when the work resolves: a tiny settled rune, glow, sorted token, progress block, "
    "staff-tip glow, sparkle, or motif-specific success cue. Use generic check marks only when the mascot's visual "
    "language supports product/tool UI; otherwise a check mark should be replaced by a character-native finished state."
)

WORK_STATE_READ_POLICY = (
    "Working must not borrow answering, sleeping, or exhaustion visuals. Do not use breath puffs, speech beads, "
    "panting clouds, sleepy exhale cues, or tired closed-eye holds to show working. A closed-eye frame in working "
    "may only be a quick blink, not a tired or sleepy beat. Keep the face busy, alert, and character-appropriate; "
    "Every working frame must stay busy-friendly or cute-focused; reject even a single frame with angry, hostile, "
    "slanted, narrowed, or V-shaped eyes. "
    "working cues must stay at the work target or tool tip, not at the mouth, and must read as sorting, charging, "
    "checking, tool use, or transformation."
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

STATE_PERFORMANCE_STORY_POLICY = (
    "State performance story arc: every state row must read as one coherent mini-story, not a random emotion collage. "
    "Expressions must be adjacent beats caused by the state action, with small believable transitions rather than "
    "shuffled faces. Avoid abrupt mood jumps, unrelated sad/serious/sleepy/angry/blank faces, and facial expressions that "
    "do not fit the state. Each expression change should be caused by the state action and supported by eye direction, "
    "mouth shape, blink timing, body tilt, appendage motion, prop motion, or cue motion. The final frame must loop "
    "cleanly back to the first frame without a sudden emotional reset."
)

THINKING_STATE_READ_POLICY = (
    "Thinking must read as curious pondering and processing, not worry, confusion, sadness, anger, sleepiness, or error. "
    "Use neutral-curious, tiny closed pondering smiles, gently upturned one-pixel thoughtful smile mouths, blink/hold, and small recognition-smile beats. "
    "Recognition in thinking should be a closed or tiny pixel smile, not a wide open speaking mouth, not an "
    "exclamation mouth, and not a syllable mouth from answering. "
    "Keep the mouth level or slightly upturned; avoid downturned mouths, downturned frowns, "
    "curled lower-lip marks, worried squiggles, serious blank faces, and confused/error mouth shapes. Any closed-eye thinking frame must "
    "read as a quick active processing blink, not sleep, idle rest, fatigue, or meditation. Keep the thought cue "
    "active during that blink, and place open-eye curious or recognition frames immediately before and after it. "
    "Processing blinks should use simple closed curved or short horizontal eyes, not squeezed shut X-eyes, chevron "
    "eyes, scrunched effort eyes, or strain grimaces. Do not use long closed-eye holds, droopy eyelids, sleepy "
    "breathing, or relaxed sleeping mouths in thinking."
)

THINKING_MOOD_CONTINUITY_POLICY = (
    "Thinking mood continuity lock: keep every thinking frame inside one adjacent curious-processing story. "
    "Use neutral-curious, focused pondering, quick active blink, recognition, and pleased settle only. "
    "There should be no worried frown frames, no serious/downturned mouth frames, no confused/error mouth frames, no sleepy closed-eye smile frames, "
    "no blank unrelated face, and no open exclamation or speaking-mouth frames that make the row read as "
    "answering, surprise, confusion, fatigue, or error."
)

THINKING_CUE_CONTINUITY_POLICY = (
    "Cue continuity lock: if a thought/processing cue is used, it must begin visually associated with the "
    "inferred thought-cue source near the expression area, then travel through adjacent frames as a readable small -> slightly larger -> medium -> "
    "smaller -> tiny/settle path while the mascot body footprint stays stable. When the chosen cue uses separated elements, "
    "they must form a stable source-to-peak trail: the smallest element stays closest to the inferred source, "
    "intermediate elements continue the same upward/outward path, and the largest/clearest element appears only "
    "at the idea-lands peak. Do not let intermediate cue elements drift downward, reverse direction, jump sideways, "
    "or reorder the trail. Keep the cue separate from the body core "
    "whenever touching would make the head/body measure larger: a close 2-4 px chroma-key gap or tiny separated tail dot "
    "is better than a bubble fused into the outline. Keep the cue separate from identity props: do not use a prop, accessory, "
    "marking, or emblem as the thought-bubble origin unless that element is explicitly the "
    "active source for the state. The cue must not cover, replace, recolor, or merge with any must-keep identity prop. "
    "It must not pop in for one frame, jump upward into a giant peak, or drop out abruptly. "
    "Near-head cue core-separation lock: do not alpha-connect the thought cue to the mascot core, expression panel, "
    "accessory, or outline when it grows; keep a 2-4 px chroma-key gap between the growing cue and the mascot core. "
    "Use proximity, eye tracking, timing, or one tiny separated tail dot to show the cue source without making QA "
    "measure the cue as body size. Near-head cue footprint lock: keep the full cue path low, close, and compact enough "
    "that it does not become the tallest or widest row element and force atlas assembly to shrink the mascot body; if "
    "the cue needs room, make the cue smaller or tuck it closer to the inferred thought-cue source instead of changing mascot scale. "
    "The final frame should either keep a tiny settled cue or clearly resolve back to frame 1 without a visual snap."
)

THINKING_CUE_VOCABULARY_POLICY = (
    "Thinking cue vocabulary lock: Use one cue family across the whole row. Choose a compact thought bubble/puff, "
    "a small idea orb, or a mascot-native processing aura, then keep that same visual language from first cue "
    "appearance through settle. do not switch between thought bubble, data cloud, lightbulb, exclamation, sparkle, "
    "or icon. There should be no detached lightbulb, no one-frame idea icon, no rays, no punctuation, no UI/data "
    "symbol substitution, and no generic icon replacing the mascot's own thinking performance. "
    "Thinking cue solidity lock: do not use loose sparkles, isolated white specks, star glints, diamond flecks, "
    "or single-pixel dust as the primary thinking read. The cue must read as one deliberate compact thought puff, "
    "bubble cluster, idea orb, or processing aura with hard-edged pixel mass and a clear inferred source near the expression area. "
    "The final frame must not leave a stray dot; either resolve cleanly to no cue or keep a tiny settled cue still visibly "
    "associated with the same state source."
)

THINKING_HANDS_STRATEGY = (
    "Hands/paws thinking strategy: perform thinking through face, eye direction, body tilt, and small safe hand "
    "acting before using a large thought bubble. Face-touch quality gate: a thinking hand, paw, sleeve, mitten, "
    "or appendage may touch or hover near the chin/cheek only when it is clearly the original appendage, remains "
    "visibly connected to its body anchor, preserves the other appendage and any held prop, leaves the eyes and "
    "mouth readable, and improves the thinking pose. If it reads as a new cheek, nose, lower-face patch, detached "
    "mitten, duplicated hand, extra paw, or covered expression, reject it and use a side-anchored beat instead. "
    "Default generic mitten-hand thinking motion remains conservative: side bob, side tilt, low side lift, tiny "
    "outward tilt, low outer-body tuck, shoulder-side lift, or one clean face-touch audition when the silhouette "
    "still reads. Do not use clasped hands under the mouth, prayer hands, finger points aimed into the face, "
    "scalloped mitten/bib clusters below the face, or under-chin presenting poses."
)

THINKING_SIMPLE_APPENDAGE_STRATEGY = (
    "Simple/ambiguous appendage thinking strategy: keep appendages side-attached or only subtly lifted unless "
    "the reference audit proves stronger affordances. Use eyes, head/body tilt, mouth shape, quick blink timing, "
    "and one compact near-head processing cue first. A near-face or face-touch beat is acceptable only when it "
    "looks like the original appendage with a clean connection and no new hand/finger anatomy; otherwise keep the "
    "appendage side-attached. Reject invented chin-touch, cheek-touch, fingered hands, detached mitts, or "
    "lower-face patches."
)

CANONICAL_BASE_ROW_LOCK = (
    "Canonical base row lock: copy the canonical base's main silhouette and design language across every row frame. "
    "Keep the same accessory count and shape, face-bearing area shape, eye style, mouth style, body markings when "
    "present, appendage count when present, outline weight, and palette relationships. Do not upgrade the face into "
    "a different eye style, add/remove/duplicate accessories, or make a quiet identity mark become a large new effect. "
    "Preserve absence as well as presence: plain body areas stay plain, a base with no visible lower appendages stays "
    "that way, and no new display details, badges, buttons, readouts, feet, legs, lower tabs, or other identity marks "
    "appear across rows. Simple face/body stability lock: do not skew, stretch, rotate, squash, or warp the mascot "
    "core or face-bearing area to create acting. Show motion through tiny bob, side shift, mouth/blink change, "
    "appendage beat, prop beat, or cue timing instead."
)

NO_LIMB_FACE_ARTIFACT_POLICY = (
    "No-limb thinking face artifact guard: do not add chin-touch, cheek-touch, hand-to-chin, lower-face squiggles, "
    "extra mouth ticks, chin marks, moustache-like pixels, or small appendage-colored marks on the lower face or chin. "
    "These read as accidental face artifacts, extra anatomy, or unsupported face-touch poses. If the mascot has no "
    "appendages, thinking must come from eyes, blink timing, mouth shape, body tilt, and the thought cue."
)

FACE_TOUCH_SILHOUETTE_POLICY = (
    "For face-touch, chin-touch, cheek-touch, near-face thinking, presenting, or held-prop gestures, keep every "
    "interacting hand, paw, sleeve, tentacle, or arm visibly connected to its original shoulder/body anchor with a "
    "clear silhouette path. Leave a tiny readable gap or outline separation where the appendage nears the face or "
    "prop so it does not merge into a new cheek, nose, mitten, duplicated hand, or face patch. Use broad pixel-mitt "
    "or paw poses rather than tiny fingers unless the reference clearly has fingers."
)

HAND_ROLE_CONTINUITY_POLICY = (
    "Hand/appendage role continuity: account for every original hand, arm, paw, sleeve, fin, wing, or tentacle in every "
    "frame before accepting a pointing, presenting, staff/tool, or work-prop gesture. If the "
    "mascot holds an identity prop, keep the prop-holding appendage attached and identifiable while the other appendage "
    "acts. Thinking hand acting may be side-based or face-touch when the pose looks polished and native; either way "
    "the acting appendage must stay connected to its original anchor and must not become a face patch, detached mitten, "
    "or new paw/finger cluster. Reject any frame with a third hand, extra arm, duplicate sleeve, detached mitten, "
    "new paw/finger cluster, or face-touch that hides the expression."
)

VISIBLE_APPENDAGE_ACTING_POLICY = (
    "Visible appendage acting policy: when the mascot has usable hands, paws, sleeves, arms, or other expressive "
    "appendages. Do not leave hands, paws, sleeves, or held props frozen across the whole row. High-visibility rows "
    "should include at least two small safe appendage acting beats while preserving the exact appendage count. If an "
    "identity prop is held, the prop-holding hand remains attached while the free hand can lift, present, tuck, point, "
    "or settle. Keep motions small and readable: no extra hands, duplicate arms, detached mittens, finger clusters, "
    "or new grip anatomy."
)

APPENDAGE_STATE_ACTING_HINTS = {
    "thinking": (
        "State-specific appendage acting: thinking rows can use a side-anchored low free-hand lift, side bob, "
        "tiny outward side tilt, low outer-body tuck beside the body, staff-hand grip shift, or one polished "
        "near-face/face-touch thinking beat when the original appendage remains connected and the expression stays "
        "readable. Reject only the bad versions: extra hands, detached mitts, lower-face patches, hidden eyes/mouth, "
        "or under-chin clusters."
    ),
    "answering": (
        "State-specific appendage acting: answering rows can use a small presenting beat, conversational hand bounce, "
        "palm-up gesture, or free-hand settle while mouth shapes stay primary."
    ),
}

IDENTITY_PROP_POLICY = (
    "Identity prop contract: preserve must-keep props, emblems, clothing silhouettes, and signature accessories as "
    "part of the mascot identity. Simplify ornate detail into a few readable pixel clusters, not noisy filigree. "
    "If a prop appears in a state row, keep its count, side, scale, attachment, and basic silhouette stable across "
    "the row; animate it with small pose/angle/follow-through changes instead of redesigning it. Preserve signature "
    "props by default even when another cue is present; place the cue in available space, near the mouth, near the "
    "head, or near the active prop end instead of dropping the prop. State cues must not cover, replace, recolor, "
    "merge with, or grow out of identity accessories, body marks, outfit details, or held props unless the state "
    "explicitly uses that element as the active source. Omit a must-keep prop only when the state card says "
    "that exact prop is optional for that whole row, never because a thought bubble, voice puff, or work cue was added. "
    "Do not duplicate signature props, turn decorative trim into extra limbs, or mutate an identity prop into a "
    "different object unless that row is explicitly auditioning a new design."
)

VOICE_CUE_POLICY = (
    "Talking performance is primary: sell answering through mouth shapes, eye engagement, blink timing, tiny "
    "conversational bob, and subtle head/body rhythm. Speech pips, sound ticks, tiny rings, breath marks, or voice "
    "pixels are optional; use them only when they improve readability. Voice cues are optional and should be omitted "
    "when they cannot stay clearly attached to the mouth. Mouth shapes must change clearly even when no voice cue is "
    "used: closed smile -> small open -> wider open -> syllable hold -> smile. If a voice cue is used, it must "
    "touch or overlap the mouth/lip edge or begin within 1-2 pixels of it, close enough to support the speaking "
    "impression instead of carrying the whole state, and not as a detached cue away from the mouth. Prefer a short "
    "2-3 frame outward trail that starts at the mouth and fades or returns; not a single isolated speck in only "
    "one frame, not one-frame voice ticks or one-frame sound marks. If a cue cannot appear in at least two adjacent "
    "frames with a mouth-origin progression, omit it; not a cheek mark, face marking, or detached fleck. "
    "For no-limb, fins-no-hands, and ambiguous-limb "
    "mascots, prefer mouth-only answering through mouth shapes, eye engagement, blink timing, and body rhythm; "
    "omit voice pixels instead of creating a cheek mark or detached fleck. Use breath, frost, smoke, or cloud puffs only "
    "when they belong to the source mascot and still read as speech. Do not make a separate chat panel, thought "
    "bubble, generic speech panel, or odd detached round bubble."
)

ANSWERING_STATE_READ_POLICY = (
    "Answering must look like engaged talking/streaming, not tired panting or exhaling. Keep the eyes lively, "
    "attentive, or characterfully focused; avoid sleepy closed-eye holds unless it is a quick speaking blink. "
    "Any voice cue should support the speaking impression instead of carrying the whole state; avoid repeated "
    "exhale clouds, cough-like puffs, or fatigue beats. Do not over-police tiny cue geometry when the mascot "
    "already reads as talking through expression, mouth rhythm, and body timing."
)

EXPRESSION_VARIATION_POLICY = (
    "Expression variation is mandatory for high-visibility states. Across the row, change at least two of: eye "
    "direction, blink/closed-eye frame, tiny anchored pupil/highlight shift, mouth shape, smile/open-mouth size, "
    "cheek/body tilt, or hand/appendage pose. Do not keep the same face in every frame while only moving the visual "
    "aid, and do not treat expression variation as permission to change the mascot's eye grammar."
)

ANATOMY_GUIDANCE = {
    "hands": (
        "Visible hands may point, present, hold, type, or write when the reference supports it. "
        "Simple mittens, sleeve nubs, rounded side hands, and fingerless blobs are conservative side appendages, "
        "not articulated hands: use side bob/tilt/tuck unless a stronger affordance has been proven. Keep exactly "
        "the original hands/arms; no duplicates. Thinking face-touch is allowed when it is a polished auditioned "
        "pose: the original hand remains connected, the expression stays readable, and no extra hand or face patch appears."
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
        "acting and small anchored aids over risky grip poses. Face-touch is allowed only when the visual result "
        "clearly reads as the original appendage and not as new anatomy."
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
        "eyeGrammar": args.eye_grammar or "Infer exact eye count, shape, spacing, fill, outline, and highlight logic from the reference.",
        "forbiddenGenericCues": forbidden,
    }


def thinking_cue_strategy_for(anatomy_class: str) -> str:
    if anatomy_class in {"hands", "paws"}:
        return THINKING_HANDS_STRATEGY
    if anatomy_class in {"fins-no-hands", "no-limbs", "ambiguous-limbs"}:
        return THINKING_SIMPLE_APPENDAGE_STRATEGY
    return ""


def build_state_plan(state: str, anatomy_class: str, state_clarity: str) -> dict[str, str]:
    visual_aid = STATE_VISUAL_AIDS.get(state, "none unless the pose is unclear")
    freestanding_prop_policy = ""
    body_surface_cue_policy = ""
    face_artifact_policy = ""
    appendage_acting_policy = ""
    if anatomy_class in {"hands", "paws", "ambiguous-limbs"}:
        appendage_acting_policy = " ".join(
            part
            for part in [
                VISIBLE_APPENDAGE_ACTING_POLICY,
                APPENDAGE_STATE_ACTING_HINTS.get(state, ""),
            ]
            if part
        )
    if state == "thinking" and anatomy_class in {"fins-no-hands", "no-limbs", "ambiguous-limbs"}:
        visual_aid = (
            "one compact thought bubble, thought puff, or idea orb with expressive face/body acting; "
            "use eyes, tilt, blink timing, and mouth changes, not hand-to-chin when anatomy cannot support it"
        )
        face_artifact_policy = NO_LIMB_FACE_ARTIFACT_POLICY
    if anatomy_class == "no-limbs" and state == "working":
        visual_aid = (
            "face/body acting plus a body-surface, rim-touching, attached, or overlapping processing cue with "
            "purposeful cycling, sorting, checking, or gathering motion; freestanding/resting props only as a "
            "last-resort fallback; no held, near-hand, or tiny detached speck props"
        )
        freestanding_prop_policy = NO_HAND_WORK_PROP_POLICY
        body_surface_cue_policy = BODY_SURFACE_CUE_POLICY
    if anatomy_class in {"fins-no-hands", "ambiguous-limbs"} and state == "working":
        visual_aid = (
            "busy-but-friendly face/body acting plus a compact attached, overlapping, rim-touching, or body-surface "
            "processing cue; freestanding/resting props only as a last-resort fallback; no held props or tiny "
            "detached specks in the draft plan"
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
        "statePerformanceStoryPolicy": STATE_PERFORMANCE_STORY_POLICY,
        "stateStoryBeats": STATE_STORY_BEATS.get(
            state,
            "notice -> perform the state -> readable peak -> clean settle",
        ),
        "stateActingChoreography": " ".join(
            part
            for part in [
                STATE_ACTING_CHOREOGRAPHY_POLICY,
                STATE_ACTING_CHOREOGRAPHY.get(
                    state,
                    "Frame 1: establish the state. Frame 2: start the acting change. Frame 3: build the "
                    "expression/body/cue action. Frame 4: clear peak read. Frame 5: hold or blink with "
                    "follow-through. Frame 6: begin recovery. Frame 7: settle. Frame 8: loop back cleanly.",
                ),
            ]
            if part
        ),
        "thinkingStateReadPolicy": THINKING_STATE_READ_POLICY if state == "thinking" else "",
        "thinkingMoodContinuityPolicy": THINKING_MOOD_CONTINUITY_POLICY if state == "thinking" else "",
        "thinkingCueStrategy": thinking_cue_strategy_for(anatomy_class) if state == "thinking" else "",
        "thinkingCueContinuityPolicy": THINKING_CUE_CONTINUITY_POLICY if state == "thinking" else "",
        "thinkingCueVocabularyPolicy": THINKING_CUE_VOCABULARY_POLICY if state == "thinking" else "",
        "faceArtifactPolicy": face_artifact_policy,
        "appendageActingPolicy": appendage_acting_policy,
        "frameArc": STATE_FRAME_ARCS.get(
            state,
            "Frame-by-frame acting arc: each frame must change face, gaze, posture, appendage motion, prop motion, or cue position enough to read as animation.",
        ),
        "freestandingPropPolicy": freestanding_prop_policy,
        "workPropMarkPolicy": WORK_PROP_MARK_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetPolicy": WORK_TARGET_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workIdentityPropEffectPolicy": WORK_IDENTITY_PROP_EFFECT_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workLongHeldPropPolicy": WORK_LONG_HELD_PROP_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetFitPolicy": WORK_TARGET_FIT_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workTargetInteractionPolicy": WORK_TARGET_INTERACTION_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workResultCuePolicy": WORK_RESULT_CUE_POLICY if state == "working" and state_clarity != "pose-only" else "",
        "workStateReadPolicy": WORK_STATE_READ_POLICY if state == "working" else "",
        "workMascotActingPolicy": WORK_MASCOT_ACTING_POLICY if state == "working" else "",
        "bodySurfaceCuePolicy": body_surface_cue_policy,
        "voiceCuePolicy": VOICE_CUE_POLICY if state == "answering" and state_clarity != "pose-only" else "",
        "answeringStateReadPolicy": ANSWERING_STATE_READ_POLICY if state == "answering" else "",
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
    eye_grammar = visual_language.get(
        "eyeGrammar",
        "Infer exact eye count, shape, spacing, fill, outline, and highlight logic from the reference.",
    )
    forbidden = ", ".join(visual_language.get("forbiddenGenericCues", []))
    key_hex = chroma_key["hex"]
    key_name = chroma_key["name"]
    return f"""# {name} canonical base companion prompt

Create one centered full-body canonical base sprite for a React/chatbot companion mascot named {name}.

Reference and concept: {description or "Use the attached reference image(s) as the mascot identity source."}
Vibe read: {source_vibe}
Mascot-native motifs to preserve when useful: {motifs}
Must-keep identity props/accessories: {identity_props}
Eye grammar to preserve: {eye_grammar}
Generic cues to avoid: {forbidden}
Anatomy class: {anatomy_class}

Style lock: Codex digital-pet pixel art, compact chibi sprite, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, hard-edged sprite details, simple expressive face, readable silhouette at website sizes. No smooth illustration, glossy rendering, 3D, painterly gradients, vector-flat icon style, text, labels, scenery, shadows, UI panels, or marketing artwork.

{BASE_PRODUCTION_LOCK}

{HARD_NATIVE_PIXEL_RENDERING_LOCK}

{SOURCE_PIXEL_GRID_LOCK}

{INDEXED_COLOR_SPRITE_CELL_LOCK}

{REFERENCE_NATIVE_STYLE_LOCK}

{REFERENCE_AWARE_PALETTE_GUIDE}

{REFERENCE_PALETTE_FIDELITY_POLICY}

{HATCHPET_COMPACT_SOURCE_TARGET}

{FLAT_CHROMA_KEY_LOCK}

{BASE_ACCEPTANCE_GATE}

{BASE_EYE_GRAMMAR_LOCK}

{TEXT_CONCEPT_ANATOMY_LOCK}

{PART_SIMPLIFICATION_LOCK}

{CHARACTER_DIRECTION_LOCK}

Output one neutral full-body mascot sprite pose only on a perfectly flat pure {key_name} {key_hex} chroma-key background. Preserve the reference identity, silhouette cues, palette family, face, must-keep markings, appendage count, and charm. Do not include state props, speech bubbles, thought bubbles, detached particles, scenery, or extra anatomy. Do not use {key_hex}, pure {key_name}, or colors close to that chroma key in the mascot, outline, highlights, or effects.
"""


def build_thinking_prompt(
    *,
    name: str,
    state_plan: dict[str, str],
    anatomy_class: str,
    frame_count: int,
    source_vibe: str,
    identity_props: list[str] | None = None,
    eye_grammar: str | None = None,
    chroma_key: dict[str, Any] | None = None,
) -> str:
    key_hex = chroma_key["hex"] if chroma_key else "the chosen chroma-key color"
    key_name = chroma_key["name"] if chroma_key else "flat"
    props = ", ".join(identity_props or [])
    identity_prop_line = (
        f"Must-keep identity props/accessories: {props}"
        if props
        else "Must-keep identity props/accessories: infer from base/reference."
    )
    if anatomy_class in {"hands", "paws"}:
        hand_line = (
            "Use only existing appendages. A free appendage may lift, tilt, settle, or make one polished thinking "
            "face-touch beat. Keep any prop-holding appendage attached. Face-touch is acceptable only when the "
            "appendage stays connected to its original anchor, leaves eyes and mouth readable, and does not read as "
            "a face patch, duplicate appendage, or lower-face blob. If unclear, use a side-anchored lift/tilt/tuck."
        )
    elif anatomy_class in {"fins-no-hands", "ambiguous-limbs"}:
        hand_line = (
            "Keep simple side appendages outside the body with tiny bobs/tilts/tucks. A near-face or "
            "face-touch beat is acceptable only if it clearly remains the original connected appendage and does not "
            "become a new hand, finger, lower-face patch, or detached blob. If unclear, leave it resting."
        )
    else:
        hand_line = (
            "No appendage acting: use eyes, mouth, body tilt/bob, and thought-cue timing only. "
            "Do not invent hands, hand-to-chin poses, or face-touching appendages."
        )
    if frame_count == 6:
        frame_story = """Six-frame acting story:
1 reset: open eyes, tiny calm closed smile, no thought cue.
2 thought starts: source-matched open eyes, no white side-glance or new sclera; one tiny compact cue appears near the inferred thought-cue source.
3 pondering: tiny closed pondering smile or gently upturned one-pixel smile; the cue grows slightly while staying close and secondary along the source-to-peak trail.
4 forming: compact source-bound cluster or pulse keeps that trail; no cue element drops or reverses.
5 idea lands: compact cue peak beside the inferred source at trail end; primary cue element is only slightly larger, never oversized; pleased blink or tiny closed-mouth recognition smile.
6 settle: eyes open; cue shrinks to one tiny close remnant or resolves cleanly; loop cleanly back to the first frame."""
    else:
        frame_story = f"""{frame_count}-frame acting story:
Neutral-curious reset -> attention shift -> closed-smile pondering -> compact cue forming -> idea lands -> pleased settle. Peak with a compact source-bound cue: primary cue element is only slightly larger, never oversized. Use a quick active processing blink or tiny closed-mouth recognition smile. Loop back cleanly to frame 1."""
    vibe_line = (
        f"\nVibe fit: {source_vibe}"
        if source_vibe and source_vibe != "Infer from the reference before choosing state cues."
        else ""
    )
    return f"""# {name} thinking row prompt - compact

Create one horizontal sprite row strip with exactly {frame_count} separated frames on a flat {key_hex} chroma-key background.

Inputs: base locks identity/eyes/scale/style; accepted rows size/padding; guide slots only.

Identity/style lock:
Preserve the same mascot body, palette, outline weight, appendage count, markings, and held props. {identity_prop_line} Match base size/padding. Do not skew, stretch, rotate, squash, or warp the body core or face-bearing area.
Eye grammar to preserve: {eye_grammar or "infer exact eye count, shape, spacing, fill, outline, and highlight logic from base/reference."}
Native Codex digital-pet pixel-art sprite: hard square pixels, chunky outline, limited palette, flat cel shading. {BACKGROUND_SOURCE_LOCK} No smooth illustration or glossy rendering.

{state_plan["semanticRead"]}; not surprised, answering, worried, sleepy, or confused. Face/body/appendage timing should sell thinking before the cue is noticed.
{STATE_SPECIFIC_GUARDS["thinking"]}

Story arc: neutral-curious -> noticing -> curious pondering -> idea lands -> pleased settle. Expressions are adjacent state-caused beats, not random sad, serious, sleepy, angry, blank, or unrelated faces. Every frame changes face, posture, body/appendage timing, or cue enough to matter; no stale same-face holds.

Frame-by-frame acting arc:
{frame_story}

Thought cue rules:
- Thinking cue solidity lock: use deliberate compact cue shapes, not loose specks.
- Use one compact source-appropriate non-chroma-key cue vocabulary only; no lightbulb, star, ray, sparkle, diamond, rune, punctuation, UI icon, or glow.
- The peak should be a compact cue beat, not a mandated symbol or puff count; primary cue element is only slightly larger, never oversized; do not enlarge the cue to prove the idea landed. Preserve the chosen cue vocabulary.
- Separated cue elements keep a stable source-to-peak trail; the smallest element stays closest to the inferred source. Do not let intermediate cue elements drift downward, reverse, jump sideways, or reorder; largest/clearest lands at peak.
- Infer thought-cue source from the canonical base; keep the cue close, low, compact, and secondary. Do not make a tall vertical stack. Do not let the cue force the mascot smaller.

Expression and eye rules:
- Use closed/thoughtful mouths only: closed smile, tiny pleased smile, or gently upturned one-pixel smile.
- No round open o-mouth, exclamation mouth, speaking syllable mouth, shocked mouth, teeth, brows, or worry marks.
- {THINKING_EYE_LOCK} Closed eyes are simple short curved lines in the same eye positions and spacing.

Hand/appendage rules:
{hand_line}

{vibe_line}

Reject if any frame has wrong eye grammar, surprised/answering mouth, stale same-face row, sad/serious/downturned expression, extra/missing held prop or limb, random symbol, giant/high thought cue, cue vocabulary switch, scale shrink, non-flat {key_name} {key_hex} background, smooth/glossy or non-native pixel-art rendering, or background texture. Good state read is not enough if identity, cleanup, eye grammar, anatomy, or scale drifts.
"""


def compact_frame_story(*, state: str, state_plan: dict[str, str], frame_count: int) -> str:
    beats = state_plan["stateStoryBeats"]
    if state == "answering":
        return (
            f"Use all {frame_count} frames as one loop: {beats}. Mouth shapes must visibly cycle from closed/tiny "
            "smile to small open to wider open or syllable hold, then back toward a settled speaking pose. Add eye "
            "engagement, blink timing, and small body/appendage rhythm so the mascot itself reads as talking."
        )
    if state == "working":
        return (
            f"Use all {frame_count} frames as one loop: {beats}. Show a concrete before/during/after work action: "
            "notice the task, focus, operate or transform one small target/cue, show progress, then settle. The "
            "mascot must act in every frame through gaze, mouth, body, appendage, prop, or surface-detail timing."
        )
    return (
        f"Use all {frame_count} frames as one loop: {beats}. Frame 1 establishes the state, early frames start the "
        "face/body change, middle frames carry the clearest read, late frames recover, and the final frame loops "
        "cleanly back to frame 1. Every frame should change face, gaze, mouth, body, appendage, prop, or cue timing "
        "enough to matter at website size."
    )


def compact_cue_rule(*, state: str, state_plan: dict[str, str]) -> str:
    if state_plan["visualAidDecision"] == "pose-only":
        return (
            "Use no detached semantic cue. Communicate the state through the canonical mascot's expression, posture, "
            "timing, existing appendages, and existing identity props only."
        )
    if state == "answering":
        return (
            "Mouth-led talking is primary. Optional voice pixels or pips may appear only as a tiny mouth-origin trail "
            "over adjacent frames; omit them if they look like cheek marks, punctuation, UI, breath/exhale, or a "
            "separate speech panel."
        )
    if state == "working":
        return (
            "Use at most one small mascot-native work cue when acting alone is unclear. It must be caused by the "
            "mascot's gaze, existing appendage, existing prop, or body-surface timing, and it must show progress or "
            "resolution. No text, pseudo-writing, generic UI panel, loose sparkle field, duplicate identity prop, or "
            "invented hand/tool."
        )
    if state == "listening":
        return (
            "If acting alone is unclear, use one tiny attached listening cue that supports attentive pose and gaze. "
            "Do not add a generic microphone, text, or detached sound clutter."
        )
    if state in {"success", "error", "confused"}:
        return (
            "If acting alone is unclear, use one small state cue that is attached to or source-bound to the mascot and "
            "fits the reference's visual language. Keep it secondary to expression and body acting."
        )
    return (
        "Use a semantic cue only if the pose would be unclear at small size. Keep it tiny, source-bound, hard-edged, "
        "non-text, and secondary to the mascot's performance."
    )


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
    eye_grammar: str | None = None,
    chroma_key: dict[str, Any] | None = None,
) -> str:
    if state == "thinking":
        return build_thinking_prompt(
            name=name,
            state_plan=state_plan,
            anatomy_class=anatomy_class,
            frame_count=frame_count,
            source_vibe=source_vibe,
            identity_props=identity_props,
            eye_grammar=eye_grammar,
            chroma_key=chroma_key,
        )
    key_hex = chroma_key["hex"] if chroma_key else "the chosen chroma-key color"
    key_name = chroma_key["name"] if chroma_key else "flat"
    props = ", ".join(identity_props or [])
    identity_prop_line = f"Must-keep identity props/accessories: {props}" if props else "Must-keep identity props/accessories: infer from the reference; keep signature props, emblems, and outfit silhouettes consistent when present."
    frame_story = compact_frame_story(state=state, state_plan=state_plan, frame_count=frame_count)
    cue_rule = compact_cue_rule(state=state, state_plan=state_plan)
    state_guard = STATE_SPECIFIC_GUARDS.get(
        state,
        "Stay inside the requested state and avoid neighboring-state reads, generic UI symbols, and random mood jumps.",
    )
    return f"""# {name} {state} row prompt - compact

Create one horizontal sprite row strip with exactly {frame_count} separated frames on a perfectly flat solid {key_hex} chroma-key background.

Use attached images this way:
- Original references define identity and source vibe.
- The canonical base is the approved design, body size, eye grammar, outline, palette, props, appendages, and style source.
- Accepted row images, when present, define apparent body size and padding.
- The layout guide is only for frame slots and safe padding. Do not draw guide lines, boxes, labels, or guide colors.

Identity lock:
- Preserve the same mascot body, silhouette, palette, outline weight, eye grammar, mouth language, appendage count, markings, accessories, and held props. Do not redesign the character.
- {identity_prop_line}
- Preserve absence too: do not add new limbs, props, display details, markings, lower tabs, or body features that are not in the canonical base/reference.
- Do not skew, stretch, rotate, squash, or warp the body core or face-bearing area to create acting.
- Eye grammar to preserve: {eye_grammar or "infer exact eye count, shape, spacing, fill, outline, and highlight/catchlight logic from the canonical base and original reference."}
- Closed-eye frames must keep the same eye positions and spacing as simple short lines/curves, not symbols or a new eye style.

Style lock:
Native Codex digital-pet pixel-art sprite, hard square pixels, thick dark 1-2 px outline, limited palette, flat cel shading, hard-edged sprite effects. {BACKGROUND_SOURCE_LOCK} Chosen chroma key: {key_name} {key_hex}. No smooth illustration, glossy sticker rendering, 3D, painterly gradients, vector icons, soft antialiasing, shadows, scenery, UI panels, text, symbols, or guide marks.

State goal:
- State: {state}
- Read: {state_plan["semanticRead"]}
- Acting first: {state_plan["actingFirst"]}
- Story: {state_plan["stateStoryBeats"]}
- State boundary: {state_guard}
- Vibe fit: {source_vibe}

State performance story arc:
Make the row a coherent mini-story, not a checklist or random emotion collage. Expressions must be adjacent beats caused by the state action and loop cleanly back to the first frame. Do not let all motion live in a cue while the mascot face and body stay frozen.

Frame plan:
{frame_story}

Cue/prop rule:
{cue_rule}

Expression and anatomy rules:
- Preserve the reference's expression language. Avoid angry brows, hostile eyes, teeth, sweat, dramatic marks, or state-inappropriate mood jumps unless the source design already supports them.
- {SOURCE_EYE_LOCK}
- Use only appendages and props visible in the canonical base/reference. Preserve count, side, attachment, and basic silhouette across the row.
- If an appendage affordance is unclear, keep movement subtle and side/body-attached; carry the state through eyes, mouth, body timing, and source-bound cue timing.
- No extra limbs, duplicate props, detached appendage blobs, prop echoes, random icons, punctuation, or text.

Scale and layout rules:
- Keep each pose fully inside an implied {cell_width}x{cell_height} cell with safe padding.
- Match the canonical base and accepted rows for apparent body size, center, top edge, bottom edge, and body core width.
- If a gesture, mouth shape, cue, or prop needs room, make that action smaller or tighter; do not shrink or enlarge the mascot body to make space.
- Do not use {key_hex}, pure {key_name}, or chroma-key-adjacent colors in the mascot, prop, outline, highlights, or effects.

Reject if: {state_plan["rejectIf"]}; wrong eye grammar; frozen same-face row; symbol-only acting; extra/missing appendages or props; scale drift versus accepted rows; non-flat {key_name} {key_hex} background; or non-native pixel-art rendering.
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
        {
            "path": rel(Path(str(ref["copiedPath"])), run_dir),
            "role": (
                "original mascot reference and style source; preserve character identity, pixel density, palette, "
                "eye grammar, outfit, and props, but do not copy noisy or non-flat preview background"
            ),
        }
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
            "generation_owner": "parent",
            "subagent_eligible": False,
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
                "generation_owner": "subagent-when-authorized",
                "subagent_eligible": True,
                "subagent_handoff": ROW_SUBAGENT_HANDOFF,
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
    parser.add_argument("--eye-grammar", help="Optional exact eye grammar inferred from the reference")
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
    unknown_states = [state for state in states if state not in SUPPORTED_STATES]
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
            eye_grammar=visual_language.get("eyeGrammar"),
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
            "row_generation_policy": ROW_GENERATION_POLICY,
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
