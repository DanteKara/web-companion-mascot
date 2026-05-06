# Web Companion Contract

## Manifest Shape

Use this shape for `manifest.json`:

```json
{
  "id": "tridy",
  "displayName": "Tridy",
  "description": "A cheerful chatbot companion.",
  "style": {
    "renderingStyle": "codex-pixel-art",
    "stateClarity": "pose-only"
  },
  "atlas": {
    "path": "atlas.webp",
    "width": 3072,
    "height": 2880,
    "columns": 12,
    "rows": 10,
    "cellWidth": 256,
    "cellHeight": 288
  },
  "states": {
    "idle": {
      "row": 0,
      "frames": 8,
      "durations": [220, 160, 160, 260, 140, 140, 180, 320],
      "loop": true
    }
  }
}
```

All `durations` are milliseconds. `frames` must equal `durations.length`.

## Default Chatbot States

Recommended defaults:

| State | Frames | Purpose |
| --- | ---: | --- |
| idle | 10 | Resting breathing/blink loop |
| greeting | 10 | Chat opens or first visit |
| listening | 10 | User is typing or speaking |
| thinking | 12 | Model is planning before output |
| working | 12 | Tools, retrieval, search, or backend work |
| answering | 12 | Response is streaming |
| success | 10 | Task complete or answer finished |
| error | 10 | Request failed or warning state |
| confused | 10 | Input unclear or needs clarification |
| sleeping | 10 | Inactive, minimized, or offline |

Use fewer rows only when the user asks for a smaller pack. Use more states when the product needs them, but keep the frame size and manifest explicit.

For a higher-FPS feel, prefer 12 columns for the atlas. `thinking`, `working`, and `answering` should get 12 frames by default because users stare at those states while waiting for the chatbot. A cinematic profile can use 14 frames for those waiting states and 12 for the others, but only if the rows remain consistent and pass quality QA. Fewer stronger frames are better than more frames with character drift or invented anatomy.

If image generation cannot reliably produce a full 12+ frame row with the correct number of mascot bodies, generate the row in smaller exact-count chunks such as two 6-frame parts and stitch those generated parts with `scripts/stitch_row_parts.py`. The stitch step may concatenate existing generated art only; it must not create missing frames, draw props, resize sprites, or patch anatomy. The stitched row must pass the same assembly, motion, cutout, readability, semantic-anchor, and visual seam QA as a single generated row.

## Prompt Planning Artifacts

Normal companion runs should start with `scripts/prepare_companion_run.py`. The preparer writes:

```text
run/
  companion_request.json
  imagegen-jobs.json
  manifest.json
  prompts/base.md
  prompts/<state>.md
  prompts/rows/<state>.md
  references/layout-guides/<state>.png
  qa/state-cue-plan.json
```

`qa/state-cue-plan.json` is a planning artifact, not production acceptance. It should record the inferred source vibe, state purpose, acting-first beat, frame-by-frame acting arc, whether a visual aid is allowed, the suggested aid, any no-hand freestanding prop policy, and rejection criteria for each state. Row prompts should use that plan to make the mascot perform the state first through expression, posture, timing, and original appendages, then add a small visual aid only when the state would otherwise be unclear at website size. `thinking` should name a visible small -> medium -> large -> hold -> settle cue arc when a bubble/orb is used. `working` should name a visible notice -> prop/cue wakes up -> sorting/checking/gathering -> progress/result -> settle arc when a work cue is used.

`imagegen-jobs.json` follows the hatch-pet-style base-first contract:

- `base` is the first ready job and may be prompt-only only when no reference exists.
- row jobs depend on `base` and must list grounding input images.
- row jobs include the original references, `references/canonical-base.png`, `generated/base.png`, and the row's layout guide.
- `scripts/record_companion_imagegen_result.py` is the only normal way to mark jobs complete and copy selected `$imagegen` outputs or finished user/artist integrated row art into the run.
- completed jobs should record source path, source provenance, hashes, metadata, and completion time.

After recording `base`, `references/canonical-base.png` must exist and should be treated as the approved identity source for every row. Do not generate row strips without attaching that canonical base and the row layout guide.

The preparer may seed enhanced states with draft metadata such as `"kind": "planned during row generation"`. After final row art is selected, replace that draft metadata with the actual accepted visual aid, for example `"kind": "near-face icy voice pixels"` or `"kind": "body-surface processing glyph"`. Strict validation warns on leftover draft enhancer wording so planning placeholders do not become shipped metadata.

Expression language is part of the identity contract. Preserve the source mascot's normal face grammar when communicating state. A calm, browless, icon-like, plush, or abstract mascot should not gain angry eyebrows, hostile eyes, teeth, sweat, blush, or dramatic emotion marks just to show focus. Use eye direction, blink timing, mouth shape, posture, timing, and approved visual aids first; stronger face marks are acceptable only when the source design already supports them or the state genuinely needs them and the result remains character-appropriate.

Semantic cues are part of the cleanup contract too. A cue that only exists as isolated tiny specks, far-away dots, or ultra-thin marks is fragile: default cleanup may remove it, while loosening cleanup can keep neighboring slivers or force the mascot body to shrink around distant effects. For ambiguous states that need a cue, prefer compact body-surface, rim-touching, attached, close-overlapping, freestanding, or resting artwork that survives default cleanup and reads at 64-96 px.

## Style Metadata

New companion packs should include top-level `style.renderingStyle` and `style.stateClarity` values. Production output from this skill must be Codex-style pixel art:

```json
{
  "style": {
    "renderingStyle": "codex-pixel-art",
    "stateClarity": "pose-only"
  }
}
```

or:

```json
{
  "style": {
    "renderingStyle": "codex-pixel-art",
    "stateClarity": "semantic-enhancers",
    "enhancerTheme": "modern-assistant",
    "visualLanguage": {
      "sourceVibe": "soft round icy companion with a cute face",
      "motifs": ["frost puffs", "snowflake dots", "pale blue rim"],
      "forbiddenGenericCues": ["gears", "circuit boards", "speech panels"],
      "stateCueRules": {
        "working": "Use frost/data flakes or a soft processing aura, not generic tech symbols.",
        "answering": "Use mouth shapes and icy breath puffs, not speech bubbles."
      }
    },
    "anatomyClass": "fins-no-hands",
    "anatomyContract": {
      "source": "reference-audit",
      "bodyCore": "round body",
      "totalAppendages": 2,
      "appendages": [
        {
          "id": "left-fin",
          "kind": "fin",
          "count": 1,
          "placement": "left side",
          "affordances": ["side-bob", "small-wave", "tilt", "brace"]
        },
        {
          "id": "right-fin",
          "kind": "fin",
          "count": 1,
          "placement": "right side",
          "affordances": ["side-bob", "small-wave", "tilt", "brace"]
        }
      ],
      "forbiddenAdditions": ["extra fins", "hands", "fingers", "detached mitts"]
    }
  }
}
```

Allowed `renderingStyle` value:

| Value | Meaning |
| --- | --- |
| `codex-pixel-art` | Codex digital-pet style: compact chibi pixel sprite, visible stepped pixel edges, thick 1-2 px outline, limited palette, flat cel shading, simple expressive face, and crisp hard-edged effects. |

Reject production rows that look like smooth illustration, glossy app-icon art, 3D rendering, painterly gradients, vector-flat clip art, high-detail antialiasing, or realistic material texture. A non-pixel reference should be translated into this pixel-sprite style while preserving identity, silhouette cues, palette family, must-keep markings, and charm.

Allowed `stateClarity` values:

| Value | Meaning |
| --- | --- |
| `pose-only` | States are differentiated with expression, posture, body motion, timing, and existing identity props. |
| `semantic-enhancers` | Ambiguous states may include one small anchored prop or effect that communicates the state. |

When `semantic-enhancers` is used, add an `enhancer` object to states that need semantic clarity:

```json
{
  "thinking": {
    "row": 2,
    "frames": 10,
    "durations": [140, 120, 120, 160, 180, 120, 120, 160, 180, 220],
    "loop": true,
    "enhancer": {
      "kind": "thought-bubble",
      "attachment": "near-head",
      "description": "Small no-text thought bubble anchored near the head.",
      "visualLanguageFit": "Uses the mascot's soft puff motif and pale palette instead of a generic UI icon."
    }
  }
}
```

For newly generated semantic-enhancer packs, the agent should infer a visual-language read from the reference. It can be recorded in the manifest when useful, especially during auditions:

```json
{
  "style": {
    "visualLanguage": {
      "sourceVibe": "soft round icy companion with a cute face and two side fins",
      "motifs": ["frost puffs", "snowflake dots", "icy breath"],
      "forbiddenGenericCues": ["gears", "circuit boards", "speech panels"],
      "stateCueRules": {
        "working": "Use frost/data flakes or a soft processing aura, not generic tech symbols.",
        "answering": "Use mouth shapes and icy breath puffs, not speech bubbles."
      }
    }
  }
}
```

`style.visualLanguage` is optional metadata, not a substitute for visual review. It is useful when a state has been failing because generic symbols or off-vibe props keep appearing. Each enhanced state may include `enhancer.visualLanguageFit`, a short note explaining why the state cue matches the reference vibe. Use `scripts/validate_companion_manifest.py --require-visual-language` only for targeted auditions where missing vibe-fit metadata should fail validation.

Held, touched, near-hand, writing, or appendage-operated work-prop enhancers should also include an `anatomyGuard` so prompts and QA do not invent new limbs:

```json
{
  "working": {
    "row": 4,
    "frames": 12,
    "durations": [120, 120, 120, 120, 140, 120, 120, 120, 140, 120, 120, 180],
    "loop": true,
    "enhancer": {
      "kind": "body-anchored work slate",
      "attachment": "attached",
      "description": "A small theme-native work slate braced against the mascot body.",
      "requiredAffordances": ["grip"],
      "anatomyGuard": {
        "limbPolicy": "no-new-limbs",
        "allowedInteractors": ["left side fin", "right side fin"],
        "forbidden": ["extra hands", "new fingers", "duplicate appendages", "detached mitts"]
      }
    }
  }
}
```

Allowed `enhancer.attachment` values:

```text
held, worn, attached, freestanding, near-head, near-face, near-hand, aura, gesture, body-pose, resting
```

Allowed `style.anatomyClass` values:

```text
hands, paws, fins-no-hands, no-limbs, ambiguous-limbs
```

Set `anatomyClass` when semantic enhancers interact with the mascot body. Existing non-human appendages can support prop or gesture interaction only when the contract says they can: fins, sleeves, tentacles, paws, or mitt-like limbs may hold, brace, tap, point, or touch the face when they are present in the reference, named in `enhancer.anatomyGuard.allowedInteractors`, and backed by matching appendage `affordances`. Strict validation rejects held/near-hand attachments and common typing/writing props for `no-limbs`, but allows `freestanding` or `resting` work props when they animate on their own beside or in front of the mascot and explicitly do not require holding, typing, writing, grip, hands, or fingers. For `fins-no-hands` and `ambiguous-limbs`, strict validation requires anatomy-guard metadata for held or appendage-operated risky props, and visual QA must reject any extra hands, fingers, duplicate fins, cloned sleeves, or invented grip anatomy.

## Reference Anatomy Contract

Before row generation, write a reference anatomy audit and copy it into `style.anatomyContract` whenever anatomy can be misread or a state uses appendages, held props, near-hand props, writing/typing tools, or expressive limb gestures. The contract should describe only what is actually visible in the source reference.

Minimum contract fields:

```json
{
  "style": {
    "renderingStyle": "codex-pixel-art",
    "anatomyClass": "fins-no-hands",
    "anatomyContract": {
      "source": "reference-audit",
      "bodyCore": "small round icy body",
      "totalAppendages": 2,
      "appendages": [
        {
          "id": "left-fin",
          "kind": "fin",
          "count": 1,
          "placement": "left side",
          "affordances": ["side-bob", "small-wave", "tilt", "brace"]
        },
        {
          "id": "right-fin",
          "kind": "fin",
          "count": 1,
          "placement": "right side",
          "affordances": ["side-bob", "small-wave", "tilt", "brace"]
        }
      ],
      "forbiddenAdditions": ["extra fins", "hands", "fingers", "detached mitts"]
    }
  }
}
```

Use exact names from this contract in every risky `enhancer.anatomyGuard.allowedInteractors`. Avoid vague values such as `"existing visible appendages only"`; strict validation warns because vague language is too easy for image models to satisfy by inventing new generic limbs. If the reference has hands, paws, wings, sleeves, tentacles, horns, tails, or no appendages, record those exact parts instead of using fin-specific language.

Appendage `affordances` describe what a visible part can safely do in generated animation. They should come from the source reference and the mascot's design language, not from the desired state alone. Use them to preserve expressive hand acting for mascots that truly have hands while keeping fins, wings, sleeves, mitts, and other simple appendages from being translated into invented hands.

For simple appendages, preserve not only side appendage count but also appendage-like shapes elsewhere on the body. A limb-colored oval, patch, detached blob, or front-body mark can read as an extra fin, paw, sleeve, mitt, or hand. Prompts and visual QA should forbid those shapes unless they are part of the original reference identity.

Common affordances:

| Affordance | Use For | Avoid When |
| --- | --- | --- |
| `side-bob`, `tilt`, `tuck` | Simple fins, wings, ears, tails, body nubs, sleeves, or ornaments that can move near their original side. | Face-touch, gripping, typing, or cross-body acting. |
| `small-wave`, `wave` | Existing appendages that can make a greeting silhouette without extra fingers. | Fine hand poses unless fingers are visible. |
| `point`, `present` | Hands, paws, sleeves, tentacles, or clear arms that can direct attention. | No-limb mascots or ambiguous marks. |
| `face-touch` | Real hands/arms, clear paws, or another appendage whose reference design can touch the chin/cheek without becoming a new hand. | Fins, wings, sleeves, mitts, or ambiguous appendages unless auditioned successfully. |
| `grip`, `brace` | Existing hands/paws/tentacles/sleeves/fins that can visibly hold or brace a chunky prop. | True no-limb mascots or appendages that would need invented fingers. |
| `typing`, `writing`, `fine-finger` | Mascots with visible fingers or a clearly fingered hand design. | Paws, fins, mitts, sleeves, or no-limb bodies. |

For risky state metadata, add `enhancer.requiredAffordances` so validation can compare the state action against `style.anatomyContract.appendages[].affordances`:

```json
{
  "thinking": {
    "enhancer": {
      "kind": "hand-to-chin thought gesture",
      "attachment": "gesture",
      "description": "The left hand touches the chin while a compact thought cue appears near the head.",
      "requiredAffordances": ["face-touch"],
      "anatomyGuard": {
        "limbPolicy": "no-new-limbs",
        "allowedInteractors": ["left hand", "right hand"],
        "forbidden": ["extra hands", "duplicate arms"]
      }
    }
  }
}
```

For `fins-no-hands` and `ambiguous-limbs`, strict validation recommends `style.anatomyContract` when risky enhancer interactions are present. In production strict mode, that warning should block acceptance until the reference appendage count and forbidden additions are explicit.

`thinking`, `working`, `listening`, and `answering` should have `enhancer` metadata when `semantic-enhancers` is selected and those states are present. Metadata cannot prove the pixels are good, but it forces each generated state to carry an explicit QA intention.

## Geometry Guidance

Use `256x288` cells by default for high-quality website companions, especially when the mascot has a detailed outfit, emblem, prop, expressive hands, or readable facial states. Use `192x208` only for smaller packs or very simple mascots.

The atlas assembler should infer frame centers from foreground runs instead of slicing row strips into equal widths. Generated row strips often have slightly variable spacing; naive slicing can leave neighboring-frame slivers or clip wide gestures even when manifest validation passes.

Explicit equal-grid extraction is allowed only when a row source was intentionally generated as an exact equal-spaced horizontal strip and foreground-center extraction visibly mis-splits close frames. Do not use silent equal fallback for production; use the explicit mode and accept it only after contact-sheet QA passes.

Component-body extraction is preferred when a row includes detached but integrated effects, such as thought orbs, sound rings, speech wisps, or attached glints, and foreground-center extraction splits or merges poses. It must fail if it cannot find the expected number of mascot body components.
If a legitimate detached enhancer is large enough to be counted as an extra body component, raise `--body-component-area` and rerun extraction. Do not lower component filtering or accept equal slicing until visual QA proves the effect remains anchored to the correct frame.

Semantic enhancers may require slightly wider safe padding. Do not rely on CSS cropping to hide bubbles, tablets, paper, sound rings, or other state props.

Frame fitting must not make the mascot body resize when a semantic effect grows. Atlas assembly should use a consistent fit scale across all frames in the same state row; otherwise a tall thought bubble or wide prop can shrink that frame's entire mascot even when the generated body was stable. If the largest frame footprint forces the whole row to become too small, increase cell size or regenerate the row with a tighter effect rather than allowing per-frame scaling.

## Motion Design Rules

Do not treat "more frames" as duplicated stills. Every used frame should earn its slot.

- `idle`: slow breathing, 1-2 blink/eye frames, tiny hand/prop settle.
- `greeting`: anticipation, arm/prop rise, peak gesture, return, friendly hold.
- `listening`: attentive lean, blink, eye tracking toward user input, subtle prop/body motion.
- `thinking`: head tilt, eye movement, hand-to-face or prop tilt, blink, small loopable shifts.
- For near-head `thinking` enhancers, prefer a side-origin path: the thought cue begins near one side of the head, drifts slightly outward and upward, holds briefly at the clearest point, then settles. The mascot's eyes and mouth should react to that motion.
- Existing appendages should be allowed to act when they are part of the reference and their recorded affordances support the action: hands can touch the chin, paws can gesture, sleeves can brace a prop, and tentacles can point when the contract says they can. QA should reject extra or duplicated anatomy, not legitimate motion from original appendages. If the acting pose makes a simple appendage look like a new hand, fingered mitten, detached object, or third limb, regenerate with a safer smaller appendage motion and move the acting beat to face, body tilt, blink timing, or the semantic enhancer.
- `working`: faster but controlled movement, prop/hand/body cycles, focused face.
- `answering`: speaking mouth shapes or expressive face/hand beats, loopable cadence.
- `success`: anticipation, bounce or proud pose, cheerful hold, return.
- `error`: recognition, slump or worried expression, attached tear/prop droop, recovery.
- `confused`: squint, tilt, small recoil, uncertain hold, recovery.
- `sleeping`: eyelids, slow breathing, small robe/body settle.

Recommended frame-duration bands:

```text
fast action: 70-120 ms
normal motion: 120-180 ms
readable hold: 200-320 ms
sleep/long idle hold: 320-500 ms
```

Avoid frame durations under 60 ms unless the user explicitly wants very fast motion; they often look jittery in browser timers.

For high-frame-count rows, treat body stability as part of the prompt, not just QA. State prompts should name the body anchor explicitly: same body center, same silhouette size, same top-of-head height, same bottom edge, same appendage count, and only subtle breathing unless the state intentionally uses a large pose. This matters most for near-head bubbles and work/status effects, where image models may shrink or move the mascot to make room for the enhancer.

## Atlas Rules

- Use a consistent cell size across the whole atlas.
- Keep one state per row.
- Keep frames ordered left to right.
- Fill unused cells with full transparency.
- Keep the mascot inside each cell with safe padding.
- Do not rely on CSS cropping to hide broken edges or off-cell props.
- Keep row strips on a removable chroma-key background before alpha extraction.
- Assemble row strips with center-aware foreground extraction and small-component cleanup.
- Prefer `--no-equal-fallback` for production assembly. Use `--extraction-mode equal` only for exact equal-spaced row-strip sources after contact-sheet QA confirms it does not chop frames or include neighboring slivers.
- Use `--extraction-mode component` for image-generated row strips with separate enhancer components when it produces a cleaner contact sheet than foreground-center extraction.
- Clear RGB values for transparent pixels and resize sprites with premultiplied alpha so hidden chroma-key color cannot bleed into semi-transparent edges.
- Keep the outline improver enabled in the assembler: key-to-alpha removal, key-colored edge cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing.
- Treat `outlineImprover.totalOutlineHaloPixels > 0` in `qa/assembly-report.json` as a production blocker unless a human explicitly accepts the edge artifact.
- Produce a cutout QA sheet on dark, light, and saturated backgrounds; checkerboards alone can hide chroma-key halos.
- Produce `qa/state-readability-check.png` for semantic-enhancer packs before strict validation.
- Produce `qa/state-cue-plan.json` before row generation for normal generated packs, or document why prompt planning was skipped.
- Produce `imagegen-jobs.json` before visual generation and use it to track base-first job readiness.
- Record the selected base output before row generation so `references/canonical-base.png` exists.
- Produce `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png` before strict validation.
- Treat `qa/quality-report.json` silhouette warnings as blockers: detached fragments, broken-cut symptoms, core scale drift, full-row core scale range, or core center drift mean the row needs regeneration or a better source strip. For production mascots, full-row core scale range should stay at or below `5%`; larger changes are usually visible as body growth/shrink even when the contact sheet looks otherwise clean.
- For split-generated rows, inspect the stitch boundary and reject visible half-to-half changes in mascot scale, top/bottom anchor, outline thickness, prop size, palette, lighting, expression style, or pixel density even when numeric QA passes.
- Produce `qa/art-direction-review.json` before production validation. This is the visual gate for reference quality, identity preservation, native enhancers, and creative state readability.
- Production art-direction review must also confirm `themeNativeStateCues`: the state cues come from the mascot's visual language rather than generic symbols that merely read as chatbot UI.
- Production visual QA must confirm Codex-style pixel art: visible stepped edges, crisp clusters, limited palette, flat cel shading, thick readable outline, and consistent pixel density. Smooth illustration, glossy app-icon rendering, painterly gradients, 3D shading, vector-flat symbols, or high-detail antialiasing are production blockers.
- Production art must come from `$imagegen` integrated row generation or user/artist-provided integrated row art. Local scripts and deterministic compositors may not draw, synthesize, or paste final mascot props/effects.
- Review assembly warnings such as equal-width fallback; they indicate the row may need regeneration or manual inspection.

## QA Checklist

Reject or repair if any of these happen:

- The chatbot profile validator fails in strict mode.
- A row changes the mascot identity, outfit, face, prop, or palette unexpectedly.
- A row is technically valid but less polished, less expressive, less creative, or noticeably simpler than the source reference.
- A prop crosses into a neighboring frame slot.
- A frame is cropped.
- A frame contains a stray sliver, speck, or fragment from a neighboring generated pose.
- A frame shows a pink, green, or key-colored edge halo on `qa/cutout-check.png`.
- `qa/assembly-report.json` is missing, has assembly warnings, or records leftover outline halo pixels.
- A `semantic-enhancers` pack is missing `qa/state-readability-check.png`.
- A required semantic enhancer disappears from `qa/contact-sheet.png` or `qa/state-readability-check.png` after cleanup. Regenerate with a larger/attached cue instead of loosening cleanup enough to preserve random noise or neighboring-frame slivers.
- A row gets its smoothness from duplicates or near-duplicates rather than meaningful in-betweens.
- `qa/quality-report.json` reports low motion, near-duplicate transitions, body jitter, major area jumps, missing enhancer presence, or semantic anchor drift.
- `qa/art-direction-review.json` is missing for a production run, has `status` other than `pass`, has `productionUse` other than `true`, contains blockers, or reports any required art-direction check as false.
- `style.renderingStyle` is missing from a new production pack or is not `codex-pixel-art`.
- `style.visualLanguage` is required by the run policy but missing, or an enhanced state omits required `enhancer.visualLanguageFit`.
- `style.stateClarity` is malformed.
- `style.stateClarity` is `pose-only` but state rows introduce unrequested semantic props.
- `style.stateClarity` is `semantic-enhancers` but `thinking`, `working`, `listening`, or `answering` omit `enhancer` metadata.
- `imagegen-jobs.json` is missing for a normal generated pack, row jobs were generated before the base job was recorded, or row jobs omitted the canonical base/layout guide inputs.
- A production run was completed by manually editing `imagegen-jobs.json` or copying row files into `generated/` instead of recording selected `$imagegen` outputs with provenance.
- Enhanced state metadata still contains draft planning wording such as `planned during row generation` instead of the accepted visual aid.
- A held, touched, near-hand, writing, or appendage-operated work-prop enhancer omits `enhancer.anatomyGuard`.
- `enhancer.anatomyGuard.allowedInteractors` uses vague language instead of exact named reference appendages or body parts.
- A `fins-no-hands` or `ambiguous-limbs` mascot uses held, near-hand, touched, writing, or appendage-operated work-prop semantics without a `style.anatomyContract` recording the stable body core, appendage count, appendage placement, and forbidden additions.
- A semantic enhancer is not readable at 64, 96, and 128 px.
- A semantic enhancer is readable only as generic particles or timid decoration rather than intentional, character-native state art.
- A semantic enhancer is readable but off-vibe: generic gears, circuit diagrams, speech panels, UI windows, or universal symbols that do not belong to the mascot's source world.
- A semantic enhancer is on-vibe but does not read as the intended state, such as decorative frost that does not communicate active work.
- The `working` face reads as angry/hostile, or gains invented angry brows, instead of busy, friendly, and character-appropriate.
- A semantic enhancer is cropped, detached, text-dependent, or appears in unrelated states.
- A semantic enhancer wanders away from its intended anchor, changes sides without intent, or makes the row read as a different state.
- A semantic enhancer looks pasted on: mismatched outline, edge treatment, lighting, scale, pixel density, palette, or occlusion.
- A row or enhancer looks smooth, painterly, glossy, 3D, vector-flat, heavily antialiased, or otherwise unlike native Codex-style pixel art.
- A held enhancer causes extra hands, duplicate arms, new fingers/paws/fins, or other anatomy that was not in the source mascot.
- A state asks an appendage to perform an action outside its recorded affordances, such as face-touch by a fin that only has side-bob/tilt, or typing by a paw without fingers.
- A simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that reads as an extra appendage.
- A true no-limb mascot uses a held, near-hand, typing, writing, or grip-based semantic. Freestanding/resting props are allowed only when they sit beside or in front of the mascot, animate on their own, and do not imply hands, fingers, holding, typing, or writing.
- A fin/no-hand or ambiguous-limb mascot uses a held/touched prop without naming the exact existing fins, sleeves, paws, tentacles, or body parts allowed to interact with the prop in both the prompt and manifest.
- A held, touched, face-touch, typing, writing, pointing, presenting, or waving enhancer omits `enhancer.requiredAffordances` when the action depends on specific appendages.
- A state changes mascot scale between frames instead of animating posture. Core silhouette scale drift, full-row core scale range, and core center drift are production blockers because they make the same state feel like multiple different mascots.
- Production semantic enhancers were added as post-process overlays instead of generated as integrated mascot art.
- Production final art was made with deterministic compositing, vector overlays, manual shape props, or another prototype-only path.
- `qa/art-direction-review.json` has a production generation method other than `imagegen-integrated-row-art`, `user-provided-integrated-row-art`, or `artist-provided-integrated-row-art`.
- `qa/art-direction-review.json` does not record `checks.themeNativeStateCues: true` for production acceptance.
- `qa/art-direction-review.json` does not record the original source reference that was used for visual comparison.
- A key chatbot state has too few frames: use 12+ for `thinking`, `working`, and `answering`; use 10+ for the other default states.
- A row contains floating symbols, shadows, glows, dust, speed lines, text, UI panels, or scenery that the user did not request.
- The atlas dimensions do not match the manifest.
- `frames` does not match the number of `durations`.
- A used cell is empty.
- An unused cell is non-transparent.

## Website State Mapping

Common mappings:

```ts
const stateMap = {
  idle: "idle",
  chatOpened: "greeting",
  userTyping: "listening",
  submitted: "thinking",
  retrieving: "working",
  toolCall: "working",
  streaming: "answering",
  complete: "success",
  error: "error",
  unclear: "confused",
  inactive: "sleeping"
};
```
