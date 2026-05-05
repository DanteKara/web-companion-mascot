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

- Pick props from the mascot's world, not from a universal icon set.
- Use one enhancer per state by default.
- Anchor enhancers to the mascot: held, worn, near-head, near-hand, near-face, aura, gesture, or body-pose.
- Write a tiny state card before generating each enhanced row: semantic read, chosen prop/effect, exact anchor, body parts allowed to interact with it, and forbidden artifacts.
- Keep enhancers inside the sprite cell with safe padding for every frame.
- Avoid text, labels, UI panels, detached punctuation, loose sparkles, and large scenery.
- Use an enhancer only when pose, expression, and motion are not enough.
- Keep the mascot's outfit, outline, palette, face, and proportions consistent across all rows.
- Animate the enhancer with follow-through; do not paste the same prop in every frame.
- Generate production enhancers as part of the mascot artwork. Do not add vector, CSS, or hand-drawn overlays after generation unless the user explicitly wants a throwaway prototype.
- Match the base mascot's line weight, pixel grid or brush texture, palette, lighting direction, shading, antialiasing, and occlusion. A good enhancer should look like it was designed by the same artist in the same pass.
- For held or touched props, the mascot must use only its existing hands, paws, fins, sleeves, tentacles, or identity body parts. Reject extra hands, duplicate arms, new fingers, cloned sleeves, disconnected mitts, or props held by anatomy the source character does not have.
- If the mascot has simple or ambiguous limbs, choose props that can sit against the body, tuck under an existing limb, or hover near the head instead of requiring detailed fingers.

## State Card Pattern

Use this compact card in row prompts and QA notes:

```text
state: working
semantic read: backend/tool work
enhancer: frosty slate
anchor: held low against body by existing fins only
allowed anatomy: two original side fins, no fingers
forbidden: extra hands, extra fins, detached slate, text labels, copied UI panel
```

The card should change with the mascot. A hooded fantasy character might use parchment and sleeves; a small round pet might use a body-anchored slate; a modern bot might use a tablet.

## State Patterns

Use these as starting points, then adapt them to the companion's theme.

| State | Semantic Read | Modern Assistant | Fantasy / Character World | Minimal Alternative |
| --- | --- | --- | --- | --- |
| `listening` | Receiving user input | small sound rings, hand-to-ear, mic only for voice apps | hand cupped to hood/ear, attentive glow rings | lean toward input, eyes tracking |
| `thinking` | Planning before output | thought bubble, idea dot cluster, hand-to-chin | small thought cloud, floating orb near head, chin pose | head tilt, eyes up, blink hold |
| `working` | Tool/backend activity | laptop, tablet, keyboard, document | parchment, quill, glowing slate, tool, spellbook | focused face, faster hands/prop |
| `answering` | Streaming response | speech bubble, presenting hand, mouth shapes | speaking gesture, scroll unfurl, guiding prop | mouth shapes, rhythmic hand beats |
| `success` | Completed successfully | small check glint, thumbs up | raised staff/tool, celebratory charm | bounce, proud pose |
| `error` | Recoverable failure | warning badge, droop, small alert mark | dimmed charm, dropped prop, worried robe slump | worried face, recoil, recovery |
| `confused` | Needs clarification | small question bubble | tilted charm, searching orb | squint, head tilt |
| `sleeping` | Inactive/offline | small sleep bubble | hood droop, dim aura | slow breathing, closed eyes |

## Manifest Metadata

Record the chosen profile so future QA and React integration can understand the design intent:

```json
{
  "style": {
    "stateClarity": "semantic-enhancers",
    "enhancerTheme": "fantasy"
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
        "description": "Small no-text thought bubble anchored near the head."
      }
    }
  }
}
```

Allowed `attachment` values:

```text
held, worn, attached, near-head, near-face, near-hand, aura, gesture, body-pose
```

## QA

For `semantic-enhancers`, reject or regenerate rows when:

- `thinking`, `working`, `listening`, or `answering` are unclear at 64, 96, and 128 px.
- `qa/state-readability-check.png` has not been generated and inspected.
- `qa/semantic-anchor-check.png`, `qa/motion-quality-check.png`, or `qa/quality-report.json` is missing for a production run.
- `qa/quality-report.json` reports semantic anchor drift, missing enhancer presence, near-duplicate animation, body jitter, or large foreground area changes.
- The enhancer is cropped, detached from the character, or visually leaks into neighboring cells.
- The enhancer changes sides, height, or anchor point without an intentional animated reason.
- The enhancer changes the mascot identity or makes the row feel like a different character.
- The enhancer appears in the wrong state or persists into unrelated states.
- The row relies on text instead of visual meaning.
- The manifest omits `style.stateClarity` or per-state `enhancer` metadata for enhanced states.
- The enhancer looks pasted on: mismatched outline thickness, different antialiasing, wrong scale, flat vector styling over painterly/pixel art, inconsistent lighting, or no believable hand/body occlusion.
- The enhancer was added by post-processing instead of generated as integrated row art, unless the package is clearly labeled as a prototype and not accepted as final.
- A held prop creates extra limbs, duplicate hands, new fingers/paws/fins, or inconsistent sleeves/body parts. This is a production blocker even if validation passes.

For `pose-only`, reject or regenerate rows when:

- Any state introduces a new semantic prop that the user did not request.
- State readability depends on labels, captions, punctuation, or external UI.
