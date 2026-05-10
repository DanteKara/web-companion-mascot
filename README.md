# Web Companion Mascot

Create high-quality pixel-art animated mascot companions for React and chatbot websites from character art, screenshots, Codex pets, or generated references.

This is a Codex skill. It helps produce a web-ready mascot package with:

- stateful animation rows such as `idle`, `listening`, `thinking`, `answering`, `success`, `error`, `confused`, and `sleeping`
- a transparent sprite atlas in `atlas.webp` and `atlas.png`
- a strict `manifest.json`
- extracted per-frame PNGs
- visual QA sheets for contact, cutout, semantic readability, semantic anchor, motion quality, and art-direction checks
- a generated React component and companion-state hook

The skill is designed for mascot companions that need to feel alive inside a product UI, especially AI chatbots.

Production mascot art uses the Codex digital-pet pixel-art house style: compact chibi sprites, visible stepped pixel edges, thick readable outlines, limited palettes, flat cel shading, and crisp hard-edged effects. Non-pixel references are translated into that style while preserving identity and charm; smooth illustration, glossy app-icon art, painterly gradients, 3D rendering, and vector-flat clip art are not production passes.

Canonical base art has the same bar as row art. It is the final atlas-frame source of truth, not concept art, a preview illustration, a pose-sheet sample, an app icon, or a softened style target. The base should read like a Codex app digital pet first and a website mascot second: fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite cell even when the final web atlas later uses larger cells. Reject and regenerate the base before row generation if it is smoother, glossier, more detailed, or less pixel-native than the intended row art; rows must preserve the accepted base, not fix it by changing eye style, body shape, colors, outline weight, props, or anatomy. For text-only concepts, the base prompt should add only named anatomy and identity props; unrequested feet, legs, chest lights, badges, emblems, screens, buttons, tools, or extra props are not harmless decoration because row prompts will try to preserve them. A good base uses indexed-color sprite discipline: roughly 8-16 non-background colors, flat pixel clusters, simple blocked highlights, no per-pixel color ramps, no smooth shade bands, no gradient-filled body/face/clothing/props/antenna/mittens, no blended intermediate palette colors, and no glossy gradients, soft airbrush shading, bloom, rim glow, or smooth vector curves. Build the palette from the reference or text concept rather than imposing a stock helper-bot palette. When a reference already comes from HatchPet or another Codex digital-pet-style source, treat it as the style floor: preserve its pixel density, chunky outline, hard block shading, eye/catchlight grammar, cheek and mouth pixel language, outfit and held-prop simplification, palette relationships, and compact proportions while ignoring only noisy preview backgrounds or unstable tiny detail. Softness belongs in shape language and expression, not blurred rendering: draw as if the mascot was first made on a tiny 64x72 or 80x90 pixel grid and enlarged with nearest-neighbor scaling. Use hard-edged square pixel clusters, 2-3 flat tone steps per material, large flat color clusters, one darker stepped shadow band at most, and tiny rectangular pixel highlights instead of broad glossy shine patches, feathered transitions, semi-transparent shines, smooth radial gradients, pillow shading, app-icon material lighting, or smooth antialias fringes. Do not compose the base as a large glossy product mascot, large hero character, app icon, or high-resolution sticker; leave generous chroma-key padding and keep it compact. Row prompts should preserve absence as well as presence: a plain canonical body must stay plain, with no new chest panel, status light, belly screen, button, badge, dot cluster, readout, emblem, or robot UI detail. A rounded footless base must stay footless and legless; reject foot nubs, shoes, base tabs, toe pixels, shadow feet, or lower protrusions.

Generated production rows default to an 8-frame HatchPet-style baseline. Use 6-frame rows for compact auditions and longer 10-12 frame rows only as an explicit smoothness pass after the mascot stays stable.

Prompt planning follows HatchPet-style sprite artifact rules: the mascot performs the state through pose, face, silhouette, and identity props first; any effect must be small, pixel-style, state-relevant, and physically attached, touching, or overlapping the mascot, mouth, hand, tool, or worn prop. Detached-but-anchored thought cues are allowed for readability, but they must not become body-core scale. The chroma-key background must be one perfectly uniform solid color from corner to corner, with no vignette, lighting falloff, texture, noise, shadow, ground plane, or background glow. Do not show bobbing or emphasis with floor shadows, contact shadows, ground lines, baseline marks, landing marks, or dark under-body strokes. Freestanding work props are fallback choices for explicitly requested no-hand `working` states, not the default.

Every state row should tell one coherent loopable performance story, not a random emotion collage. The expressions should be adjacent beats caused by the state action, such as calm -> blink -> settle, neutral-curious -> pondering -> recognition -> pleased settle, or ready -> speaking -> conversational blink/smile -> settle. Abrupt mood jumps and unrelated sad/sleepy/angry/blank faces are art-direction blockers.

Production prompts include positive state choreography. Each row should coordinate expression, body/appendage, and cue/prop tracks so the mascot acts the state instead of sitting still under a moving symbol. A good `answering` row changes mouth shapes, eye direction/blinks inside the source eye grammar, body rhythm, and supported hand gestures; a good `thinking` row changes gaze, mouth, blink, body/hand posture, and a modest thought cue. Thinking cues should have deliberate pixel mass, not loose sparkle dust: use a compact thought puff, bubble cluster, idea orb, or processing aura that stays connected to the head and resolves without a stray final dot. Parked hands, frozen appendages, unchanged faces, and symbol-only rows are not production passes.

For prompt tuning and visual auditions, test one high-risk row at a time whenever possible. A full multi-state sheet is useful as a stress test, but production quality should be judged row by row with the canonical base, layout guide, QA sheets, and visual review.

For explicitly requested `working` rows on mascots with staffs, wands, tools, brushes, pens, or other long held identity props, cues use the original prop as one continuous object. Prefer a small hard-edged active-end bloom, aura, pulse, or contact mark wrapped around or touching the existing prop tip/head. The bloom should visibly change frame by frame, such as dim seed -> small bloom -> brighter wrap -> peak cluster -> shrinking settle, instead of becoming a static glow. Small sparkle pixels are fine when they stay close enough to read as part of that active-end bloom. An active prop pose replaces the resting pose, hand-to-prop attachment stays visible, the body core stays stable, and any separate target must touch or overlap the active end instead of becoming a detached diamond/object, second prop, or floor-level duplicate cue.

The full reference palette is part of identity. Row prompts should preserve the actual source colors for eyes/highlights, pupils, face, outfit, props, cheek marks, and signature markings instead of forcing white eyes or letting prop glows recolor the mascot. Eye grammar is identity too: preserve the canonical base's eye count, shape, size, spacing, outline color, pupil/fill color, and catchlight/highlight logic. Do not let rows invert dark pupils into hollow white eyes, turn solid eyes into white ovals with dark rims, add extra catchlights, invent glossy anime eyes or square UI eyes, or swap eye styles for a single frame. For solid dark base eyes, open eyes should remain mostly dark with the original tiny highlight; gaze can move the dark oval or tiny highlight slightly, but should not expose white sclera crescents, carve white crescent gaps for side glances, or make a white cutout the dominant eye shape. If an up-glance, side-glance, blink, or speaking beat would require changing eye style, keep the eyes forward or nearly forward and carry the acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead. Keep eye centers inside the original eye boxes; never slide eyes onto cheeks, panel edges, the mouth line, or outside the face panel. Blinks should use the source's own style as simple closed curves or horizontal pixel lines in the same eye positions, not X-eyes, chevrons, reaction glyphs, or lower-face squiggles. Default chatbot packs fold tool/search/backend waiting into a stronger `thinking` state instead of generating `working`; optional explicitly requested `working` rows still reject angry/hostile frames and require visible body/emotion acting rather than only animating a cue.

For references with distinctive or fragile eyes, pass an inferred `--eye-grammar` note to `prepare_companion_run.py` so base and row prompts carry a compact eye contract alongside the broader eye-continuity policy. The note should name the eye count, shape, spacing, fill/pupil color, outline color, highlight/catchlight count, and blink style.

State cues must not consume must-keep props. A thought bubble, voice puff, work glyph, or status cue should not cover, replace, recolor, merge with, or grow out of antenna bulbs, ears, horns, hats, badges, emblems, staffs, wands, or other identity props unless that prop is explicitly the active source. For antenna mascots, thinking cues should originate from the main head/hood side or top edge, not from the antenna tip, and the antenna bulb should remain visible and stable. For screen-faced, mask-faced, or simple front-panel mascots, preserve the face panel as identity; do not skew, stretch, rotate, squash, or trapezoid the face/body core to fake animation. Use tiny bob, side shift, mouth/blink change, appendage beats, and cue timing instead.

Thinking cues should animate modestly: small -> slightly larger -> medium -> smaller -> tiny/settle. Medium is the maximum thought cue size, so the bubble/puff/orb should never become a second head or make the mascot shrink. Thinking cues should move through adjacent frames; they should not pop in for one frame, jump upward into a giant peak, fuse into the body core, or drop out abruptly at the loop. Keep the mascot body footprint stable; when a near-head cue would enlarge the measured head/body outline, use a close 2-4 px chroma-key gap or tiny separated tail dot instead of merging the bubble into the sprite. The cue can be visually associated by proximity, eye tracking, timing, or a separated tail dot without alpha-connecting to the head, antenna, hood, face panel, body core, or outline. Use one cue family across the whole row instead of morphing from thought bubble to data cloud to lightbulb/icon/rays. Thinking expressions should stay curious/pondering/processing, not worried, confused, sad, angry, sleepy, idle/resting, meditating, strained, answering-like, surprised, or error-like. Recognition in thinking should be a closed or tiny pixel smile, not a wide open speaking/exclamation/syllable mouth from answering. Closed-eye thinking frames should be quick active processing blinks with the thought cue still active and open-eye frames before and after; use simple closed curved or short horizontal eyes, not squeezed X-eyes or chevrons. For default hand or paw mascots, prompts keep the face panel and lower face clear: no hand, paw, sleeve, mitten, finger, or prop should enter the face panel, touch the cheek/mouth/chin/lower face, or sit centered directly below the mouth/chin. Default generic mitten-hand thinking motion should be side-anchored: side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck only. Treat simple mittens, sleeve nubs, rounded side hands, and fingerless blobs as conservative side appendages: do not use pointing, presenting across the body, typing, writing, gripping, or face-touch acting unless the reference and an audition prove the affordance. Do not move one hand inward toward the face, point toward the head, cross the body front, or drop the hands to the bottom edge where they read as feet, legs, or lower tabs. Reject hand-to-chin, hand-to-mouth, clasped hands under the mouth, prayer hands, finger points into the face, scalloped mitten/bib clusters below the face, lower-face/chin-adjacent hand poses, under-chin presenting poses, and lower-face mitten/hand patches unless a future explicit face-touch affordance has already passed visual audition. For no-limb and simple-appendage mascots, prompts reject chin-touch, cheek-touch, hand-to-chin, lower-face squiggles, extra mouth ticks, chin marks, moustache-like pixels, or small appendage-colored marks on the lower face/chin. Answering cues are optional; for no-limb, fins-no-hands, and ambiguous-limb mascots, prefer mouth-only answering unless a cue is unmistakably mouth-attached. When used, voice cues should touch or begin within 1-2 pixels of the mouth and form a short 2-3 frame outward trail, not a single detached speck, one-frame voice tick, or cheek-like face mark. If the cue cannot appear in at least two adjacent frames with a mouth-origin progression, omit it.

Visible hands, paws, sleeves, arms, and held props should also perform. High-visibility rows should include at least two small safe appendage acting beats, such as a low free-hand lift, tiny outward point, present/tuck/settle, palm-up gesture, low outer-body tuck, staff-hand grip shift, conversational hand bounce, or free-hand settle. Keep prop-holding hands attached and reject extra hands, duplicate arms, detached mittens, finger clusters, new grip anatomy, and default thinking poses that touch, cover, underline, or frame the mouth, chin, cheeks, lower face, or face panel.

Production mascot art must come from integrated row art generated with `$imagegen` or from finished user/artist-provided row strips. The bundled scripts assemble, clean, validate, and integrate assets; they must not draw or paste final semantic props into production mascot frames.

## Install

### Recommended

Use the Skills CLI:

```bash
npx --yes skills add DanteKara/web-companion-mascot -g -y
```

Or with the full GitHub URL:

```bash
npx --yes skills add https://github.com/DanteKara/web-companion-mascot -g -y
```

The `-g` flag installs the skill globally for your user, and `-y` skips confirmation prompts.

### Manual Fallback

### Windows PowerShell

```powershell
$dest = "$env:USERPROFILE\.codex\skills\web-companion-mascot"
if (Test-Path $dest) {
  git -C $dest pull
} else {
  git clone https://github.com/DanteKara/web-companion-mascot.git $dest
}
```

### macOS / Linux

```bash
dest="$HOME/.codex/skills/web-companion-mascot"
if [ -d "$dest/.git" ]; then
  git -C "$dest" pull
else
  git clone https://github.com/DanteKara/web-companion-mascot.git "$dest"
fi
```

Restart Codex after installing or updating the skill.

## Usage

In Codex, reference the skill when asking for a companion:

```text
Use $web-companion-mascot to create a React chatbot mascot from this image.
Use semantic enhancers and include thinking, listening, answering, success, and error states.
```

For quieter mascots:

```text
Use $web-companion-mascot to create a pose-only companion from this character.
```

## Output

The default generated package looks like:

```text
run/
  companion_request.json
  imagegen-jobs.json
  manifest.json
  prompts/base.md
  prompts/<state>.md
  prompts/rows/<state>.md
  references/canonical-base.png
  references/layout-guides/<state>.png
  atlas.webp
  atlas.png
  frames/<state>/*.png
  qa/assembly-report.json
  qa/state-cue-plan.json
  qa/contact-sheet.png
  qa/cutout-check.png
  qa/state-readability-check.png
  qa/quality-report.json
  qa/anatomy-review.png
  qa/anatomy-review.json
  qa/state-performance-review.png
  qa/state-performance-review.json
  qa/art-direction-review.json
  qa/semantic-anchor-check.png
  qa/motion-quality-check.png
  qa/previews/*.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

`references/layout-guides/<state>.png` files are intentionally empty construction inputs for spacing and safe padding. They are not mascot previews; inspect `qa/contact-sheet.png`, `qa/state-readability-check.png`, previews, and the final atlas for visual output.

## Quality Gates

The skill includes deterministic QA scripts and requires visual inspection before accepting a mascot:

- `prepare_companion_run.py` creates the initial manifest draft, per-state row prompts, and `qa/state-cue-plan.json` so vibe inference, acting beats, visual aids, and anatomy limits are planned before image generation.
- `companion_job_status.py` reports which `$imagegen` jobs are ready or blocked from `imagegen-jobs.json`.
- `record_companion_imagegen_result.py` records selected `$imagegen` outputs, creates the canonical base reference, stores base style analysis, and keeps source provenance/hashes out of manual editing. It reads the run chroma key from `companion_request.json` or `manifest.style.chromaKey` for base-style checks. For production base recording, pass `--strict-base-style` so non-flat chroma keys, smooth gradients, glossy shading, and over-detailed palette ramps fail before row generation. If the base is already finished transparent HatchPet/Codex sprite art supplied by the user or an artist, record it with `--source-provenance user-provided-integrated-row-art` or `--source-provenance artist-provided-integrated-row-art`; strict style still blocks real background/foreground failures, while palette-complexity warnings remain visible for visual review instead of blocking trusted integrated art by themselves.
- `assemble_companion_atlas.py` extracts and cleans row strips into an atlas. It reads the chroma key from the run manifest/request by default, like HatchPet, so generated green/magenta backgrounds are temporary row-generation inputs and the final atlas/frames are transparent.
- `create_state_readability_sheet.py` creates 64, 96, and 128 px previews for state readability.
- `analyze_companion_quality.py` flags near-duplicate frames, low motion, body jitter, large foreground area jumps, same-row and cross-state body scale drift, and drifting semantic enhancers; it also creates semantic-anchor and motion QA sheets. Near-head cues can set `enhancer.componentPolicy: "overlap-ok"` only when manual visual review accepts intentional hood/head overlap or occlusion.
- `create_anatomy_review.py` records the manual/agent frame-by-frame anatomy review for appendage count, identity props, and state cues that might be mistaken for anatomy.
- `create_state_performance_review.py` records the manual/agent frame-by-frame state-performance review for intended state read, expression, cue motion, and wrong-state failures such as `thinking` reading as idle dots or `answering` reading as tired exhale.
- `create_art_direction_review.py` records the manual/agent visual review that the result preserves the reference quality, identity, eye grammar, Codex pixel-art style, creative state readability, theme-native state cues, and native enhancer look.
- `validate_companion_manifest.py` verifies manifest shape, atlas dimensions, transparency, unused cells, cropped sprites, state clarity metadata, rendering-style metadata, assembly warnings, quality warnings, anatomy guard specificity, appendage affordance mismatches, anatomy review blockers, state-performance review blockers, art-direction blockers, and residual key-colored outline halos. For halo checks it uses the assembly report key first, then the run manifest/request chroma key, matching the assembler.
- `generate_react_component.py` emits a TypeScript React component that animates by per-frame manifest durations.

The assembler keeps an outline improver enabled by default:

- key-to-alpha removal
- edge spill cleanup
- spill-color replacement
- transparent RGB cleanup
- premultiplied resizing

Production runs should pass strict validation with zero warnings:

`prepare_companion_run.py` writes draft enhancer metadata such as `planned during row generation`; after selecting final row art, update each enhanced state to describe the actual accepted visual aid. Strict validation warns on leftover draft wording so planning placeholders do not ship as production truth.

```bash
python scripts/prepare_companion_run.py \
  --companion-name MyCompanion \
  --reference /path/to/reference.png \
  --output-dir /path/to/run \
  --state-clarity semantic-enhancers \
  --anatomy-class ambiguous-limbs \
  --force

python scripts/companion_job_status.py \
  --run-dir /path/to/run

python scripts/record_companion_imagegen_result.py \
  --run-dir /path/to/run \
  --job-id base \
  --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png \
  --strict-base-style

python scripts/analyze_companion_quality.py \
  --manifest /path/to/run/manifest.json

# For production, add one --expected-state-read entry for every state in the manifest.
python scripts/create_state_performance_review.py \
  --manifest /path/to/run/manifest.json \
  --status pass \
  --production-use \
  --review-all-frames \
  --expected-state-read thinking="Expressive planning/processing with a readable thought cue or body/face acting; not idle status dots." \
  --expected-state-read answering="Engaged talking/streaming through mouth shapes, eye engagement, and optional supporting voice cues; not tired panting or exhale clouds." \
  --check frameByFrameStateReadReviewed=true \
  --check intendedStateReadable=true \
  --check noWrongStateRead=true \
  --check expressionMatchesState=true \
  --check cueMotionMatchesState=true \
  --check noTiredPantingUnlessStateRequiresIt=true \
  --check noOffVibeGenericCue=true \
  --notes "Frame-by-frame state-performance review passed."

python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile audition \
  --strict \
  --require-state-clarity \
  --require-rendering-style \
  --require-quality-report
```

Use `--profile audition` for one-row or partial-pack tests. Use the full chatbot profile only after the production pack includes the expected chatbot states:

```bash

python scripts/create_art_direction_review.py \
  --manifest /path/to/run/manifest.json \
  --status pass \
  --production-use \
  --generation-method imagegen-integrated-row-art \
  --source-reference /path/to/original-reference.png \
  --check referenceQualityMaintained=true \
  --check identityPreserved=true \
  --check eyeGrammarPreserved=true \
  --check stylePreserved=true \
  --check pixelArtStyle=true \
  --check creativeStateReadability=true \
  --check themeNativeStateCues=true \
  --check nativeEnhancers=true \
  --check integratedEnhancers=true \
  --check anatomyPreserved=true \
  --check noExtraAnatomy=true \
  --check believableOcclusion=true \
  --check noPrototypeFlattening=true \
  --notes "Visual review passed."

python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile chatbot \
  --strict \
  --require-state-clarity \
  --require-rendering-style \
  --require-quality-report \
  --require-state-performance-review \
  --require-art-direction-review \
  --max-outline-halo-pixels 0
```

## Python Dependencies

The scripts use Pillow:

```bash
python -m pip install -r requirements.txt
```

Codex Desktop users can also use the bundled workspace Python runtime if the system Python does not have Pillow installed.

## React Integration

Generated assets are meant to be copied into your app's served assets folder, usually:

```text
public/mascots/<companion-id>/
```

Then use the generated component:

```tsx
import { CompanionMascot } from "./CompanionMascot";
import { toCompanionState } from "./useCompanionState";

export function ChatMascot({ status }: { status: "idle" | "submitted" | "streaming" | "error" }) {
  return (
    <CompanionMascot
      state={toCompanionState(status)}
      size={0.75}
      assetBase="/mascots/my-companion"
    />
  );
}
```

## Repository Contents

```text
SKILL.md
agents/openai.yaml
references/
scripts/
```

Generated mascot assets are intentionally not included in this repository.

## License

MIT
