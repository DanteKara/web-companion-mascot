# State Enhancers

Use this reference when a chatbot mascot needs states that read clearly at website size.

## Clarity Choice

Before generating rows, ask the user to choose one profile unless they already specified it:

| Profile | Use When | Rule |
| --- | --- | --- |
| `pose-only` | The brand should feel quiet, premium, or minimal | Use expression, posture, timing, hands, and held identity props only. |
| `semantic-enhancers` | Users must instantly read waiting/status states | Add one small, anchored prop or effect to ambiguous states. |

Recommend `semantic-enhancers` for chatbot companions with `thinking`, `working`, `listening`, or `answering` states. Accept `pose-only` when the user wants a cleaner mascot and weaker state labeling is acceptable.

## Generic Enhancer Rules

- Start normal generated runs with `scripts/prepare_companion_run.py` so each state has a row prompt, layout guide, `imagegen-jobs.json`, and `qa/state-cue-plan.json` before image generation. Treat those files as planning aids, not proof that the final art works.
- Generate and record the canonical base before semantic rows. Enhanced row jobs should use the original reference, `references/canonical-base.png`, `generated/base.png`, and the state layout guide as grounding inputs.
- Pick props from the mascot's world, not from a universal icon set.
- Before picking state cues, infer the mascot's vibe from the reference: source personality, recurring motifs, and generic cues to avoid. The user should not have to provide this. Record it briefly when useful, but treat it as a prompt-planning aid rather than paperwork.
- Use one enhancer per state by default.
- Anchor enhancers to the mascot: held, worn, near-head, near-hand, near-face, aura, gesture, or body-pose.
- Write a tiny state card before generating each enhanced row: semantic read, chosen prop/effect, exact anchor, body parts allowed to interact with it, and forbidden artifacts.
- Keep enhancers inside the sprite cell with safe padding for every frame.
- Avoid text, labels, UI panels, detached punctuation, loose sparkles, and large scenery.
- Use an enhancer only when pose, expression, and motion are not enough.
- Keep the mascot's outfit, outline, palette, face, proportions, and pixel density consistent across all rows.
- Production enhancers and state rows must stay in Codex-style pixel art: visible stepped pixel edges, crisp clusters, thick 1-2 px outline, limited palette, flat cel shading, and hard-edged sprite effects. Reject smooth illustration, glossy app-icon art, painterly gradients, 3D shading, vector-flat symbols, high-detail antialiasing, or realistic material texture.
- Animate the enhancer with follow-through; do not paste the same prop in every frame.
- Design semantic enhancers with a state-specific motion path, not just a static icon. Name where the effect begins, how it travels, where it holds for readability, and how it settles into the loop.
- The mascot must emotionally perform the state. Row prompts should specify eyes, mouth, blink, head angle, body settle, and appendage/prop follow-through; reject rows where the symbol reads but the face feels neutral or unrelated.
- For near-head bubbles, sound rings, work orbs, and similar detached-but-anchored effects, lock the mascot body footprint first: same body center, same silhouette scale, same top and bottom body edges, and the same appendage count across the row. Animate the effect around the mascot; do not let the model make the character zoom, shrink, or reposition to accommodate the effect.
- For thinking bubbles or puffs, prefer a believable side-origin trajectory: begin near one side of the head or hood, grow from small bubble to medium bubble to the largest readable bubble/orb, hold while the mascot tracks it, then settle. Avoid straight-up hovering icons unless that direction is intentionally chosen for the character, and reject rows where the same bubble is pasted into every frame.
- Avoid under-designed semantics. Tiny dots, generic particles, or minimal marks are not enough for production unless they clearly look like intentional character art at 64, 96, and 128 px. If a state reads as "status particles" rather than the intended behavior, regenerate with a richer but still anchored concept.
- Avoid off-vibe semantics, but do not replace them with decorative ambiguity. Generic gears, circuit diagrams, speech panels, UI windows, or universal assistant icons are blockers when the source mascot's world suggests softer or different motifs. So are motif-native effects that do not communicate the state. For example, icy breath can read as `answering`, but a pretty frost shimmer may not read as `working` unless the face, timing, and motion also show purposeful activity.
- Preserve the mascot's expression grammar. Do not invent angry brows, hostile eyes, teeth, sweat, blush, or dramatic emotion marks as shortcuts for state clarity when the source design does not use them. For `working`, concentration should come from attentive eyes, blink timing, mouth shape, lean, pace, existing props/appendages, or a purposeful processing cue while staying character-appropriate.
- Make semantic cues survive assembly. Isolated tiny specks, far-away dots, or ultra-thin marks often disappear during cleanup, while preserving them can shrink the body around the effect. If a cue is necessary, make it compact, attached, rim-touching, body-surface, or close-overlapping enough to remain readable at 64-96 px without looking like a new limb.
- Use this semantic ladder: first acting through face, eyes, mouth, posture, timing, and original appendages; second existing identity props if the mascot has them; third one small attached/anchored effect; fourth detached effects only when they are natural for the character and remain readable.
- Generate production enhancers as part of the mascot artwork. Do not add vector, CSS, or hand-drawn overlays after generation unless the user explicitly wants a throwaway prototype.
- Do not use local scripts or deterministic compositors to create final enhancer pixels. Scripts may assemble and validate row art, but production semantics must come from `$imagegen` row generation or from user/artist-provided integrated row art.
- Match the base mascot's line weight, pixel grid, palette, lighting direction, flat shading, edge treatment, pixel density, and occlusion. A good enhancer should look like it was designed by the same pixel artist in the same pass.
- Preserve the reference's identity and personality while translating it into the Codex pixel companion style. Do not simplify a detailed mascot into a flatter or more generic sprite just to make enhancers easier to place.
- For held or touched props, the mascot must use only existing hands, paws, fins, sleeves, tentacles, or identity body parts that have a matching `grip`, `brace`, `face-touch`, `typing`, or `writing` affordance. Reject extra hands, duplicate arms, new fingers, cloned sleeves, disconnected mitts, or props held by anatomy the source character does not have.
- Existing appendages may be expressive when their audited affordances support the action. Do not overconstrain real hands into static side limbs; hands with `face-touch`, `grip`, `point`, or `present` affordances can use rich acting. For fins, paws, sleeves, mitts, tentacles, wings, or similar simple appendages, use only the actions recorded in `style.anatomyContract.appendages[].affordances`. The blocker is invented anatomy or unsupported action, not motion itself.
- If the mascot has simple or ambiguous limbs, choose props that can sit against the body, tuck under an existing limb, hover near the head, or rest beside/in front of the mascot instead of requiring detailed fingers. Face-touch and cross-body gestures are high-risk unless the exact appendage has a `face-touch` affordance and an audition proves it reads as the original appendage.
- For mascots with fins, sleeves, tentacles, or mitten-like limbs, held/touched props are allowed only when those appendages already exist in the reference and declare a matching `grip` or `brace` affordance. Keep props chunky and easy to brace; avoid finger-dependent typing/writing unless the reference has fingers and `typing` or `writing` affordances. The state card must name the exact existing appendages from `style.anatomyContract` and forbid extra hands, fingers, fins, sleeves, or grip anatomy.
- For mascots with `style.anatomyClass` set to `no-limbs`, avoid grip semantics entirely. Do not use held/touched/typing/writing props such as slates, tablets, keyboards, pencils, quills, parchment, or paper, even if the prompt says "no extra hands"; these words often cause image models to invent hand-like anatomy. A freestanding or resting work prop is allowed only when it sits beside or in front of the mascot, animates on its own, and the prompt says the mascot works by looking, leaning, bobbing, and reacting, not by holding, typing, writing, or inventing hands. Keep a clear background gap between the mascot and prop; no part of the prop or activity marks may touch the body, appendages, outline, or effects. Keep sorting/checking/gathering motion inside or on the prop surface, not in the empty gap, because rising pips, sparkles, crystals, or motion marks can merge the prop with the mascot body during cleanup and QA. Otherwise prefer non-grip semantics: body-surface processing glyphs, pulsing core marks, aura/status bands, near-head work orbs, facial/mouth motion, body-pose, or worn charms.
- For held, touched, near-hand, writing, or appendage-operated work-prop enhancers, add `enhancer.anatomyGuard` metadata to the manifest. Strict validation treats missing anatomy guards as a production warning, which fails strict runs.
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

For simple appendages, treat face-touching as a high-risk gesture. If a fin, sleeve, paw, tentacle, wing, or mitt-like limb lifted toward the face starts reading like a new hand, a fingered mitten, a detached prop, or an extra limb, reject that row and regenerate with no cross-body appendage gesture. Keep the appendages side-attached with only small tilt/tuck motion, and make the state read through eye direction, mouth shape, blink timing, body lean, and the anchored enhancer.

Also reject simple-appendage rows where a limb-colored oval, patch, detached blob, or front-body shape appears and could be read as an extra fin, sleeve, paw, mitt, or hand. This can happen even when the side appendages remain correctly attached. Regenerate with plain body shading and move the state read into the face, body tilt, blink timing, or a clearly separate near-head/aura/body-surface enhancer that does not share the appendage silhouette.

## State Card Pattern

Use this compact card in row prompts and QA notes:

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
forbidden: extra hands, extra limbs, new fingers, cloned sleeves, detached prop, pasted-on prop, text labels, copied UI panel
```

For no-hand mascots, use a non-grip card instead:

```text
state: working
rendering style: codex-pixel-art
semantic read: backend/tool work
anatomy class: no-limbs or fins-no-hands
enhancer: freestanding or resting work prop
vibe fit: why a small slate, tablet, notebook, card stack, or work surface belongs to the mascot
frame arc: notice prop -> prop wakes up -> sorting/checking/gathering -> active work peak -> progress/result tick -> settle
anchor: beside or in front of the mascot, close enough to feel integrated, not held
required affordance: none
allowed anatomy: mascot looks, leans, bobs, and reacts; no appendage operates the prop
forbidden: holding, typing, writing, hands, fingers, grip anatomy, decorative particles, static prop, text labels, copied UI panel, prop touching the body, rising pips/sparkles/crystals in the gap
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

The card should change with the mascot. A hooded fantasy character might use parchment and sleeves; a modern bot might use a tablet; a small round icy pet might use cold breath for speaking and a focused lean plus a tiny frosted work slate resting beside it. A true no-limb mascot should use face/body acting and one non-grip attached, near-head, body-surface, freestanding, or resting cue instead of a held prop.

## State Patterns

Use these as starting points, then adapt them to the companion's theme.

| State | Semantic Read | Modern Assistant | Fantasy / Character World | Minimal Alternative |
| --- | --- | --- | --- | --- |
| `listening` | Receiving user input | small sound rings, hand-to-ear, mic only for voice apps | hand cupped to hood/ear, attentive glow rings | lean toward input, eyes tracking |
| `thinking` | Planning before output | compact thought cloud, idea orb, small processing halo, hand-to-chin | side-origin theme-native thought puff, floating crystal/orb near head, small aura loop, chin pose | head tilt, eyes up/side, blink hold |
| `working` | Tool/backend activity | laptop/tablet when hands can operate it; freestanding tablet/slate when they cannot | parchment/quill/tool when hands can operate it; freestanding glowing slate/card stack when they cannot | focused face, lean, body bob, purposeful prop/cue motion |
| `answering` | Streaming response | mouth shapes, presenting hand, tiny no-text near-face voice pixels | speaking gesture, scroll unfurl, guiding prop | mouth shapes, rhythmic hand beats |
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

- `thinking`, `working`, `listening`, or `answering` are unclear at 64, 96, and 128 px.
- `qa/state-readability-check.png` has not been generated and inspected.
- `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, or `qa/quality-report.json` is missing for a production run.
- `qa/art-direction-review.json` is missing, fails, or marks the pack as not ready for production.
- `qa/quality-report.json` reports semantic anchor drift, missing enhancer presence, near-duplicate animation, body jitter, or large foreground area changes.
- `qa/quality-report.json` reports detached fragments, broken-cut symptoms, core silhouette scale drift, or core center drift.
- The enhancer is technically stable but creatively weak, such as tiny dots or generic particles that do not look like deliberate state art.
- The enhancer is technically readable but off-vibe, such as gears, circuit glyphs, speech panels, or generic assistant symbols on a mascot whose visual language suggests different motifs.
- The enhancer is on-vibe but does not read as the intended state, such as decorative frost that does not communicate `working`.
- The `working` face becomes angry, hostile, gains invented brows, or feels unrelated to the work beat instead of busy, friendly, and character-appropriate.
- The working cue disappears in the contact sheet/readability sheet after cleanup, or only remains when cleanup is loosened enough to keep noise/slivers.
- The enhancer is readable but mechanically placed, such as a bubble that only floats straight above the head with no acting beat, eye tracking, expression change, or believable trajectory.
- The enhancer is cropped, detached from the character, or visually leaks into neighboring cells.
- The enhancer changes sides, height, or anchor point without an intentional animated reason.
- The enhancer changes the mascot identity or makes the row feel like a different character.
- A near-head or aura enhancer causes the mascot body to resize, jump, or drift. Regenerate with a silhouette-locked prompt rather than accepting the row.
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
- A pose uses appendage motion but changes the appendage count, invents grip anatomy, detaches a limb, or makes the moving appendage look like a new object instead of the original body part.
- A state asks an appendage to perform an action outside its `style.anatomyContract.appendages[].affordances`, such as face-touch by a fin that only has side-bob/tilt, or typing by a paw without fingers.
- A simple appendage mascot gains a limb-colored oval, patch, detached blob, or front-body shape that reads as an extra appendage, even if the original side appendages are still present.
- A face-touching or cross-body simple-appendage gesture reads as a hand, fingered mitten, detached prop, or extra limb. Regenerate with safer side-attached appendage motion and stronger face/enhancer acting.
- The working state uses a typing/writing prop with hands/fingers the reference character does not have. Use simpler braced/touched props or a non-grip semantic instead.
- The working state uses a slate, tablet, keyboard, pencil, quill, paper, or other grip prop for a true no-limb mascot. Use a non-grip body-surface, aura, near-head, facial, pose, freestanding, or resting semantic instead.
- A freestanding/resting work prop is static, too far away, looks like generic UI, touches the mascot body, or implies hidden hands/typing/writing instead of animating beside or in front of the mascot.
- Rising pips, sparkles, crystals, motion marks, or highlights bridge the empty gap between a freestanding prop and the mascot body. Keep work motion inside or on the prop surface so QA does not merge the prop with the body core.
- A held, touched, near-hand, writing, or appendage-operated work-prop enhancer is missing `enhancer.anatomyGuard` metadata.
- A held, touched, face-touch, typing, writing, pointing, presenting, or waving enhancer omits `enhancer.requiredAffordances` when the action depends on specific appendages.
- `enhancer.anatomyGuard.allowedInteractors` says only `existing appendages` or similar vague language instead of exact audited parts.
- A simple or ambiguous appendage mascot uses risky prop/near-hand semantics without `style.anatomyContract`.

For `pose-only`, reject or regenerate rows when:

- Any state introduces a new semantic prop that the user did not request.
- State readability depends on labels, captions, punctuation, or external UI.
