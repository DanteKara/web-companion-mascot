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
  qa/previews/*.mp4 or *.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

Default high-quality sprite geometry:

```text
cell: 256x288
columns: max frame count across states, usually 10
rows: one row per website state
atlas width: columns * 256
atlas height: rows * 288
```

Use `192x208` only when the user explicitly prioritizes smaller files or the mascot has very simple detail. Detailed outfits, props, emblems, hand gestures, or high-quality website mascots should use `256x288` or larger.

Use `references/companion-contract.md` for the manifest schema, default states, and QA rules. Use `references/state-enhancers.md` when the user has not chosen a state clarity profile or when `semantic-enhancers` are requested. Use `references/react-integration.md` when wiring the mascot into a React app.

## Motion Quality

Default to a high-motion website companion profile rather than the smaller Codex pet frame counts:

```text
idle/listening/greeting/success/error/confused/sleeping: 8+ frames
thinking/working/answering: 10+ frames
```

Use fewer frames only when the user explicitly prioritizes file size or when a target app has a hard frame limit. For chatbot companions, `thinking`, `working`, and `answering` are the most visible states and should get the richest motion.

Design rows as true animation, not static variants:

- Include anticipation, action, and settle frames for one-shot-feeling loops such as `success` and `error`.
- Include at least two blink or eye-position changes in long idle/thinking rows.
- Include prop or hand follow-through when the mascot holds an item.
- Stagger face, body, robe/clothing, and prop motion so the row feels alive.
- Keep frame durations mostly between 80 and 220 ms. Use occasional 260-420 ms holds for readable blinks, idle breaths, or sleeping only.
- Do not increase apparent smoothness by adding near-duplicate frames. Every frame should change silhouette, face, prop, or body position enough to matter at display size.

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

## Generation Workflow

1. Establish mascot identity: name, reference image(s), must-keep features, prop rules, palette, target website vibe, state list, and state clarity profile (`pose-only` or `semantic-enhancers`).
2. Generate or select one canonical base sprite with `$imagegen`.
3. Generate one row strip per state with `$imagegen`, using the canonical base and any original references as grounding images.
4. Keep all row strips on a clean flat chroma-key background. Pick a key color absent from the character; avoid yellow for gold props, avoid magenta for pink/purple characters, and avoid green for green characters.
5. Preserve identity across every row: silhouette, face, palette, props, outfit, outline weight, and proportions.
6. If using `semantic-enhancers`, include the chosen profile in row prompts and generate each enhancer as integrated mascot artwork, not as a post-process overlay. Add only one small anchored enhancer per ambiguous state unless the user explicitly requests more.
7. Seed `manifest.json` with the state rows, frame counts, durations, `id`, `displayName`, `style.stateClarity`, and per-state `enhancer` metadata when semantic enhancers are used.
8. Assemble the atlas with the bundled assembler. This script handles variable row-strip spacing, chroma-key gradients, wide gestures, transparent unused cells, extracted frames, contact sheets, GIF previews, and an assembly report. Its outline improver must remain enabled: key-to-alpha removal, edge-spill cleanup, spill-color replacement, transparent RGB cleanup, and premultiplied resizing all protect the sprite edge from chroma halos.

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --columns 10 --cell-width 256 --cell-height 288 --max-outline-halo-pixels 0
```

9. Create the small-size readability QA sheet for semantic states:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
```

10. Visually inspect the contact sheet, cutout check, readability sheet, and previews before accepting the mascot. If the contact sheet shows neighboring-frame slivers, chopped hands/props, stray specks, or off-center sprites, repair the generated row or adjust assembler settings before validation. If `qa/cutout-check.png` shows pink/magenta halos on dark, white, blue, or green backgrounds, rebuild with stronger chroma cleanup or regenerate the row with a flatter key background. For `semantic-enhancers`, reject rows where the enhancer is unclear at 64, 96, and 128 px, cropped, detached, leaking into other states, or visually pasted on.
11. Run manifest validation with the chatbot profile before finishing. Strict validation must fail on assembly warnings, missing readability QA, malformed state clarity metadata, cropped sprites, non-transparent unused cells, or any remaining key-colored outline halo pixels:

```bash
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity --max-outline-halo-pixels 0
```

12. Generate the React component only after visual QA and strict validation pass.

When the mascot has side-specific props, text, emblems, handed items, or asymmetric lighting, generate left/right directional states separately instead of mirroring.

## Visual Rules

Prefer sprite-readable animation over decorative effects.

- Keep poses fully inside each frame with safe padding.
- Use every listed frame as a meaningful pose or in-between.
- Keep props attached to, held by, or clearly anchored near the mascot.
- Avoid shadows, glows, blur, motion streaks, dust, loose sparkles, detached punctuation, UI panels, scenery, and text unless the user explicitly requests a website-only effect and the atlas extraction can preserve it.
- For `pose-only`, show `thinking`, `working`, and `answering` through head tilt, eye movement, hand/prop pose, blink, mouth shapes, and body motion.
- For `semantic-enhancers`, add one small anchored enhancer for ambiguous states, such as a thought bubble near the head, a held paper/tablet/tool, listening rings, or a small success/error charm. The enhancer must match the mascot's theme.
- Production enhancers must match the mascot's exact rendering style: same line weight, pixel grid or brush texture, palette, lighting direction, shading, antialiasing, and occlusion with hands/clothing. Do not ship hand-drawn/vector overlays on top of generated mascot frames unless the user explicitly asked for a prototype.
- For `working`, choose the work prop from the companion's world: laptop/tablet for modern assistants, parchment/quill/glowing slate/tool for fantasy or character mascots.
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
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --columns 10 --cell-width 256 --cell-height 288
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/validate_companion_manifest.py --manifest /path/to/manifest.json --profile chatbot --strict --require-state-clarity
python scripts/generate_react_component.py --manifest /path/to/manifest.json --out-dir /path/to/react
```

If the system `python` cannot import Pillow/PIL, use the Codex bundled workspace runtime instead: call `load_workspace_dependencies`, then run the same scripts with the returned Python executable.

`assemble_companion_atlas.py` reads row strips named `<state>.png`, updates the manifest atlas fields, extracts clean per-frame PNGs, writes `atlas.webp` and `atlas.png`, creates `qa/contact-sheet.png`, creates `qa/cutout-check.png`, creates `qa/previews/*.gif`, and writes `qa/assembly-report.json`. It uses foreground-run center detection rather than naive equal-width slicing, which prevents common generated-strip issues such as variable frame spacing, clipped wide gestures, and neighboring-frame slivers. It also runs the outline improver: transparent RGB clearing, key spill removal, key-colored edge cleanup, spill-color replacement, and premultiplied resizing so invisible chroma-key pixels do not bleed into sprite edges. The assembly report records `outlineImprover.totalOutlineHaloPixels`; production runs should keep this at `0`. If it reports `equal-fallback` or outline warnings, review that state manually and prefer regenerating the row if the contact sheet looks uneven.

`create_state_readability_sheet.py` writes `qa/state-readability-check.png`, showing enhanced states at 64, 96, and 128 px. Use it before validation for `semantic-enhancers` packs.

`validate_companion_manifest.py` verifies manifest shape, state frame counts, durations, atlas path, dimensions, alpha channel, empty used cells, non-transparent unused cells, edge-touching/cropped sprites, residual key-colored outline halos, assembly-report warnings, missing readability QA, and optional state clarity metadata. The `chatbot` profile warns when core website states are missing or when important states have too few frames for smooth motion. Use `--strict --require-state-clarity --max-outline-halo-pixels 0` for newly generated production packs so warnings, missing clarity metadata, missing QA, and outline halo pixels block acceptance.

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
- Chatbot profile validation passes in strict mode, or every warning is explicitly reviewed and accepted.
- `manifest.json` records `style.stateClarity` as `pose-only` or `semantic-enhancers` for newly generated packs.
- If `semantic-enhancers` is selected, `thinking`, `working`, `listening`, and `answering` include per-state `enhancer` metadata and read clearly at 64, 96, and 128 px.
- Semantic enhancers look native to the mascot artwork, not pasted on. Reject any row where prop/effect outline, shading, scale, perspective, antialiasing, or pixel density does not match the base mascot.
- If `pose-only` is selected, no new semantic props appear unless the user explicitly requested them.
- `thinking`, `working`, and `answering` have 10+ frames by default unless the user requested a smaller atlas.
- `idle`, `greeting`, `listening`, `success`, `error`, `confused`, and `sleeping` have 8+ frames by default unless the user requested a smaller atlas.
- Every requested chatbot state is visually distinct enough to read at website size.
- Contact sheet and at least one preview format are produced.
- React component can display `idle`, `thinking`, `working`, `answering`, `success`, and `error`.
- The final answer reports asset paths, manifest path, React component path, and QA result.
