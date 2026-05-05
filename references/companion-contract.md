# Web Companion Contract

## Manifest Shape

Use this shape for `manifest.json`:

```json
{
  "id": "tridy",
  "displayName": "Tridy",
  "description": "A cheerful chatbot companion.",
  "style": {
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

## State Clarity Metadata

New companion packs should include a top-level `style.stateClarity` value:

```json
{
  "style": {
    "stateClarity": "pose-only"
  }
}
```

or:

```json
{
  "style": {
    "stateClarity": "semantic-enhancers",
    "enhancerTheme": "modern-assistant"
  }
}
```

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
      "description": "Small no-text thought bubble anchored near the head."
    }
  }
}
```

Allowed `enhancer.attachment` values:

```text
held, worn, attached, near-head, near-face, near-hand, aura, gesture, body-pose
```

`thinking`, `working`, `listening`, and `answering` should have `enhancer` metadata when `semantic-enhancers` is selected and those states are present. Metadata cannot prove the pixels are good, but it forces each generated state to carry an explicit QA intention.

## Geometry Guidance

Use `256x288` cells by default for high-quality website companions, especially when the mascot has a detailed outfit, emblem, prop, expressive hands, or readable facial states. Use `192x208` only for smaller packs or very simple mascots.

The atlas assembler should infer frame centers from foreground runs instead of slicing row strips into equal widths. Generated row strips often have slightly variable spacing; naive slicing can leave neighboring-frame slivers or clip wide gestures even when manifest validation passes.

Semantic enhancers may require slightly wider safe padding. Do not rely on CSS cropping to hide bubbles, tablets, paper, sound rings, or other state props.

## Motion Design Rules

Do not treat "more frames" as duplicated stills. Every used frame should earn its slot.

- `idle`: slow breathing, 1-2 blink/eye frames, tiny hand/prop settle.
- `greeting`: anticipation, arm/prop rise, peak gesture, return, friendly hold.
- `listening`: attentive lean, blink, eye tracking toward user input, subtle prop/body motion.
- `thinking`: head tilt, eye movement, hand-to-face or prop tilt, blink, small loopable shifts.
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

## Atlas Rules

- Use a consistent cell size across the whole atlas.
- Keep one state per row.
- Keep frames ordered left to right.
- Fill unused cells with full transparency.
- Keep the mascot inside each cell with safe padding.
- Do not rely on CSS cropping to hide broken edges or off-cell props.
- Keep row strips on a removable chroma-key background before alpha extraction.
- Assemble row strips with center-aware foreground extraction and small-component cleanup.
- Prefer `--no-equal-fallback` for production assembly; equal slicing is a repair/debug fallback, not a clean final state.
- Clear RGB values for transparent pixels and resize sprites with premultiplied alpha so hidden chroma-key color cannot bleed into semi-transparent edges.
- Keep the outline improver enabled in the assembler: key-to-alpha removal, key-colored edge cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing.
- Treat `outlineImprover.totalOutlineHaloPixels > 0` in `qa/assembly-report.json` as a production blocker unless a human explicitly accepts the edge artifact.
- Produce a cutout QA sheet on dark, light, and saturated backgrounds; checkerboards alone can hide chroma-key halos.
- Produce `qa/state-readability-check.png` for semantic-enhancer packs before strict validation.
- Produce `qa/quality-report.json`, `qa/semantic-anchor-check.png`, and `qa/motion-quality-check.png` before strict validation.
- Review assembly warnings such as equal-width fallback; they indicate the row may need regeneration or manual inspection.

## QA Checklist

Reject or repair if any of these happen:

- The chatbot profile validator fails in strict mode.
- A row changes the mascot identity, outfit, face, prop, or palette unexpectedly.
- A prop crosses into a neighboring frame slot.
- A frame is cropped.
- A frame contains a stray sliver, speck, or fragment from a neighboring generated pose.
- A frame shows a pink, green, or key-colored edge halo on `qa/cutout-check.png`.
- `qa/assembly-report.json` is missing, has assembly warnings, or records leftover outline halo pixels.
- A `semantic-enhancers` pack is missing `qa/state-readability-check.png`.
- A row gets its smoothness from duplicates or near-duplicates rather than meaningful in-betweens.
- `qa/quality-report.json` reports low motion, near-duplicate transitions, body jitter, major area jumps, missing enhancer presence, or semantic anchor drift.
- `style.stateClarity` is malformed.
- `style.stateClarity` is `pose-only` but state rows introduce unrequested semantic props.
- `style.stateClarity` is `semantic-enhancers` but `thinking`, `working`, `listening`, or `answering` omit `enhancer` metadata.
- A semantic enhancer is not readable at 64, 96, and 128 px.
- A semantic enhancer is cropped, detached, text-dependent, or appears in unrelated states.
- A semantic enhancer wanders away from its intended anchor, changes sides without intent, or makes the row read as a different state.
- A semantic enhancer looks pasted on: mismatched outline, antialiasing, lighting, scale, pixel density, palette, or occlusion.
- A held enhancer causes extra hands, duplicate arms, new fingers/paws/fins, or other anatomy that was not in the source mascot.
- Production semantic enhancers were added as post-process overlays instead of generated as integrated mascot art.
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
