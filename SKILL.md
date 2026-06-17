---
name: web-companion-mascot
description: Use when creating, validating, or integrating custom animated mascot companions for React/chatbot websites from concept art, screenshots, existing Codex pets, or generated references, especially when states like idle, greeting, listening, thinking, answering, success, error, confused, or sleeping are needed.
---

# Web Companion Mascot

## Overview

Create website-first pixel-art chatbot companions with a custom sprite atlas, state manifest, QA assets, and optional React integration. Prefer this skill for web/chat companions rather than fixed Codex app pets.

Use `$imagegen` for all production visual generation. Use this skill's scripts only for deterministic preparation, provenance recording, cleanup, atlas assembly, QA, validation, and React file generation.

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

Default production geometry is `256x288` per cell, one row per website state, and usually 8 frames per row. Use `192x208` only for deliberately small/simple companions.

## Workflow

1. Establish identity, references, must-keep features, anatomy class, prop rules, palette, target site vibe, state list, and state clarity profile (`pose-only` or `semantic-enhancers`).
2. Prepare the run folder and prompt plan:

```bash
python scripts/prepare_companion_run.py --companion-name "<Name>" --reference /path/to/reference.png --output-dir /path/to/run --anatomy-class ambiguous-limbs --state-clarity semantic-enhancers --force
```

3. Inspect ready jobs:

```bash
python scripts/companion_job_status.py --run-dir /path/to/run
```

4. Generate/select the canonical Codex-style pixel-art base with `$imagegen`, then record it:

```bash
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id base --source /absolute/path/to/generated/base.png --strict-base-style
```

5. Generate one grounded row strip per ready state with `$imagegen`, then record each selected row:

```bash
python scripts/record_companion_imagegen_result.py --run-dir /path/to/run --job-id thinking --source /absolute/path/to/generated/thinking.png --strict-row-style
```

6. Assemble and inspect the atlas:

```bash
python scripts/assemble_companion_atlas.py --manifest /path/to/run/manifest.json --row-dir /path/to/run/generated --out-dir /path/to/run --cell-width 256 --cell-height 288 --max-outline-halo-pixels 0 --no-equal-fallback
```

7. Run QA and manual review scripts before acceptance:

```bash
python scripts/create_state_readability_sheet.py --manifest /path/to/run/manifest.json
python scripts/analyze_companion_quality.py --manifest /path/to/run/manifest.json
python scripts/validate_companion_manifest.py --manifest /path/to/run/manifest.json --profile chatbot --strict --require-state-clarity --require-rendering-style --require-quality-report --require-anatomy-review --require-state-performance-review --require-eye-grammar-review --require-art-direction-review --max-outline-halo-pixels 0
python scripts/create_companion_production_readiness_report.py --manifest /path/to/run/manifest.json --json-out /path/to/run/qa/production-readiness-report.json
```

8. Generate React files only after visual QA, strict validation, and production-readiness checks pass:

```bash
python scripts/generate_react_component.py --manifest /path/to/run/manifest.json --out-dir /path/to/run/react
```

If `python` cannot import required image libraries, call `load_workspace_dependencies` and rerun the same scripts with the bundled Python executable.

## Visual Standards

Production art must be native pixel-art sprite work: compact chibi proportions, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, readable face, stable silhouette, stable eye grammar, and consistent appendage/prop count.

Reject smooth illustration, glossy app-icon rendering, painterly gradients, 3D material shading, high-detail antialiasing, vector-flat symbols, CSS-scaled smooth art, fake transparency, non-flat chroma backgrounds, cropped frames, detached random symbols, shadows, glows, smear effects, and identity drift.

State rows should act through the mascot first: expression, blink, mouth shape, body rhythm, appendages, and identity props. Use one small mascot-native semantic enhancer only when acting alone would not read clearly.

## React Notes

When integrating into React, serve final assets from a stable public path, drive animation from manifest frame durations, respect `prefers-reduced-motion`, keep `state`, `size`, and `paused` controlled by app state, and use `image-rendering: pixelated`.

## Acceptance

Before calling a production companion complete, require:

- `manifest.json`, `imagegen-jobs.json`, prompts, canonical base, atlas, extracted frames, previews, and QA files exist.
- Base and rows have strict source-style evidence and no blocking warning codes.
- Contact sheet, cutout check, readability sheet, semantic anchor sheet, motion sheet, anatomy review, state-performance review, eye-grammar review, and art-direction review pass.
- `qa/assembly-report.json` reports outline improvement enabled and `totalOutlineHaloPixels: 0`.
- Strict chatbot validation passes, or any exception is explicitly reviewed and documented.
- `qa/production-readiness-report.json` records `productionReady: true`.
