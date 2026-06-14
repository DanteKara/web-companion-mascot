---
name: web-companion-mascot
description: Use when creating, validating, or integrating custom animated mascot companions for React/chatbot websites from concept art, screenshots, existing Codex pets, or generated references, especially when states like idle, greeting, listening, thinking, answering, success, error, confused, or sleeping are needed.
---

# Web Companion Mascot

## Overview

Create web-first pixel-art animated chatbot mascots with a custom sprite atlas, state manifest, React component, and QA assets. Prefer this skill when the target is a website companion rather than a Codex app pet.

This skill composes `$imagegen` for visual generation and borrows the useful discipline from `$hatch-pet`: grounded references, row prompts, chroma-key cleanup, deterministic validation, and visual QA. It does not use the fixed Codex 8x9 atlas unless the user explicitly asks for Codex compatibility.

## Generation Delegation

Use `$imagegen` for all normal visual generation.

Before generating base art, state rows, or repair rows, load and follow the installed image generation skill:

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

Do not call the Image API directly for the normal path. Let `$imagegen` choose its own built-in-first path and fallback rules. If `$imagegen` says a fallback requires confirmation, ask the user before continuing.

When invoking `$imagegen` from this skill, pass the generated companion prompt as the authoritative visual spec. Do not wrap it in the generic `$imagegen` shared prompt schema and do not add extra polish, hero-art, photo, product, or illustration-style augmentation. Companion prompts should stay terse, sprite-specific, and website-companion oriented; only add role labels for input images and essential user constraints.

Use this skill's scripts for deterministic work only: preparing prompts and manifests, ingesting selected `$imagegen` outputs, extracting frames, assembling the atlas, creating QA media, validating the manifest, and generating React integration files.

Hard boundary: do not create, draw, tile, warp, mirror, or synthesize production mascot visuals with local Python/Pillow scripts, SVG, canvas, HTML/CSS, or other code-native art as a substitute for `$imagegen`. If `$imagegen` is unavailable and the user has not provided finished integrated sprite art, stop and explain the blocker instead of fabricating rows locally.

Do not mark visual jobs complete by editing `imagegen-jobs.json`, copying files into `generated/`, or writing helper scripts that populate row outputs. Use `record_companion_imagegen_result.py` for selected built-in `$imagegen` outputs, built-in `$imagegen` chroma-key cleanup outputs produced by the installed `remove_chroma_key.py` helper, explicit approved `$imagegen` CLI fallback outputs, or explicit user/artist-provided integrated sprite art.

Only the base job may be prompt-only, and only when no reference exists. Every state-row job generated through `$imagegen` must use the input images listed in `imagegen-jobs.json`, including the canonical base reference created after the base job is recorded. Treat any row generation without attached grounding images as invalid.

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
  qa/anatomy-review.png
  qa/anatomy-review.json
  qa/eye-grammar-review.png
  qa/eye-grammar-review.json
  qa/state-performance-review.png
  qa/state-performance-review.json
  qa/art-direction-review.json
  qa/production-readiness-report.json
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

## Prompt Boundary

Generated `$imagegen` prompts should follow the `$hatch-pet` pattern: terse, sprite-specific, grounded by input images, and authoritative. Do not paste this skill's full policy text, reference files, QA rationale, or long mascot-anatomy examples into row prompts. Keep detailed planning and failure analysis in `qa/state-cue-plan.json`, `manifest.json`, QA reports, and manual review notes.

The skill is generic. Row prompts must not hard-code a particular mascot's colors, props, anatomy, outfit, or cue source unless those details are user-supplied, reference-inferred, or already recorded in the canonical base/manifest. Use generic language such as `appendage`, `held prop`, `identity accessory`, `face-bearing area`, and `source-bound cue`; let the canonical base, original reference, and accepted rows define the actual character. Examples in this skill are explanatory only and must not become default prompt content.

Each row prompt should contain only the production essentials: input-image roles, exact frame count, native pixel-art style lock, identity/eye/scale lock, cleanup-ready row-source layout, state story, concise cue rule, and rejection criteria. If a state needs more nuance, improve the state plan or regenerate the row; do not solve weak generation by piling every possible rule into the image prompt.

## Codex Pixel Companion Style

Production mascots created by this skill must use the Codex digital-pet pixel-art house style, even when the user reference is a smooth illustration, logo, plush, 3D render, anime drawing, or screenshot. Translate the reference identity into a small sprite: compact chibi proportions, chunky readable silhouette, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, simple expressive face, and tiny readable appendages.

Do not accept polished illustration, painterly rendering, 3D/app-icon gloss, soft airbrush gradients, realistic fur/material texture, vector-flat clip art, high-detail antialiasing, or smooth cartoon rendering as production output. The React component can display the atlas crisply with `image-rendering: pixelated`, but CSS cannot turn smooth generated art into real pixel art. If the row looks like a scaled-down illustration instead of native sprite art, regenerate it with stronger pixel-art language.

The canonical base must already be production-grade native pixel art before row generation. Treat it as the final atlas-frame source of truth, not concept art, a preview illustration, a pose-sheet sample, an app icon, or a softened style target. The base should read like a Codex app digital pet first and a website mascot second: fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite cell even if the final web atlas later uses larger cells. It must be simple enough to reproduce across eight row frames without redesign: stable silhouette, top edge, bottom edge, face-bearing area, appendage count, prop count, and no tiny high-detail marks that will flicker in rows. Reject and regenerate the base before any row prompt if it is smoother, glossier, more detailed, or less pixel-native than the intended row art; rows must preserve the accepted base, not fix it by changing eye style, body shape, colors, outline weight, props, or anatomy. For text-only concepts, add only anatomy and identity props named in the concept or command; do not invent extra feet, legs, tails, markings, lights, display details, buttons, tools, or other identity marks. Draw the base as if it was first made on a tiny 64x72 or 80x90 pixel grid and enlarged with nearest-neighbor scaling. Use indexed-color sprite discipline: roughly 8-16 total non-background colors, no per-pixel color ramps, no smooth shade bands, no gradient-filled body areas, face areas, clothing, props, accessories, or appendages, no blended intermediate palette colors, and no dozens of near-identical colors. Build the palette from the reference or concept; never impose a preselected helper palette on unrelated mascots. If an attached reference already looks like a HatchPet or Codex digital-pet sprite, treat it as the visual style floor: preserve its pixel density, chunky outline, block shading, eye/catchlight grammar, cheek/mouth pixel language, outfit simplification, held-prop simplification, palette relationships, and compact proportions while removing only preview-background noise and unstable tiny detail. Use hard-edged square pixel clusters, 2-3 flat tone steps per material, hard stepped edges, large flat color clusters, one darker stepped shadow band at most, and tiny rectangular pixel highlights; reject glossy gradients, soft airbrush shading, bloom, rim glow, broad shine patches, transparent or semi-transparent shines, feathered transitions, high-detail specular shine, 3D lighting, smooth radial gradients, soft cylindrical shading, pillow shading, app-icon material lighting, smooth antialias fringes, and smooth vector curves in the base. If the source vibe is soft or friendly, carry that through rounded silhouette and expression, not blurred rendering. Do not compose the base as a large glossy product mascot, large hero character, app icon, or high-resolution sticker; leave generous chroma-key padding and keep the sprite compact. A row prompt cannot reliably preserve a base that is itself too glossy, over-detailed, or anatomically ambiguous. Row prompts must also preserve absence: plain body areas stay plain, absent limbs stay absent, and absent identity details should not be invented just because a broad mascot category might suggest them. Preserve the face-bearing area as identity: do not skew, stretch, rotate, squash, or warp it to create acting. Use tiny bob, side shift, mouth/blink change, appendage beat, prop beat, or cue timing instead of warping the mascot core.

The goal is not to make every mascot identical. Preserve the reference's identity, silhouette cues, palette family, face, must-keep markings, and charm, but simplify them into the pixel-sprite language above. Avoid "generic pixel blob" simplification: a good output should clearly be the referenced mascot translated into Codex-style pixel art.

Treat the full reference palette as identity, not decoration. Preserve the actual reference colors for eye whites/highlights, pupils, eye outlines, face base colors, cheek marks, outfit, props, and signature markings when translating into pixel art. Do not force white eyes or white highlights when the reference uses another color; only keep whites white when the source uses white. Do not let a prop glow, bloom, aura, or palette accent tint or recolor the mascot identity palette.

Treat eye grammar as identity, not generic expression inventory. Preserve the canonical base eye count, shape, size, spacing, outline color, pupil/fill color, and catchlight/highlight logic across every row. Gaze and tiny pupil/highlight shifts are allowed when they are deliberate acting beats, but both eyes must remain matched and anchored to the same face-panel positions. Reject hollow or inverted eyes, solid dark eyes turned into white ovals with dark rims, extra catchlights, glossy anime eyes, vertical slit pupils, square UI eyes, mismatched eyes, and one-frame eye-style swaps. For solid dark base eyes, open eyes should remain mostly dark with the original tiny highlight; do not expose white sclera crescents, carve white crescent gaps to fake side glances, or make a white cutout the dominant eye shape. If an up-glance, side-glance, blink, or speaking beat would require changing eye style, keep the eyes forward or nearly forward and carry the acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead. Keep eye centers inside the original eye boxes; never slide eyes onto cheeks, panel edges, the mouth line, or outside the face panel. Do not replace eyes with loading dots, LEDs, status bars, diagonal slashes, crosses, punctuation, or reaction icons. Closed-eye blinks should replace each open eye with a simple closed curve or horizontal pixel line in the same positions and spacing, not X-eyes, chevrons, eyebrows, reaction glyphs, or lower-face squiggles.

When a reference has distinctive eyes, record a short eye-grammar note during run preparation whenever possible. Name the eye count, shape, spacing, fill/pupil color, outline color, highlight or catchlight count, and blink style. This note is especially important for mascots with large black eyes plus white highlight blocks, screen eyes, mask eyes, or unusual colored pupils, because rows should animate those eyes without replacing them with a generic expression set.

For detailed references, audit signature props, emblems, clothing silhouettes, markings, and accessories as identity, not decoration. Simplify ornate detail into a few readable pixel clusters, but keep must-keep props stable when they appear. A staff, wand, tool, badge, emblem, hat, bag, weapon, shell, or clothing trim should not flicker in and out across frames, duplicate itself, change sides unexpectedly, mutate into a different object, or turn into extra anatomy. If a state is too crowded for a signature prop, omit that prop intentionally for the whole row instead of letting it appear inconsistently.

Preserve signature props by default even when a state also needs a semantic cue. A thought bubble, voice puff, work glyph, or progress target should be staged around the mascot and prop, not treated as a reason to drop a must-keep accessory, mark, outfit feature, or held object. State cues must not cover, replace, recolor, merge with, or grow out of identity props unless the state explicitly uses that prop as the active source. For mascots with prominent identity accessories, thinking cues should originate from the inferred thought-cue source near the expression area, not from an unrelated accessory, and identity accessories should remain visible and stable. Omit a must-keep prop only when the state card explicitly marks that exact prop optional for the whole row. When a state uses a held identity prop as the source of an action, the cue must stay visually distinct from that prop. For long held props, prefer an attached hard-edged pixel bloom/aura/pulse/contact mark wrapped around or touching the active end over a separate object, emblem, badge, or prop echo. Use the existing prop to point, tap, aim, charge, or bloom at the active end; do not summon a second copy or prop-shaped glyph, and do not echo identity emblems, logos, badges, weapon silhouettes, or signature markings inside any target. If the held prop moves into an active pose, that active pose replaces the resting pose; never show both a resting copy and an active copy in the same frame.

## Transparency And Effects

Companion rows are processed into transparent atlas cells, so every generated pixel must either belong to the mascot sprite or be cleanly removable chroma-key background. Prefer pose, expression, silhouette, and original identity props over decorative effects.

Generated row strips must leave a wide empty chroma-key margin around the outer row image border. No sprite body, identity prop, accessory, appendage, outline, cue, or effect should touch the outer source image edge; the first and last frames need safe empty chroma padding outside them before assembly.

Allowed effects must satisfy all of these conditions:

- The effect is state-relevant and helps explain the state.
- The effect is physically attached to, touching, overlapping, or tightly source-bound to the mascot.
- The effect stays inside the same frame slot as the mascot and does not become a separate competing sprite.
- The effect is opaque, hard-edged, pixel-style, and uses non-chroma-key colors.
- The effect is small enough to remain readable at website sizes without forcing the mascot body to shrink.

Avoid shadows, glows, blur, motion streaks, speed lines, action rays, sound rays, emphasis strokes, wave lines, alert marks, cartoon motion marks, dust fields, loose sparkles, floating punctuation, detached icons, text, labels, UI panels, scenery, checkerboard transparency, white/black backgrounds, guide marks, stray pixels, and chroma-key-adjacent colors inside the mascot or effect.

For near-head thought, listening, voice, or processing cues, visual association can come from proximity, gaze, timing, overlap, a tiny separated tail dot, or a source-bound motion path. Do not alpha-connect a growing cue to the mascot core when that would make QA measure the cue as body size; keep the cue tiny, close, and secondary to the character.

## Art Direction Gate

Technical QA is necessary but not sufficient. A mascot can have a clean atlas, no halo pixels, and stable anchors while still being a bad companion. Production output must preserve the reference's identity, silhouette, charm, pixel-sprite art quality, and creative state reads.

Do not preserve a non-pixel rendering style from the reference. Translate identity into Codex pixel companion style. Deterministic compositing, vector overlays, hand-drawn helper props, and procedural shape props are prototype-only paths; production state cues must be generated or supplied as integrated native sprite art.

Before state generation, infer a lightweight visual-language read from the reference: what the mascot feels like, which motifs naturally belong to it, and which generic cues would look out of place. Record it in `style.visualLanguage` when useful, but do not let metadata substitute for art direction. The row should look like the referenced character naturally performing the state.

Every row prompt should carry a positive acting card, not only bans. Coordinate expression, body/appendage, and cue/prop tracks so the mascot performs the state. Reject rows where all motion lives in a bubble, sparkle, prop glow, or check mark while the mascot keeps the same face, parked appendages, or weak posture.

High-visibility states such as `thinking`, `answering`, and any explicitly requested `working` state must vary expression and body timing inside the source eye/face grammar. Do not invent hostile brows, symbol eyes, hand-to-face poses, or generic emotion marks unless the reference clearly supports them and the visual audition succeeds.

Treat thinking, working, and answering as high-visibility audition rows too. When the mascot has visible or ambiguous appendages, a partial audition can approve the story direction, but it must not approve production art without anatomy review, state-performance review, and eye-grammar review; strong state read cannot hide extra/drifting appendages, stale mascot acting, frozen expressions, cue-only motion, white-sclera swaps, hollow eyes, mismatched highlights, symbol eyes, or off-source blinks.

Before final validation, create `qa/art-direction-review.json` and fail the run if any required art-direction check is false. This review is a manual/agent visual gate over the contact sheet, readability sheet, cutout sheet, previews, and original reference; it exists because scripts cannot judge taste or creativity by themselves.

## Production Art Boundary

Follow `$hatch-pet`'s generation boundary for production art: `$imagegen` or a user/artist-provided integrated sprite source creates the pixels; this skill's scripts only assemble, clean, validate, preview, and generate React code.

Do not create, draw, tile, warp, or synthesize final mascot frames with local Python/Pillow scripts, SVG, canvas, CSS, vector overlays, procedural shape code, or deterministic compositors. Do not write ad hoc `generate_<mascot>.py` scripts that create row art for a production pack. If `$imagegen` is unavailable and the user has not provided finished row-strip art, stop and explain the blocker instead of fabricating a lower-quality mascot locally.

Use deterministic code only for:

- preparing manifests, prompts, state cards, and QA files
- tracking `$imagegen` jobs, canonical base references, selected-source provenance, and ready/blocked row status
- chroma-key cleanup, frame extraction, atlas assembly, and previews
- validation, reports, packaging, and React integration

Do not manually edit `imagegen-jobs.json` to mark jobs complete, copy images into `generated/`, or fabricate canonical references. Use `scripts/record_companion_imagegen_result.py` to ingest the selected original `$imagegen` output. For production, the recorded source should be the original `$CODEX_HOME/generated_images/.../ig_*.png` file unless it came from one of the explicit provenance paths below. If a visually accepted built-in output has a non-flat chroma background but can be converted to real alpha by the installed `$imagegen` `remove_chroma_key.py` helper, write the cleaned PNG outside the run directory and record it with `--source-provenance built-in-imagegen-chroma-cleanup --chroma-cleanup-source <original-$CODEX_HOME/generated_images/.../ig_*.png> --strict-row-style`; this is allowed cleanup, not local art creation, and the original raw `$imagegen` source remains hashed in the job record. If the output came from an explicit approved `$imagegen` CLI fallback, pass `--source-provenance imagegen-cli-fallback` plus `--cli-fallback-approved --cli-fallback-model gpt-image-1.5 --cli-fallback-background transparent --cli-fallback-output-format png --cli-fallback-prompt-file <prompt>`. If the base/row art is explicitly user/artist-provided integrated sprite art, pass `--source-provenance user-provided-integrated-row-art` or `--source-provenance artist-provided-integrated-row-art`. Finished transparent HatchPet/Codex pet frames can be recorded this way as trusted integrated art: strict base style still blocks opaque non-flat backgrounds and missing foregrounds, but treats palette-complexity warnings as visual-review advisories because existing pet assets may be richer than a prompt-generated indexed source while still being production sprite art.

This boundary matters most for `semantic-enhancers`: props/effects must be painted into the row as native character art, with real occlusion by existing body parts. A post-process prop can make a state technically readable while making the mascot look cheap; production QA must reject that.

## Motion Quality

Default to a HatchPet-style 8-frame baseline for production rows. Use 6-frame rows for compact auditions. Use 10-12 frame rows only after an 8-frame row proves identity, scale, appendage count, pixel density, and state readability are stable, or when the user explicitly requests extra smoothness.

Design rows as true animation, not static variants. Each row should read as one coherent loopable mini-story: establish the state, start face/body/appendage motion, reach the clearest read, recover, and settle back into the first frame. Stagger expression, body, appendage, prop, and cue timing so the mascot feels alive.

`thinking` and `answering` are the most visible waiting states. Give them richer acting inside the 8-frame baseline before adding frames. `thinking` should read as curious processing with an idea-lands moment when a cue is needed; `answering` should be mouth-led talking with eye engagement and conversational body rhythm.

When testing smoother motion, a new enhancer style, or a new prompt policy, run a small row audition before committing to a full production pack. Prefer one high-risk row at a time, especially `thinking`, `answering`, or any row with hands/held props. Assemble auditions with the real outline cleanup, run quality analysis, and validate with `--profile audition`.

For opt-in 10-12 frame rows, first try a single integrated row when the model reliably follows the count. If it returns too few or too many mascot bodies, generate smaller exact-count chunks and stitch only those generated parts with `scripts/stitch_row_parts.py`. Stitching is assembly, not art creation; any visible scale, outline, palette, anchor, prop, or expression change across the stitch boundary is a blocker.

## State Design

Choose states from the product behavior, not from the Codex pet contract. Recommended default chatbot companion states:

```text
idle       default resting loop
greeting   first page load, chat open, welcome
listening  user typing or microphone/listen mode
thinking   prompt submitted, model planning, retrieval, tool-use waiting, or backend progress
answering  assistant response streaming
success    answer completed or task succeeded
error      failed request or recoverable error
confused   unclear input or validation issue
sleeping   inactivity, minimized chat, offline
```

Map product states explicitly in the React integration; for example, typing/listening inputs map to `listening`, submitted/retrieval/tool-call waits map to `thinking`, streaming maps to `answering`, and completion/failure map to `success` or `error`.

## State Clarity Gate

Before generating state rows, ask the user to choose a state clarity profile unless they already specified one:

```text
pose-only            expression, posture, timing, hands, and existing identity props only
semantic-enhancers   one small anchored prop/effect for ambiguous states
```

Recommend `semantic-enhancers` for chatbot companions because users need to read `thinking`, `listening`, and `answering` while they wait. Use `pose-only` when the user wants a quieter/minimal mascot.

Do not include `working` in default companion packs. For most chatbots, `thinking` is the better combined state for planning, retrieval, tool calls, file/search waits, and backend progress. Generate `working` only when the user explicitly asks for a visually distinct work/tool state and the mascot has believable anatomy, a held prop, or a theme-native way to perform it.

When `semantic-enhancers` is selected, read `references/state-enhancers.md`. Choose cues from the mascot's own visual language instead of hard-coding universal objects. Use generic state aids only when the user, reference, canonical base, or manifest makes them native to the character.

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

Record those as `style.anatomyContract.appendages[].affordances`. Then choose the acting language from the affordances: real hands can present, hold, point, type, and use default clear-face thinking beats; paws or mitts can use broad gestures and chunky braced props; fins, wings, sleeves, and ambiguous simple appendages should usually stay side-attached unless the reference and an audition prove a riskier gesture reads correctly; no-limb mascots should use face, body, aura, near-head, or body-surface semantics.

When real hands, paws, sleeves, tentacles, or arms present an idea, brace a prop, operate a work surface, or use an explicitly auditioned face-touch gesture, preserve a clear silhouette path back to the original body anchor. Leave enough outline or tiny negative space for the appendage to read as the original appendage, not a new cheek, nose, detached mitten, duplicated hand, extra paw, or face patch. Prefer broad pixel-mitt/paw gestures over tiny fingers unless the reference clearly has fingers.

For risky enhancer or pose metadata, add `enhancer.requiredAffordances` such as `["face-touch"]`, `["grip"]`, or `["typing"]`. The validator compares those actions against the named interactors in `enhancer.anatomyGuard.allowedInteractors` and the appendage affordances in `style.anatomyContract`.

For simple appendage mascots, also guard against fake appendages that appear as body markings. A fin-colored oval, sleeve-colored patch, mitten-shaped highlight, or detached blob on the front of the body can read as an extra limb even when the real side appendages stay attached. State prompts should forbid new limb-colored body patches or front-facing appendage shapes, and near-head effects should use a distinct anchor, silhouette, and placement so they do not resemble the mascot's appendages.

## Companion Naming

Ask the user for a companion name when they have not provided one and the conversation naturally allows it. If asking would slow down a direct execution request, choose a short appropriate name from the concept or reference filenames and use it consistently as the display name and package id.

For generic requests, prefer a neutral placeholder such as `Companion` in prompts and manifests. Do not let examples in this skill become default mascot identity, color, anatomy, outfit, or prop choices.

## Visible Progress Plan

For every normal companion run, keep a visible checklist so the user can see where the work is up to. Create the checklist before starting, keep one step active at a time, and update it as each step finishes.

Use this checklist for a normal run, replacing `<Companion>` with the companion's name or `your companion`:

1. Getting `<Companion>` ready.
2. Imagining `<Companion>`'s main look.
3. Picturing `<Companion>`'s states.
4. Packaging `<Companion>` for React.

What each step means:

- `Getting <Companion> ready.` Choose or confirm the name, description, references, state list, state clarity profile, chroma key, and working folder.
- `Imagining <Companion>'s main look.` Generate or record the canonical base sprite. This is required for new mascots because it becomes the visual source of truth for every state row.
- `Picturing <Companion>'s states.` Generate state rows one row at a time, using the canonical base, original references, layout guide, and compact row prompt for each row.
- `Packaging <Companion> for React.` Assemble the atlas, produce QA sheets and previews, run quality analysis and strict validation, generate React files when requested, and report the asset paths.

Only mark a step complete when the real file, image, or decision exists. If this is a repair or audition run, start from the first relevant step instead of restarting the whole checklist.

## Default Workflow

1. Establish mascot identity: name, reference image(s), must-keep features, anatomy class, prop rules, palette, target website vibe, state list, state clarity profile (`pose-only` or `semantic-enhancers`), `style.renderingStyle: "codex-pixel-art"`, and an inferred visual-language read. When anatomy matters, audit the reference before generation: stable body core, exact visible appendages with count and placement, appendage affordances, allowed motion for those exact parts, forbidden additions, signature props/accessories, and any ambiguous marks that are not limbs. Record this as `style.anatomyClass` (`hands`, `paws`, `fins-no-hands`, `no-limbs`, or `ambiguous-limbs`) and, for simple/ambiguous appendages, detailed references, signature props, or risky prop interactions, `style.anatomyContract` plus `style.visualLanguage.identityProps` when useful. For normal runs, start with the preparer so the state acting plan and `$imagegen` job manifest exist before image generation:

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
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png --strict-base-style
```

   Recording the base copies it to `generated/base.png`, creates `references/canonical-base.png`, updates `imagegen-jobs.json`, stores `base_style_analysis` and `base_style_strict_blocking_warning_codes`, and stores canonical-reference metadata in `manifest.json` and `companion_request.json`. Production base recording should use `--strict-base-style`; if it fails for `non_uniform_chroma_key_background`, `smooth_or_overdetailed_foreground_palette`, or `no_foreground_sprite_detected`, reject/regenerate the base before any row generation. Audition/chatbot validation fails completed base jobs that lack this strict base-source evidence or retain blocking codes.
5. Re-run `companion_job_status.py`. Row jobs become ready after the canonical base exists. Generate one row strip per ready state with `$imagegen`, using the compact row prompt and every input image listed in `imagegen-jobs.json`: original references, `references/canonical-base.png`, `generated/base.png`, and that state's layout guide. Every row prompt must restate the pixel-art contract in brief: visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, exact flat chroma-key background, safe empty outer row-image margin, no painterly gradients, no glossy 3D, no smooth vector/cartoon look, no soft antialiasing, and no generic action/sound/emphasis marks. Do not generate rows prompt-only unless there is no possible reference image.
6. Record each selected row output:

```bash
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png --strict-row-style
```

   The parent agent owns all recording and manifest writes. Production row recording should use `--strict-row-style`; if it fails for `fake_checkerboard_transparency_background`, `non_uniform_chroma_key_background`, or `no_foreground_sprite_detected`, reject/regenerate the row source before assembly. Recording with this flag stores `row_source_style_analysis` and `row_source_style_strict_blocking_warning_codes` in `imagegen-jobs.json`; audition/chatbot validation fails completed generated row jobs that lack this evidence. This keeps row-strip backgrounds cleanup-ready without pretending deterministic alpha cleanup can fix a bad generated source or fake transparency. If multiple workers or subagents generate row candidates, they should return only the selected original source path and a short QA note; they must not edit manifests or copy files into the run. Their QA note must call out visible chroma-key falloff, vignette, green-looking-but-non-uniform backgrounds, eye-grammar swaps, wrong-state frames, stale acting, extra anatomy, or face-touch drift instead of summarizing those candidates as clean.
7. Keep all row strips on the prepared flat chroma-key background. The preparer chooses a key color absent from the copied references when possible; avoid yellow for gold props, avoid magenta for pink/purple characters, and avoid green for green characters.
   Keep the row source padded too: first and last frames should be fully visible with empty chroma outside them, and no mascot part or cue may touch the outer row image border. If a generated source crops the row edge, record it as rejected and regenerate instead of trying to rescue the source with assembly.
   If two built-in `$imagegen` attempts for the same row fail `--strict-row-style` for `non_uniform_chroma_key_background` or `fake_checkerboard_transparency_background`, stop retrying the same built-in prompt pattern. Follow `$imagegen`'s true-transparency fallback policy instead: explain that the built-in path is not producing a cleanup-ready source, ask the user before CLI/API fallback, and proceed only after the user explicitly confirms and the required environment is available. The fallback source should be the current recorded row `source_path` by default. If no row has been recorded and the best visual story exists only as a strict-rejected candidate, use `create_imagegen_cli_fallback_handoff.py --allow-rejected-candidate-source` so the candidate remains non-mutating repair input rather than accepted art. Do not repair stale row candidates by accident. Do not record a locally flood-filled, fill-bucketed, composited, or fake-transparent row as a production generated source.
8. Preserve identity and pixel-art treatment across every row: silhouette, face, palette, props, outfit, outline weight, pixel density, stepped edges, and proportions.
9. If using `semantic-enhancers`, include the chosen profile and inferred visual-language read in the plan, then generate each enhancer as integrated mascot artwork, not as a post-process overlay. Add only one small attached, touching, overlapping, or tightly anchored enhancer per ambiguous state unless the user explicitly requests more. Before each enhanced row, keep the detailed state card in `qa/state-cue-plan.json` or QA notes, then pass `$imagegen` a compact row prompt derived from it. The choreography must coordinate expression, body/appendage, and cue/prop tracks, with the mascot visibly acting in the row instead of sitting unchanged under a moving symbol. For held, touched, face-touch, pointing, presenting, typing, writing, or appendage-operated work props, the plan and manifest must name the exact existing interactors and forbid extra anatomy; the final image prompt should only carry the concise version needed for generation.
10. For near-head effects, held props, and any higher-frame-count waiting state, add explicit silhouette-lock language to the row prompt: same body footprint, same body center, same top edge, same bottom edge, same named appendage count, and enhancer motion around that stable base. Later rows must also match the apparent body size and padding of the canonical base plus any already accepted state rows, not zoom in or shrink to accommodate a gesture/cue. Near-head effects must stay compact enough that the assembler does not have to shrink the whole state row to fit a bubble, puff, voice cue, or aura. The motion should come from expression, blink, small pose beats, prop follow-through, or enhancer changes, not from resizing the mascot.
11. Generate at least two visual approaches or row candidates for high-visibility states when the first pass looks bland, overly literal, drifty, non-pixel, or less polished than the source. Prefer regenerating the row over post-processing a weak one into compliance. If a candidate has pasted-on semantics, mismatched art style, smooth illustration rendering, invented anatomy, core scale drift, or core center drift, discard the candidate; do not repair it by compositing.
12. Seed `manifest.json` with the state rows, frame counts, durations, `id`, `displayName`, `style.renderingStyle: "codex-pixel-art"`, `style.stateClarity`, `style.anatomyClass`, `style.anatomyContract.appendages[].affordances` when used, and per-state `enhancer` metadata including `requiredAffordances` for appendage-dependent actions. The preparer defaults to 8 frames per state and may write draft enhancer metadata such as `planned during row generation`; after selecting the final row art, replace those placeholders with the actual accepted visual aid before production validation.
13. If an opt-in 10-12 frame row repeatedly misses the requested frame count, generate shorter row parts with exact count prompts and stitch the accepted generated parts before atlas assembly:

```bash
python scripts/stitch_row_parts.py --parts /path/to/state-part-a.png /path/to/state-part-b.png --out /path/to/run/row-strips/state.png --json-out /path/to/run/qa/state-stitch-report.json
```

   Visually inspect the stitched source or contact sheet for a seam between parts. Regenerate the weaker part if the mascot scale, line weight, prop size, anchor, palette, or expression quality changes across the stitch boundary.
14. Assemble the atlas with the bundled assembler. This script handles variable row-strip spacing, chroma-key gradients, wide gestures, transparent unused cells, extracted frames, contact sheets, GIF previews, and an assembly report. By default it reads the run's `style.chromaKey`/`companion_request.json` chroma key; do not force a fixed green or magenta key unless intentionally overriding a bad run setting. Its outline improver must remain enabled: key-to-alpha removal, edge-spill cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing all protect the sprite edge from chroma halos.
   For row strips with detached bubbles, voice marks, or aura components, prefer `--extraction-mode component`. If a large semantic effect is mistaken for an extra body component, raise `--body-component-area` rather than accepting equal slicing; the effect should be assigned to the nearest real body, not treated as a mascot.

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --max-outline-halo-pixels 0 --no-equal-fallback
```

15. Create the small-size readability QA sheet for semantic states:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
```

16. Run the quality analyzer before acceptance. It writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`; strict production runs should have no analyzer warnings. This catches near-duplicate frames, static rows, body jumps, foreground area jumps that often signal extra limbs or missing props, detached fragments from broken cuts, core silhouette scale drift, full-row core scale range, cross-state core scale mismatch, core center drift, and drifting semantic enhancers. For polished production mascots, full-row mascot core scale range should stay at or below `8%`, and cross-state median core scale range should stay within the analyzer threshold; larger changes usually look like the mascot grows or shrinks even when each row technically assembles:

```bash
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
```

17. Visually inspect the contact sheet, cutout check, readability sheet, semantic anchor sheet, motion quality sheet, previews, and the original reference before accepting the mascot. If the contact sheet shows neighboring-frame slivers, chopped hands/props, stray specks, off-center sprites, simplified anatomy, inconsistent mascot scale, lower polish than the reference, smooth/non-pixel rendering, or less creative state reads than the brief implies, regenerate the row. If `qa/cutout-check.png` shows pink/magenta halos on dark, white, blue, or green backgrounds, rebuild with stronger chroma cleanup or regenerate the row with a flatter key background. For `semantic-enhancers`, reject rows where the enhancer is unclear at 64, 96, and 128 px, cropped, detached, leaking into other states, visually pasted on, drifting away from its anchor, causing extra anatomy, mismatching pixel density, or changing quality across a split-row stitch.
18. Create the frame-by-frame anatomy review only after inspecting every used frame at enlarged size. This is a manual/agent visual gate, not an automatic limb detector: it exists to catch failures such as a late frame gaining a third hand, a sleeve turning into a duplicate arm, a thought puff becoming a new appendage, or a must-keep staff/tool changing count. Use `status: "pass"` and `productionUse: true` only when every state frame has been counted against the reference:

```bash
python scripts/create_anatomy_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-anatomy "Stable body core, exact appendage count, appendage placement/anchors, allowed motion/interactors, and forbidden extra anatomy from the reference audit." --expected-identity-props "Expected must-keep props/accessories and their stable count/side/attachment." --check frameByFrameAnatomyReviewed=true --check appendageCountStable=true --check noExtraAppendages=true --check noDuplicatedAppendages=true --check identityPropsStable=true --check stateCuesNotMisreadAsAnatomy=true --check contactAndOverlapBelievable=true --notes "Every used frame was inspected at enlarged size; appendage count, identity props, and state cues stay consistent."
```

19. Create the frame-by-frame state-performance review only after inspecting every used frame for the intended state read. This is a manual/agent visual gate, not an automatic taste detector: it exists to catch failures such as `thinking` reading as idle/status dots instead of planning/processing, `answering` reading as tired exhaling instead of engaged speech, or optional `working` reading as panting, sleeping, talking, or generic decoration. Use `status: "pass"` and `productionUse: true` only when every state frame reads as the intended state through expression, pose, cue motion, and mascot-native acting, and when the row forms one coherent loopable state story rather than shuffled faces or cue-only motion. Add one `--expected-state-read <state>="..."` argument for every state in the manifest; the example below shows the two default high-risk chatbot states:

```bash
python scripts/create_state_performance_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-state-read thinking="Expressive planning/processing with a readable thought cue or body/face acting; not idle status dots." --expected-state-read answering="Engaged talking/streaming through mouth shapes, eye engagement, and optional supporting voice cues; not tired panting or exhale clouds." --check frameByFrameStateReadReviewed=true --check intendedStateReadable=true --check noWrongStateRead=true --check expressionMatchesState=true --check cueMotionMatchesState=true --check coherentStateStoryArc=true --check mascotActingVariesAcrossFrames=true --check noTiredPantingUnlessStateRequiresIt=true --check noOffVibeGenericCue=true --notes "Every used frame was inspected for intended state read, coherent story arc, expression, cue motion, and mascot acting."
```

20. Create the frame-by-frame eye-grammar review only after inspecting every used frame against the canonical base/reference eyes. This is a manual/agent visual gate, not an automatic eye detector: it exists to catch rows that have a strong state story but swap the source eyes into white sclera crescents, hollow eyes, mismatched eyes, extra catchlights, symbol eyes, or a different blink style. Use `status: "pass"` and `productionUse: true` only when every state frame preserves the source eye count, shape, fill, highlight logic, placement, and blink grammar:

```bash
python scripts/create_eye_grammar_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-eye-grammar "Expected source eye count, shape, fill/pupil color, highlight count/placement, spacing, and blink style." --check frameByFrameEyeGrammarReviewed=true --check eyeCountStable=true --check eyeShapeStable=true --check eyeFillAndHighlightStable=true --check eyePlacementStable=true --check noWhiteScleraOrCrescentSwap=true --check noMismatchedOrSymbolEyes=true --check blinkStyleMatchesSource=true --notes "Every used frame was inspected against the canonical eye grammar; no eye-style swaps or white-sclera/crescent substitutions."
```

21. Write the art-direction review only after the visual inspection passes. Use `status: "pass"` and `productionUse: true` only when the pack preserves the source quality, identity, eye grammar, and does not rely on deterministic/vector/post-process overlays for final art:

```bash
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check eyeGrammarPreserved=true --check eyeGrammarStableEveryFrame=true --check stylePreserved=true --check pixelArtStyle=true --check cleanupReadyFlatChroma=true --check creativeStateReadability=true --check themeNativeStateCues=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --check identityCleanupAndAnatomyOverrideStateRead=true --notes "Preserves the reference identity, every-frame eye grammar, flat cleanup-ready chroma, and Codex-style pixel art; every used frame was reviewed; states read clearly through mascot-native cues; enhancers are native/integrated; no new anatomy appears."
```

   Good state read is not enough for a production pass. If identity, eye grammar, cleanup readiness, pixel-art treatment, or anatomy regresses, fail the art-direction review even when the animation idea is appealing.

22. Run manifest validation with the chatbot profile before finishing. Strict validation must fail on assembly warnings, completed base jobs missing `base_style_analysis`/`base_style_strict_blocking_warning_codes`, base-source cleanup/style blockers, completed generated row jobs missing `row_source_style_analysis`/`row_source_style_strict_blocking_warning_codes`, row-source cleanup blockers, missing readability QA, missing quality report, missing anatomy review, missing state-performance review, missing eye-grammar review, missing art-direction review, malformed state clarity metadata, cropped sprites, non-transparent unused cells, quality warnings, or any remaining key-colored outline halo pixels:

```bash
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review --require-art-direction-review --max-outline-halo-pixels 0
```

23. Create the production-readiness report. This summarizes source audit blockers, validation errors, quality status, missing manual reviews, stale visual QA evidence, and stale fallback handoffs into one final gate. It should say `productionReady: true` only after the strict source cleanup, validation, and visual review evidence all pass. Manual visual reviews must be newer than the manifest, atlas, `qa/contact-sheet.png`, `qa/cutout-check.png`, `qa/state-readability-check.png`, `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, and `qa/previews/` files that were used for acceptance. Fallback handoffs must be newer than the current manifest, current imagegen-jobs.json, current row source, and current fallback prompt so a repair command cannot preserve or repair stale evidence:

```bash
python scripts/create_companion_production_readiness_report.py --manifest /path/to/run/manifest.json --json-out /path/to/run/qa/production-readiness-report.json
```

24. Generate the React component only after visual QA, strict validation, and the production-readiness report pass.

When the mascot has side-specific props, text, emblems, handed items, or asymmetric lighting, generate left/right directional states separately instead of mirroring.

## Subagent Row Generation

After the base job has been recorded and `references/canonical-base.png` exists, full companion row-strip generation should follow the HatchPet-style parent/subagent boundary whenever subagents are authorized for the session. The parent may generate and record the base, but row jobs are independent after the base and are eligible for subagent generation. If the user or environment requires explicit authorization before subagents, get that authorization before spawning them.

The parent agent must own manifest writes, result recording, atlas assembly, QA, validation, and packaging. Subagents may generate or inspect row candidates only; they must not edit `imagegen-jobs.json`, copy files into `generated/`, run `record_companion_imagegen_result.py`, assemble atlases, create final QA acceptance records, validate the manifest, or package React assets. This keeps provenance and acceptance centralized.

Use `imagegen-jobs.json` as the delegation source of truth. Row jobs marked `subagent_eligible: true` and `generation_owner: "subagent-when-authorized"` may be delegated only after their dependencies are complete. The job's `subagent_handoff` records the expected return fields, forbidden actions, and visual checks. The base job remains parent-owned and is not subagent-eligible.

Delegate one state row per subagent unless the user has explicitly requested a different batching strategy. Give the subagent the row id, prompt file path, full prompt text or instruction to read that exact prompt file, and every input image listed for the job with role labels. Include the original references, canonical base, generated base, row layout guide, and any accepted row images listed by the job. Tell the subagent to use `$imagegen` only and to avoid local drawing, tiling, compositing, SVG, canvas, CSS, or deterministic row synthesis.

Before returning, each subagent must visually check:

- exact requested frame count
- same mascot identity as the canonical base
- recordable cleanup-ready background: true transparency, or exact flat chroma key with no visible falloff, vignette, studio lighting, texture, darker/lighter key-color variation, shadow, glow, or anti-aliased matte
- complete, separated, unclipped poses
- source eye grammar, palette, appendage count, and prop count preserved; no white-sclera/crescent eye swaps, mismatched highlights, or one-frame eye-style changes
- coherent state story that does not drift into a neighboring state such as thinking reading as sleepy/confused, listening reading as thinking/surprised, error reverting into happy/answering, or confused becoming sad/error
- no forbidden detached effects, random symbols, guide marks, text, or slot-crossing artifacts

The subagent QA note should be blunt. A row can be visually promising and still not recordable; report that honestly so the parent can write a candidate rejection report or escalate to the true-transparency fallback rather than repeatedly prompt-churning the same failure.

Return only:

```text
selected_source=/absolute/path/to/$CODEX_HOME/generated_images/.../ig_*.png
qa_note=<one sentence>
```

The parent records the selected source with `record_companion_imagegen_result.py --strict-row-style`, then runs assembly, QA, validation, and readiness checks.

No silent sequential fallback: if subagents are expected for a full row-generation pass but cannot be used because the tool environment blocks them, the user has not authorized them, or the user explicitly disallowed them, stop before row generation and ask for direction. Continue sequentially only when the user explicitly chooses a sequential run. A compact one-row repair or audition may stay parent-run when the user requested that narrow scope.

## Repair Workflow

If QA, validation, or visual review fails, repair the smallest failing scope: the failed state row, not the whole companion pack. Keep the accepted canonical base and any accepted rows as grounding inputs unless the failure proves the base is not production-grade.

For row repairs, reuse the existing run folder, `imagegen-jobs.json`, canonical base, original references, contact sheet, readability sheet, quality report, and exact failure note. Generate a replacement row with `$imagegen`, inspect it visually, then record it with `record_companion_imagegen_result.py` only if it improves the failed issue without regressing identity, scale, eye grammar, pixel-art style, frame count, chroma key, or state readability.

When several replacement candidates are visually inspected and rejected, write a candidate rejection report instead of relying on memory or prompt-churn notes. The report should name each source image, hash it, copy over deterministic source warnings, list the visual blockers, mark `recorded: false`, and preserve the current recorded row as the row to keep for now. This is non-mutating QA evidence: it does not copy files, assemble rows, mark jobs complete, or edit `imagegen-jobs.json`.

For base failures, regenerate or replace the base before generating new rows. Do not accept rows that merely compensate for a weak base by changing colors, anatomy, eye style, outline weight, body scale, or signature props.

## Secondary Image Generation Fallback

This skill does not define a separate direct Image API fallback script. Normal companion creation should delegate visual generation to `$imagegen`, because `$imagegen` owns the built-in-first image generation policy and its own fallback behavior.

If the installed `$imagegen` skill is unavailable, blocked, or cannot accept the necessary references, stop and explain the blocker. Continue only when the user provides finished integrated sprite art or explicitly chooses another generation path.

If built-in `$imagegen` can create a visually good row but repeatedly fails strict source cleanup (`non_uniform_chroma_key_background` or `fake_checkerboard_transparency_background`), treat that as a generation-path blocker, not a reason to weaken validation. Ask the user whether to use `$imagegen`'s true-transparency CLI fallback. That fallback requires explicit user confirmation and a configured `OPENAI_API_KEY`; do not silently switch to it and do not substitute a local background-normalized source for production provenance.

## Visual Rules

Prefer sprite-readable animation over decorative effects.

- Production rows must look like native pixel-art sprites: visible pixel steps, crisp clusters, limited palette, flat cel shading, thick readable outline, and consistent pixel density across the mascot and enhancer.
- Reject smooth illustration, glossy app-icon rendering, painterly gradients, 3D material shading, high-detail antialiasing, vector-flat symbols, or CSS-scaled smooth art. Regenerate from the reference as Codex-style pixel art instead of trying to fix it after assembly.
- Keep poses fully inside each frame with safe padding.
- Use every listed frame as a meaningful pose or in-between.
- Keep props attached to, held by, or clearly anchored near the mascot.
- Avoid shadows, glows, blur, motion streaks, speed lines, action rays, sound rays, emphasis strokes, wave lines, alert marks, cartoon motion marks, dust, loose sparkles, detached punctuation, UI panels, scenery, and text unless the user explicitly requests a website-only effect and the atlas extraction can preserve it.
- Follow HatchPet-style sprite artifact rules: pose, expression, and silhouette carry the state first. Effects are allowed only when they are state-relevant, opaque, hard-edged, pixel-style, inside the same frame slot, and source-bound to the mascot silhouette, mouth edge, hand, tool, worn prop, or state source. Near-head thought cues may use proximity or a tiny separated tail dot instead of touching when overlap would merge into the mascot core; all cues must stay tiny, close, and secondary to the mascot.
- For `pose-only`, show `thinking` and `answering` through head tilt, eye movement, hand/prop pose, blink, mouth shapes, and body motion. If the user explicitly requested `working`, use the same performance-first approach.
- For `semantic-enhancers`, add one small attached, touching, overlapping, or otherwise tightly anchored enhancer only when ambiguous states would not read through acting alone. Examples include a mouth-tailed voice pip, a near-head thought cue, a body-surface processing mark, a hard-edged active-end bloom around an existing prop tip, listening rings, or a small success/error charm. The enhancer must match the mascot's theme and never become a separate competing component.
- Use a semantic ladder, not a symbol-first shortcut: first make the face, eyes, mouth, posture, timing, and original appendages perform the state; next use existing identity props or appendages if they can do the action; only then add a small attached or tightly anchored effect. A motif-native effect that does not read as the state is still a failure.
- Semantic cues must come from the mascot's visual language and still communicate the state. Reject generic symbols, universal UI shortcuts, and motif-native marks that look pretty but do not convey the intended behavior.
- For `thinking`, use a visibly expressive thought/processing cue when acting alone is too subtle: one compact thought bubble, puff, idea orb, mascot-native processing aura, or other source-bound cue should begin close to the inferred thought-cue source, using overlap or touch only if it will not merge into the mascot core, grow from small to slightly larger to medium, then shrink back down before the loop settles. Any later drift must remain tiny and visually connected to the source. Medium is the maximum thought cue size; it must stay secondary to the mascot, never larger than about one-quarter of the mascot body width, and must not become a second head/body-sized orb. At the idea peak, the primary cue element is only slightly larger, never oversized, and do not enlarge the cue to prove the idea landed. When the chosen cue uses separated elements, they must form a stable source-to-peak trail: the smallest element stays closest to the inferred source, intermediate elements continue the same upward/outward path, and the largest/clearest element appears only at the idea-lands peak. Do not let intermediate cue elements drift downward, reverse direction, jump sideways, or reorder the trail. Preserve the accepted cue vocabulary across the row; puff-specific shape rules apply only when the current cue is puff-based. The cue should move through adjacent frames and should not pop in, jump upward into a giant peak, or drop out abruptly at the loop. Reject rows that morph from bubble to data cloud to lightbulb/icon/rays. The row should show a real frame-by-frame thinking arc, not the same cue pasted into every frame. Default `thinking` also covers tool/retrieval/backend waiting.
- Do not freeze expressive appendages just to avoid anatomy mistakes. Existing fins, paws, sleeves, mitts, tentacles, wings, hands, or other visible appendages may move, brace props, gesture, or settle when that action matches the source character and the appendage's recorded affordances. Face-touch is a separate opt-in action that requires an explicit `requiredAffordances` entry and a successful visual audition. The prompt must name the exact existing appendages, include any required affordances, and forbid extra copies, new fingers, detached mitts, duplicated sleeves, or changed appendage count.
- For pointing, presenting, held-prop, work-prop, or face-touch gestures, assign roles to every original appendage across the whole row. In `thinking`, face-touch is allowed when it looks polished, connected to the original appendage, character-native, and keeps the expression readable; reject any frame where a state cue, clothing edge, appendage, or accessory reads as a third hand/arm, detached mitten, hidden expression, or lower-face patch.
- If a simple appendage gesture makes a fin, sleeve, paw, tentacle, or mitt-like limb read as a new hand, fingered mitten, or third limb, regenerate with safer acting: keep appendages side-attached, let them tilt or tuck only slightly, and carry the state through eyes, mouth, body tilt, blink timing, and the anchored enhancer instead.
- If a simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that could be read as a new appendage, reject the row even when the appendage count looks correct at the sides. Regenerate with plain body-surface shading and keep semantic effects clearly near-head, worn, aura-like, or otherwise distinct from the appendages.
- Production enhancers must match the mascot's exact pixel-sprite rendering style: same line weight, pixel grid, palette, lighting direction, flat shading, edge treatment, pixel density, and occlusion with hands/clothing. Do not ship hand-drawn/vector overlays on top of generated mascot frames unless the user explicitly asked for a prototype.
- Do not let a prop make the state read correctly while the mascot itself becomes less expressive, less polished, or less like the source reference.
- If the user explicitly requests optional `working`, the row must read as active work, not anger, decoration, panting, sleeping, talking, or tired exhaling. Make the mascot perform a concrete before/during/after action through busy-friendly face, gaze, body timing, original appendages, existing identity props, or one compact source-bound cue. Use only anatomy and prop affordances recorded from the reference; no invented hands, grip anatomy, duplicate props, text-like surfaces, generic UI panels, detached targets, or cue motion that replaces mascot acting. Keep detailed `working` prop choices and anatomy guard notes in `references/state-enhancers.md`, `qa/state-cue-plan.json`, and manifest metadata rather than bloating the row prompt.
- For `answering`, prefer mouth shapes, presenting gestures, and a conversational body rhythm. The row should look like engaged talking or streaming, not tired panting or exhaling. Prompt a clear mouth cycle such as closed smile -> small open -> wider open -> syllable hold -> smile, with lively eyes and a quick speaking blink. Speech pips, sound ticks, tiny rings, breath marks, or voice pixels are optional; when used, they should support the speaking impression, touch or overlap the mouth/lip edge or begin within 1-2 pixels of it, and form a short 2-3 frame outward trail rather than a single isolated speck. Omit the cue when it cannot stay clearly attached. Reject cues that read as thought bubbles, random orbs, chat panels, detached round bubbles, cheek marks, face markings, or detached flecks. Do not reject a row solely because a tiny cue is not geometrically perfect when the mascot already clearly reads as talking.
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
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png --strict-base-style
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png --strict-row-style
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --no-equal-fallback
python scripts/stitch_row_parts.py --parts /path/to/part-a.png /path/to/part-b.png --out /path/to/run/row-strips/state.png
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
python scripts/create_anatomy_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-anatomy "Stable body core, exact appendage count, appendage placement/anchors, allowed motion/interactors, and forbidden extra anatomy from the reference audit." --expected-identity-props "Expected must-keep prop/accessory continuity." --check frameByFrameAnatomyReviewed=true --check appendageCountStable=true --check noExtraAppendages=true --check noDuplicatedAppendages=true --check identityPropsStable=true --check stateCuesNotMisreadAsAnatomy=true --check contactAndOverlapBelievable=true --notes "Frame-by-frame anatomy review passed."
python scripts/create_state_performance_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-state-read thinking="Expressive planning/processing with a readable thought cue or body/face acting; not idle status dots." --expected-state-read answering="Engaged talking/streaming through mouth shapes, eye engagement, and optional supporting voice cues; not tired panting or exhale clouds." --check frameByFrameStateReadReviewed=true --check intendedStateReadable=true --check noWrongStateRead=true --check expressionMatchesState=true --check cueMotionMatchesState=true --check coherentStateStoryArc=true --check mascotActingVariesAcrossFrames=true --check noTiredPantingUnlessStateRequiresIt=true --check noOffVibeGenericCue=true --notes "Frame-by-frame state-performance review passed with coherent story arcs and mascot acting variation."
python scripts/create_eye_grammar_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --expected-eye-grammar "Expected source eye count, shape, fill/pupil color, highlights, placement, and blink style." --check frameByFrameEyeGrammarReviewed=true --check eyeCountStable=true --check eyeShapeStable=true --check eyeFillAndHighlightStable=true --check eyePlacementStable=true --check noWhiteScleraOrCrescentSwap=true --check noMismatchedOrSymbolEyes=true --check blinkStyleMatchesSource=true --notes "Frame-by-frame eye grammar review passed."
python scripts/create_art_direction_review.py --manifest /path/to/run/manifest.json --status pass --production-use --review-all-frames --generation-method imagegen-integrated-row-art --source-reference /path/to/original-reference.png --check referenceQualityMaintained=true --check identityPreserved=true --check eyeGrammarPreserved=true --check eyeGrammarStableEveryFrame=true --check stylePreserved=true --check pixelArtStyle=true --check cleanupReadyFlatChroma=true --check creativeStateReadability=true --check themeNativeStateCues=true --check nativeEnhancers=true --check integratedEnhancers=true --check anatomyPreserved=true --check noExtraAnatomy=true --check believableOcclusion=true --check noPrototypeFlattening=true --check identityCleanupAndAnatomyOverrideStateRead=true --notes "Every used frame passed art-direction review."
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile audition --strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review --require-art-direction-review
python scripts/create_companion_candidate_rejection_report.py --run-dir /path/to/run --job-id thinking --candidates-json /path/to/rejected-candidates.json
python scripts/create_imagegen_cli_fallback_handoff.py --run-dir /path/to/run --job-id thinking --source /path/to/current-recorded-row-or-rejected-candidate.png --out /path/to/output.png --write-default-prompt --allow-rejected-candidate-source --json-out /path/to/run/qa/thinking-cli-fallback-handoff.json
python scripts/create_companion_production_readiness_report.py --manifest /path/to/run/manifest.json --json-out /path/to/run/qa/production-readiness-report.json
python scripts/generate_react_component.py --manifest /path/to/manifest.json --out-dir /path/to/react
```

If the system `python` cannot import Pillow/PIL, use the Codex bundled workspace runtime instead: call `load_workspace_dependencies`, then run the same scripts with the returned Python executable.

`prepare_companion_run.py` creates the run folder, `companion_request.json`, `imagegen-jobs.json`, `manifest.json`, copied references, `references/layout-guides/<state>.png`, `prompts/base.md`, `prompts/<state>.md`, `prompts/rows/<state>.md`, and `qa/state-cue-plan.json`. It does not infer pixels or draw anything; it gives `$imagegen` concise, hatch-pet-style row prompts that say what the state should read as, how the mascot should act first, when a visual aid is allowed, and what to reject.

`companion_job_status.py` reads `imagegen-jobs.json` and shows ready and blocked `$imagegen` jobs. The base job is ready first; row jobs are blocked until the base is recorded.

`record_companion_imagegen_result.py` records the selected `$imagegen` source for a job, verifies dependencies and required grounding images, copies the source to the expected run output path, stores hashes/metadata/provenance, and creates `references/canonical-base.png` when recording the base job. It reads the run chroma key from `companion_request.json` or `manifest.style.chromaKey` for source-style checks. Use `--strict-base-style` for production base recording so the script blocks non-flat chroma-key backgrounds and smooth/glossy/over-detailed foreground palettes before row jobs become ready. Use `--strict-row-style` for production row recording so fake checkerboard transparency, non-flat chroma-key backgrounds, and missing foreground sprites are blocked before assembly. Normal built-in outputs should use the built-in `$CODEX_HOME/generated_images/.../ig_*.png` source path. If the built-in output is visually accepted but needs the default `$imagegen` transparent workflow, run the installed `remove_chroma_key.py` helper, keep the cleaned alpha PNG outside the companion run directory, and record it with `--source-provenance built-in-imagegen-chroma-cleanup --chroma-cleanup-source <original-$CODEX_HOME/generated_images/.../ig_*.png>`. Use `--source-provenance imagegen-cli-fallback` only for explicit approved `$imagegen` CLI fallback outputs, and include the required CLI fallback metadata flags so the manifest records `cli_fallback.approved`, model, transparent background, PNG output format, and prompt file. Otherwise use explicit user/artist integrated art provenance. Use it instead of manually copying files or editing `imagegen-jobs.json`. For finished user/artist row art, pass `--source-provenance user-provided-integrated-row-art` or `--source-provenance artist-provided-integrated-row-art`.

`audit_companion_imagegen_sources.py` audits completed base and row job `source_path` images without copying files, recording jobs, or mutating `imagegen-jobs.json`. Use it on older or audition runs when you need concrete source-style evidence before deciding whether to re-record, regenerate, or escalate to the true-transparency fallback. It reports the same strict base blockers as `record_companion_imagegen_result.py --strict-base-style`, plus the same strict row-source blockers as `--strict-row-style`, including non-flat chroma-key backgrounds, fake checkerboard transparency, and missing foreground sprites.

`create_companion_candidate_rejection_report.py` writes `qa/<job-id>-candidate-rejection-report.json` for generated row candidates that were inspected and rejected. Use it when a candidate has an appealing story read but fails eye grammar, flat chroma cleanup, anatomy, scale, or native pixel-art review, or when repeated built-in attempts show the same failure pattern. It reads a small candidates JSON file, analyzes each source with the same strict row-source checks as recording, stores hashes and visual blockers, marks every candidate `recorded: false`, and leaves `imagegen-jobs.json` untouched. If the rejection count reaches the configured threshold, the report recommends stopping the same built-in prompt path and preserving the current recorded row for a narrow source repair or explicit true-transparency fallback.

`create_imagegen_cli_fallback_handoff.py` writes reproducible dry-run, real-run, and record commands for the explicit `$imagegen` true-transparency CLI fallback. Use it only after the built-in path has produced a visually promising row that repeatedly fails strict source cleanup and the user has approved CLI/API fallback. It does not call the API; it reads `imagegen-jobs.json`, uses the row's grounding images, puts the repair source image first, records a narrow source repair intent, records `requiredEnvironment: ["OPENAI_API_KEY"]` plus `requiresExplicitUserApproval: true`, and includes the required `imagegen-cli-fallback` provenance flags for later recording. By default the repair source must match the current recorded row `source_path`. When the promising source is a strict-rejected candidate that must not be recorded, pass `--allow-rejected-candidate-source`; the handoff records `sourceMode: "rejected-candidate"` and is a non-mutating repair plan only. Do not record the rejected candidate or copy it into `generated/`; record only the inspected CLI fallback output if it passes strict row style. It can write a compact generic story-preserving repair prompt with `--write-default-prompt`; use that when the row should preserve its current story/scale and repair only transparent cleanup, eye grammar, or visual-review blockers. Prefer this generated prompt over hand-written mascot-specific fallback prompts unless the user has supplied exact art-direction language. Generated prompt handoffs record `defaultPromptWritten: true` and `repairPromptSource: "generic-story-preserving-default"` so the production-readiness report can distinguish the generic repair path from an existing or user-provided fallback prompt. It also records `promptRepairContract` evidence proving that the fallback prompt preserves the current story, scale, accepted expression/blink/mouth/appendage performance, and accepted cue vocabulary while repairing only named blockers and avoiding redesign. The contract is cue-agnostic: it should preserve accepted cue timing and compactness without forcing a particular mascot, prop, or visual-aid vocabulary; puff-specific wording belongs only when the current accepted row actually uses puffs. If the user explicitly approves the fallback, regenerate the handoff with `--user-approved --approval-note "<short approval context>"` so it records `explicitUserApprovalReceived: true` and `approvalNote`; otherwise leave it unapproved. The fallback should preserve the current row story and scale while fixing cleanup, eye grammar, or visual-review blockers; it is not a redesign path.

`assemble_companion_atlas.py` reads row strips named `<state>.png`, updates the manifest atlas fields, extracts clean per-frame PNGs, writes `atlas.webp` and `atlas.png`, creates `qa/contact-sheet.png`, creates `qa/cutout-check.png`, creates `qa/previews/*.gif`, and writes `qa/assembly-report.json`. It uses the chroma key stored in the run manifest/request unless `--key-color` is explicitly provided, matching HatchPet's discipline of choosing a safe key per reference instead of assuming one fixed background color. It uses foreground-run center detection rather than naive equal-width slicing, which prevents common generated-strip issues such as variable frame spacing, clipped wide gestures, and neighboring-frame slivers. In `--extraction-mode component`, it locks rows to a shared body/core target, using `idle` by default, so detached bubbles, sound rings, held-prop blooms, or other semantic enhancers do not decide the mascot's body scale. If an over-tall cue no longer fits the cell after body scale is preserved, strict validation should report the cell-edge contact; treat that as a cue/headroom problem to fix by regenerating a lower/shorter cue or choosing a taller cell, not as permission to silently shrink the mascot. Use `--allow-edge-clearance-scale` only as an explicit fallback when a tiny uniform row shrink is preferable to regenerating or increasing headroom. It also runs the outline improver: transparent RGB clearing, key spill removal, key-colored edge cleanup, spill-color replacement, and premultiplied resizing so invisible chroma-key pixels do not bleed into sprite edges. The assembly report records `outlineImprover.totalOutlineHaloPixels`; production runs should keep this at `0`. If it reports `equal-fallback` or outline warnings, review that state manually and prefer regenerating the row if the contact sheet looks uneven.

Use `--extraction-mode component` when row sources contain detached but integrated state effects, such as thought orbs, sound rings, or speech wisps. It groups each mascot body with nearby components instead of slicing through neighboring poses, centers on the body/core rather than side props, and records `bodyFitTarget` plus per-state `fitScaleMode` in `qa/assembly-report.json`. Use `--extraction-mode equal` only when the row sources were intentionally generated as exact equal-spaced horizontal strips and foreground-center extraction visibly splits or merges close frames. These are explicit production choices, not silent fallbacks: accept them only when the contact sheet shows no chopped frames, neighboring slivers, body-scale drift, or lost props.

`create_state_readability_sheet.py` writes `qa/state-readability-check.png`, showing enhanced states at 64, 96, and 128 px. Use it before validation for `semantic-enhancers` packs.

`analyze_companion_quality.py` writes `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png`. It flags near-duplicate frames, low average motion, body jitter, large foreground area jumps, detached fragments, core silhouette scale drift, full-row core scale range over the production default of `8%`, cross-state median core scale mismatch, core center drift, missing separate enhancers, and drifting semantic anchors. If a visually accepted near-head cue intentionally overlaps or sits partly behind an identity accessory or silhouette feature, record `enhancer.componentPolicy: "overlap-ok"` so the analyzer keeps checking motion/body stability without requiring a separate alpha component. This is not a substitute for visual judgment, but it catches the common symptoms of wrong cuts, cropped/slivered frames, unstable body size, unstable props, pasted-on effects, and fake smoothness.

`create_anatomy_review.py` writes `qa/anatomy-review.png` and `qa/anatomy-review.json`. The PNG enlarges and numbers every used state frame for appendage and prop counting; the JSON records that every frame was reviewed against the expected anatomy and identity props. The `expectedAnatomy` text must specifically describe body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy. This is a required visual gate for detailed mascots, risky face-touch/held-prop states, and production packs because numeric QA cannot reliably know whether a clothing edge, thought puff, hand, fin, or simple appendage has become extra anatomy.

`create_state_performance_review.py` writes `qa/state-performance-review.png` and `qa/state-performance-review.json`. The PNG enlarges and numbers every used state frame for state-read review; the JSON records that every frame was reviewed against the intended state performance. This is a required visual gate for high-visibility chatbot states because numeric QA cannot reliably know whether `thinking` reads as idle/status dots instead of planning/processing, whether `answering` reads as tired exhaling, whether a mascot-native cue is pretty but semantically wrong, whether the row has a coherent story arc, or whether visible motion lives only in the cue while the mascot stays stale. Production reviews must set `coherentStateStoryArc=true` and `mascotActingVariesAcrossFrames=true`. If optional `working` is present, review it with the same frame-by-frame standard.

`create_eye_grammar_review.py` writes `qa/eye-grammar-review.png` and `qa/eye-grammar-review.json`. The PNG enlarges and numbers every used state frame for source-eye review; the JSON records that every frame preserved the canonical eye count, shape, fill/highlight logic, placement, and blink style. `expectedEyeGrammar` must be specific enough to review against: name the source eye count/shape, fill or pupil color, highlight/catchlight logic, spacing/placement, and blink style. This is a required visual gate for high-visibility chatbot states because a row can have an excellent thinking/answering story while still becoming a different mascot through white-sclera swaps, crescent side-glances, mismatched highlights, hollow eyes, symbol eyes, or off-source blinks.

`create_art_direction_review.py` writes `qa/art-direction-review.json`. Use it as a production review record after visual inspection. A production pass requires `--review-all-frames` so the review records every state frame inspected for identity, eye grammar, cleanup readiness, anatomy, and source quality. It should fail, not pass, when a result is technically clean but looks worse, less creative, over-simplified, or prototype-like compared with the source.

`validate_companion_manifest.py` verifies manifest shape, state frame counts, durations, atlas path, dimensions, alpha channel, empty used cells, non-transparent unused cells, edge-touching/cropped sprites, residual key-colored outline halos, assembly-report warnings, recorded base source-style blockers, recorded row source-style blockers, missing readability QA, quality-report warnings, risky enhancer metadata, anatomy-guard specificity, anatomy-contract shape, appendage affordance mismatches, anatomy review blockers, state-performance review blockers, eye-grammar review blockers, art-direction review blockers, and optional state clarity, rendering-style, and visual-language metadata. For halo checks it uses the assembly report key first, then the run manifest/request chroma key, matching the assembler. The `audition` profile is for strict one-row or partial-pack tests and does not warn about missing `idle` or other chatbot states, but high-visibility audition rows still warn when `thinking`, `working`, or `answering` lacks frame-by-frame state-performance review or eye review, and visible/ambiguous appendage mascots also warn when anatomy review is missing. The `chatbot` profile warns when core website states are missing or when important states have too few frames for smooth motion. Use `--strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review --require-art-direction-review --max-outline-halo-pixels 0` for newly generated production packs so warnings, missing clarity metadata, missing rendering-style metadata, missing QA, quality issues, base/row source-style blockers, anatomy-guard issues, anatomy-contract warnings, affordance warnings, anatomy-review issues, state-performance issues, eye-grammar issues, art-direction issues, and outline halo pixels block acceptance. Use `--require-visual-language` only for targeted auditions where you specifically want to fail missing vibe-fit metadata.

`create_companion_production_readiness_report.py` writes `qa/production-readiness-report.json`. Use it after source audit, strict validation, quality analysis, and manual reviews to combine final acceptance evidence into one production-readiness report. It blocks non-flat source backgrounds, missing row-source evidence, unresolved strict validation warnings, missing or failing visual reviews, missing required manual-review checks, quality failures, stale QA evidence, stale manual visual reviews older than the manifest, atlas, `qa/contact-sheet.png`, `qa/cutout-check.png`, `qa/state-readability-check.png`, `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, or `qa/previews/` files, and stale fallback handoffs older than the current manifest, current imagegen-jobs.json, current row source, or current fallback prompt; it also summarizes any fallback repair intent, requiredEnvironment, approval requirement, `requiredEnvironmentStatus`, `explicitUserApprovalReceived`, `approvalNote`, `executionBlockedBy`, `promptRepairContractOk`, missing prompt-repair contract checks, and candidate rejection reports so the next generation step remains a narrow repair, not a redesign. It records `fallbackRepairReady`, `blockedHandoffCount`, and `runnableHandoffCount` separately from `productionReady` so a valid repair plan is not mistaken for a runnable repair command. Candidate rejection summaries do not block production by themselves, but they keep repeated failed built-in attempts visible and mark the evidence stale when the recorded row source changes. Fallback handoff summaries are preflight evidence only: missing `OPENAI_API_KEY`, missing explicit approval, stale fallback handoffs, or a failed `promptRepairContract` appears in `executionBlockedBy` and must be resolved before running real CLI/API generation. Its verdict repeats the HatchPet-style rule that good state read is not enough if identity, cleanup, source evidence, or anatomy/eye review is missing.

`generate_react_component.py` emits a TypeScript React component that reads the manifest and animates by per-frame durations.

## Rules

- Keep `$imagegen` as the primary visual generation layer.
- Keep reference images attached for `$imagegen` whenever the chosen path supports references.
- Attach the row's `references/layout-guides/<state>.png` image to every state-row job as a layout-only guide, and do not accept outputs that copy guide pixels.
- Generate every normal visual job with `$imagegen`: base plus one grounded row strip per requested state.
- Treat only the base job as eligible for prompt-only generation; every row job must attach its listed grounding images after the base is recorded.
- Never substitute locally drawn, tiled, transformed, mirrored, or code-generated row strips for missing `$imagegen` outputs.
- Never manually mutate `imagegen-jobs.json` to claim a visual job completed.
- Do not rely on generated images for exact atlas geometry; use this skill's deterministic scripts.
- Use the chroma key stored in `companion_request.json` or `manifest.json`; do not force a fixed green screen.
- Keep the mascot's silhouette, face, eye grammar, materials, palette, props, appendage count, and pixel-art rendering consistent across all rows.
- Enforce the transparency and effects rules above in every base, row, and repair prompt.
- Treat visual identity drift as a blocker even when deterministic geometry QA passes.
- Treat a contact sheet that shows cropped references, repeated tiles, white cell backgrounds, non-sprite fragments, chopped props, or neighboring-frame slivers as failed.
- Treat forbidden detached effects, chroma-key-adjacent artifacts, shadows, glows, smears, dust, landing marks, wave marks, speed lines, motion trails, and random symbols as failed rows.
- Treat `qa/quality-report.json`, anatomy review, state-performance review, eye-grammar review, art-direction review, and strict validation warnings as blockers unless the user explicitly approves a documented exception.

## Acceptance Criteria

- `manifest.json` lists every state, row, frame count, frame size, durations, and atlas path.
- `imagegen-jobs.json` exists, records `base` plus one row job per generated state, and shows selected-source provenance for completed jobs.
- The completed `base` job records `base_style_analysis` and `base_style_strict_blocking_warning_codes: []`; production validation fails missing evidence or blockers because the canonical base defines eye grammar, cleanup assumptions, palette, and row identity.
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
- `qa/anatomy-review.png` and `qa/anatomy-review.json` exist for production packs; the review has `status: "pass"`, `productionUse: true`, every used frame of every state listed in `reviewedFrames`, specific `expectedAnatomy` describing body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy, plus true checks for frame-by-frame review, appendage count stability, no extra appendages, no duplicated appendages, stable identity props, state cues not misread as anatomy, and believable contact/overlap.
- `qa/state-performance-review.png` and `qa/state-performance-review.json` exist for production packs; the review has `status: "pass"`, `productionUse: true`, every used frame of every state listed in `reviewedFrames`, non-empty `expectedStateReads` for every state, and true checks for frame-by-frame state-read review, intended state readability, no wrong-state read, matching expression, matching cue motion, coherent state story arc, mascot acting variation across frames, no tired/panting read unless the state requires it, and no off-vibe generic cue.
- `qa/eye-grammar-review.png` and `qa/eye-grammar-review.json` exist for production packs; the review has `status: "pass"`, `productionUse: true`, every used frame of every state listed in `reviewedFrames`, specific `expectedEyeGrammar` describing source eye count/shape, fill or pupil color, highlight/catchlight logic, spacing/placement, and blink style, plus true checks for frame-by-frame eye review, stable eye count, stable shape, stable fill/highlights, stable placement, no white-sclera/crescent swaps, no mismatched/symbol eyes, and source-matched blink style.
- `qa/art-direction-review.json` exists, has `status: "pass"`, has `productionUse: true`, records every used frame of every state in `reviewedFrames`, records the original `sourceReference`, and records that reference quality, identity, eye grammar, every-frame eye stability, style, pixel-art style, flat cleanup-ready chroma, creative state readability, native enhancers, integrated enhancers, anatomy preservation, no extra anatomy, believable occlusion, no prototype flattening, and identity/cleanup/anatomy overriding state-read all passed.
- `qa/production-readiness-report.json` exists and records `productionReady: true`; it must have no blockers for source cleanup, row-source evidence, quality, manual reviews, validation, stale QA evidence, stale manual visual reviews, or fallback handoff freshness.
- The final art is not accepted if its production method is deterministic compositing, vector overlays, manual shape overlays, or another prototype-only path.
- Chatbot profile validation passes in strict mode, or every warning is explicitly reviewed and accepted.
- `manifest.json` records `style.stateClarity` as `pose-only` or `semantic-enhancers` for newly generated packs.
- `manifest.json` records `style.renderingStyle` as `codex-pixel-art` for newly generated packs.
- The prompt plan or manifest records the inferred mascot vibe and why each enhanced state cue belongs to that mascot. This can use `style.visualLanguage` and `enhancer.visualLanguageFit`, but visual quality matters more than metadata.
- State rows translate the reference into Codex-style pixel art; reject smooth illustration, glossy rendering, painterly gradients, 3D shading, high-detail antialiasing, or vector-flat art.
- If `semantic-enhancers` is selected, `thinking`, `listening`, and `answering` include per-state `enhancer` metadata and read clearly at 64, 96, and 128 px. Optional explicitly requested states such as `working` need the same metadata when present.
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
- React component can display `idle`, `thinking`, `answering`, `success`, and `error`.
- The final answer reports asset paths, manifest path, React component path, and QA result.
