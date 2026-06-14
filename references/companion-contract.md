# Web Companion Contract

## Manifest Shape

Use this shape for `manifest.json`:

```json
{
  "id": "companion",
  "displayName": "Companion",
  "description": "A cheerful chatbot companion.",
  "style": {
    "renderingStyle": "codex-pixel-art",
    "stateClarity": "pose-only"
  },
  "atlas": {
    "path": "atlas.webp",
    "width": 2048,
    "height": 2592,
    "columns": 8,
    "rows": 9,
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
| idle | 8 | Resting breathing/blink loop |
| greeting | 8 | Chat opens or first visit |
| listening | 8 | User is typing or speaking |
| thinking | 8 | Model is planning, retrieving, using tools, searching, or waiting on backend progress |
| answering | 8 | Response is streaming |
| success | 8 | Task complete or answer finished |
| error | 8 | Request failed or warning state |
| confused | 8 | Input unclear or needs clarification |
| sleeping | 8 | Inactive, minimized, or offline |

Use fewer rows only when the user asks for a smaller pack. Use more states when the product needs them, but keep the frame size and manifest explicit. Do not include `working` in default chatbot packs; use `thinking` for planning, retrieval, tool calls, search waits, file waits, and backend progress. Add `working` only when the user explicitly asks for a separate work/tool state.

Default production companion atlases should use an 8-column baseline like `$hatch-pet`. `thinking` and `answering` are the most visible waiting states, but they should get richer acting inside 8 frames before they get more frames. Use 10-12 frame rows only as an opt-in smoothness pass after a shorter row proves identity, scale, appendage count, state readability, and pixel-art quality are stable. Fewer stronger frames are better than more frames with character drift or invented anatomy.

If image generation cannot reliably produce an opt-in 10-12 frame row with the correct number of mascot bodies, generate the row in smaller exact-count chunks and stitch those generated parts with `scripts/stitch_row_parts.py`. The stitch step may concatenate existing generated art only; it must not create missing frames, draw props, resize sprites, or patch anatomy. The stitched row must pass the same assembly, motion, cutout, readability, semantic-anchor, and visual seam QA as a single generated row.

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

`qa/state-cue-plan.json` is a planning artifact, not production acceptance. It should record the inferred source vibe, state purpose, acting-first beat, frame-by-frame acting arc, professional state acting choreography, whether a visual aid is allowed, the suggested aid, any no-hand fallback prop policy, and rejection criteria for each state. Layout guide PNGs are also planning inputs: they are intentionally empty construction guides for spacing and safe padding, not mascot previews or QA output. Row prompts should use that plan to make the mascot perform the state first through expression, posture, timing, and original appendages, then add a small visual aid only when the state would otherwise be unclear at website size. Professional choreography coordinates three tracks: expression, body/appendage, and cue/prop. Do not accept rows where all visible motion lives in the enhancer while the mascot keeps parked hands, frozen appendages, or the same face in every frame. Production state-performance review must explicitly set `coherentStateStoryArc=true` and `mascotActingVariesAcrossFrames=true`; otherwise a cute cue can hide a stale mascot. Use HatchPet-style sprite artifact rules: effects must be state-relevant, opaque, hard-edged, pixel-style, inside the same frame slot, and source-bound to the mascot silhouette, mouth edge, hand, tool, worn prop, or state source. Near-head thought cues may use proximity or a tiny separated tail dot instead of touching when overlap would merge into the mascot core; all cues must stay tiny, close, and secondary to the mascot. Keep an art direction floor: the row should look like a polished mascot performance with expressive eyes, mouth shapes, head/body tilt, timing, appendage follow-through, tasteful asymmetry, and deliberate frame-to-frame acting; reject bland, stiff, generic, timid, or symbol-only rows even when anatomy is correct.

Prompt economy is part of the contract. The preparer may keep rich policy text in `qa/state-cue-plan.json`, but generated `$imagegen` row prompts should stay compact and generic: identity/style locks, exact frame count, state story, concise cue rule, scale/layout lock, and rejects. Do not copy this whole reference into row prompts. Do not inject mascot-specific colors, props, anatomy, accessories, or cue origins unless they come from the user, the canonical base/reference, accepted rows, or manifest metadata.

`thinking` is the default chatbot waiting/processing state. It should preserve identity props by default, change expression through a neutral-curious -> noticing -> curious pondering -> idea lands -> pleased settle arc, and name a visible small -> slightly larger -> medium -> smaller -> tiny/settle cue arc when a bubble, puff, idea orb, mascot-native processing aura, or other source-bound cue is used. Near-head cues should begin close to the inferred thought-cue source with a 2-4 px chroma-key gap or a tiny separated tail dot, any later drift must remain tiny and visually associated, and medium should be the maximum cue size. The cue must stay secondary to the mascot, never larger than about one-quarter of the body width, and never become a second head/body-sized orb. At the idea peak, the primary cue element is only slightly larger, never oversized, and do not enlarge the cue to prove the idea landed. When the chosen cue uses separated elements, they must form a stable source-to-peak trail: the smallest element stays closest to the inferred source, intermediate elements continue the same upward/outward path, and the largest/clearest element appears only at the idea-lands peak. Do not let intermediate cue elements drift downward, reverse direction, jump sideways, or reorder the trail. Preserve the accepted cue vocabulary across the row; puff-specific shape rules apply only when the chosen cue is puff-based. It should move through adjacent frames rather than popping in for one frame, jumping upward into a giant peak, alpha-connecting to the mascot core, or dropping out abruptly at the loop. Use one cue family across the row: do not morph from thought bubble to data cloud to detached lightbulb/icon/rays. Thinking frames should not become worried frowns, sad/serious/downturned expressions, stale same-face holds, sleepy closed-eye smiles, open exclamation/speaking-mouth beats, dot/colon/vertical-bead mouths, or confused/error faces. Recognition should be a closed or tiny pixel smile, not a wide open speaking mouth, exclamation mouth, or answering syllable mouth. It should cover model planning, retrieval, tool-use waiting, search/file waits, and backend progress without requiring a separate `working` row.

`answering` should make the talking performance primary: clear mouth shapes, eye engagement, blink timing, tiny conversational body bob, and a loopable speaking rhythm. Speech pips, sound ticks, tiny rings, breath marks, or voice pixels are optional; omit them when they cannot stay clearly attached to the mouth. When used, the cue should touch or overlap the mouth/lip edge or begin within 1-2 pixels of it, form a short 2-3 frame outward trail, and stay secondary to the mouth animation. If a cue cannot appear in at least two adjacent frames with a mouth-origin progression, omit it. Use breath, frost, smoke, or cloud puffs only when they belong to the source mascot and still read as speech. Compact speech-bead trails or small mouth-tailed puffs should read as speech rather than thought bubbles, detached round orbs, single isolated specks, one-frame voice ticks, one-frame sound marks, cheek marks, face markings, or detached flecks.

If the user explicitly requests `working`, it should name a concrete mascot-native action plus a visible notice -> operate/sort/check -> progress/result -> settle transformation; the row should not be accepted if it only shows random status icons or a final check mark. Work cues should match visual language and anatomy. Tech mascots can use panels/tablets/sliders/status blocks; nature mascots can sort leaves, seeds, stones, or wooden tokens; icy/water mascots can use frost tiles, droplets, or crystal tokens. Magic mascots with long held props should prefer attached active-end blooms, staff-tip glyphs, or glowing sorted motes before separate spell circles, rune tiles, or charm tokens. The cue should sit in a believable interaction zone near the active hand, active tool end, staff head, wand tip, mouth, gaze focus, body surface, or body rim, or else use a visible causal link such as body lean, aura, or active-end alignment. For long held props, the active end is the wand tip, staff head, tool bit, pointer tip, brush tip, pen tip, blade tip, or nozzle, not the floor, base, butt end, handle end, or lower shaft unless the source clearly uses that end. Prefer a small hard-edged pixel bloom, aura, pulse, or contact mark wrapped around, touching, or overlapping that active end; it communicates progress through intensity/shape changes, eye tracking, mouth changes, and subtle hand/prop motion, not through a separate drifting diamond/object. Do not echo identity emblems, logos, badges, weapon silhouettes, or signature markings inside the work target. If a held prop aims, taps, charges, points, or moves, that active pose replaces the resting pose; do not show both resting and active copies in the same frame, and keep the original hand-to-prop attachment visible. Keep long-prop working motion small and stable: preserve the same top edge, bottom edge, body core width, prop count, and appendage count; avoid large full-body leans, big cross-body swings, diagonal staff sweeps, and full-body scale shifts. For simple/no-hand mascots, prefer face/body acting plus body-surface, rim-touching, attached, or overlapping processing cues before separate objects; freestanding/resting props are last-resort fallbacks only when attached/body acting cannot read at 64-96 px.

`imagegen-jobs.json` follows the hatch-pet-style base-first contract:

- `base` is the first ready job and may be prompt-only only when no reference exists.
- row jobs depend on `base` and must list grounding input images.
- row jobs include the original references, `references/canonical-base.png`, `generated/base.png`, and the row's layout guide.
- row jobs are subagent-eligible only after the base is recorded and only when subagents are authorized for the session. Subagents may generate or inspect candidates, then return only `selected_source` and `qa_note`; the parent owns all manifest writes, recording, atlas assembly, QA, validation, and packaging.
- `scripts/record_companion_imagegen_result.py` is the only normal way to mark jobs complete and copy selected `$imagegen` outputs, built-in `$imagegen` chroma-key cleanup outputs from the installed `remove_chroma_key.py` helper, explicit approved `$imagegen` CLI fallback outputs, or finished user/artist integrated row art into the run. It reads the run chroma key from `companion_request.json` or `manifest.style.chromaKey` for strict source checks. Production base jobs should be recorded with `--strict-base-style` so non-flat chroma-key backgrounds, missing foreground sprites, and smooth/glossy/over-detailed foreground palettes are blocked before row jobs become ready. Completed base jobs must retain `base_style_analysis` and `base_style_strict_blocking_warning_codes`; audition/chatbot validation fails base jobs that are missing this source-style evidence or retain blocking codes. Production row jobs should be recorded with `--strict-row-style` so fake checkerboard transparency backgrounds, non-flat chroma-key backgrounds, and missing foreground sprites are blocked before assembly. Completed generated row jobs must retain `row_source_style_analysis` and `row_source_style_strict_blocking_warning_codes`; audition/chatbot validation fails generated row jobs that are missing this source-style evidence. A row source that merely looks green but has visible or measured falloff is not cleanup-ready by itself; if the visual row is worth keeping, first try the default `$imagegen` transparent workflow by running `remove_chroma_key.py`, then record the cleaned alpha PNG with `--source-provenance built-in-imagegen-chroma-cleanup --chroma-cleanup-source <original-$CODEX_HOME/generated_images/.../ig_*.png> --strict-row-style`. This allowed helper cleanup is not the same as locally flood-filling, drawing, compositing, or normalizing final art; the original raw `$imagegen` source remains part of the job provenance. If helper cleanup cannot produce a strict-clean alpha row, record the candidate as rejected or rerun through the approved true-transparency fallback instead of calling it clean. CLI fallback provenance must include `--cli-fallback-approved`, model `gpt-image-1.5`, background `transparent`, output format `png`, and the fallback prompt file.
- `scripts/audit_companion_imagegen_sources.py` may write a non-mutating QA report for older completed row jobs. It analyzes `source_path` images with the same strict row-source checks but does not copy files, mark jobs complete, or edit `imagegen-jobs.json`.
- `scripts/create_companion_candidate_rejection_report.py` may write a non-mutating QA report for generated row candidates that were visually inspected and rejected before recording. It analyzes each candidate source with the same strict row-source checks, stores hashes, visual blockers, deterministic warning codes, and `recorded: false`, preserves the current recorded row source as the row to keep for now, and does not copy files, assemble rows, mark jobs complete, or edit `imagegen-jobs.json`.
- `scripts/create_imagegen_cli_fallback_handoff.py` may prepare the dry-run command, real `$imagegen` CLI edit command, and matching record command for an explicitly approved true-transparency fallback. It is a handoff generator only; it must not be treated as user approval, does not run image generation, and should use the current recorded row source_path by default. If the most promising input is a visually inspected but strict-rejected candidate, pass `--allow-rejected-candidate-source`; the handoff records `sourceMode: "rejected-candidate"` and remains non-mutating evidence only. Do not record the rejected candidate, copy it into `generated/`, or treat it as accepted art. Record only the inspected CLI fallback output if it passes strict row style. It can write a compact generic repair prompt with `--write-default-prompt`; use that generated prompt when the goal is to preserve the current row story, cue timing, body scale, and identity while repairing source cleanup, eye grammar, or visual-review blockers. Generated prompt handoffs record `defaultPromptWritten: true` and `repairPromptSource: "generic-story-preserving-default"`; production-readiness summaries should carry those fields so reviewers can see when the repair prompt came from the generic skill path. The handoff must record `requiredEnvironment: ["OPENAI_API_KEY"]`, `requiresExplicitUserApproval: true`, and `promptRepairContract` evidence that the fallback prompt preserves story and scale, repairs only named blockers, and avoids redesign. After explicit user approval, regenerate the handoff with `--user-approved --approval-note "<short approval context>"` so it records `explicitUserApprovalReceived: true` and `approvalNote`; otherwise leave the handoff unapproved. Treat each fallback as a story-preserving source repair, not as a new concept prompt.
- completed jobs should record source path, source provenance, hashes, metadata, and completion time.

After recording `base`, `references/canonical-base.png` must exist and should be treated as the approved identity source for every row. Do not generate row strips without attaching that canonical base and the row layout guide.

The canonical base is not a sketch placeholder. It must already be a native Codex-style pixel-art sprite with flat cel-shaded pixel clusters, hard stepped edges, simple blocked highlights, and a readable compact silhouette. Treat it as the final atlas-frame source of truth, not concept art, a preview illustration, a pose-sheet sample, an app icon, or a softened style target. The base should read like a Codex app digital pet first and a website mascot second: fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite cell even if the final web atlas later uses larger cells. It must be simple enough to reproduce across eight row frames without redesign: stable silhouette, top edge, bottom edge, face-bearing area, appendage count, prop count, and no tiny high-detail marks that will flicker in rows. Reject and regenerate the base before row generation if it is smoother, glossier, more detailed, or less pixel-native than the intended row art; rows must preserve the accepted base, not fix it by changing eye style, body shape, colors, outline weight, props, or anatomy. For text-only concepts, the base should include only anatomy and identity props named in the concept or command; do not invent unrequested limbs, body markings, display details, tools, or extra props. Draw the base as if it was first made on a tiny 64x72 or 80x90 pixel grid and enlarged with nearest-neighbor scaling. Use indexed-color sprite discipline: roughly 8-16 total non-background colors, no per-pixel color ramps, no smooth shade bands, no gradient-filled body areas, face areas, clothing, props, accessories, or appendages, no blended intermediate palette colors, and no dozens of near-identical color steps. Preserve the strongest accepted character choices while flattening the rendering; only simplify colors and material treatment. Reject bases that rely on glossy gradients, soft airbrush shading, bloom, rim glow, broad shine patches, transparent or semi-transparent shines, feathered transitions, high-detail specular shine, 3D lighting, smooth radial gradients, soft cylindrical shading, pillow shading, app-icon material lighting, smooth antialias fringes, or smooth vector curves, because later row prompts will either preserve those bad details or drift away from the base. Use one or two chunky stair-step shadow clusters, not continuous tone ramps. If the source vibe is soft or friendly, the softness should come from rounded shape language and expression, not blurred rendering. Do not compose the base as a large glossy product mascot, large hero character, app icon, or high-resolution sticker; leave generous chroma-key padding and keep the sprite compact. Row prompts must preserve absence too: plain body areas stay plain, absent limbs stay absent, and absent identity details should not be invented just because a broad mascot category might suggest them.

The preparer may seed enhanced states with draft metadata such as `"kind": "planned during row generation"`. After final row art is selected, replace that draft metadata with the actual accepted visual aid, for example `"kind": "near-face icy voice pixels"` or `"kind": "body-surface processing glyph"`. Strict validation warns on leftover draft enhancer wording so planning placeholders do not become shipped metadata.

Expression language is part of the identity contract. Preserve the source mascot's normal face grammar when communicating state. A calm, browless, icon-like, plush, or abstract mascot should not gain angry eyebrows, hostile eyes, slanted angry eyes, narrowed hostile eyes, V-shaped eye/brow marks, teeth, sweat, blush, or dramatic emotion marks just to show focus. Use eye direction, blink timing, mouth shape, posture, timing, and approved visual aids first; stronger face marks are acceptable only when the source design already supports them or the state genuinely needs them and the result remains character-appropriate. For optional `working`, reject even one frame that reads angry or hostile rather than busy-friendly.

Usable appendages should act, not just survive. For mascots with visible hands, paws, sleeves, arms, or other expressive appendages, high-visibility rows should include at least two small safe appendage acting beats while preserving exact appendage count. Do not leave hands, paws, sleeves, or held props frozen across the whole row. If a prop is held, the prop-holding hand must remain attached while the free hand can lift, present, tuck, point, settle, or make a polished thinking face-touch when the reference supports that action. Face-touch is acceptable when it clearly uses the original appendage, remains connected to its body anchor, preserves the other appendage and any held prop, keeps the expression readable, and improves the pose. For generic mitten-hand mascots, prefer conservative side-anchored thinking motion such as side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck unless a visual audition proves the face-touch reads cleanly. `answering` can use a small presenting beat, conversational hand bounce, palm-up gesture, or free-hand settle. Reject extra hands, duplicate arms, detached mittens, finger clusters, new grip anatomy, clasped hands under the mouth, under-chin clusters, scalloped mitten/bib clusters below the face, and any face-touch that reads as a new cheek, nose, lower-face patch, detached mitten, duplicated hand, extra paw, or hidden expression.

The full reference palette is also identity. Preserve the actual source colors for eye whites/highlights, pupils, eye outlines, face base color, cheek marks, outfit, props, and signature markings. Do not force white eyes or white highlights when the reference uses another color; only keep whites white when the source uses white. Do not let a glow, aura, bloom, prop color, or gold effect tint or recolor the mascot identity palette unless the source design already uses that color there.

Eye grammar is a separate identity lock, not just a palette detail. Preserve the canonical base eye count, shape, size, spacing, outline color, pupil/fill color, and catchlight/highlight logic in every generated row. Gaze shifts and blinks can animate the state, but both eyes should stay matched and anchored to the same face-panel positions. Reject hollow or inverted eyes, dark eyes turned into white ovals with dark rims, extra catchlights, glossy anime eyes, vertical slit pupils, square UI eyes, mismatched eyes, and one-frame eye-style swaps. For solid dark base eyes, open eyes should remain mostly dark with the original tiny highlight; do not expose white sclera crescents, carve white crescent gaps to fake side glances, or make a white cutout the dominant eye shape. If an up-glance, side-glance, blink, or speaking beat would require changing eye style, keep the eyes forward or nearly forward and carry the acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead. Keep eye centers inside the original eye boxes; never slide eyes onto cheeks, panel edges, the mouth line, or outside the face panel. Do not replace eyes with loading dots, LEDs, status bars, diagonal slashes, crosses, punctuation, or reaction icons. Closed-eye blinks should replace each open eye with a simple closed curve or horizontal pixel line in the same eye positions and spacing, not X-eyes, chevrons, reaction glyphs, eyebrows, or mouth-like lower-face squiggles. Face-panel grammar is identity too: for screen-faced, mask-faced, and simple front-panel mascots, do not skew, stretch, rotate, squash, or turn the panel into a trapezoid to create state acting.

Semantic cues are part of the cleanup contract too. A cue that only exists as isolated tiny specks, far-away dots, ultra-thin marks, or a separate detached blob is fragile: default cleanup may remove it, while loosening cleanup can keep neighboring slivers or force the mascot body to shrink around distant effects. For thinking, loose sparkles, isolated white specks, star glints, diamond flecks, single-pixel dust, and stray final-frame dots are not enough; the cue should read as one deliberate compact thought puff, bubble cluster, idea orb, or processing aura with hard-edged pixel mass and a clear inferred source near the expression area. Near-head cues must not alpha-connect to the mascot core, expression panel, accessory, or outline when they grow, because QA may then measure the cue as mascot body size. Prefer a 2-4 px chroma-key gap, proximity, eye tracking, timing, or one tiny separated tail dot for visual association. For ambiguous states that need a cue, prefer compact body-surface, rim-touching, attached, close-overlapping, worn, mouth-tailed, or prop-tip artwork that survives default cleanup and reads at 64-96 px. Freestanding or resting artwork is a fallback for no-hand work only, not the first instinct. For body-surface or rim-touching work cues on no-limb/simple-appendage mascots, keep marks inside the body core or as one small rim-touching mark; repeated leaf, oval, wing, paw, mitten, droplet, or appendage-colored tokens along lower/side edges often read as feet, extra limbs, extra wings, new paws, or detached appendages. Use one central glyph/status band or 1-3 high-contrast square, dot, check, or token marks instead.

Motion cues must not create a floor. The chroma-key background must be one perfectly uniform solid color from corner to corner, with no vignette, lighting falloff, texture, noise, shadow, ground plane, or background glow. Do not show bobbing, jumping, thinking, emphasis, or state timing with floor shadows, contact shadows, ground lines, baseline marks, landing marks, or dark under-body strokes. The production sprite should contain only the mascot and approved state cue on chroma key; any floor-like mark is an artifact, not animation.

State cues must not consume identity props. A thought bubble, voice puff, work glyph, or status cue should not cover, replace, recolor, merge with, or grow out of antenna bulbs, ears, horns, hats, badges, emblems, staffs, wands, or other must-keep props unless the state explicitly uses that prop as the active source. For antenna mascots, thinking cues should originate from the inferred thought-cue source near the expression area, not from the antenna tip, and the antenna bulb should remain visible and stable. Near-head cues must also preserve the body footprint: if touching the cue to the outline makes the core silhouette measure larger, use a close 2-4 px chroma-key gap or tiny separated tail dot instead of fusing the bubble into the sprite.

Appendage gestures should be expressive when the reference supports them, but clear silhouette matters. For presenting, held-prop, appendage-operated props, or face-touch gestures, the prompt and art review should preserve a visible path back to the original body anchor and enough outline or tiny negative space near the face/prop to avoid reading as a new cheek, nose, face patch, detached mitten, duplicated hand, or extra paw. Near-mouth and under-chin thinking poses are acceptable only when they look deliberate, connected, and character-native; otherwise regenerate with safer side motion.

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
        "thinking": "Use one compact frost/data thought puff or processing aura for planning and tool waits.",
        "answering": "Use mouth shapes first; icy breath puffs are optional only when they read as speech."
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
      "componentPolicy": "separate",
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
        "thinking": "Use one compact frost/data thought puff or processing aura for planning and tool waits.",
        "answering": "Use mouth shapes first; icy breath puffs are optional only when they read as speech."
      }
    }
  }
}
```

`style.visualLanguage` is optional metadata, not a substitute for visual review. It is useful when a state has been failing because generic symbols or off-vibe props keep appearing. Each enhanced state may include `enhancer.visualLanguageFit`, a short note explaining why the state cue matches the reference vibe. Use `scripts/validate_companion_manifest.py --require-visual-language` only for targeted auditions where missing vibe-fit metadata should fail validation.

For detailed references, `style.visualLanguage.identityProps` may list must-keep props, emblems, clothing silhouettes, markings, and signature accessories. These are part of identity, not optional decoration. Simplify ornate detail into readable pixel clusters, but when a signature prop appears in a state row, keep its count, side, scale, attachment, and basic silhouette stable across the row. Preserve signature props by default even when semantic cues are present; stage thought cues, voice cues, and any explicitly requested work targets around the prop instead of dropping it. Omit a must-keep prop only when the state card explicitly marks that exact prop optional for the whole row. If a held prop moves, the active pose replaces the resting pose and remains one continuous object attached to the original hand/body part. Visual QA should reject duplicated staffs/tools, simultaneous resting and active prop copies, changing emblem placement, mutated props, prop-shaped cue copies, and trim or accessories that read as extra anatomy.

If the user explicitly requests `working`, held, touched, near-hand, writing, or appendage-operated work-prop enhancers should also include an `anatomyGuard` so prompts and QA do not invent new limbs:

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

Optional `enhancer.componentPolicy` values:

```text
separate, overlap-ok, integrated-ok, occlusion-ok
```

Use `separate` or omit the field when a near-head/aura enhancer should remain a visibly separate component for automated semantic-anchor checks. Use `overlap-ok` only after visual review accepts intentional close overlap or partial occlusion, such as a thought puff tucked behind a hood, hat, hair, ear, or antenna. In that case the quality analyzer still checks motion, body scale, center drift, fragments, and readability sheets, but it does not require the cue to be a separate alpha component.

Allowed `style.anatomyClass` values:

```text
hands, paws, fins-no-hands, no-limbs, ambiguous-limbs
```

Set `anatomyClass` when semantic enhancers interact with the mascot body. Existing non-human appendages can support prop or gesture interaction only when the contract says they can: fins, sleeves, tentacles, paws, or mitt-like limbs may hold, brace, tap, or point when they are present in the reference, named in `enhancer.anatomyGuard.allowedInteractors`, and backed by matching appendage `affordances`. Face-touch is opt-in only when the exact appendage declares that affordance and an audition proves it stays connected without becoming a face patch or extra hand. Strict validation rejects held/near-hand attachments and common typing/writing props for `no-limbs`, but allows `freestanding` or `resting` work props when they animate on their own beside or in front of the mascot and explicitly do not require holding, typing, writing, grip, hands, or fingers. Freestanding prop animation must not bridge the empty gap with pips, sparkles, crystals, or motion marks; keep those marks inside/on the prop surface so the body remains a separate component. For `fins-no-hands` and `ambiguous-limbs`, strict validation requires anatomy-guard metadata for held or appendage-operated risky props, and visual QA must reject any extra hands, fingers, duplicate fins, cloned sleeves, or invented grip anatomy.

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
      "kind": "clear-face low side-hand thinking gesture",
      "attachment": "gesture",
      "description": "The left hand touches the chin while a compact thought cue appears near the head.",
      "requiredAffordances": ["point"],
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

`thinking`, `listening`, and `answering` should have `enhancer` metadata when `semantic-enhancers` is selected and those states are present. Optional explicitly requested states such as `working` need the same metadata when present. Metadata cannot prove the pixels are good, but it forces each generated state to carry an explicit QA intention.

## Geometry Guidance

Use `256x288` cells by default for high-quality website companions, especially when the mascot has a detailed outfit, emblem, prop, expressive hands, or readable facial states. Use `192x208` only for smaller packs or very simple mascots.

The atlas assembler should infer frame centers from foreground runs instead of slicing row strips into equal widths. Generated row strips often have slightly variable spacing; naive slicing can leave neighboring-frame slivers or clip wide gestures even when manifest validation passes.

Explicit equal-grid extraction is allowed only when a row source was intentionally generated as an exact equal-spaced horizontal strip and foreground-center extraction visibly mis-splits close frames. Do not use silent equal fallback for production; use the explicit mode and accept it only after contact-sheet QA passes.

Component-body extraction is preferred when a row includes detached but integrated effects, such as thought orbs, sound rings, speech wisps, or attached glints, and foreground-center extraction splits or merges poses. It must fail if it cannot find the expected number of mascot body components.
If a legitimate detached enhancer is large enough to be counted as an extra body component, raise `--body-component-area` and rerun extraction. Do not lower component filtering or accept equal slicing until visual QA proves the effect remains anchored to the correct frame.

Semantic enhancers may require slightly wider safe padding. Do not rely on CSS cropping to hide bubbles, tablets, paper, sound rings, or other state props.

Frame fitting must not make the mascot body resize when a semantic effect grows. Atlas assembly should use a consistent fit scale across all frames in the same state row; otherwise a tall thought bubble or wide prop can shrink that frame's entire mascot even when the generated body was stable. Row prompts should also match the apparent body size and padding of the canonical base plus any already accepted state rows, so later rows do not become zoomed-in or shrunken copies of the same mascot. If the largest frame footprint forces the whole row to become too small, increase cell size or regenerate the row with a tighter effect rather than allowing per-frame scaling or accepting a cross-state scale mismatch.

## Motion Design Rules

Do not treat "more frames" as duplicated stills. Every used frame should earn its slot.

- Every state should tell one coherent loopable performance story, not a random emotion collage. Expressions should be adjacent beats caused by the state action: calm -> blink -> settle, notice -> greet -> settle, neutral-curious -> noticing -> curious pondering -> idea lands -> pleased settle, ready -> speaking -> conversational blink/smile -> settle, or another state-appropriate arc. Reject abrupt mood jumps, unrelated sad/serious/sleepy/angry/blank faces, and expression changes that do not fit the state or cannot loop back to frame 1 cleanly.
- `idle`: slow breathing, 1-2 blink/eye frames, tiny hand/prop settle.
- `greeting`: anticipation, arm/prop rise, peak gesture, return, friendly hold.
- `listening`: attentive lean, blink, eye tracking toward user input, subtle prop/body motion.
- `thinking`: expressive planning/processing through head tilt, source-matched eye/highlight shifts, safe side-anchored appendage or prop tilt when anatomy supports it, blink, small loopable shifts, and one compact thought bubble/puff/orb when acting alone would be too subtle. The emotion should read as curious pondering and processing, not worry, confusion, sadness, anger, sleepiness, surprise, answering, or error. Use neutral-curious, tiny closed pondering smiles, gently upturned one-pixel thoughtful smile mouths, quick active processing blink/hold, and small recognition-smile beats. Keep mouths level or slightly upturned and smile-like; avoid flat serious line mouths, single-dot, two-dot, colon, vertical bead, and round mouths, plus downturned mouths, downturned frowns, curled lower-lip marks, worried squiggles, serious blank faces, confused/error mouth shapes, sleepy closed-eye smiles, and open exclamation or speaking-mouth frames. Any closed-eye thinking frame must read as a quick active processing blink, not sleep, idle rest, fatigue, or meditation; keep the thought cue active during that blink and place open-eye curious or recognition frames immediately before and after it. Processing blinks should use simple closed curved or short horizontal eyes, not squeezed shut X-eyes, chevron eyes, scrunched effort eyes, or strain grimaces.
- For near-head `thinking` enhancers, prefer a side-origin path: the thought cue begins near one side of the head, grows from small to slightly larger to medium, then shrinks back down before the loop settles. Medium is the maximum thought cue size; it must stay secondary to the mascot, never larger than about one-quarter of the mascot body width, and must not become a second head/body-sized orb. At the idea peak, the primary cue element is only slightly larger, never oversized, and do not enlarge the cue to prove the idea landed. When the chosen cue uses separated elements, they must form a stable source-to-peak trail: the smallest element stays closest to the inferred source, intermediate elements continue the same upward/outward path, and the largest/clearest element appears only at the idea-lands peak. Do not let intermediate cue elements drift downward, reverse direction, jump sideways, or reorder the trail. Preserve the accepted cue vocabulary across the row; puff-specific shape rules apply only when the chosen cue is puff-based. Keep the full cue path low, close, and compact enough that it does not become the tallest or widest row element and force atlas assembly to shrink the mascot body; reduce or tuck the cue instead of changing mascot scale. The cue should move through adjacent frames rather than popping in, jumping upward into a giant peak, or disappearing abruptly; the final frame should either keep a tiny settled cue or resolve cleanly back to frame 1. Use one cue vocabulary for the full row; reject rows that switch between bubble, data cloud, detached lightbulb, exclamation, sparkle, UI/data icon, or rays. The mascot's eyes and mouth should react to that motion.
- Existing appendages should be allowed to act when they are part of the reference and their recorded affordances support the action: hands can gesture low at the side, lift to the shoulder side, make a tiny outward point, go palm-up, present, touch the chin/cheek, or settle against the body; paws can gesture; sleeves can brace a prop; and tentacles can point when the contract says they can. Face-touch is acceptable when the reference or audition supports it, the appendage remains connected to its original arm/body anchor, the other appendage is still accounted for, and the expression remains readable. QA should reject extra or duplicated anatomy, not legitimate motion from original appendages. If the acting pose makes a hand read as a lower-face patch or makes a simple appendage look like a new hand, fingered mitten, detached object, or third limb, regenerate with a safer smaller appendage motion and move the acting beat to face, body tilt, blink timing, or the semantic enhancer. For no-limb thinking rows, reject chin-touch, cheek-touch, lower-face squiggles, extra mouth ticks, chin marks, moustache-like pixels, or small appendage-colored marks on the lower face/chin.
- Optional `working`: faster but controlled movement, prop/hand/body cycles, focused but friendly face, and a concrete before/during/after work cue.
- `answering`: talking performance through changing mouth shapes, expressive eyes, subtle face/hand beats, and loopable conversational cadence. For no-limb, fins-no-hands, and ambiguous-limb mascots, prefer mouth-only answering unless the optional voice cue can stay unmistakably mouth-attached; omit voice pixels instead of creating a cheek mark or detached fleck.
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

For high-frame-count rows, treat body stability as part of the prompt, not just QA. State prompts should name the body anchor explicitly: same body center, same silhouette size, same top edge, same bottom edge, same appendage count, and only subtle breathing unless the state intentionally uses a large pose. They should also preserve the canonical base's apparent body size and padding across different state rows instead of zooming one state to fill the cell. This matters most for near-head thinking cues, answering gestures, and optional work/status effects, where image models may shrink, enlarge, or move the mascot to make room for the enhancer.

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
- Produce a cutout QA sheet on dark, light, and saturated backgrounds; checkerboards alone can hide chroma-key halos. The assembler and validator must use the run's stored chroma key, not a fixed green or magenta assumption.
- If repeated built-in `$imagegen` row attempts fail strict source cleanup for `non_uniform_chroma_key_background` or `fake_checkerboard_transparency_background`, stop retrying that same generation path and escalate to the installed `$imagegen` true-transparency fallback only after explicit user confirmation and a configured environment. Use the current recorded row `source_path` by default so the fallback preserves the row currently under review, not an older candidate. If no row is recorded yet and the promising story exists only as a visually inspected strict-rejected candidate, keep it as non-mutating rejection evidence and create the fallback handoff with `--allow-rejected-candidate-source`; do not locally flood-fill the source to create fake provenance. Do not accept locally flood-filled, fill-bucketed, composited, or fake-transparent row sources as production generated provenance.
- If repeated candidates fail visual review for eye grammar, flat cleanup-ready chroma, anatomy, scale, or native pixel-art quality, preserve the evidence in a candidate rejection report before the next generation path decision. A rejected candidate should not be recorded or assembled. It may be used as true-transparency fallback input only through the explicit `sourceMode: "rejected-candidate"` handoff, and the candidate itself remains rejected until the fallback output is inspected and strict-recorded.
- Produce `qa/state-readability-check.png` for semantic-enhancer packs before strict validation.
- Produce `qa/state-cue-plan.json` before row generation for normal generated packs, or document why prompt planning was skipped.
- Produce `imagegen-jobs.json` before visual generation and use it to track base-first job readiness.
- Record the selected base output before row generation so `references/canonical-base.png` exists.
- Completed base jobs must record strict base-source evidence (`base_style_analysis` and `base_style_strict_blocking_warning_codes: []`). If an older run lacks it, audit or re-record the selected source before treating the base as production-grade.
- Produce `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png` before strict validation.
- Treat `qa/quality-report.json` silhouette warnings as blockers: detached fragments, broken-cut symptoms, core scale drift, full-row core scale range, or core center drift mean the row needs regeneration or a better source strip. For production mascots, full-row core scale range should stay at or below `5%`; larger changes are usually visible as body growth/shrink even when the contact sheet looks otherwise clean.
- For split-generated rows, inspect the stitch boundary and reject visible half-to-half changes in mascot scale, top/bottom anchor, outline thickness, prop size, palette, lighting, expression style, or pixel density even when numeric QA passes.
- Produce `qa/anatomy-review.png` and `qa/anatomy-review.json` before production validation. This is the frame-by-frame visual gate for body core stability, appendage count, hand/arm/sleeve/fin continuity, placement/anchors, allowed motion/interactors, forbidden extra anatomy, identity prop stability, and state cues that might be mistaken for anatomy; numeric QA cannot reliably detect those failures. Its `expectedAnatomy` must specifically describe body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy.
- Produce `qa/state-performance-review.png` and `qa/state-performance-review.json` before production validation. This is the frame-by-frame visual gate for state acting/readability; numeric QA cannot reliably detect when `thinking` reads as idle/status dots, when `answering` reads as tired exhaling instead of engaged speech, when optional `working` reads as panting, sleeping, talking, or decoration, when the row lacks a coherent story arc, or when all motion lives in the cue while the mascot stays stale.
- Produce `qa/eye-grammar-review.png` and `qa/eye-grammar-review.json` before production validation. This is the frame-by-frame visual gate for source-eye identity; numeric QA cannot reliably detect when a good state story swaps source eyes into white sclera crescents, hollow eyes, mismatched highlights, symbol eyes, or off-source blink styles.
- Treat thinking, working, and answering as high-visibility audition rows too. When the mascot has visible or ambiguous appendages, a partial audition can approve story direction, but it must not approve production art without anatomy review, state-performance review, and eye-grammar review; good state read is not enough when appendages drift, mascot acting stays stale, or source-eye identity drifts.
- Produce `qa/art-direction-review.json` before production validation. This is the visual gate for reference quality, identity preservation, eye grammar preservation, every-frame eye stability, flat cleanup-ready chroma, native enhancers, creative state readability, and the rule that identity/cleanup/anatomy regressions override a good state read. A production pass must record `statesReviewed` and `reviewedFrames` for every used frame; a pack-level checkbox is not enough to prove every-frame eye grammar.
- Produce `qa/production-readiness-report.json` after source audit, strict validation, quality analysis, and manual reviews. This production-readiness report should be the final evidence summary before human visual approval; it must block unresolved source cleanup failures, row-source evidence gaps, validation errors, strict validation warnings, quality failures, missing visual reviews, stale QA evidence, stale fallback handoffs, and stale manual visual reviews. It should summarize fallback repair intent, requiredEnvironment, explicit approval requirements, `requiredEnvironmentStatus`, `explicitUserApprovalReceived`, `approvalNote`, `executionBlockedBy`, `promptRepairContractOk`, missing prompt-repair contract checks, `sourceMode`, and candidate rejection reports when they exist so source repair preserves story, scale, identity, accepted expression/blink/mouth/appendage performance, and accepted cue vocabulary instead of becoming a redesign. Prompt repair contracts should be cue-agnostic: preserve accepted cue timing and compactness without forcing a particular mascot, prop, or visual-aid vocabulary; puff-specific wording belongs only when the current accepted row actually uses puffs. It records `fallbackRepairReady`, `blockedHandoffCount`, and `runnableHandoffCount` separately from `productionReady` so valid handoff evidence cannot be mistaken for permission or ability to run the repair. Candidate rejection summaries do not block production by themselves, but they keep repeated failed built-in attempts visible and mark the evidence stale when the recorded row source changes. A `sourceMode: "rejected-candidate"` fallback handoff is valid preflight evidence for a repair command; it does not make the rejected candidate a production source, and the run still needs a strict-recorded repaired row before acceptance. Fallback handoff summaries are preflight evidence only: missing `OPENAI_API_KEY`, missing explicit approval, stale fallback handoffs, or a failed `promptRepairContract` appears in `executionBlockedBy` and must be resolved before running real CLI/API generation. The rule is: manual visual reviews must be newer than the current manifest, atlas image, `qa/contact-sheet.png`, `qa/cutout-check.png`, `qa/state-readability-check.png`, `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, and `qa/previews/` files so a previous visual pass cannot approve newly assembled or newly analyzed art. Fallback handoffs must be newer than the current manifest, current imagegen-jobs.json, current row source or rejected-candidate repair source, and current fallback prompt so an old repair command cannot preserve stale story/scale evidence or repair the wrong source.
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
- `qa/quality-report.json` reports low motion, near-duplicate transitions, body jitter, major area jumps, same-row or cross-state scale drift, missing enhancer presence, or semantic anchor drift.
- `qa/anatomy-review.json` is missing for a production run, has `status` other than `pass`, omits a used frame from `reviewedFrames`, uses vague `expectedAnatomy` instead of naming body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy, contains blockers, or reports any required anatomy check as false.
- `qa/state-performance-review.json` is missing for a production run, has `status` other than `pass`, has `productionUse` other than `true`, omits a used frame from `reviewedFrames`, omits `expectedStateReads` for any state, contains blockers, omits `checks.coherentStateStoryArc`, omits `checks.mascotActingVariesAcrossFrames`, or reports any required state-performance check as false.
- `qa/eye-grammar-review.json` is missing for a production run, has `status` other than `pass`, has `productionUse` other than `true`, omits a used frame from `reviewedFrames`, omits `expectedEyeGrammar`, records vague `expectedEyeGrammar` that does not describe source eye count/shape, fill or pupil color, highlight/catchlight logic, spacing/placement, and blink style, contains blockers, or reports any required eye-grammar check as false.
- `qa/art-direction-review.json` is missing for a production run, has `status` other than `pass`, has `productionUse` other than `true`, omits a used frame from `reviewedFrames`, contains blockers, or reports any required art-direction check as false.
- `qa/production-readiness-report.json` is missing, records `productionReady` other than `true`, or lists any blocker, including stale QA evidence; a good state read does not override source cleanup, identity, eye grammar, anatomy, validation, or fallback provenance gaps.
- A row has an appealing state performance but fails the source-character contract: eye grammar swaps in any frame, the source chroma key is not flat/cleanup-ready, pixel-art treatment changes, anatomy/identity props regress, or the mascot no longer matches the canonical base.
- A state row reads as a random emotion collage instead of one coherent loopable performance story, including abrupt mood jumps, unrelated sad/serious/sleepy/angry/blank faces, or expression changes not caused by the state action.
- A state row lacks coordinated expression, body/appendage, and cue/prop choreography, or the enhancer moves while the mascot itself keeps parked hands, frozen appendages, or an unchanged face.
- A mascot with usable hands, paws, sleeves, arms, or held props leaves those appendages frozen across a high-visibility row instead of using small safe appendage acting beats.
- A `thinking` row reads as worried, confused, sad, angry, sleepy, idle/resting, meditating, strain/effort grimace, or error-state acting instead of curious pondering/processing, or adds unsupported lower-face/chin marks that read as accidental face artifacts or extra anatomy rather than a connected thinking gesture.
- `style.renderingStyle` is missing from a new production pack or is not `codex-pixel-art`.
- `style.visualLanguage` is required by the run policy but missing, or an enhanced state omits required `enhancer.visualLanguageFit`.
- `style.stateClarity` is malformed.
- `style.stateClarity` is `pose-only` but state rows introduce unrequested semantic props.
- `style.stateClarity` is `semantic-enhancers` but `thinking`, `listening`, or `answering` omit `enhancer` metadata; optional explicitly requested states such as `working` need the same metadata when present.
- `imagegen-jobs.json` is missing for a normal generated pack, row jobs were generated before the base job was recorded, or row jobs omitted the canonical base/layout guide inputs.
- A completed base job is missing `base_style_analysis`, missing `base_style_strict_blocking_warning_codes`, or records strict base-source blockers such as `non_uniform_chroma_key_background`, `smooth_or_overdetailed_foreground_palette`, or `no_foreground_sprite_detected`.
- A production run was completed by manually editing `imagegen-jobs.json` or copying row files into `generated/` instead of recording selected `$imagegen` outputs with provenance. Explicit approved `$imagegen` CLI fallback outputs must use `source_provenance: "imagegen-cli-fallback"` and record `cli_fallback` metadata rather than being mislabeled as built-in, user, or artist art.
- Enhanced state metadata still contains draft planning wording such as `planned during row generation` instead of the accepted visual aid.
- A held, touched, near-hand, writing, or appendage-operated work-prop enhancer omits `enhancer.anatomyGuard`.
- `enhancer.anatomyGuard.allowedInteractors` uses vague language instead of exact named reference appendages or body parts.
- A `fins-no-hands` or `ambiguous-limbs` mascot uses held, near-hand, touched, writing, or appendage-operated work-prop semantics without a `style.anatomyContract` recording the stable body core, appendage count, appendage placement, and forbidden additions.
- A semantic enhancer is not readable at 64, 96, and 128 px.
- A semantic enhancer is readable only as generic particles or timid decoration rather than intentional, character-native state art.
- A semantic enhancer is readable but off-vibe: generic gears, circuit diagrams, speech panels, UI windows, or universal symbols that do not belong to the mascot's source world.
- A semantic enhancer is on-vibe but does not read as the intended state, such as decorative frost that does not communicate thinking/processing or speech.
- An optional work cue clones or echoes a must-keep identity prop, such as a second staff, wand, weapon, tool, badge, emblem, detached diamond/object, or prop-shaped glyph, instead of using the original prop to drive an attached active-end bloom/pulse/contact mark or a distinct target that touches the active end.
- An optional long-prop `working` row uses big body leans, cross-body swings, diagonal staff sweeps, unstable hand attachment, body-size changes, detached floor/object targets, or prop-count changes instead of small active-end-focused motion.
- An optional long-prop bloom is present but static, with no readable frame-by-frame change in size, shape, contact area, brightness, or cluster pattern.
- Optional active-end sparkle pixels drift away from the bloom cluster instead of staying touching, overlapping, or within a few pixels of the active prop end.
- An optional `working` row animates only the cue while the mascot body and emotion remain essentially static; every frame needs a small acting change such as body bob, head tilt, clothing settle, hand grip shift, subtle prop follow-through, eye direction, blink, mouth shape, or cheek/body tilt.
- An answering cue looks like a thinking bubble, random orb, detached round bubble, single isolated speck, one-frame voice tick, one-frame sound mark, cheek mark, face marking, or detached fleck rather than mouth-origin speech/voice motion.
- An optional `working` frame uses breath puffs, speech beads, panting clouds, sleepy exhale marks, mouth-origin puffs, or tired closed-eye holds that make the mascot read as panting, sleeping, or answering instead of working.
- An `answering` frame reads as tired panting or exhaling instead of engaged speaking/streaming from changing mouth shapes.
- The optional `working` face reads as angry/hostile, or gains invented angry brows, slanted angry eyes, narrowed hostile eyes, or V-shaped eye/brow marks, instead of busy, friendly, and character-appropriate.
- Eye whites/highlights, pupils, face base color, outfit, props, cheek marks, or signature markings change color because a state glow, bloom, aura, or prop palette bleeds into the mascot identity.
- An optional working prop surface uses readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, list rows, fine stripes, wood grain, plank lines, parallel grooves, or a tiny-document look instead of chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens.
- An optional no-hand work prop defaults to a notebook, paper, page, or parchment-like surface with lines/document texture instead of a slate, tablet, blank card stack, token tray, chunky tile, or blank non-text surface.
- A body-surface or rim-touching processing/work cue on a no-limb/simple-appendage mascot creates lower-rim or side-edge tokens that read as feet, extra limbs, extra wings, new paws, or detached appendages.
- A semantic enhancer is cropped, detached, text-dependent, or appears in unrelated states.
- A semantic enhancer wanders away from its intended anchor, changes sides without intent, or makes the row read as a different state.
- A semantic enhancer looks pasted on: mismatched outline, edge treatment, lighting, scale, pixel density, palette, or occlusion.
- A row or enhancer looks smooth, painterly, glossy, 3D, vector-flat, heavily antialiased, or otherwise unlike native Codex-style pixel art.
- A held enhancer causes extra hands, duplicate arms, new fingers/paws/fins, or other anatomy that was not in the source mascot.
- A state asks an appendage to perform an action outside its recorded affordances, such as face-touch by a fin that only has side-bob/tilt, or typing by a paw without fingers.
- A simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that reads as an extra appendage.
- A true no-limb mascot uses a held, near-hand, typing, writing, or grip-based semantic. Freestanding/resting props are allowed only when they sit beside or in front of the mascot, animate on their own, keep activity marks inside/on the prop surface, and do not imply hands, fingers, holding, typing, or writing.
- A fin/no-hand or ambiguous-limb mascot uses a held/touched prop without naming the exact existing fins, sleeves, paws, tentacles, or body parts allowed to interact with the prop in both the prompt and manifest.
- A held, touched, face-touch, typing, writing, pointing, presenting, or waving enhancer omits `enhancer.requiredAffordances` when the action depends on specific appendages.
- A state changes mascot scale between frames or between state rows instead of animating posture. Core silhouette scale drift, full-row core scale range, cross-state core scale mismatch, and core center drift are production blockers because they make the pack feel like multiple different mascots.
- Production semantic enhancers were added as post-process overlays instead of generated as integrated mascot art.
- Production final art was made with deterministic compositing, vector overlays, manual shape props, or another prototype-only path.
- `qa/art-direction-review.json` has a production generation method other than `imagegen-integrated-row-art`, `user-provided-integrated-row-art`, or `artist-provided-integrated-row-art`.
- `qa/art-direction-review.json` does not record `checks.eyeGrammarPreserved: true` for production acceptance.
- `qa/art-direction-review.json` does not record `checks.eyeGrammarStableEveryFrame: true` for production acceptance.
- `qa/art-direction-review.json` does not record `checks.cleanupReadyFlatChroma: true` for production acceptance.
- `qa/art-direction-review.json` does not record `checks.identityCleanupAndAnatomyOverrideStateRead: true` for production acceptance.
- `qa/art-direction-review.json` does not record `checks.themeNativeStateCues: true` for production acceptance.
- `qa/art-direction-review.json` does not include every used frame of every state in `reviewedFrames` for production acceptance.
- `qa/art-direction-review.json` does not record the original source reference that was used for visual comparison.
- `qa/eye-grammar-review.json` does not record `checks.noWhiteScleraOrCrescentSwap: true`, `checks.noMismatchedOrSymbolEyes: true`, and `checks.blinkStyleMatchesSource: true` for production acceptance.
- `qa/eye-grammar-review.json` does not include every used frame of every state in `reviewedFrames` for production acceptance.
- `qa/eye-grammar-review.json` uses a vague `expectedEyeGrammar` note instead of a concrete source-eye contract naming count/shape, fill or pupil color, highlight/catchlight logic, spacing/placement, and blink style.
- A key chatbot state has too few frames: use 8 frames for default production rows, 6 only for compact auditions, and 10-12 only for explicit smoothness passes that preserve identity and anatomy.
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
  retrieving: "thinking",
  toolCall: "thinking",
  streaming: "answering",
  complete: "success",
  error: "error",
  unclear: "confused",
  inactive: "sleeping"
};
```
