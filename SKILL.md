---
name: web-companion-mascot
description: Use when creating, validating, or integrating custom animated mascot companions for React/chatbot websites from concept art, screenshots, existing Codex pets, or generated references, especially when states like idle, greeting, listening, thinking, working, answering, success, error, confused, or sleeping are needed.
---

# Web Companion Mascot

## Overview

Create web-first animated chatbot mascots with a custom sprite atlas, state manifest, React component, and QA assets. Prefer this skill when the target is a website companion rather than a Codex app pet.

This skill composes `$imagegen` for visual generation and borrows the useful discipline from `$hatch-pet`: grounded references, row prompts, chroma-key cleanup, deterministic validation, and visual QA. It does not use the fixed Codex 8x9 atlas unless the user explicitly asks for Codex compatibility.

## Output Model

Default package:

```text
run/
  manifest.json
  atlas.webp
  atlas.png
  frames/<state>/*.png
  qa/assembly-report.json
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
columns: max frame count across states, usually 12
rows: one row per website state
atlas width: columns * 256
atlas height: rows * 288
```

Use `192x208` only when the user explicitly prioritizes smaller files or the mascot has very simple detail. Detailed outfits, props, emblems, hand gestures, or high-quality website mascots should use `256x288` or larger.

Use `references/companion-contract.md` for the manifest schema, default states, and QA rules. Use `references/state-enhancers.md` when the user has not chosen a state clarity profile or when `semantic-enhancers` are requested. Use `references/react-integration.md` when wiring the mascot into a React app.

## Art Direction Gate

Technical QA is necessary but not sufficient. A mascot can have a clean atlas, no halo pixels, and stable anchors while still being a bad companion. Production output must preserve the reference's art quality, silhouette, charm, rendering style, and creative state reads.

Do not down-convert a detailed reference into a simpler pixel blob unless the user explicitly asks for pixel-art simplification. Deterministic compositing, vector overlays, hand-drawn helper props, or programmatic shape props are acceptable for prototypes, diagnostics, or repair sketches only; they cannot be accepted as production final art. Final semantic enhancers must be generated or painted as native mascot artwork with matching line, shading, texture, occlusion, and personality.

Do not accept a semantic enhancer just because it passes geometry QA. A stable but timid state read, such as tiny status dots that do not look like deliberate thinking art, should fail art direction. Regenerate with a more character-native idea that is still anchored and silhouette-safe.

Before final validation, create `qa/art-direction-review.json` and fail the run if any required art-direction check is false. This review is a manual/agent visual gate over the contact sheet, readability sheet, cutout sheet, previews, and original reference; it exists because scripts cannot judge taste or creativity by themselves.

## Production Art Boundary

Follow `$hatch-pet`'s generation boundary for production art: `$imagegen` or a user/artist-provided integrated sprite source creates the pixels; this skill's scripts only assemble, clean, validate, preview, and generate React code.

Do not create, draw, tile, warp, or synthesize final mascot frames with local Python/Pillow scripts, SVG, canvas, CSS, vector overlays, procedural shape code, or deterministic compositors. Do not write ad hoc `generate_<mascot>.py` scripts that create row art for a production pack. If `$imagegen` is unavailable and the user has not provided finished row-strip art, stop and explain the blocker instead of fabricating a lower-quality mascot locally.

Use deterministic code only for:

- preparing manifests, prompts, state cards, and QA files
- chroma-key cleanup, frame extraction, atlas assembly, and previews
- validation, reports, packaging, and React integration

This boundary matters most for `semantic-enhancers`: props/effects must be painted into the row as native character art, with real occlusion by existing body parts. A post-process prop can make a state technically readable while making the mascot look cheap; production QA must reject that.

## Motion Quality

Default to a high-motion website companion profile rather than the smaller Codex pet frame counts:

```text
standard: idle/listening/greeting/success/error/confused/sleeping 10+ frames; thinking/working/answering 12+ frames
cinematic: idle/listening/greeting/success/error/confused/sleeping 12+ frames; thinking/working/answering 14+ frames
```

Use the standard profile by default for production chatbot mascots. Use the cinematic profile when the user explicitly asks for extra smoothness or the mascot is simple enough to stay consistent across more frames. Use fewer frames only when the user explicitly prioritizes file size or when a target app has a hard frame limit. For chatbot companions, `thinking`, `working`, and `answering` are the most visible states and should get the richest motion.

Design rows as true animation, not static variants:

- Include anticipation, action, and settle frames for one-shot-feeling loops such as `success` and `error`.
- Treat every state as a short acting beat. The prompt should separately name the face, eyes, mouth, body, appendages, clothing/identity props, and semantic enhancer motion so the mascot performs the state instead of merely carrying a symbol.
- Include at least two blink or eye-position changes in long idle/thinking rows.
- Include prop or hand follow-through when the mascot holds an item.
- Stagger face, body, robe/clothing, and prop motion so the row feels alive.
- For near-head semantic effects such as thought bubbles, sound rings, or work orbs, give the effect a readable motion path: origin, travel, hold, and settle. Avoid straight-up static hovering unless the character design specifically calls for it.
- Keep frame durations mostly between 80 and 220 ms. Use occasional 260-420 ms holds for readable blinks, idle breaths, or sleeping only.
- Do not increase apparent smoothness by adding near-duplicate frames. Every frame should change silhouette, face, prop, or body position enough to matter at display size.
- If extra frames make the character drift, mutate, or invent anatomy, prefer fewer better frames over more broken frames.

When testing smoother motion or a new enhancer style, run a small row audition before committing to a full production pack. Generate 1-4 representative rows, assemble them with the real outline cleanup, run the quality analyzer, and validate with `--profile audition` so partial packs can be strict without requiring every chatbot state. Regenerate only rows that trigger core scale drift, full-row core scale range, core center drift, semantic anchor drift, clipping, halos, or invented anatomy. Do not show older failed sheets as current output; keep only the latest accepted contact sheet visible in the final response.

For 12+ frame rows, first try a single integrated row when the model reliably follows the count. If it returns too few or too many mascot bodies, switch to split-row generation: generate two 6-frame parts, or small chunks whose counts are reliable, then stitch the generated parts with `scripts/stitch_row_parts.py`. This is assembly, not art creation; do not use scripts to draw missing frames. Split rows must still pass contact-sheet QA, and any visible half-to-half seam in scale, outline, palette, vertical anchor, prop size, or expression quality is a blocker.

For high-risk semantic states, do an art-direction audition before a 12-frame row. Generate 2-4 single-frame or 4-frame concepts for the same state, judge them against the source reference and small-size readability, then animate only the strongest concept. This prevents the workflow from optimizing toward technically stable but visually weak symbols.

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

For risky enhancer or pose metadata, add `enhancer.requiredAffordances` such as `["face-touch"]`, `["grip"]`, or `["typing"]`. The validator compares those actions against the named interactors in `enhancer.anatomyGuard.allowedInteractors` and the appendage affordances in `style.anatomyContract`.

## Generation Workflow

1. Establish mascot identity: name, reference image(s), must-keep features, anatomy class, prop rules, palette, target website vibe, state list, and state clarity profile (`pose-only` or `semantic-enhancers`). When anatomy matters, audit the reference before generation: stable body core, exact visible appendages with count and placement, appendage affordances, allowed motion for those exact parts, forbidden additions, and any ambiguous marks that are not limbs. Record this as `style.anatomyClass` (`hands`, `paws`, `fins-no-hands`, `no-limbs`, or `ambiguous-limbs`) and, for simple/ambiguous appendages or risky prop interactions, `style.anatomyContract`.
2. Generate or select one canonical base sprite with `$imagegen` or a user/artist-provided integrated source image.
3. Generate one row strip per state with `$imagegen`, using the canonical base and any original references as grounding images. Attach the state card and reference images to every row-generation job. Do not generate rows prompt-only unless there is no possible reference image.
4. Keep all row strips on a clean flat chroma-key background. Pick a key color absent from the character; avoid yellow for gold props, avoid magenta for pink/purple characters, and avoid green for green characters.
5. Preserve identity across every row: silhouette, face, palette, props, outfit, outline weight, and proportions.
6. If using `semantic-enhancers`, include the chosen profile in row prompts and generate each enhancer as integrated mascot artwork, not as a post-process overlay. Add only one small anchored enhancer per ambiguous state unless the user explicitly requests more. Before each enhanced row, write a small state card: semantic read, prop/effect, exact anchor, anatomy class, required appendage affordance, exact allowed body parts from `style.anatomyContract`, forbidden artifacts, and any `anatomyGuard` needed for the manifest. For held, touched, face-touch, pointing, presenting, typing, writing, or work-prop enhancers, explicitly require the mascot's named existing hands, paws, fins, sleeves, tentacles, or other visible appendages to have the matching affordance and forbid extra hands, duplicated arms, detached fingers, cloned sleeves, or new anatomy. Do not use vague `allowedInteractors` values like `existing visible appendages only`; name the exact parts, such as `left side fin` and `right side fin`, `left sleeve` and `right sleeve`, or `front paws`. If the source character truly has no usable appendages, do not choose held, touched, typing, writing, keyboard, slate, tablet, paper, or pencil semantics. Use a non-grip semantic instead: body-surface glyphs, pulsing processing cores, aura/status bands, near-head thought/activity effects, facial animation, body-pose, worn charms, or theme-native effects that require no limb interaction.
7. For near-head effects, held props, and any higher-frame-count waiting state, add explicit silhouette-lock language to the row prompt: same body footprint, same body center, same top-of-head height, same bottom edge, same named appendage count, and enhancer motion around that stable base. The motion should come from expression, blink, small pose beats, prop follow-through, or enhancer changes, not from resizing the mascot.
8. Generate at least two visual approaches or row candidates for high-visibility states when the first pass looks bland, overly literal, drifty, or less polished than the source. Prefer regenerating the row over post-processing a weak one into compliance. If a candidate has pasted-on semantics, mismatched art style, invented anatomy, core scale drift, or core center drift, discard the candidate; do not repair it by compositing.
9. Seed `manifest.json` with the state rows, frame counts, durations, `id`, `displayName`, `style.stateClarity`, `style.anatomyClass`, `style.anatomyContract.appendages[].affordances` when used, and per-state `enhancer` metadata including `requiredAffordances` for appendage-dependent actions.
10. If a 12+ frame row repeatedly misses the requested frame count, generate shorter row parts with exact count prompts and stitch the accepted generated parts before atlas assembly:

```bash
python scripts/stitch_row_parts.py --parts /path/to/state-part-a.png /path/to/state-part-b.png --out /path/to/run/row-strips/state.png --json-out /path/to/run/qa/state-stitch-report.json
```

   Visually inspect the stitched source or contact sheet for a seam between parts. Regenerate the weaker part if the mascot scale, line weight, prop size, anchor, palette, or expression quality changes across the stitch boundary.
11. Assemble the atlas with the bundled assembler. This script handles variable row-strip spacing, chroma-key gradients, wide gestures, transparent unused cells, extracted frames, contact sheets, GIF previews, and an assembly report. Its outline improver must remain enabled: key-to-alpha removal, edge-spill cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing all protect the sprite edge from chroma halos.
   For row strips with detached bubbles, voice marks, or aura components, prefer `--extraction-mode component`. If a large semantic effect is mistaken for an extra body component, raise `--body-component-area` rather than accepting equal slicing; the effect should be assigned to the nearest real body, not treated as a mascot.

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --columns 12 --cell-width 256 --cell-height 288 --max-outline-halo-pixels 0 --no-equal-fallback
```

12. Create the small-size readability QA sheet for semantic states:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
```

13. Run the quality analyzer before acceptance. It writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`; strict production runs should have no analyzer warnings. This catches near-duplicate frames, static rows, body jumps, foreground area jumps that often signal extra limbs or missing props, detached fragments from broken cuts, core silhouette scale drift, full-row core scale range, core center drift, and drifting semantic enhancers. For polished production mascots, full-row mascot core scale range should stay at or below `5%`; values above that usually look like the body grows or shrinks even when the row technically assembles:

```bash
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
```

14. Visually inspect the contact sheet, cutout check, readability sheet, semantic anchor sheet, motion quality sheet, previews, and the original reference before accepting the mascot. If the contact sheet shows neighboring-frame slivers, chopped hands/props, stray specks, off-center sprites, simplified anatomy, inconsistent mascot scale, lower polish than the reference, or less creative state reads than the brief implies, regenerate the row. If `qa/cutout-check.png` shows pink/magenta halos on dark, white, blue, or green backgrounds, rebuild with stronger chroma cleanup or regenerate the row with a flatter key background. For `semantic-enhancers`, reject rows where the enhancer is unclear at 64, 96, and 128 px, cropped, detached, leaking into other states, visually pasted on, drifting away from its anchor, causing extra anatomy, or changing quality across a split-row stitch.
15. Write the art-direction review only after the visual inspection passes. Use `status: "pass"` and `productionUse: true` only when the pack preserves the source quality and does not rely on deterministic/vector/post-process overlays for final art:

```bash
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check stylePreserved=true --check creativeStateReadability=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --notes "Preserves the reference style, states read clearly, enhancers are native/integrated, and no new anatomy appears."
```

16. Run manifest validation with the chatbot profile before finishing. Strict validation must fail on assembly warnings, missing readability QA, missing quality report, missing art-direction review, malformed state clarity metadata, cropped sprites, non-transparent unused cells, quality warnings, or any remaining key-colored outline halo pixels:

```bash
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-quality-report --require-art-direction-review --max-outline-halo-pixels 0
```

17. Generate the React component only after visual QA and strict validation pass.

When the mascot has side-specific props, text, emblems, handed items, or asymmetric lighting, generate left/right directional states separately instead of mirroring.

## Visual Rules

Prefer sprite-readable animation over decorative effects.

- Keep poses fully inside each frame with safe padding.
- Use every listed frame as a meaningful pose or in-between.
- Keep props attached to, held by, or clearly anchored near the mascot.
- Avoid shadows, glows, blur, motion streaks, dust, loose sparkles, detached punctuation, UI panels, scenery, and text unless the user explicitly requests a website-only effect and the atlas extraction can preserve it.
- For `pose-only`, show `thinking`, `working`, and `answering` through head tilt, eye movement, hand/prop pose, blink, mouth shapes, and body motion.
- For `semantic-enhancers`, add one small anchored enhancer for ambiguous states, such as a thought bubble near the head, a held paper/tablet/tool, listening rings, or a small success/error charm. The enhancer must match the mascot's theme.
- For `thinking`, prefer a side-origin thought cue over a generic icon directly above the head: the effect should begin near one side of the head/hood/face, drift slightly outward and upward, reach a clear readable hold, then settle back into a loop. The eyes and mouth should track the thought with a curious, focused, or pondering expression.
- Do not freeze expressive appendages just to avoid anatomy mistakes. Existing fins, paws, sleeves, mitts, tentacles, wings, hands, or other visible appendages may move, brace props, gesture, touch the face, or settle when that action matches the source character and the appendage's recorded affordances. The prompt must name the exact existing appendages, include any `requiredAffordances`, and forbid extra copies, new fingers, detached mitts, duplicated sleeves, or changed appendage count.
- If a simple appendage gesture makes a fin, sleeve, paw, tentacle, or mitt-like limb read as a new hand, fingered mitten, or third limb, regenerate with safer acting: keep appendages side-attached, let them tilt or tuck only slightly, and carry the state through eyes, mouth, body tilt, blink timing, and the anchored enhancer instead.
- Production enhancers must match the mascot's exact rendering style: same line weight, pixel grid or brush texture, palette, lighting direction, shading, antialiasing, and occlusion with hands/clothing. Do not ship hand-drawn/vector overlays on top of generated mascot frames unless the user explicitly asked for a prototype.
- Do not let a prop make the state read correctly while the mascot itself becomes less expressive, less polished, or less like the source reference.
- For `working`, choose the cue from the companion's anatomy and world. Use laptop/tablet/parchment/quill/tool only when the source has existing appendages or identity props with plausible `grip`, `brace`, `typing`, `writing`, `point`, or `present` affordances. Fins, sleeves, paws, and tentacles can count only when the reference already shows them and the contract allows that action; prompts must name those exact interactors and forbid extra anatomy. For true no-limb mascots, use non-grip cues such as a body-surface processing glyph, pulsing core, aura/status band, near-head work orb, focused face, or faster body motion. Reject rows that invent extra hands, duplicate arms, new fingers/paws/fins, or grip anatomy.
- For `answering`, prefer mouth shapes, presenting gestures, or a small no-text speech cue.
- For `success`, use body pose, bounce, wave, raised prop, or a small anchored check/glint. Detached confetti/sparkles should be avoided unless the user wants website-only effects and the atlas extraction can preserve them.
- For `error`, use expression, slump, prop droop, attached tear, warning charm, or attached smoke/stars only when they remain inside the cell and attached to the mascot.

## React Integration

When implementing the mascot in a React app:

1. Put final assets under the app's served assets path, typically `public/mascots/<id>/`.
2. Import or fetch `manifest.json`.
3. Animate with frame durations from the manifest rather than assuming equal CSS `steps()` timing.
4. Respect `prefers-reduced-motion`: show the first frame or a slow idle frame when the user prefers reduced motion.
5. Keep the component controlled by app state: `state`, `size`, `paused`, and optional `onClick`.
6. Use CSS `image-rendering: pixelated` for pixel-adjacent mascots, unless the generated style is deliberately smooth.

Read `references/react-integration.md` for a reusable component pattern.

## Scripts

Use bundled scripts when useful:

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --columns 12 --cell-width 256 --cell-height 288 --no-equal-fallback
python scripts/stitch_row_parts.py --parts /path/to/part-a.png /path/to/part-b.png --out /path/to/run/row-strips/state.png
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check stylePreserved=true --check creativeStateReadability=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --notes "Visual review passed."
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile audition --strict --require-state-clarity --require-quality-report
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-quality-report --require-art-direction-review
python scripts/generate_react_component.py --manifest /path/to/manifest.json --out-dir /path/to/react
```

If the system `python` cannot import Pillow/PIL, use the Codex bundled workspace runtime instead: call `load_workspace_dependencies`, then run the same scripts with the returned Python executable.

`assemble_companion_atlas.py` reads row strips named `<state>.png`, updates the manifest atlas fields, extracts clean per-frame PNGs, writes `atlas.webp` and `atlas.png`, creates `qa/contact-sheet.png`, creates `qa/cutout-check.png`, creates `qa/previews/*.gif`, and writes `qa/assembly-report.json`. It uses foreground-run center detection rather than naive equal-width slicing, which prevents common generated-strip issues such as variable frame spacing, clipped wide gestures, and neighboring-frame slivers. It fits all frames in the same state row with one shared scale so a growing thought bubble, sound ring, work prop, or other semantic enhancer cannot make only that frame's mascot body shrink. It also runs the outline improver: transparent RGB clearing, key spill removal, key-colored edge cleanup, spill-color replacement, and premultiplied resizing so invisible chroma-key pixels do not bleed into sprite edges. The assembly report records `outlineImprover.totalOutlineHaloPixels`; production runs should keep this at `0`. If it reports `equal-fallback` or outline warnings, review that state manually and prefer regenerating the row if the contact sheet looks uneven.

Use `--extraction-mode component` when row sources contain detached but integrated state effects, such as thought orbs, sound rings, or speech wisps. It groups each mascot body with nearby components instead of slicing through neighboring poses. Use `--extraction-mode equal` only when the row sources were intentionally generated as exact equal-spaced horizontal strips and foreground-center extraction visibly splits or merges close frames. These are explicit production choices, not silent fallbacks: accept them only when the contact sheet shows no chopped frames, neighboring slivers, or lost props.

`create_state_readability_sheet.py` writes `qa/state-readability-check.png`, showing enhanced states at 64, 96, and 128 px. Use it before validation for `semantic-enhancers` packs.

`analyze_companion_quality.py` writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`. It flags near-duplicate frames, low average motion, body jitter, large foreground area jumps, detached fragments, core silhouette scale drift, full-row core scale range over the production default of `5%`, core center drift, missing separate enhancers, and drifting semantic anchors. This is not a substitute for visual judgment, but it catches the common symptoms of wrong cuts, cropped/slivered frames, unstable body size, unstable props, pasted-on effects, and fake smoothness.

`create_art_direction_review.py` writes `qa/art-direction-review.json`. Use it as a production review record after visual inspection. It should fail, not pass, when a result is technically clean but looks worse, less creative, over-simplified, or prototype-like compared with the source.

`validate_companion_manifest.py` verifies manifest shape, state frame counts, durations, atlas path, dimensions, alpha channel, empty used cells, non-transparent unused cells, edge-touching/cropped sprites, residual key-colored outline halos, assembly-report warnings, missing readability QA, quality-report warnings, risky enhancer metadata, anatomy-guard specificity, anatomy-contract shape, appendage affordance mismatches, art-direction review blockers, and optional state clarity metadata. The `audition` profile is for strict one-row or partial-pack tests and does not warn about missing `idle` or other chatbot states. The `chatbot` profile warns when core website states are missing or when important states have too few frames for smooth motion. Use `--strict --require-state-clarity --require-quality-report --require-art-direction-review --max-outline-halo-pixels 0` for newly generated production packs so warnings, missing clarity metadata, missing QA, quality issues, anatomy-guard issues, anatomy-contract warnings, affordance warnings, art-direction issues, and outline halo pixels block acceptance.

`generate_react_component.py` emits a TypeScript React component that reads the manifest and animates by per-frame durations.

## Acceptance Criteria

- `manifest.json` lists every state, row, frame count, frame size, durations, and atlas path.
- `atlas.webp` or `atlas.png` exists, has transparency, and matches manifest dimensions.
- Every used frame is non-empty and unclipped.
- Unused cells are transparent.
- `qa/assembly-report.json` exists and any extraction warnings are reviewed.
- `qa/assembly-report.json` records `outlineImprover.enabled: true` and `outlineImprover.totalOutlineHaloPixels: 0` for production packs.
- `qa/cutout-check.png` shows no visible chroma-key halo on dark, light, and saturated backgrounds.
- `qa/state-readability-check.png` exists for `semantic-enhancers` packs and shows enhanced states at 64, 96, and 128 px.
- `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png` exist and show no unresolved quality warnings for production packs.
- `qa/art-direction-review.json` exists, has `status: "pass"`, has `productionUse: true`, records the original `sourceReference`, and records that reference quality, identity, style, creative state readability, native enhancers, integrated enhancers, anatomy preservation, no extra anatomy, believable occlusion, and no prototype flattening all passed.
- The final art is not accepted if its production method is deterministic compositing, vector overlays, manual shape overlays, or another prototype-only path.
- Chatbot profile validation passes in strict mode, or every warning is explicitly reviewed and accepted.
- `manifest.json` records `style.stateClarity` as `pose-only` or `semantic-enhancers` for newly generated packs.
- If `semantic-enhancers` is selected, `thinking`, `working`, `listening`, and `answering` include per-state `enhancer` metadata and read clearly at 64, 96, and 128 px.
- Semantic enhancers look native to the mascot artwork, not pasted on. Reject any row where prop/effect outline, shading, scale, perspective, antialiasing, or pixel density does not match the base mascot.
- Enhanced states do not create extra limbs, duplicate hands, new fingers/paws/fins, or body parts that were not in the original character design.
- Held, touched, writing, near-hand, or work-prop enhancers include `enhancer.anatomyGuard` metadata with a no-new-limbs policy, exact allowed interactors, and forbidden anatomy artifacts. For `style.anatomyClass: "no-limbs"`, do not use grip/typing/writing props at all; strict validation rejects them even when an anatomy guard is present. For `fins-no-hands` or `ambiguous-limbs`, held props are allowed only when `style.anatomyContract`, the prompt, and the manifest name the exact existing appendages that interact with the prop.
- `enhancer.anatomyGuard.allowedInteractors` does not use vague entries such as `existing visible appendages only`; it names concrete reference parts like `left side fin`, `right side fin`, `front paws`, `left sleeve`, or `right tentacle`.
- When `style.anatomyClass` is `fins-no-hands` or `ambiguous-limbs` and risky enhancer interactions are used, `manifest.json` records `style.anatomyContract` with a stable body core, counted appendages, placements, and forbidden additions.
- Per-state body scale stays consistent: no unresolved core silhouette scale drift, full-row core scale range, core center drift, detached fragments, or broken-cut warnings in `qa/quality-report.json`.
- Production final art uses `imagegen-integrated-row-art`, `user-provided-integrated-row-art`, or `artist-provided-integrated-row-art`; deterministic local drawing/compositing is a prototype-only failure path.
- If `pose-only` is selected, no new semantic props appear unless the user explicitly requested them.
- `thinking`, `working`, and `answering` have 12+ frames by default unless the user requested a smaller atlas.
- `idle`, `greeting`, `listening`, `success`, `error`, `confused`, and `sleeping` have 10+ frames by default unless the user requested a smaller atlas.
- Every requested chatbot state is visually distinct enough to read at website size.
- Contact sheet and at least one preview format are produced.
- React component can display `idle`, `thinking`, `working`, `answering`, `success`, and `error`.
- The final answer reports asset paths, manifest path, React component path, and QA result.
