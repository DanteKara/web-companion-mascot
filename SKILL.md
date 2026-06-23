---
name: web-companion-mascot
description: Use when creating, validating, or integrating custom animated mascot companions, sprite sheets, sprite atlases, or React/chatbot website mascot assets from concept art, screenshots, existing Codex pets, or generated references, especially when states like idle, hover, dragging, greeting, listening, thinking, answering, success, error, or sleeping are needed.
---

# Web Companion Mascot

## Overview

Create website-first pixel-art chatbot companions with custom sprite sheets, a sprite atlas, state manifest, QA assets, and optional React integration for chat, hover, and drag/drop companion behavior. Prefer this skill for web/chat companions rather than fixed Codex app pets.

Use `$imagegen` for all production visual generation. Use this skill's scripts only for deterministic preparation, provenance recording, cleanup, atlas assembly, QA, validation, and React file generation.

Default behavior is agent-led: infer the mascot identity, state list, clarity approach, geometry, and cue style from the user's prompt/reference. Do not ask the user to choose workflow modes. Ask only when a missing decision would materially change the character or target product.

## Reference Routing

Load only what the task needs:

- `references/production-workflow.md`: full production workflow, art-direction rules, script details, repair workflow, validation commands, and acceptance criteria. Read this for normal end-to-end mascot creation, production QA, failed validation repair, fallback decisions, or any task where visual quality/provenance matters.
- `references/companion-contract.md`: manifest shape, default chatbot states, style metadata, anatomy contract, geometry, atlas rules, QA checklist, and website state mapping.
- `references/state-enhancers.md`: use when the user chooses or needs `semantic-enhancers`, state cards, mascot-native cues, anatomy-sensitive props/effects, or clarity-profile decisions.
- `references/react-integration.md`: use when wiring the mascot into a React app or modifying generated React component behavior.

## Core Boundaries

- Do not draw, tile, mirror, warp, synthesize, or replace production mascot pixels with local Python/Pillow, SVG, canvas, CSS, vector overlays, or deterministic compositors.
- Do not manually edit `imagegen-jobs.json`, copy files into `generated/`, or mark visual jobs complete by hand.
- Record selected visual outputs with `scripts/record_companion_imagegen_result.py`; keep source provenance explicit.
- Only the base job may be prompt-only when no reference exists. Every state-row job must use the grounding images listed in `imagegen-jobs.json`, including `references/canonical-base.png` after the base is recorded.
- For a normal React/chatbot companion request, deliver the full companion package. Base-only or single-image outputs are incomplete unless the user explicitly asks for a concept image, canonical base, audition, or narrow repair.
- Run the Codex app image capture preflight before treating `$imagegen` output as production art. If the image appears inline in Codex app rather than as an obvious file, use `scripts/capture_codex_app_imagegen_result.py` to capture the app's `image_generation_call` result to a PNG and `.codex-imagegen.json` sidecar, then record it with `--source-provenance codex-app-imagegen`.
- If a captured Codex app `$imagegen` row is visually good but needs chroma cleanup, use the installed `$imagegen` chroma helper to create a transparent PNG outside the run directory, then record the cleaned PNG with `--source-provenance codex-app-imagegen-chroma-cleanup --chroma-cleanup-source <original-captured-png>`.
- If `$imagegen` is unavailable and the user has not provided finished integrated sprite art, stop and explain the blocker.

## Default Output

Default package:

```text
run/
  companion_request.json
  imagegen-jobs.json
  manifest.json
  prompts/base.md
  prompts/rows/<state>.md
  references/canonical-base.png
  references/layout-guides/<state>.png
  generated/<state>.png
  frames/<state>/*.png
  atlas.webp
  atlas.png
  qa/*.json
  qa/*.png
  qa/previews/*.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

Default production geometry starts at `256x288` per cell, one row per website state, and usually 8 frames per row. Choose larger cells without asking when the character needs headroom: use `320x320`, `384x384`, or another explicit size for tall hats, long held props, wings, long tails, large ears, readable hand acting, or theme-native effects. Use `192x208` only for deliberately small/simple companions.

This default output is the full companion package. Do not call a normal React/chatbot mascot complete until the atlas, frames, manifest, QA evidence, and requested React files exist.

## Workflow

1. Establish identity, references, must-keep features, anatomy class, prop rules, palette, target site vibe, state list, and state clarity. For normal React website companions, include `hover` and `dragging` interaction rows unless the request is deliberately compact or non-interactive. Infer `semantic-enhancers` for normal chatbot companions unless the user asks for a quieter/minimal mascot; infer `pose-only` only when acting alone will read clearly.
2. Prepare the run folder and prompt plan:

```bash
python scripts/prepare_companion_run.py --companion-name "<Name>" --reference /path/to/reference.png --output-dir /path/to/run --anatomy-class ambiguous-limbs --state-clarity semantic-enhancers --force
```

3. Inspect ready jobs:

```bash
python scripts/companion_job_status.py --run-dir /path/to/run
```

4. Generate/select the canonical Codex-style pixel-art base with `$imagegen`, capture it if needed, then record it. Do not stop after the canonical base during a normal full companion run:

```bash
python scripts/capture_codex_app_imagegen_result.py --out /absolute/path/to/codex-app-imagegen/ig_base.png
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /absolute/path/to/codex-app-imagegen/ig_base.png --source-provenance codex-app-imagegen --strict-base-style
```

5. Generate one grounded row strip per ready state with `$imagegen`, then record each selected row:

```bash
python scripts/capture_codex_app_imagegen_result.py --out /absolute/path/to/codex-app-imagegen/ig_thinking.png
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /absolute/path/to/codex-app-imagegen/ig_thinking.png --source-provenance codex-app-imagegen --strict-row-style
```

After the canonical base is recorded, delegate independent state rows to subagents by default when the current Codex environment exposes multi-agent tools and the user's request is a normal local companion asset run. Do not ask for extra approval solely because rows are delegated; ask only when the tool policy itself requires approval, the user disallowed subagents, or the delegation would materially change cost, time, or external side effects. The parent agent still records selected sources, updates manifests, assembles, reviews, validates, and packages.

6. Assemble and inspect the atlas:

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --extraction-mode component --allow-edge-clearance-scale --max-outline-halo-pixels 0 --no-equal-fallback
```

If the contact sheet shows edge pressure, neighbor slivers, prop clipping, or mascot scale shrink from tall/wide cues, rerun assembly with a larger explicit cell such as `384x384`, then rerun QA on that final atlas.

7. Run QA and manual review scripts before acceptance:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
python scripts/audit_companion_imagegen_sources.py --run-dir /path/to/run --json-out /path/to/run/qa/imagegen-source-style-audit-latest.json
python scripts/validate_companion_manifest.py --manifest /path/to/run/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review --require-art-direction-review --max-outline-halo-pixels 0 --json-out /path/to/run/qa/validation.json
python scripts/create_companion_production_readiness_report.py --manifest /path/to/run/manifest.json --json-out /path/to/run/qa/production-readiness-report.json
```

If the manifest, atlas, quality sheets, or source audit changes after manual reviews are written, regenerate the affected manual reviews before rerunning production readiness; stale reviews must not approve new art.

8. Generate React files only after visual QA, strict validation, and production-readiness checks pass:

```bash
python scripts/generate_react_component.py --manifest /path/to/run/manifest.json --out-dir /path/to/run/react
```

If `python` cannot import required image libraries, call `load_workspace_dependencies` and rerun the same scripts with the bundled Python executable.

## Visual Standards

Production art must be native pixel-art sprite work: compact digital-pet proportions appropriate to the reference, visible stepped pixel edges, thick dark 1-2 px outline, readable face, stable silhouette, stable eye grammar, and consistent appendage/prop count.

Reject smooth illustration, glossy app-icon rendering, painterly gradients, 3D material shading, high-detail antialiasing, vector-flat symbols, CSS-scaled smooth art, fake transparency, non-flat chroma backgrounds, cropped frames, detached random symbols, shadows, glows, smear effects, and identity drift.

The user prompt/reference vibe is authoritative. Do not impose a default cute, happy, friendly, harmless, or helper-like personality. A dark, evil, stern, sly, chaotic, elegant, shy, soft, heroic, or strange mascot should perform every state through that personality. Keep state readability and app usability, but let the source vibe choose the emotional language.

State rows should act through the mascot first: expression, blink, mouth shape, body rhythm, appendages, and identity props. Let rows be expressive and characterful: bounces, tilts, prop beats, costume/accessory/appendage motion, mouth shapes, and theme-native effects are good when identity stays stable and the reference vibe supports them. Use one small mascot-native semantic enhancer when acting alone would not read clearly.

Do not let validation make the art timid or flatten personality. Technical blockers must be fixed, but intentional state-specific acting such as a triumphant success beat, ominous success beat, sleepy droop, annoyed/recoverable error beat, or intense thinking lean can pass when the manual review documents that it improves the read without breaking identity or app usability.

Review state rows as animation loops, not just still images. A technically clean row can still fail when one frame has an exaggerated side glance, closed-eye style swap, odd mood jump, or expression outlier that breaks the left-to-right motion story. For `thinking`, prefer a steady processing/working loop carried by body, appendage/prop, blink, mouth, and compact cue timing before using dramatic eye-direction changes.

## React Notes

When integrating into React, serve final assets from a stable public path, drive animation from manifest frame durations, respect `prefers-reduced-motion`, keep `state`, `size`, and `paused` controlled by app state, map pointer hover to `hover`, map active drag/drop movement to `dragging`, and use `image-rendering: pixelated`.

## Acceptance

Before calling a production companion complete, require:

- `manifest.json`, `imagegen-jobs.json`, prompts, canonical base, atlas, extracted frames, previews, and QA files exist.
- Base and rows have strict source-style evidence and no blocking warning codes.
- Contact sheet, cutout check, readability sheet, semantic anchor sheet, motion sheet, anatomy review, state-performance review, eye-grammar review, and art-direction review pass.
- `qa/assembly-report.json` reports outline improvement enabled and `totalOutlineHaloPixels: 0`.
- `qa/imagegen-source-style-audit-latest.json` and `qa/validation.json` exist from the final run.
- Strict chatbot validation passes, or any exception is explicitly reviewed and documented.
- `qa/production-readiness-report.json` records `productionReady: true`.
