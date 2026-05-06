---
name: web-companion-mascot
description: Use when creating, validating, or integrating custom animated mascot companions for React/chatbot websites from concept art, screenshots, existing Codex pets, or generated references, especially when states like idle, greeting, listening, thinking, working, answering, success, error, confused, or sleeping are needed.
---

# Web Companion Mascot

## Overview

Create web-first pixel-art animated chatbot mascots with a custom sprite atlas, state manifest, React component, and QA assets. Prefer this skill when the target is a website companion rather than a Codex app pet.

This skill composes `$imagegen` for visual generation and borrows the useful discipline from `$hatch-pet`: grounded references, row prompts, chroma-key cleanup, deterministic validation, and visual QA. It does not use the fixed Codex 8x9 atlas unless the user explicitly asks for Codex compatibility.

## Output Model

Default package:

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
  qa/art-direction-review.json
  qa/previews/*.mp4 or *.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

Default high-quality sprite geometry:

```text
cell: 256x288
columns: max frame count across states, usually 8
rows: one row per website state
atlas width: columns * 256
atlas height: rows * 288
```

Use `192x208` only when the user explicitly prioritizes smaller files or the mascot has very simple detail. Detailed outfits, props, emblems, hand gestures, or high-quality website mascots should use `256x288` or larger.

Use `references/companion-contract.md` for the manifest schema, default states, and QA rules. Use `references/state-enhancers.md` when the user has not chosen a state clarity profile or when `semantic-enhancers` are requested. Use `references/react-integration.md` when wiring the mascot into a React app. Use `scripts/prepare_companion_run.py` to create the first manifest draft, row prompts, and `qa/state-cue-plan.json` before visual generation.

## Codex Pixel Companion Style

Production mascots created by this skill must use the Codex digital-pet pixel-art house style, even when the user reference is a smooth illustration, logo, plush, 3D render, anime drawing, or screenshot. Translate the reference identity into a small sprite: compact chibi proportions, chunky readable silhouette, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, simple expressive face, and tiny readable appendages.

Do not accept polished illustration, painterly rendering, 3D/app-icon gloss, soft airbrush gradients, realistic fur/material texture, vector-flat clip art, high-detail antialiasing, or smooth cartoon rendering as production output. The React component can display the atlas crisply with `image-rendering: pixelated`, but CSS cannot turn smooth generated art into real pixel art. If the row looks like a scaled-down illustration instead of native sprite art, regenerate it with stronger pixel-art language.

The goal is not to make every mascot identical. Preserve the reference's identity, silhouette cues, palette family, face, must-keep markings, and charm, but simplify them into the pixel-sprite language above. Avoid "generic pixel blob" simplification: a good output should clearly be the referenced mascot translated into Codex-style pixel art.

## Art Direction Gate

Technical QA is necessary but not sufficient. A mascot can have a clean atlas, no halo pixels, and stable anchors while still being a bad companion. Production output must preserve the reference's identity, silhouette, charm, pixel-sprite art quality, and creative state reads.

Do not preserve a non-pixel rendering style from the reference. Instead, preserve the mascot's identity while translating it into the Codex pixel companion style. Deterministic compositing, vector overlays, hand-drawn helper props, or programmatic shape props are acceptable for prototypes, diagnostics, or repair sketches only; they cannot be accepted as production final art. Final semantic enhancers must be generated or painted as native pixel-sprite mascot artwork with matching line, pixel density, shading, texture, occlusion, and personality.

Do not accept a semantic enhancer just because it passes geometry QA. A stable but timid state read, such as tiny status dots that do not look like deliberate thinking art, should fail art direction. Regenerate with a more character-native idea that is still anchored and silhouette-safe.

Before state generation, infer a lightweight visual-language read from the reference: what the mascot feels like, which motifs naturally belong to it, and which generic cues would look out of place. The user should not have to supply this. Record it in `style.visualLanguage` when useful, especially for auditions, but do not let metadata become a substitute for good art direction. The real goal is the same as `$hatch-pet`: the row should look like the referenced character naturally performing the state.

Keep an art direction floor in every row prompt. The mascot should look like a polished character performance, not a checklist of constraints: expressive eyes, mouth shapes, head/body tilt, timing, appendage follow-through, and a tiny state cue only when it improves readability. Reject bland, stiff, generic, or symbol-only rows even when the anatomy is technically correct. The skill should constrain failure modes without flattening the model's ability to make charming, character-native pixel-art choices.

Preserve the reference's expression language as part of identity. Do not make an eyebrowless, calm, sleepy, plush, abstract, or icon-like mascot "focused" by inventing angry brows, hostile eye shapes, slanted angry eyes, V-shaped eye/brow marks, teeth, sweat, blush, or dramatic emotion marks. Use the source's own face grammar first: eye direction, blink timing, mouth shape, head/body tilt, pace, and appendage motion. Add stronger facial marks only when the source design already supports them or the state truly needs them and the result still feels character-appropriate.

State cues must survive the deterministic cleanup. Do not rely on isolated tiny specks, far-away dots, or ultra-thin marks as the only semantic enhancer; chroma-key cleanup may remove them, or preserving them may force the body to shrink around the effect. For simple or no-limb mascots, prefer compact body-surface, rim-touching, attached, or close-overlapping cues that remain readable at 64-96 px without being mistaken for new limbs.

For body-surface, rim-touching, or compact attached work cues on no-limb or simple-appendage mascots, keep the cue inside the body core or as one small rim-touching mark. Repeated leaf, oval, wing, paw, mitten, droplet, or appendage-colored tokens along the lower rim or side edges often read as feet, extra limbs, extra wings, new paws, or detached appendages. Prefer one small central glyph/status band or 1-3 high-contrast square, dot, check, or token marks inside the silhouette, with colors and shapes distinct from real anatomy.

Before final validation, create `qa/art-direction-review.json` and fail the run if any required art-direction check is false. This review is a manual/agent visual gate over the contact sheet, readability sheet, cutout sheet, previews, and original reference; it exists because scripts cannot judge taste or creativity by themselves.

## Production Art Boundary

Follow `$hatch-pet`'s generation boundary for production art: `$imagegen` or a user/artist-provided integrated sprite source creates the pixels; this skill's scripts only assemble, clean, validate, preview, and generate React code.

Do not create, draw, tile, warp, or synthesize final mascot frames with local Python/Pillow scripts, SVG, canvas, CSS, vector overlays, procedural shape code, or deterministic compositors. Do not write ad hoc `generate_<mascot>.py` scripts that create row art for a production pack. If `$imagegen` is unavailable and the user has not provided finished row-strip art, stop and explain the blocker instead of fabricating a lower-quality mascot locally.

Use deterministic code only for:

- preparing manifests, prompts, state cards, and QA files
- tracking `$imagegen` jobs, canonical base references, selected-source provenance, and ready/blocked row status
- chroma-key cleanup, frame extraction, atlas assembly, and previews
- validation, reports, packaging, and React integration

Do not manually edit `imagegen-jobs.json` to mark jobs complete, copy images into `generated/`, or fabricate canonical references. Use `scripts/record_companion_imagegen_result.py` to ingest the selected original `$imagegen` output. For production, the recorded source should be the original `$CODEX_HOME/generated_images/.../ig_*.png` file unless the row art is explicitly user/artist-provided integrated art, in which case pass `--source-provenance user-provided-integrated-row-art` or `--source-provenance artist-provided-integrated-row-art`.

This boundary matters most for `semantic-enhancers`: props/effects must be painted into the row as native character art, with real occlusion by existing body parts. A post-process prop can make a state technically readable while making the mascot look cheap; production QA must reject that.

## Motion Quality

Default to a HatchPet-style 8-frame baseline for production rows. Eight well-acted frames usually preserve identity, appendage count, pixel density, and state readability better than long rows that drift or invent anatomy.

```text
audition/compact: 6 frames per tested row
default production: 8 frames per state
smooth opt-in: 10-12 frames only after an 8-frame row proves stable, or when the user explicitly requests extra smoothness
```

Use the default 8-frame profile for first production passes. `thinking`, `working`, and `answering` are the most visible states, so they should get the richest acting, not automatically more frames. Add frames only when the character has already stayed consistent in a shorter row and the longer row still passes visual QA, quality analysis, and strict validation. A polished 8-frame loop is better than a 12-frame row with body growth, inconsistent expression, extra appendages, or weak state acting.

Design rows as true animation, not static variants:

- Include anticipation, action, and settle frames for one-shot-feeling loops such as `success` and `error`.
- Treat every state as a short acting beat. The prompt should separately name the face, eyes, mouth, body, appendages, clothing/identity props, and semantic enhancer motion so the mascot performs the state instead of merely carrying a symbol.
- Include blink or eye-position changes in idle/thinking rows when the frame count allows it.
- Include prop or hand follow-through when the mascot holds an item.
- Stagger face, body, robe/clothing, and prop motion so the row feels alive.
- For near-head semantic effects such as thought bubbles, sound rings, or work orbs, give the effect a readable motion path: origin, travel, hold, and settle. Avoid straight-up static hovering unless the character design specifically calls for it.
- Keep frame durations mostly between 80 and 220 ms. Use occasional 260-420 ms holds for readable blinks, idle breaths, or sleeping only.
- Do not increase apparent smoothness by adding near-duplicate frames. Every frame should change silhouette, face, prop, or body position enough to matter at display size.
- If extra frames make the character drift, mutate, or invent anatomy, prefer fewer better frames over more broken frames.

When testing smoother motion or a new enhancer style, run a small row audition before committing to a full production pack. Generate 1-4 representative rows, assemble them with the real outline cleanup, run the quality analyzer, and validate with `--profile audition` so partial packs can be strict without requiring every chatbot state. Regenerate only rows that trigger core scale drift, full-row core scale range, core center drift, semantic anchor drift, clipping, halos, or invented anatomy. Do not show older failed sheets as current output; keep only the latest accepted contact sheet visible in the final response.

For opt-in 10-12 frame rows, first try a single integrated row when the model reliably follows the count. If it returns too few or too many mascot bodies, switch to split-row generation: generate smaller exact-count chunks whose counts are reliable, then stitch those generated parts with `scripts/stitch_row_parts.py`. This is assembly, not art creation; do not use scripts to draw missing frames. Split rows must still pass contact-sheet QA, and any visible half-to-half seam in scale, outline, palette, vertical anchor, prop size, or expression quality is a blocker.

For high-risk semantic states, do an art-direction audition before extending beyond 8 frames. Generate 2-4 single-frame or 4-frame concepts for the same state, judge them against the source reference and small-size readability, then animate only the strongest concept. This prevents the workflow from optimizing toward technically stable but visually weak symbols.

## State Design

Choose states from the product behavior, not from the Codex pet contract. Recommended chatbot companion states:

```text
idle       default resting loop
greeting   first page load, chat open, welcome
listening  user typing or microphone/listen mode
thinking   prompt submitted, model planning
working    tool call, search, retrieval, file work, backend task
answering  assistant response streaming
success    answer completed or task succeeded
error      failed request or recoverable error
confused   unclear input or validation issue
sleeping   inactivity, minimized chat, offline
```

Map product states explicitly. Example:

```ts
const chatStatusToMascotState = {
  idle: "idle",
  userTyping: "listening",
  submitted: "thinking",
  toolCall: "working",
  streaming: "answering",
  complete: "success",
  error: "error",
};
```

## State Clarity Gate

Before generating state rows, ask the user to choose a state clarity profile unless they already specified one:

```text
pose-only            expression, posture, timing, hands, and existing identity props only
semantic-enhancers   one small anchored prop/effect for ambiguous states
```

Recommend `semantic-enhancers` for chatbot companions because users need to read `thinking`, `working`, `listening`, and `answering` while they wait. Use `pose-only` when the user wants a quieter/minimal mascot.

When `semantic-enhancers` is selected, read `references/state-enhancers.md`. Choose props from the mascot's world instead of hard-coding universal objects. A modern assistant can use a laptop or tablet; a fantasy mascot can use parchment, a quill, a glowing slate, or a small magical thought bubble.

## Appendage Affordance Gate

Do not solve invented-limb failures by banning expressive gestures. First classify what each visible appendage can safely do:

```text
side-bob / tilt / tuck     fins, wings, ears, tails, sleeves, body nubs
small-wave / wave          simple appendages or real hands that can wave
point / present            clear hands, paws, sleeves, tentacles, or arms
face-touch                 real hands/arms or appendages that can touch chin/cheek without becoming a new hand
grip / brace               appendages that can hold or support a chunky prop
typing / writing           visible fingers or clearly fingered hands only
```

Record those as `style.anatomyContract.appendages[].affordances`. Then choose the acting language from the affordances: real hands can use hand-to-chin thinking, presenting, holding, pointing, and typing; paws or mitts can use broad gestures and chunky braced props; fins, wings, sleeves, and ambiguous simple appendages should usually stay side-attached unless the reference and an audition prove a riskier gesture reads correctly; no-limb mascots should use face, body, aura, near-head, or body-surface semantics.

When real hands, paws, sleeves, tentacles, or arms touch the face, present an idea, brace a prop, or operate a work surface, preserve a clear silhouette path back to the original body anchor. Leave enough outline or tiny negative space for the appendage to read as the original appendage, not a new cheek, nose, detached mitten, duplicated hand, extra paw, or face patch. Prefer broad pixel-mitt/paw gestures over tiny fingers unless the reference clearly has fingers.

For risky enhancer or pose metadata, add `enhancer.requiredAffordances` such as `["face-touch"]`, `["grip"]`, or `["typing"]`. The validator compares those actions against the named interactors in `enhancer.anatomyGuard.allowedInteractors` and the appendage affordances in `style.anatomyContract`.

For simple appendage mascots, also guard against fake appendages that appear as body markings. A fin-colored oval, sleeve-colored patch, mitten-shaped highlight, or detached blob on the front of the body can read as an extra limb even when the real side appendages stay attached. State prompts should forbid new limb-colored body patches or front-facing appendage shapes, and near-head effects should use a distinct anchor, silhouette, and placement so they do not resemble the mascot's appendages.

## Generation Workflow

1. Establish mascot identity: name, reference image(s), must-keep features, anatomy class, prop rules, palette, target website vibe, state list, state clarity profile (`pose-only` or `semantic-enhancers`), `style.renderingStyle: "codex-pixel-art"`, and an inferred visual-language read. When anatomy matters, audit the reference before generation: stable body core, exact visible appendages with count and placement, appendage affordances, allowed motion for those exact parts, forbidden additions, and any ambiguous marks that are not limbs. Record this as `style.anatomyClass` (`hands`, `paws`, `fins-no-hands`, `no-limbs`, or `ambiguous-limbs`) and, for simple/ambiguous appendages or risky prop interactions, `style.anatomyContract`. For normal runs, start with the preparer so the state acting plan and `$imagegen` job manifest exist before image generation:

```bash
python scripts/prepare_companion_run.py --companion-name "<Name>" --reference /path/to/reference.png --output-dir /path/to/run --anatomy-class ambiguous-limbs --state-clarity semantic-enhancers --force
```

   Review `qa/state-cue-plan.json`, `prompts/base.md`, and `prompts/rows/<state>.md` before generating. Edit the prompt plan if a high-visibility state needs a stronger or safer read. This step is the web-companion equivalent of `$hatch-pet` preparing row prompts, layout guides, and `imagegen-jobs.json` before image generation. Layout guides are intentionally empty construction inputs for spacing only; do not present them to the user as mascot output or QA result.
2. Inspect ready jobs:

```bash
python scripts/companion_job_status.py --run-dir /path/to/run
```

   The `base` job should be ready first. State row jobs should be blocked until the base job is recorded.
3. Generate or select the canonical Codex-style pixel-art base sprite with `$imagegen` or a user/artist-provided integrated source image. Use the `base` job prompt and its listed input images from `imagegen-jobs.json`. If the user provided non-pixel art, the base generation translates that reference into the required pixel-sprite style while preserving identity.
4. Record the selected base output:

```bash
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png
```

   Recording the base copies it to `generated/base.png`, creates `references/canonical-base.png`, updates `imagegen-jobs.json`, and stores canonical-reference metadata in `manifest.json` and `companion_request.json`.
5. Re-run `companion_job_status.py`. Row jobs become ready after the canonical base exists. Generate one row strip per ready state with `$imagegen`, using the row prompt and every input image listed in `imagegen-jobs.json`: original references, `references/canonical-base.png`, `generated/base.png`, and that state's layout guide. Every row prompt must restate the pixel-art contract: visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, no painterly gradients, no glossy 3D, no smooth vector/cartoon look, no soft antialiasing. Do not generate rows prompt-only unless there is no possible reference image.
6. Record each selected row output:

```bash
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png
```

   The parent agent owns all recording and manifest writes. If multiple workers or subagents generate row candidates, they should return only the selected original source path and a short QA note; they must not edit manifests or copy files into the run.
7. Keep all row strips on the prepared flat chroma-key background. The preparer chooses a key color absent from the copied references when possible; avoid yellow for gold props, avoid magenta for pink/purple characters, and avoid green for green characters.
8. Preserve identity and pixel-art treatment across every row: silhouette, face, palette, props, outfit, outline weight, pixel density, stepped edges, and proportions.
9. If using `semantic-enhancers`, include the chosen profile and inferred visual-language read in row prompts and generate each enhancer as integrated mascot artwork, not as a post-process overlay. Add only one small anchored enhancer per ambiguous state unless the user explicitly requests more. Before each enhanced row, write a small state card: rendering style, semantic read, acting beat, frame-by-frame arc, prop/effect if any, why it fits the mascot, exact anchor, anatomy class, required appendage affordance, exact allowed body parts from `style.anatomyContract`, forbidden artifacts, and any `anatomyGuard` needed for the manifest. For held, touched, face-touch, pointing, presenting, typing, writing, or appendage-operated work props, explicitly require the mascot's named existing hands, paws, fins, sleeves, tentacles, or other visible appendages to have the matching affordance and forbid extra hands, duplicated arms, detached fingers, cloned sleeves, or new anatomy. Do not use vague `allowedInteractors` values like `existing visible appendages only`; name the exact parts, such as `left side fin` and `right side fin`, `left sleeve` and `right sleeve`, or `front paws`. If the source character truly has no usable appendages, do not choose held, touched, typing, writing, or hand-operated prop semantics. For simple/no-hand mascots, a freestanding or resting work prop may sit beside or in front of the mascot when it animates on its own and the mascot works by looking, leaning, bobbing, and reacting, not by holding, typing, writing, or inventing hands. Keep a clear background gap between the mascot and freestanding prop, and keep the prop's activity marks inside/on the prop surface so pips, sparkles, crystals, or motion marks do not bridge the empty gap and merge the prop with the body during cleanup. For no-hand mascots, default to a slate, tablet, blank card stack, token tray, chunky work tile, or solid work surface rather than notebook/paper/page surfaces that invite ruled lines or pseudo-writing. Any slate, tablet, blank card stack, token tray, panel, or work surface must use chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens, not readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, list rows, fine stripes, wood-grain lines, plank lines, parallel grooves, or a tiny document full of writing. If anatomy supports typing or writing, show that action through hand/body motion while the surface marks remain non-text. Use acting first: busy-friendly face, eye tracking, body lean, blink timing, faster attentive motion, and a small attached, near-head, body-surface, rim-touching, or freestanding/resting cue only when it makes the state clearer. If the first motif-native cue is pretty but does not read as the state, reject it.
10. For near-head effects, held props, and any higher-frame-count waiting state, add explicit silhouette-lock language to the row prompt: same body footprint, same body center, same top-of-head height, same bottom edge, same named appendage count, and enhancer motion around that stable base. The motion should come from expression, blink, small pose beats, prop follow-through, or enhancer changes, not from resizing the mascot.
11. Generate at least two visual approaches or row candidates for high-visibility states when the first pass looks bland, overly literal, drifty, non-pixel, or less polished than the source. Prefer regenerating the row over post-processing a weak one into compliance. If a candidate has pasted-on semantics, mismatched art style, smooth illustration rendering, invented anatomy, core scale drift, or core center drift, discard the candidate; do not repair it by compositing.
12. Seed `manifest.json` with the state rows, frame counts, durations, `id`, `displayName`, `style.renderingStyle: "codex-pixel-art"`, `style.stateClarity`, `style.anatomyClass`, `style.anatomyContract.appendages[].affordances` when used, and per-state `enhancer` metadata including `requiredAffordances` for appendage-dependent actions. The preparer defaults to 8 frames per state and may write draft enhancer metadata such as `planned during row generation`; after selecting the final row art, replace those placeholders with the actual accepted visual aid before production validation.
13. If an opt-in 10-12 frame row repeatedly misses the requested frame count, generate shorter row parts with exact count prompts and stitch the accepted generated parts before atlas assembly:

```bash
python scripts/stitch_row_parts.py --parts /path/to/state-part-a.png /path/to/state-part-b.png --out /path/to/run/row-strips/state.png --json-out /path/to/run/qa/state-stitch-report.json
```

   Visually inspect the stitched source or contact sheet for a seam between parts. Regenerate the weaker part if the mascot scale, line weight, prop size, anchor, palette, or expression quality changes across the stitch boundary.
14. Assemble the atlas with the bundled assembler. This script handles variable row-strip spacing, chroma-key gradients, wide gestures, transparent unused cells, extracted frames, contact sheets, GIF previews, and an assembly report. Its outline improver must remain enabled: key-to-alpha removal, edge-spill cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing all protect the sprite edge from chroma halos.
   For row strips with detached bubbles, voice marks, or aura components, prefer `--extraction-mode component`. If a large semantic effect is mistaken for an extra body component, raise `--body-component-area` rather than accepting equal slicing; the effect should be assigned to the nearest real body, not treated as a mascot.

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --max-outline-halo-pixels 0 --no-equal-fallback
```

15. Create the small-size readability QA sheet for semantic states:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
```

16. Run the quality analyzer before acceptance. It writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`; strict production runs should have no analyzer warnings. This catches near-duplicate frames, static rows, body jumps, foreground area jumps that often signal extra limbs or missing props, detached fragments from broken cuts, core silhouette scale drift, full-row core scale range, core center drift, and drifting semantic enhancers. For polished production mascots, full-row mascot core scale range should stay at or below `5%`; values above that usually look like the body grows or shrinks even when the row technically assembles:

```bash
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
```

17. Visually inspect the contact sheet, cutout check, readability sheet, semantic anchor sheet, motion quality sheet, previews, and the original reference before accepting the mascot. If the contact sheet shows neighboring-frame slivers, chopped hands/props, stray specks, off-center sprites, simplified anatomy, inconsistent mascot scale, lower polish than the reference, smooth/non-pixel rendering, or less creative state reads than the brief implies, regenerate the row. If `qa/cutout-check.png` shows pink/magenta halos on dark, white, blue, or green backgrounds, rebuild with stronger chroma cleanup or regenerate the row with a flatter key background. For `semantic-enhancers`, reject rows where the enhancer is unclear at 64, 96, and 128 px, cropped, detached, leaking into other states, visually pasted on, drifting away from its anchor, causing extra anatomy, mismatching pixel density, or changing quality across a split-row stitch.
18. Write the art-direction review only after the visual inspection passes. Use `status: "pass"` and `productionUse: true` only when the pack preserves the source quality and does not rely on deterministic/vector/post-process overlays for final art:

```bash
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check stylePreserved=true --check pixelArtStyle=true --check creativeStateReadability=true --check themeNativeStateCues=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --notes "Preserves the reference identity as Codex-style pixel art, states read clearly through mascot-native cues, enhancers are native/integrated, and no new anatomy appears."
```

19. Run manifest validation with the chatbot profile before finishing. Strict validation must fail on assembly warnings, missing readability QA, missing quality report, missing art-direction review, malformed state clarity metadata, cropped sprites, non-transparent unused cells, quality warnings, or any remaining key-colored outline halo pixels:

```bash
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-art-direction-review --max-outline-halo-pixels 0
```

20. Generate the React component only after visual QA and strict validation pass.

When the mascot has side-specific props, text, emblems, handed items, or asymmetric lighting, generate left/right directional states separately instead of mirroring.

## Visual Rules

Prefer sprite-readable animation over decorative effects.

- Production rows must look like native pixel-art sprites: visible pixel steps, crisp clusters, limited palette, flat cel shading, thick readable outline, and consistent pixel density across the mascot and enhancer.
- Reject smooth illustration, glossy app-icon rendering, painterly gradients, 3D material shading, high-detail antialiasing, vector-flat symbols, or CSS-scaled smooth art. Regenerate from the reference as Codex-style pixel art instead of trying to fix it after assembly.
- Keep poses fully inside each frame with safe padding.
- Use every listed frame as a meaningful pose or in-between.
- Keep props attached to, held by, or clearly anchored near the mascot.
- Avoid shadows, glows, blur, motion streaks, dust, loose sparkles, detached punctuation, UI panels, scenery, and text unless the user explicitly requests a website-only effect and the atlas extraction can preserve it.
- For `pose-only`, show `thinking`, `working`, and `answering` through head tilt, eye movement, hand/prop pose, blink, mouth shapes, and body motion.
- For `semantic-enhancers`, add one small anchored enhancer for ambiguous states, such as a thought bubble near the head, an anatomy-supported held paper/tablet/tool, a freestanding/resting work surface, listening rings, or a small success/error charm. The enhancer must match the mascot's theme.
- Use a semantic ladder, not a symbol-first shortcut: first make the face, eyes, mouth, posture, timing, and original appendages perform the state; next use existing identity props or appendages if they can do the action; only then add a small attached or anchored effect. A motif-native effect that does not read as the state is still a failure.
- Semantic cues must come from the mascot's visual language and still communicate the state. A tech bot may use tablets or UI glyphs; an icy pet might use cold breath or snow puffs for speaking, but a decorative frost shimmer alone may not read as `working`. Reject generic gears, circuit diagrams, speech panels, universal icons, and also pretty motif marks that do not convey the intended behavior.
- For `thinking`, prefer a side-origin thought cue over a generic icon directly above the head: the effect should begin near one side of the head/hood/face, grow from small bubble to medium bubble to the largest compact bubble/orb, hold while the eyes track it, then settle back into a loop. The largest thought cue must stay secondary to the mascot, never larger than about one-third of the mascot body width, and must not become a second head/body-sized orb. The row should show a real frame-by-frame thinking arc, not the same bubble pasted into every frame.
- Do not freeze expressive appendages just to avoid anatomy mistakes. Existing fins, paws, sleeves, mitts, tentacles, wings, hands, or other visible appendages may move, brace props, gesture, touch the face, or settle when that action matches the source character and the appendage's recorded affordances. The prompt must name the exact existing appendages, include any `requiredAffordances`, and forbid extra copies, new fingers, detached mitts, duplicated sleeves, or changed appendage count.
- If a simple appendage gesture makes a fin, sleeve, paw, tentacle, or mitt-like limb read as a new hand, fingered mitten, or third limb, regenerate with safer acting: keep appendages side-attached, let them tilt or tuck only slightly, and carry the state through eyes, mouth, body tilt, blink timing, and the anchored enhancer instead.
- If a simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that could be read as a new appendage, reject the row even when the appendage count looks correct at the sides. Regenerate with plain body-surface shading and keep semantic effects clearly near-head, worn, aura-like, or otherwise distinct from the appendages.
- Production enhancers must match the mascot's exact pixel-sprite rendering style: same line weight, pixel grid, palette, lighting direction, flat shading, edge treatment, pixel density, and occlusion with hands/clothing. Do not ship hand-drawn/vector overlays on top of generated mascot frames unless the user explicitly asked for a prototype.
- Do not let a prop make the state read correctly while the mascot itself becomes less expressive, less polished, or less like the source reference.
- For `working`, the row must read as active work, not anger and not decoration. Prefer busy-but-friendly face, eye tracking, small lean-in, faster purposeful motion, and an existing prop/appendage action when anatomy allows it. Do not invent angry brows, hostile eye shapes, slanted angry eyes, or V-shaped eye/brow marks as shorthand for focus. Use held laptop/tablet/parchment/quill/tool actions only when the source has existing appendages or identity props with plausible `grip`, `brace`, `typing`, `writing`, `point`, or `present` affordances. Fins, sleeves, paws, and tentacles can count only when the reference already shows them and the contract allows that action; prompts must name those exact interactors and forbid extra anatomy. For true no-limb or simple-fin mascots, use face/body acting plus a compact attached, rim-touching, body-surface, freestanding, or resting work cue with a purposeful cycling, sorting, checking, or gathering motion. Good no-hand work props include a small slate, tablet, blank card stack, token tray, chunky work tile, or solid work surface placed beside or in front of the mascot; they animate on their own while the mascot looks, leans, bobs, and reacts. Avoid notebook/paper/page surfaces by default for no-hand mascots because they tend to become ruled pages or pseudo-writing. For any work prop surface, use only chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens that read at 64-96 px; reject readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, list rows, fine stripes, wood-grain lines, plank lines, parallel grooves, or tiny-document surfaces. For body-surface/rim cues, reject lower-rim or side-edge clusters that look like feet, extra limbs, extra wings, new paws, or detached appendages; prefer one central glyph/status band or 1-3 high-contrast simple marks inside the body silhouette. If anatomy supports typing or writing, show the action through hands, posture, and timing while surface marks remain non-text. For freestanding props, keep a clear background gap from the body and keep all pips, sparkles, crystals, motion marks, and sorting/checking/gathering marks inside or on the prop surface, not in the empty gap. Reject rows where the cue is merely decorative, disappears after assembly cleanup, shrinks the body, touches or merges with the body, implies holding/typing/writing, invents hands, uses text-like prop marks, or where the expression becomes hostile.
- For `answering`, prefer mouth shapes, presenting gestures, or a small no-text speech cue. Tiny near-face voice pixels may be attached to the mouth/cheek silhouette; they do not need to be detached bubbles when the mouth animation already carries the state.
- For `success`, use body pose, bounce, wave, raised prop, or a small anchored check/glint. Detached confetti/sparkles should be avoided unless the user wants website-only effects and the atlas extraction can preserve them.
- For `error`, use expression, slump, prop droop, attached tear, warning charm, or attached smoke/stars only when they remain inside the cell and attached to the mascot.

## React Integration

When implementing the mascot in a React app:

1. Put final assets under the app's served assets path, typically `public/mascots/<id>/`.
2. Import or fetch `manifest.json`.
3. Animate with frame durations from the manifest rather than assuming equal CSS `steps()` timing.
4. Respect `prefers-reduced-motion`: show the first frame or a slow idle frame when the user prefers reduced motion.
5. Keep the component controlled by app state: `state`, `size`, `paused`, and optional `onClick`.
6. Use CSS `image-rendering: pixelated`; production assets from this skill are pixel-art sprites, not smooth illustrations.

Read `references/react-integration.md` for a reusable component pattern.

## Scripts

Use bundled scripts when useful:

```bash
python scripts/prepare_companion_run.py --companion-name "<Name>" --reference /path/to/reference.png --output-dir /path/to/run --anatomy-class ambiguous-limbs --state-clarity semantic-enhancers --force
python scripts/companion_job_status.py --run-dir /path/to/run
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --no-equal-fallback
python scripts/stitch_row_parts.py --parts /path/to/part-a.png /path/to/part-b.png --out /path/to/run/row-strips/state.png
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check stylePreserved=true --check pixelArtStyle=true --check creativeStateReadability=true --check themeNativeStateCues=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --notes "Visual review passed."
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile audition --strict --require-state-clarity --require-rendering-style --require-quality-report
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-art-direction-review
python scripts/generate_react_component.py --manifest /path/to/manifest.json --out-dir /path/to/react
```

If the system `python` cannot import Pillow/PIL, use the Codex bundled workspace runtime instead: call `load_workspace_dependencies`, then run the same scripts with the returned Python executable.

`prepare_companion_run.py` creates the run folder, `companion_request.json`, `imagegen-jobs.json`, `manifest.json`, copied references, `references/layout-guides/<state>.png`, `prompts/base.md`, `prompts/<state>.md`, `prompts/rows/<state>.md`, and `qa/state-cue-plan.json`. It does not infer pixels or draw anything; it gives `$imagegen` concise, hatch-pet-style row prompts that say what the state should read as, how the mascot should act first, when a visual aid is allowed, and what to reject.

`companion_job_status.py` reads `imagegen-jobs.json` and shows ready and blocked `$imagegen` jobs. The base job is ready first; row jobs are blocked until the base is recorded.

`record_companion_imagegen_result.py` records the selected original `$imagegen` source for a job, verifies dependencies and required grounding images, copies the source to the expected run output path, stores hashes/metadata/provenance, and creates `references/canonical-base.png` when recording the base job. Use it instead of manually copying files or editing `imagegen-jobs.json`. For finished user/artist row art, pass `--source-provenance user-provided-integrated-row-art` or `--source-provenance artist-provided-integrated-row-art`.

`assemble_companion_atlas.py` reads row strips named `<state>.png`, updates the manifest atlas fields, extracts clean per-frame PNGs, writes `atlas.webp` and `atlas.png`, creates `qa/contact-sheet.png`, creates `qa/cutout-check.png`, creates `qa/previews/*.gif`, and writes `qa/assembly-report.json`. It uses foreground-run center detection rather than naive equal-width slicing, which prevents common generated-strip issues such as variable frame spacing, clipped wide gestures, and neighboring-frame slivers. It fits all frames in the same state row with one shared scale so a growing thought bubble, sound ring, work prop, or other semantic enhancer cannot make only that frame's mascot body shrink. It also runs the outline improver: transparent RGB clearing, key spill removal, key-colored edge cleanup, spill-color replacement, and premultiplied resizing so invisible chroma-key pixels do not bleed into sprite edges. The assembly report records `outlineImprover.totalOutlineHaloPixels`; production runs should keep this at `0`. If it reports `equal-fallback` or outline warnings, review that state manually and prefer regenerating the row if the contact sheet looks uneven.

Use `--extraction-mode component` when row sources contain detached but integrated state effects, such as thought orbs, sound rings, or speech wisps. It groups each mascot body with nearby components instead of slicing through neighboring poses. Use `--extraction-mode equal` only when the row sources were intentionally generated as exact equal-spaced horizontal strips and foreground-center extraction visibly splits or merges close frames. These are explicit production choices, not silent fallbacks: accept them only when the contact sheet shows no chopped frames, neighboring slivers, or lost props.

`create_state_readability_sheet.py` writes `qa/state-readability-check.png`, showing enhanced states at 64, 96, and 128 px. Use it before validation for `semantic-enhancers` packs.

`analyze_companion_quality.py` writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`. It flags near-duplicate frames, low average motion, body jitter, large foreground area jumps, detached fragments, core silhouette scale drift, full-row core scale range over the production default of `5%`, core center drift, missing separate enhancers, and drifting semantic anchors. This is not a substitute for visual judgment, but it catches the common symptoms of wrong cuts, cropped/slivered frames, unstable body size, unstable props, pasted-on effects, and fake smoothness.

`create_art_direction_review.py` writes `qa/art-direction-review.json`. Use it as a production review record after visual inspection. It should fail, not pass, when a result is technically clean but looks worse, less creative, over-simplified, or prototype-like compared with the source.

`validate_companion_manifest.py` verifies manifest shape, state frame counts, durations, atlas path, dimensions, alpha channel, empty used cells, non-transparent unused cells, edge-touching/cropped sprites, residual key-colored outline halos, assembly-report warnings, missing readability QA, quality-report warnings, risky enhancer metadata, anatomy-guard specificity, anatomy-contract shape, appendage affordance mismatches, art-direction review blockers, and optional state clarity, rendering-style, and visual-language metadata. The `audition` profile is for strict one-row or partial-pack tests and does not warn about missing `idle` or other chatbot states. The `chatbot` profile warns when core website states are missing or when important states have too few frames for smooth motion. Use `--strict --require-state-clarity --require-rendering-style --require-quality-report --require-art-direction-review --max-outline-halo-pixels 0` for newly generated production packs so warnings, missing clarity metadata, missing rendering-style metadata, missing QA, quality issues, anatomy-guard issues, anatomy-contract warnings, affordance warnings, art-direction issues, and outline halo pixels block acceptance. Use `--require-visual-language` only for targeted auditions where you specifically want to fail missing vibe-fit metadata.

`generate_react_component.py` emits a TypeScript React component that reads the manifest and animates by per-frame durations.

## Acceptance Criteria

- `manifest.json` lists every state, row, frame count, frame size, durations, and atlas path.
- `imagegen-jobs.json` exists, records `base` plus one row job per generated state, and shows selected-source provenance for completed jobs.
- `references/canonical-base.png` exists after the base job is recorded, and row jobs used it as grounding.
- `prompts/<state>.md` and `qa/state-cue-plan.json` exist or the final answer explains why a prepared prompt plan was not used.
- Any draft `enhancer.kind` from prompt planning has been replaced with the actual accepted visual aid before production acceptance.
- `atlas.webp` or `atlas.png` exists, has transparency, and matches manifest dimensions.
- Every used frame is non-empty and unclipped.
- Unused cells are transparent.
- `qa/assembly-report.json` exists and any extraction warnings are reviewed.
- `qa/assembly-report.json` records `outlineImprover.enabled: true` and `outlineImprover.totalOutlineHaloPixels: 0` for production packs.
- `qa/cutout-check.png` shows no visible chroma-key halo on dark, light, and saturated backgrounds.
- `qa/state-readability-check.png` exists for `semantic-enhancers` packs and shows enhanced states at 64, 96, and 128 px.
- `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png` exist and show no unresolved quality warnings for production packs.
- `qa/art-direction-review.json` exists, has `status: "pass"`, has `productionUse: true`, records the original `sourceReference`, and records that reference quality, identity, style, pixel-art style, creative state readability, native enhancers, integrated enhancers, anatomy preservation, no extra anatomy, believable occlusion, and no prototype flattening all passed.
- The final art is not accepted if its production method is deterministic compositing, vector overlays, manual shape overlays, or another prototype-only path.
- Chatbot profile validation passes in strict mode, or every warning is explicitly reviewed and accepted.
- `manifest.json` records `style.stateClarity` as `pose-only` or `semantic-enhancers` for newly generated packs.
- `manifest.json` records `style.renderingStyle` as `codex-pixel-art` for newly generated packs.
- The prompt plan or manifest records the inferred mascot vibe and why each enhanced state cue belongs to that mascot. This can use `style.visualLanguage` and `enhancer.visualLanguageFit`, but visual quality matters more than metadata.
- State rows translate the reference into Codex-style pixel art; reject smooth illustration, glossy rendering, painterly gradients, 3D shading, high-detail antialiasing, or vector-flat art.
- If `semantic-enhancers` is selected, `thinking`, `working`, `listening`, and `answering` include per-state `enhancer` metadata and read clearly at 64, 96, and 128 px.
- Semantic enhancers look native to the mascot artwork, not pasted on. Reject any row where prop/effect outline, shading, scale, perspective, edge treatment, or pixel density does not match the base mascot.
- Semantic enhancers fit the source vibe and motif vocabulary while still reading as the intended state. Reject rows that are readable only because of generic UI symbols, and reject rows that are on-vibe but fail the state, such as decorative frost that does not read as work.
- Enhanced states do not create extra limbs, duplicate hands, new fingers/paws/fins, or body parts that were not in the original character design.
- Held, touched, writing, near-hand, or appendage-operated work-prop enhancers include `enhancer.anatomyGuard` metadata with a no-new-limbs policy, exact allowed interactors, and forbidden anatomy artifacts. For `style.anatomyClass: "no-limbs"`, do not use grip/typing/writing props at all; strict validation rejects them even when an anatomy guard is present. Freestanding/resting work props are allowed for no-hand mascots only when they sit beside or in front of the mascot, animate without appendage interaction, keep a visible gap from the body, keep activity marks on the prop itself, and are explicitly not held, typed on, written on, or hand-operated. For `fins-no-hands` or `ambiguous-limbs`, held props are allowed only when `style.anatomyContract`, the prompt, and the manifest name the exact existing appendages that interact with the prop.
- `enhancer.anatomyGuard.allowedInteractors` does not use vague entries such as `existing visible appendages only`; it names concrete reference parts like `left side fin`, `right side fin`, `front paws`, `left sleeve`, or `right tentacle`.
- When `style.anatomyClass` is `fins-no-hands` or `ambiguous-limbs` and risky enhancer interactions are used, `manifest.json` records `style.anatomyContract` with a stable body core, counted appendages, placements, and forbidden additions.
- Per-state body scale stays consistent: no unresolved core silhouette scale drift, full-row core scale range, core center drift, detached fragments, or broken-cut warnings in `qa/quality-report.json`.
- Production final art uses `imagegen-integrated-row-art`, `user-provided-integrated-row-art`, or `artist-provided-integrated-row-art`; deterministic local drawing/compositing is a prototype-only failure path.
- If `pose-only` is selected, no new semantic props appear unless the user explicitly requested them.
- Each default production state has 8 frames unless the user explicitly requested a compact audition or a smoother opt-in row count.
- Longer 10-12 frame rows are accepted only when they preserve identity, body scale, appendage count, state readability, and pixel-art quality better than or equal to the 8-frame baseline.
- Every requested chatbot state is visually distinct enough to read at website size.
- Contact sheet and at least one preview format are produced.
- React component can display `idle`, `thinking`, `working`, `answering`, `success`, and `error`.
- The final answer reports asset paths, manifest path, React component path, and QA result.
