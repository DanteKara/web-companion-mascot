# State Enhancers

Use this reference when a chatbot mascot needs states that read clearly at website size.

## Clarity Choice

Before generating rows, ask the user to choose one profile unless they already specified it:

| Profile | Use When | Rule |
| --- | --- | --- |
| `pose-only` | The brand should feel quiet, premium, or minimal | Use expression, posture, timing, hands, and held identity props only. |
| `semantic-enhancers` | Users must instantly read waiting/status states | Add one small, anchored prop or effect to ambiguous states. |

Recommend `semantic-enhancers` for chatbot companions with `thinking`, `listening`, or `answering` states. Accept `pose-only` when the user wants a cleaner mascot and weaker state labeling is acceptable. Default chatbot packs should not include `working`; fold tool calls, retrieval, search, and backend waits into a more expressive `thinking`/processing row unless the user explicitly asks for a distinct work/tool state.

## Generic Enhancer Rules

- Start normal generated runs with `scripts/prepare_companion_run.py` so each state has a row prompt, layout guide, `imagegen-jobs.json`, and `qa/state-cue-plan.json` before image generation. Treat those files as planning aids, not proof that the final art works. Layout guide PNGs are intentionally empty construction inputs for spacing and safe padding; they are not mascot previews and should not be shown as the current output.
- Generate and record the canonical base before semantic rows. For production, record the base with `scripts/record_companion_imagegen_result.py --strict-base-style`; reject/regenerate bases that report `non_uniform_chroma_key_background`, `smooth_or_overdetailed_foreground_palette`, or `no_foreground_sprite_detected` before row jobs are generated. Enhanced row jobs should use the original reference, `references/canonical-base.png`, `generated/base.png`, and the state layout guide as grounding inputs.
- Treat the canonical base as production art, not a loose sketch. It is the final atlas-frame source of truth, not concept art, a preview illustration, a pose-sheet sample, an app icon, or a softened style target. It should read like a Codex app digital pet first and a website mascot second: fully visible, readable as a tiny digital pet, and suitable for animation into a 192x208 sprite cell even if the final web atlas later uses larger cells. It should already be native flat pixel art with only named anatomy and identity props, simple enough to reproduce across eight row frames without redesign; unrequested feet, legs, chest lights, badges, emblems, screens, buttons, tools, or extra props become row-preservation baggage. Draw it as if it was first made on a tiny 64x72 or 80x90 pixel grid and enlarged with nearest-neighbor scaling. Use indexed-color sprite discipline: roughly 8-16 non-background colors, no per-pixel color ramps, no smooth shade bands, no gradient-filled body, face panel, antenna, or mittens, no blended intermediate palette colors, and no dozens of near-identical color steps. Preserve the strongest accepted character choices while flattening the rendering; only simplify colors and material treatment. Reject and regenerate bases that are smoother, glossier, more detailed, or less pixel-native than the intended row art. Reject glossy gradients, soft airbrush shading, bloom, rim glow, broad shine patches, transparent or semi-transparent shines, feathered transitions, high-detail shine, 3D lighting, smooth radial gradients, soft cylindrical shading, pillow shading, app-icon material lighting, smooth antialias fringes, and smooth vector curves in the base before generating enhanced rows. Use one or two chunky stair-step shadow clusters, not continuous tone ramps. If the source vibe is soft or friendly, keep that softness in rounded silhouette and expression, not blurred rendering. Do not compose it as a large glossy product mascot, large hero character, app icon, or high-resolution sticker; leave generous chroma-key padding and keep it compact. Preserve absence in rows: when the canonical base has a plain body, reject new chest panels, status lights, belly screens, buttons, badges, dot clusters, readouts, emblems, or robot UI details. When the canonical base has a rounded footless lower body, reject foot nubs, shoes, base tabs, toe pixels, shadow feet, or lower protrusions.
- Pick props from the mascot's world, not from a universal icon set.
- Before picking state cues, infer the mascot's vibe from the reference: source personality, recurring motifs, and generic cues to avoid. The user should not have to provide this. Record it briefly when useful, but treat it as a prompt-planning aid rather than paperwork.
- Use one enhancer per state by default.
- Follow HatchPet-style sprite artifact rules: pose, expression, and silhouette carry the state first; effects are allowed only when state-relevant, opaque, hard-edged, pixel-style, inside the same frame slot, and source-bound to the mascot silhouette, mouth edge, hand, tool, worn prop, or state source. Use a perfectly uniform solid chroma-key background from corner to corner; reject vignette, lighting falloff, texture, noise, shadow, ground plane, or background glow.
- Anchor enhancers to the mascot by touch, overlap, tail, held contact, worn contact, body-surface marks, prop-tip contact, mouth-edge contact, or another clear physical relationship. Detached-but-anchored cues are exception-only for chatbot readability; keep them tiny, close to their source, visually associated by proximity, timing, gaze, or a tiny tail dot, and secondary to the mascot.
- Write a tiny state card before generating each enhanced row: semantic read, chosen prop/effect, exact anchor, body parts allowed to interact with it, and forbidden artifacts.
- Keep enhancers inside the sprite cell with safe padding for every frame.
- Avoid text, labels, UI panels, detached punctuation, loose sparkles, and large scenery.
- Use an enhancer only when pose, expression, and motion are not enough.
- Keep the mascot's outfit, outline, palette, face, proportions, and pixel density consistent across all rows.
- Production enhancers and state rows must stay in Codex-style pixel art: visible stepped pixel edges, crisp clusters, thick 1-2 px outline, limited palette, flat cel shading, and hard-edged sprite effects. Reject smooth illustration, glossy app-icon art, painterly gradients, 3D shading, vector-flat symbols, high-detail antialiasing, or realistic material texture.
- For detailed references, treat signature props, emblems, clothing silhouettes, markings, and accessories as part of identity. Simplify ornate trim or tiny detail into a few readable pixel clusters, but keep must-keep props stable when they appear. A staff, wand, tool, badge, emblem, hat, bag, weapon, shell, or clothing trim should not flicker in and out across frames, duplicate itself, change sides unexpectedly, mutate into another object, or turn into extra anatomy. If a state is too crowded for a signature prop, omit it intentionally for the whole row instead of inconsistently across frames.
- Preserve signature props by default even when a semantic cue is present. Stage the cue in available space, near the mouth, near the head, or near the active prop end instead of dropping a must-keep staff, wand, tool, emblem, hat, or accessory. Omit a must-keep prop only when the state card explicitly marks that exact prop optional for the whole row. If a held prop aims, taps, charges, points, or moves, that active pose replaces the resting pose; do not show both the resting prop and a second active copy in the same frame.
- Animate the enhancer with follow-through; do not paste the same prop in every frame.
- Design semantic enhancers with a state-specific motion path, not just a static icon. Name where the effect begins, how it travels, where it holds for readability, and how it settles into the loop.
- The mascot must emotionally perform the state. Row prompts should specify eyes, mouth, blink, head angle, body settle, and appendage/prop follow-through; reject rows where the symbol reads but the face feels neutral or unrelated.
- Every state row should have a coherent performance story, not a random emotion collage. Expressions must be adjacent beats caused by the state action and loop cleanly back to the first frame. Good arcs look like calm -> blink -> settle, notice -> greet -> settle, neutral-curious -> pondering -> idea lands -> pleased settle, or ready -> speaking -> conversational blink/smile -> settle. Reject abrupt mood jumps, unrelated sad/sleepy/angry/blank faces, and facial expressions that do not fit the state.
- Enhanced row prompts should include positive acting choreography, not only bans. Coordinate three synchronized tracks: expression, body/appendage, and cue/prop. A good row lets those tracks take turns carrying motion so the state reads through the mascot's performance. Reject rows where a bubble, sparkle, check mark, or prop glow moves while the mascot keeps parked hands, frozen appendages, or the same face in every frame.
- High-visibility states must vary the expression across frames. `thinking` and `answering` should change at least two of eye direction, blink/closed eyes, tiny anchored pupil/highlight shifts, mouth shape, smile/open-mouth size, cheek/body tilt, and hand/appendage pose. Expression variation must stay inside the mascot's existing eye grammar, not swap eye styles. Optional explicitly requested `working` rows should meet the same acting standard. Reject rows where every frame has the same face while only the visual aid changes.
- For mascots with usable hands, paws, sleeves, arms, or other expressive appendages, require small appendage acting, not merely appendage continuity. Do not leave hands, paws, sleeves, or held props frozen across the whole row. High-visibility rows should include at least two small safe appendage acting beats while preserving exact appendage count. For default generic mitten-hand thinking, use side-anchored hand motion only: side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck. Treat simple mittens, sleeve nubs, rounded side hands, and fingerless blobs as conservative side appendages, not articulated hands; do not use pointing, presenting across the body, typing, writing, gripping, or face-touch acting unless the reference and an audition prove the affordance. If an identity prop is held, keep the prop-holding hand attached. For default thinking, keep a face-panel exclusion zone: no hand, paw, sleeve, mitten, finger, or prop may enter the face panel, touch the cheek/mouth/chin/lower face, or sit centered directly below the mouth/chin. Reject extra hands, duplicate arms, detached mittens, finger clusters, new grip anatomy, hand-to-chin poses, hand-to-mouth poses, clasped hands under the mouth, lower-face/chin-adjacent hand poses, under-chin presenting poses, and scalloped mitten/bib clusters below the face.
- Keep an art direction floor. Reject rows that are anatomically correct but bland, stiff, generic, timid, or symbol-only. Good production rows should look like polished mascot acting: expressive eyes, mouth shapes, head/body tilt, timing, appendage follow-through, tasteful asymmetry, and deliberate frame-to-frame changes inside the reference's own visual language.
- Preserve the full reference palette as identity. Keep the actual source colors for eye whites/highlights, pupils, eye outlines, face base color, cheek marks, outfit, props, and signature markings. Do not force white eyes or white highlights when the reference uses another color; only keep whites white when the source uses white. Do not let a glow, aura, bloom, prop color, or gold effect tint or recolor the mascot identity palette.
- Preserve eye grammar as identity. Keep the canonical base eye count, shape, size, spacing, outline color, pupil/fill color, and catchlight/highlight logic across the row. Use gaze shifts, blinks, and tiny pupil/highlight shifts only as deliberate acting beats. Reject hollow or inverted eyes, dark eyes turned into white ovals with dark rims, extra catchlights, glossy anime eyes, vertical slit pupils, square UI eyes, mismatched eyes, and one-frame eye-style swaps. For solid dark base eyes, open eyes should remain mostly dark with the original tiny highlight; do not expose white sclera crescents, carve white crescent gaps to fake side glances, or make a white cutout the dominant eye shape. If an up-glance, side-glance, blink, or speaking beat would require changing eye style, keep the eyes forward or nearly forward and carry the acting through head tilt, body bob, mouth shape, blink timing, appendage pose, or the approved cue instead. Keep eye centers inside the original eye boxes; never slide eyes onto cheeks, panel edges, the mouth line, or outside the face panel. Do not replace eyes with loading dots, LEDs, status bars, diagonal slashes, crosses, punctuation, or reaction icons. Closed-eye blinks should be simple closed curves or horizontal pixel lines in the same eye positions and spacing, not X-eyes, chevrons, reaction glyphs, eyebrows, or lower-face squiggles.
- For near-head bubbles, sound rings, work orbs, and similar detached-but-anchored effects, lock the mascot body footprint first: same body center, same silhouette scale, same top and bottom body edges, and the same appendage count across the row. Animate the effect around the mascot; do not let the model make the character zoom, shrink, or reposition to accommodate the effect. Use visual association without making QA count the cue as body size: keep a 2-4 px chroma-key gap when a growing cue would otherwise alpha-connect to the mascot core, expression panel, accessory, or outline. Proximity, eye tracking, timing, or one tiny separated tail dot can show the source.
- Keep near-head cues separate from must-keep identity props. A thought bubble, voice puff, work glyph, or status cue should not cover, replace, recolor, merge with, or grow out of antenna bulbs, ears, horns, hats, badges, emblems, staffs, wands, or other identity props unless that prop is explicitly the active source. For antenna mascots, thinking cues should originate from the inferred thought-cue source near the expression area, not from the antenna tip, and the antenna bulb should remain visible and stable. Preserve the body footprint too: if touching the cue to the outline would make the head/body measure larger, use a close 2-4 px chroma-key gap or tiny separated tail dot instead of fusing the bubble into the sprite.
- For thinking bubbles or puffs, prefer a believable side/top-origin trajectory when acting alone is too subtle: begin close to the inferred thought-cue source with a 2-4 px chroma-key gap or a tiny separated tail dot, grow from small bubble to slightly larger bubble to medium bubble, then shrink back down before the loop settles. Any later drift must remain tiny and visually associated with the source without alpha-connecting to the mascot core. Medium is the maximum thought cue size; the cue stays secondary to the mascot, never larger than about one-quarter of the mascot body width, and must not become a second head/body-sized orb. Use one cue family across the row; avoid giant bubble peaks, straight-up hovering icons unless that direction is intentionally chosen for the character, cue pop-in, one-frame cue appearances, abrupt cue dropout at the loop, detached lightbulbs, rays, punctuation, data-cloud substitutions, and rows where the same bubble is pasted into every frame. `thinking` also covers planning, retrieval, tool-use waiting, and backend progress by default.
- `thinking` should read as curious pondering and processing, not worry, confusion, sadness, anger, sleepiness, surprise, answering, or error. Prefer neutral-curious, tiny closed pondering mouths, one-pixel thoughtful line mouths, quick active processing blink/hold, and small recognition-smile beats. Recognition in thinking should be a closed or tiny pixel smile, not a wide open speaking mouth, exclamation mouth, or answering syllable mouth. Avoid downturned frowns, curled lower-lip marks, worried squiggles, confused/error mouth shapes, sleepy closed-eye smiles, and open exclamation or speaking-mouth frames. Any closed-eye thinking frame must read as a quick active processing blink, not sleep, idle rest, fatigue, or meditation; keep the thought cue active during that blink and place open-eye curious or recognition frames immediately before and after it. Processing blinks should use simple closed curved or short horizontal eyes, not squeezed shut X-eyes, chevron eyes, scrunched effort eyes, or strain grimaces. For default hand or paw mascots, keep the face panel and lower face completely clear; use side-anchored hand motion such as side bob, side tilt, low side lift, tiny outward tilt, or low outer-body tuck only. For simple mittens, sleeve nubs, rounded side hands, or fingerless blobs, use side-bob, side-tilt, tiny outward tilt, low side lift, or side tuck only; do not use pointing, presenting across the body, typing, writing, gripping, or face-touch acting unless the reference and an audition prove the affordance. Do not move one hand inward toward the face, point toward the head, cross the body front, or drop hands to the bottom edge where they read as feet, legs, or lower tabs. Reject hand-to-chin, hand-to-mouth, clasped hands under the mouth, prayer hands, finger points into the face, scalloped mitten/bib clusters below the face, lower-face/chin-adjacent hand poses, under-chin presenting poses, and lower-face patches. Face-touch requires an explicit affordance and a successful audition. For no-limb and simple-appendage mascots, do not fake a thinking pose with chin-touch, cheek-touch, hand-to-chin, lower-face squiggles, extra mouth ticks, chin marks, moustache-like pixels, or small appendage-colored marks on the lower face/chin; those read as accidental artifacts or extra anatomy. Use eyes, blink timing, mouth shape, body tilt, and the thought cue instead.
- Avoid under-designed semantics. Tiny dots, generic particles, or minimal marks are not enough for production unless they clearly look like intentional character art at 64, 96, and 128 px. For `thinking`, loose sparkles, isolated white specks, star glints, diamond flecks, single-pixel dust, and stray final-frame dots are blockers; use one deliberate compact thought puff, bubble cluster, idea orb, or processing aura with hard-edged pixel mass and a clear inferred source near the expression area. If a state reads as "status particles" rather than the intended behavior, regenerate with a richer but still anchored concept.
- Avoid off-vibe semantics, but do not replace them with decorative ambiguity. Generic gears, circuit diagrams, speech panels, UI windows, or universal assistant icons are blockers when the source mascot's world suggests softer or different motifs. So are motif-native effects that do not communicate the state. For example, icy breath can read as `answering`, but a pretty frost shimmer may not read as planning/processing unless the face, timing, and motion also show purposeful thought.
- If the user explicitly requests optional `working`, it must show a concrete action with a before/during/after transformation, not a decorative detached prop or status icon. The mascot should operate, sort, check, gather, stamp, charge, pulse, bloom, or resolve something through face, gaze, body lean, original hands/appendages, identity prop, or a compact attached/overlapping cue. Random floating squares, decorative sparkles, status icons, detached diamonds, or a final check mark with no preceding work action are not production-quality working semantics.
- Choose optional work cues from the mascot's visual language. Tech/robot mascots can use panels, tablets, sliders, or status blocks; fantasy/magic mascots with long held props should usually use attached active-end blooms, staff-tip glyphs, or glowing sorted motes before separate spell circles, rune tiles, or charm tokens; nature mascots can sort leaves, seeds, stones, or wooden tokens; icy/water mascots can use frost tiles, droplets, or crystal tokens. Generic UI blocks are off-vibe unless the mascot itself is tech/product/tool themed.
- If an explicitly requested work state uses a signature staff, wand, weapon, tool, brush, pen, pointer, badge, or emblem, use that existing prop as the source of the work action and keep the cue visually distinct. For long held props, prefer a small hard-edged pixel bloom, aura, pulse, or contact mark wrapped around, touching, or overlapping the active end; animate its intensity/shape while eyes, mouth, and subtle hand/prop motion perform the state. Use a visible cycle such as dim seed -> small bloom -> brighter wrap -> peak cluster -> shrinking settle, then loop cleanly. Small sparkle pixels are allowed only when they belong to the active-end bloom cluster and remain touching, overlapping, or within a few pixels of the active prop end. Do not paste the same static glow in every frame. Do not draw a detached diamond/object, second copy of the prop, prop-shaped glyph, floor target, badge, emblem, or echo that reads as a duplicate identity object. Do not echo identity emblems, logos, badges, weapon silhouettes, or signature markings inside any work target; no copied trident, logo, badge, emblem, or identity symbol inside the target. Use plain abstract dots, squares, diamonds, bars, or motes instead. When the prop moves, keep it one continuous object with the original hand-to-prop attachment visible.
- Place optional work cues in the mascot's believable interaction zone: near the active hand, paw, mouth, active tool end, staff head, wand tip, or gaze focus. For long props, the active end is the wand tip, staff head, tool bit, pointer tip, brush tip, pen tip, blade tip, or nozzle, not the floor, base, butt end, handle end, or lower shaft unless the source design clearly uses that end. Separate targets are fallback choices for long props; if used, they must touch or overlap the active end and not drift into the floor, far side, or empty space.
- For mascots with real hands, paws, staffs, wands, tools, or held identity props, optional work cues should touch, overlap, hover just above, wrap around, or sit within a few pixels of the active hand or active prop end. Avoid floor-level token rows and far-floating targets unless that interaction style is native to the character.
- Keep optional long-prop working motion small and active-end-focused: preserve the same top edge, bottom edge, body core width, prop count, appendage count, and hand-to-prop attachment; avoid large full-body leans, big cross-body swings, diagonal staff sweeps, and full-body scale shifts.
- Every optional `working` frame should include visible mascot acting, not only cue animation. Use small stable changes such as body bob, head tilt, surface/detail settle, hand grip shift, subtle prop follow-through, eye direction, blink, mouth shape, or cheek/body tilt. The emotional beat should read as notice -> focus -> effort -> progress -> pleased settle while staying friendly.
- `answering` should read as talking through performance first: clear mouth shapes, lively eyes, blink timing, tiny conversational bob, and loopable speaking rhythm. Speech pixels, tiny sound rings, sound ticks, breath marks, or glow marks are optional; omit them when they cannot stay clearly attached to the mouth. For no-limb, fins-no-hands, and ambiguous-limb mascots, prefer mouth-only answering unless a cue is unmistakably mouth-attached; omit voice pixels instead of creating a cheek mark or detached fleck. When used, they must touch or overlap the mouth/lip edge or begin within 1-2 pixels of it, form a short 2-3 frame outward trail, and stay secondary to the mouth animation. If a cue cannot appear in at least two adjacent frames with a mouth-origin progression, omit it. Use breath, frost, smoke, or cloud puffs only when they belong to the source mascot and still read as speech. Reject thought-bubble-like cues, chat panels, repeated exhale clouds, odd detached round bubbles, single isolated specks, one-frame voice ticks, one-frame sound marks, cheek marks, face markings, or detached flecks that do not read as streaming speech, but do not over-police tiny cue geometry when the mascot already clearly looks like it is talking.
- Preserve the mascot's expression grammar. Do not invent angry brows, hostile eyes, slanted angry eyes, narrowed hostile eyes, V-shaped eye/brow marks, teeth, sweat, blush, or dramatic emotion marks as shortcuts for state clarity when the source design does not use them. For optional `working`, concentration should come from attentive eyes, blink timing, mouth shape, lean, pace, existing props/appendages, or a purposeful processing cue while staying character-appropriate. Reject even a single `working` frame that reads angry or hostile.
- Make semantic cues survive assembly. Isolated tiny specks, far-away dots, or ultra-thin marks often disappear during cleanup, while preserving them can shrink the body around the effect. If a cue is necessary, make it compact, attached, rim-touching, body-surface, or close-overlapping enough to remain readable at 64-96 px without looking like a new limb.
- For body-surface, rim-touching, or compact attached processing/work cues on no-limb or simple-appendage mascots, keep the cue inside the body core or as one small rim-touching mark. Repeated leaf, oval, wing, paw, mitten, droplet, or appendage-colored tokens along the lower rim or side edges often read as feet, extra limbs, extra wings, new paws, or detached appendages. Prefer one small central glyph/status band or 1-3 high-contrast square, dot, check, or token marks inside the silhouette, with colors and shapes distinct from sprouts, ears, fins, wings, paws, sleeves, tails, and other real anatomy.
- Use this semantic ladder: first acting through face, eyes, mouth, posture, timing, and original appendages; second existing identity props if the mascot has them; third one small attached, overlapping, body-surface, rim-touching, or tightly anchored effect; fourth detached effects only when they are natural for the character, remain readable, and stay visibly connected to the source.
- Generate production enhancers as part of the mascot artwork. Do not add vector, CSS, or hand-drawn overlays after generation unless the user explicitly wants a throwaway prototype.
- Do not use local scripts or deterministic compositors to create final enhancer pixels. Scripts may assemble and validate row art, but production semantics must come from `$imagegen` row generation or from user/artist-provided integrated row art.
- Match the base mascot's line weight, pixel grid, palette, lighting direction, flat shading, edge treatment, pixel density, and occlusion. A good enhancer should look like it was designed by the same pixel artist in the same pass.
- Preserve the reference's identity and personality while translating it into the Codex pixel companion style. Do not simplify a detailed mascot into a flatter or more generic sprite just to make enhancers easier to place.
- For held or touched props, the mascot must use only existing hands, paws, fins, sleeves, tentacles, or identity body parts that have a matching `grip`, `brace`, `face-touch`, `typing`, or `writing` affordance. Reject extra hands, duplicate arms, new fingers, cloned sleeves, disconnected mitts, or props held by anatomy the source character does not have.
- Existing appendages may be expressive when their audited affordances support the action. Do not overconstrain real hands into static side limbs; hands with `face-touch`, `grip`, `point`, or `present` affordances can use rich acting. For fins, paws, sleeves, mitts, tentacles, wings, or similar simple appendages, use only the actions recorded in `style.anatomyContract.appendages[].affordances`. The blocker is invented anatomy or unsupported action, not motion itself.
- For face-touch, cheek-touch, chin-touch, presenting, held-prop, or appendage-operated props, preserve a clear silhouette path back to the original body anchor. Leave enough outline or tiny negative space where the appendage nears the face or prop so the gesture reads as the original hand, paw, sleeve, tentacle, or arm, not a new cheek, nose, face patch, detached mitten, duplicated hand, or extra paw. Prefer broad pixel-mitt/paw poses over tiny fingers unless the reference clearly has fingers.
- If the mascot has simple or ambiguous limbs, choose props that can sit against the body, tuck under an existing limb, hover near the head, or rest beside/in front of the mascot instead of requiring detailed fingers. Face-touch and cross-body gestures are high-risk unless the exact appendage has a `face-touch` affordance and an audition proves it reads as the original appendage.
- For mascots with fins, sleeves, tentacles, or mitten-like limbs, held/touched props are allowed only when those appendages already exist in the reference and declare a matching `grip` or `brace` affordance. Keep props chunky and easy to brace; avoid finger-dependent typing/writing unless the reference has fingers and `typing` or `writing` affordances. The state card must name the exact existing appendages from `style.anatomyContract` and forbid extra hands, fingers, fins, sleeves, or grip anatomy.
- For mascots with `style.anatomyClass` set to `no-limbs`, avoid grip semantics entirely. Do not use held/touched/typing/writing props such as slates, tablets, keyboards, pencils, quills, parchment, or paper, even if the prompt says "no extra hands"; these words often cause image models to invent hand-like anatomy. First try face/body acting plus body-surface, rim-touching, attached, or overlapping processing cues. A freestanding or resting work prop is a last-resort fallback only for explicitly requested `working`, when it sits beside or in front of the mascot, animates on its own, and the prompt says the mascot works by looking, leaning, bobbing, and reacting, not by holding, typing, writing, or inventing hands. Prefer slates, tablets, blank card stacks, token trays, chunky work tiles, or solid work surfaces over notebook/paper/page surfaces; if the user specifically asks for paper, keep it blank except for large non-text tokens. Keep a clear background gap between the mascot and prop; no part of the prop or activity marks may touch the body, appendages, outline, or effects. Keep sorting/checking/gathering motion inside or on the prop surface, not in the empty gap, because rising pips, sparkles, crystals, or motion marks can merge the prop with the mascot body during cleanup and QA. Otherwise prefer non-grip semantics: body-surface processing glyphs, pulsing core marks, aura/status bands, near-head processing orbs, facial/mouth motion, body-pose, or worn charms.
- For held, touched, near-hand, writing, or appendage-operated optional work-prop enhancers, add `enhancer.anatomyGuard` metadata to the manifest. Strict validation treats missing anatomy guards as a production warning, which fails strict runs.
- After final row art is selected, replace any draft `enhancer.kind` such as `planned during row generation` with the actual visual aid that passed review. Strict validation warns on leftover planning placeholders.

## Reference Anatomy Audit

Before generating state cards, audit the source image and write the contract into the manifest:

```text
body core: the stable central body shape that should not scale or drift
appendages: exact visible appendages, counted and named by placement
affordances: what each appendage can safely do, such as side-bob, tilt, wave, point, present, face-touch, grip, brace, typing, or writing
allowed motion: how those exact appendages may move
forbidden additions: anatomy the generator must not add
ambiguous marks: highlights, shadows, clothing edges, or effects that are not appendages
```

Use the audit as a lock, not as a freeze. Existing appendages can lift, wave, brace, tuck, or settle if the state needs acting and the appendage affordances allow it, but the row must keep the same appendage count and identity. If the reference has two side fins, the prompt should say `left side fin` and `right side fin`; if it has sleeves, name the sleeves; if it has paws, name the paws. Do not use generic phrases like `existing appendages only` in the final state card or manifest, because they do not tell the next agent what to inspect.

For simple appendages, treat face-touching as a high-risk gesture. If a fin, sleeve, paw, tentacle, wing, or mitt-like limb lifted toward the face starts reading like a new hand, a fingered mitten, a detached prop, or an extra limb, reject that row and regenerate with no cross-body appendage gesture. Keep the appendages side-attached with only small tilt/tuck motion, and make the state read through eye direction, mouth shape, blink timing, body lean, and the anchored enhancer. For screen-faced, mask-faced, or simple front-panel mascots, also preserve the face/body panel shape; do not skew, stretch, rotate, squash, or trapezoid the panel to create acting.

Also reject simple-appendage rows where a limb-colored oval, patch, detached blob, or front-body shape appears and could be read as an extra fin, sleeve, paw, mitt, or hand. This can happen even when the side appendages remain correctly attached. Regenerate with plain body shading and move the state read into the face, body tilt, blink timing, or a clearly separate near-head/aura/body-surface enhancer that does not share the appendage silhouette.

## State Card Pattern

Use this compact card in row prompts and QA notes. The first two examples are for explicitly requested optional `working` rows:

```text
state: working
rendering style: codex-pixel-art
semantic read: backend/tool work
anatomy class: simple-appendages
enhancer: theme-native work prop
vibe fit: why this prop/effect belongs to the source mascot's world and still reads as work
frame arc: notice prop -> prop wakes up -> sorting/checking/gathering -> active work peak -> progress/result tick -> settle
anchor: held low and braced only by the original visible appendages
required affordance: grip or brace
allowed anatomy: exact named appendages from style.anatomyContract only, no new grip anatomy
prop continuity: one physical held prop only; if the prop moves, active pose replaces resting pose and keeps original hand-to-prop attachment visible
forbidden: extra hands, extra limbs, new fingers, cloned sleeves, detached prop, duplicate active/resting prop copies, pasted-on prop, text labels, copied UI panel, pseudo-writing, tiny code/text lines
```

For no-hand mascots, use a non-grip card instead:

```text
state: working
rendering style: codex-pixel-art
semantic read: backend/tool work
anatomy class: no-limbs or fins-no-hands
enhancer: body-surface/rim-touching/attached processing cue first; freestanding or resting work prop only as fallback
vibe fit: why a central glyph, status band, token mark, or last-resort slate/tablet/token tray belongs to the mascot
frame arc: notice cue -> cue wakes up -> sorting/checking/gathering -> active work peak -> progress/result tick -> settle
anchor: inside the body core, touching the rim, overlapping the body/prop, or beside/in front only when fallback freestanding prop is necessary
required affordance: none for no-hand acting; exact named appendage affordance if any appendage operates the cue
allowed anatomy: mascot looks, leans, bobs, and reacts; no appendage operates a prop unless the state card names the original appendage and affordance
allowed marks: chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens only; avoid notebook/paper/page surfaces unless specifically requested, and keep them blank except for non-text tokens; keep tray/tile/slate surfaces solid and unruled, without fine stripes, wood-grain lines, plank lines, or parallel grooves
forbidden: holding, typing, writing, hands, fingers, grip anatomy, decorative particles, static prop, text labels, copied UI panel, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, list rows, tiny-document surfaces, extra appendage-like lower-rim marks, prop touching the body if it is meant to be freestanding, rising pips/sparkles/crystals in the gap
```

For expressive pose states, the same guard should allow motion that the audited appendages can actually perform:

```text
state: thinking
rendering style: codex-pixel-art
semantic read: planning before output
anatomy class: simple-appendages
enhancer: side-origin theme-native thought cue
vibe fit: why this cue uses the mascot's own motifs instead of generic symbols
anchor: near upper-right side of head
required affordance: face-touch only for mascots whose exact hand/paw/appendage declares face-touch
allowed anatomy: same named original appendages may move within their affordances; otherwise keep simple appendages side-attached
forbidden: extra limbs, extra hands, fingers, detached mitts, duplicated appendages, changed body scale, pasted-on effect
```

The card should change with the mascot. The card should derive props and cue style from the specific reference instead of using a fixed universal object set. A true no-limb mascot should use face/body acting and one non-grip attached, near-head, body-surface, freestanding, or resting cue instead of a held prop.

## State Patterns

Use these as starting points, then adapt them to the companion's theme.

| State | Semantic Read | Modern Assistant | Fantasy / Character World | Minimal Alternative |
| --- | --- | --- | --- | --- |
| `listening` | Receiving user input | small sound rings, hand-to-ear, mic only for voice apps | hand cupped to hood/ear, attentive glow rings | lean toward input, eyes tracking |
| `thinking` | Planning, retrieval, tool-use waiting, or backend progress before output | compact thought cloud, idea orb, small processing halo, clear-face low hand beat | side/top-origin theme-native thought puff, floating crystal/orb near head, small aura loop, low side-lift or palm-up beat | head tilt, eyes up/side, blink hold, clear pondering/processing arc |
| `working` optional | Explicitly requested distinct tool/backend activity | laptop/tablet when hands can operate it; active tool-end pulse/contact mark for held tools; body-surface/rim processing cue first when hands cannot operate; freestanding tablet/slate/token tray only as fallback; non-text progress/check marks only | parchment/quill/tool when hands can operate it; attached staff/wand-tip bloom, aura, pulse, or contact mark first for long props; freestanding glowing slate/blank card stack only as fallback; non-text progress/check marks only | busy-friendly face, lean, body bob, purposeful attached cue motion |
| `answering` | Streaming response | mouth shapes, presenting hand, optional tiny speech pips/sound ticks/rings | speaking gesture, scroll unfurl, guiding prop, source-native breath only if it reads as speech | mouth shapes, rhythmic body/hand beats, conversational bob |
| `success` | Completed successfully | small check glint, thumbs up | raised staff/tool, celebratory charm | bounce, proud pose |
| `error` | Recoverable failure | warning badge, droop, small alert mark | dimmed charm, dropped prop, worried robe slump | worried face, recoil, recovery |
| `confused` | Needs clarification | small question bubble | tilted charm, searching orb | squint, head tilt |
| `sleeping` | Inactive/offline | small sleep bubble | hood droop, dim aura | slow breathing, closed eyes |

## Manifest Metadata

Record the chosen profile so future QA and React integration can understand the design intent:

```json
{
  "style": {
    "renderingStyle": "codex-pixel-art",
    "stateClarity": "semantic-enhancers",
    "enhancerTheme": "fantasy",
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
  },
  "states": {
    "thinking": {
      "row": 2,
      "frames": 10,
      "durations": [140, 120, 120, 160, 180, 120, 120, 160, 180, 220],
      "loop": true,
      "enhancer": {
        "kind": "thought-bubble",
        "attachment": "near-head",
        "description": "Small no-text thought bubble anchored near the head.",
        "visualLanguageFit": "Uses the same soft puff silhouette and pale blue snow highlights as the source mascot."
      }
    }
  }
}
```

For anatomy-risky props, record the guard explicitly:

```json
{
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
```

Allowed `attachment` values:

```text
held, worn, attached, freestanding, near-head, near-face, near-hand, aura, gesture, body-pose, resting
```

Allowed `style.anatomyClass` values:

```text
hands, paws, fins-no-hands, no-limbs, ambiguous-limbs
```

For `no-limbs`, strict validation rejects held/near-hand grip semantics and common typing/writing/work props, but allows explicit `freestanding` or `resting` work props that animate without appendage interaction. For `fins-no-hands` and `ambiguous-limbs`, strict validation allows held props only with `anatomyGuard` metadata and matching appendage affordances; visual QA must still reject any generated extra hands, fingers, duplicate fins, cloned sleeves, or invented grip anatomy.

## QA

For `semantic-enhancers`, reject or regenerate rows when:

- `thinking`, `listening`, or `answering` are unclear at 64, 96, and 128 px; optional explicitly requested `working` rows are unclear when present.
- `qa/state-readability-check.png` has not been generated and inspected.
- `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, or `qa/quality-report.json` is missing for a production run.
- `qa/anatomy-review.png` or `qa/anatomy-review.json` is missing for a production run, or the review does not explicitly cover every used frame of every state.
- `qa/state-performance-review.png` or `qa/state-performance-review.json` is missing for a production run, or the review does not explicitly cover every used frame of every state for intended state read, expression, cue motion, and wrong-state failures.
- `qa/art-direction-review.json` is missing, fails, or marks the pack as not ready for production.
- `qa/quality-report.json` reports semantic anchor drift, missing enhancer presence, near-duplicate animation, body jitter, or large foreground area changes.
- `qa/quality-report.json` reports detached fragments, broken-cut symptoms, core silhouette scale drift, or core center drift.
- The row reads as shuffled expressions instead of one coherent loopable mini-story, with abrupt mood jumps, unrelated sad/sleepy/angry/blank faces, or expression changes that are not caused by the state action.
- The row lacks positive acting choreography across expression, body/appendage, and cue/prop tracks, or all visible motion lives in the enhancer while the mascot itself stays static.
- A mascot with usable hands, paws, sleeves, arms, or held props keeps appendages frozen across the row instead of using at least two small safe appendage acting beats.
- A `thinking` row reads as worried, confused, sad, angry, sleepy, idle/resting, meditating, strain/effort grimace, or error-state acting instead of curious pondering/processing, or uses lower-face/chin marks that look like face-touch, extra anatomy, moustache-like pixels, or accidental squiggles.
- A default hand/paw `thinking` row lets a hand, paw, sleeve, mitten, finger, or prop enter the face panel, touch the cheek/mouth/chin/lower face, sit centered under the mouth/chin, form a lower-face/chin-adjacent hand pose, or become an under-chin presenting pose.
- A `thinking` recognition beat uses a wide open speaking mouth, exclamation mouth, or answering syllable mouth instead of a closed or tiny pixel smile.
- The enhancer is technically stable but creatively weak, such as tiny dots or generic particles that do not look like deliberate state art.
- The enhancer is technically readable but off-vibe, such as gears, circuit glyphs, speech panels, or generic assistant symbols on a mascot whose visual language suggests different motifs.
- The enhancer is on-vibe but does not read as the intended state, such as decorative frost that does not communicate thinking/processing or speech.
- An optional working cue clones or echoes a must-keep identity prop, such as a second staff, wand, weapon, badge, emblem, detached diamond/object, or prop-shaped glyph, instead of using the existing prop to drive an attached active-end bloom/pulse/contact mark or a distinct target that touches the active end.
- An optional long-prop working row turns the cue into a separate object that drifts away from the active end, or uses big body leans, cross-body swings, diagonal staff sweeps, unstable hand attachment, body-size changes, or prop-count changes to make the state read.
- An optional long-prop bloom is present but static, with no readable frame-by-frame change in size, shape, contact area, brightness, or cluster pattern.
- The answering row fails to look like talking through mouth shapes, eyes, and body rhythm, or its optional cue looks like a thinking bubble, random orb, chat panel, detached round bubble, single isolated speck, one-frame voice tick, one-frame sound mark, cheek mark, face marking, or detached fleck rather than supporting speech/voice motion.
- An optional working cue borrows answering/sleeping/exhaustion visuals: breath puffs, speech beads, panting clouds, sleepy exhale cues, mouth-origin puffs, or tired closed-eye holds make the frame read as panting, sleeping, or talking instead of working.
- The answering row reads as tired panting or exhaling rather than engaged talking/streaming; use lively or quick-blink eyes, changing mouth shapes, conversational body rhythm, and optional supporting voice pips/rings or one small mouth-tailed puff.
- The optional `working` face becomes angry, hostile, gains invented brows, slanted angry eyes, or V-shaped eye/brow marks, or feels unrelated to the work beat instead of busy, friendly, and character-appropriate.
- Eye whites/highlights, pupils, face base color, cheek marks, or signature face markings change color because a state glow, bloom, aura, or prop palette bleeds into the mascot identity.
- Eye grammar changes across the row: hollow or inverted eyes, dark eyes becoming white rimmed ovals, side glances carved as white crescent gaps in solid dark eyes, extra catchlights, glossy anime eyes, vertical slit pupils, square UI eyes, mismatched eye shapes, one-frame eye-style swaps, or closed-eye blinks that become X-eyes, chevrons, reaction glyphs, eyebrows, or lower-face squiggles.
- An optional working prop uses readable text, pseudo-writing, handwriting, numbers, letters, code lines, UI paragraphs, ruled notebook lines, list rows, or tiny-document surfaces instead of chunky non-text progress blocks, dots, check marks, sliders, or sorting tokens.
- An optional no-hand work prop defaults to a notebook, paper, page, or parchment-like surface with lines or document texture instead of a slate, tablet, blank card stack, token tray, chunky tile, or blank non-text surface.
- A tray, tile, or slate uses fine stripes, wood grain, plank lines, or parallel grooves that read like ruled notebook lines or pseudo-writing at website size.
- A body-surface or rim-touching processing/work cue on a no-limb/simple-appendage mascot creates repeated lower-rim or side-edge tokens that read as feet, extra limbs, extra wings, new paws, or detached appendages.
- A `thinking` cue is only loose sparkle dust, isolated white specks, star glints, diamond flecks, single-pixel dust, or a stray final-frame dot rather than a deliberate compact thought puff, bubble cluster, idea orb, or processing aura.
- A simple face panel, screen face, mask face, or plain body core skews, stretches, rotates, squashes, or becomes a trapezoid instead of preserving the canonical panel shape.
- An optional working cue disappears in the contact sheet/readability sheet after cleanup, or only remains when cleanup is loosened enough to keep noise/slivers.
- The enhancer is readable but mechanically placed, such as a bubble that only floats straight above the head with no acting beat, eye tracking, expression change, or believable trajectory.
- The enhancer is cropped, detached from the character, or visually leaks into neighboring cells.
- The enhancer changes sides, height, or anchor point without an intentional animated reason.
- The enhancer changes the mascot identity or makes the row feel like a different character.
- A near-head or aura enhancer causes the mascot body to resize, jump, or drift. Regenerate with a silhouette-locked prompt rather than accepting the row.
- A near-head cue alpha-connects to the mascot core, expression panel, accessory, or outline and makes QA measure the cue as body size instead of a separate semantic cue.
- A row shows bobbing, jumping, thinking, or emphasis with floor shadows, contact shadows, ground lines, baseline marks, landing marks, or dark under-body strokes instead of keeping the sprite to the mascot plus approved cue on chroma key.
- A semantic enhancer grows, rises, or widens and the mascot body appears to shrink or grow with it. The assembler should use a shared state-row fit scale, and the analyzer should still reject unresolved body core scale range above production tolerance.
- The row is less polished, less expressive, less creative, or visibly simpler than the source reference.
- The mascot face, eyes, mouth, posture, or body motion do not match the intended emotion of the state.
- The enhancer appears in the wrong state or persists into unrelated states.
- The row relies on text instead of visual meaning.
- The manifest omits `style.stateClarity` or per-state `enhancer` metadata for enhanced states.
- The enhanced row was generated without the canonical base and row layout guide listed in `imagegen-jobs.json`.
- The manifest still contains draft enhancer wording instead of the actual accepted visual aid.
- The manifest omits `style.renderingStyle: "codex-pixel-art"` for a new production pack.
- The enhancer looks pasted on: mismatched outline thickness, different edge treatment, wrong scale, flat vector styling over pixel art, inconsistent lighting, different pixel density, or no believable hand/body occlusion.
- The row or enhancer looks like smooth illustration, glossy app-icon art, 3D rendering, painterly gradients, high-detail antialiasing, vector-flat symbols, or CSS-scaled smooth art instead of native Codex-style pixel art.
- The enhancer was added by post-processing instead of generated as integrated row art, unless the package is clearly labeled as a prototype and not accepted as final.
- A held prop creates extra limbs, duplicate hands, new fingers/paws/fins, or inconsistent sleeves/body parts. This is a production blocker even if validation passes.
- A late frame in a row gains an extra hand, arm, sleeve, paw, fin, wing, mitten, or other appendage that earlier frames did not have. This should be caught in `qa/anatomy-review.png` by counting each numbered frame, not only by glancing at the overall contact sheet.
- A pose uses appendage motion but changes the appendage count, invents grip anatomy, detaches a limb, or makes the moving appendage look like a new object instead of the original body part.
- A state asks an appendage to perform an action outside its `style.anatomyContract.appendages[].affordances`, such as face-touch by a fin that only has side-bob/tilt, or typing by a paw without fingers.
- A simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that reads as an extra appendage, even if the original side appendages are still present.
- A face-touching or cross-body simple-appendage gesture reads as a hand, fingered mitten, detached prop, or extra limb. Regenerate with safer side-attached appendage motion and stronger face/enhancer acting.
- An optional working state uses a typing/writing prop with hands/fingers the reference character does not have. Use simpler braced/touched props or a non-grip semantic instead.
- An optional working state uses a slate, tablet, keyboard, pencil, quill, paper, or other grip prop for a true no-limb mascot. Use a non-grip body-surface, aura, near-head, facial, pose, freestanding, or resting semantic instead.
- An optional freestanding/resting work prop is static, too far away, looks like generic UI, touches the mascot body, or implies hidden hands/typing/writing instead of animating beside or in front of the mascot.
- Optional freestanding work motion bridges the empty gap between a freestanding prop and the mascot body with rising pips, sparkles, crystals, motion marks, or highlights. Keep work motion inside or on the prop surface so QA does not merge the prop with the body core.
- A held, touched, near-hand, writing, or appendage-operated optional work-prop enhancer is missing `enhancer.anatomyGuard` metadata.
- A held, touched, face-touch, typing, writing, pointing, presenting, or waving enhancer omits `enhancer.requiredAffordances` when the action depends on specific appendages.
- `enhancer.anatomyGuard.allowedInteractors` says only `existing appendages` or similar vague language instead of exact audited parts.
- A simple or ambiguous appendage mascot uses risky prop/near-hand semantics without `style.anatomyContract`.

For `pose-only`, reject or regenerate rows when:

- Any state introduces a new semantic prop that the user did not request.
- State readability depends on labels, captions, punctuation, or external UI.
