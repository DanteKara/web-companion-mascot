# Web Companion Mascot

Create high-quality pixel-art animated mascot companions for React and chatbot websites from character art, screenshots, Codex pets, or generated references.

This is a Codex skill. It helps produce a web-ready mascot package with:

- stateful animation rows such as `idle`, `listening`, `thinking`, `working`, `answering`, `success`, `error`, `confused`, and `sleeping`
- a transparent sprite atlas in `atlas.webp` and `atlas.png`
- a strict `manifest.json`
- extracted per-frame PNGs
- visual QA sheets for contact, cutout, semantic readability, semantic anchor, motion quality, and art-direction checks
- a generated React component and companion-state hook

The skill is designed for mascot companions that need to feel alive inside a product UI, especially AI chatbots.

Production mascot art uses the Codex digital-pet pixel-art house style: compact chibi sprites, visible stepped pixel edges, thick readable outlines, limited palettes, flat cel shading, and crisp hard-edged effects. Non-pixel references are translated into that style while preserving identity and charm; smooth illustration, glossy app-icon art, painterly gradients, 3D rendering, and vector-flat clip art are not production passes.

Generated production rows default to an 8-frame HatchPet-style baseline. Use 6-frame rows for compact auditions and longer 10-12 frame rows only as an explicit smoothness pass after the mascot stays stable.

Production mascot art must come from integrated row art generated with `$imagegen` or from finished user/artist-provided row strips. The bundled scripts assemble, clean, validate, and integrate assets; they must not draw or paste final semantic props into production mascot frames.

## Install

### Recommended

Use the Skills CLI:

```bash
npx --yes skills add DanteKara/web-companion-mascot -g -y
```

Or with the full GitHub URL:

```bash
npx --yes skills add https://github.com/DanteKara/web-companion-mascot -g -y
```

The `-g` flag installs the skill globally for your user, and `-y` skips confirmation prompts.

### Manual Fallback

### Windows PowerShell

```powershell
$dest = "$env:USERPROFILE\.codex\skills\web-companion-mascot"
if (Test-Path $dest) {
  git -C $dest pull
} else {
  git clone https://github.com/DanteKara/web-companion-mascot.git $dest
}
```

### macOS / Linux

```bash
dest="$HOME/.codex/skills/web-companion-mascot"
if [ -d "$dest/.git" ]; then
  git -C "$dest" pull
else
  git clone https://github.com/DanteKara/web-companion-mascot.git "$dest"
fi
```

Restart Codex after installing or updating the skill.

## Usage

In Codex, reference the skill when asking for a companion:

```text
Use $web-companion-mascot to create a React chatbot mascot from this image.
Use semantic enhancers and include thinking, working, listening, answering, success, and error states.
```

For quieter mascots:

```text
Use $web-companion-mascot to create a pose-only companion from this character.
```

## Output

The default generated package looks like:

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
  qa/quality-report.json
  qa/anatomy-review.png
  qa/anatomy-review.json
  qa/state-performance-review.png
  qa/state-performance-review.json
  qa/art-direction-review.json
  qa/semantic-anchor-check.png
  qa/motion-quality-check.png
  qa/previews/*.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

`references/layout-guides/<state>.png` files are intentionally empty construction inputs for spacing and safe padding. They are not mascot previews; inspect `qa/contact-sheet.png`, `qa/state-readability-check.png`, previews, and the final atlas for visual output.

## Quality Gates

The skill includes deterministic QA scripts and requires visual inspection before accepting a mascot:

- `prepare_companion_run.py` creates the initial manifest draft, per-state row prompts, and `qa/state-cue-plan.json` so vibe inference, acting beats, visual aids, and anatomy limits are planned before image generation.
- `companion_job_status.py` reports which `$imagegen` jobs are ready or blocked from `imagegen-jobs.json`.
- `record_companion_imagegen_result.py` records selected `$imagegen` outputs, creates the canonical base reference, and keeps source provenance/hashes out of manual editing.
- `assemble_companion_atlas.py` extracts and cleans row strips into an atlas.
- `create_state_readability_sheet.py` creates 64, 96, and 128 px previews for state readability.
- `analyze_companion_quality.py` flags near-duplicate frames, low motion, body jitter, large foreground area jumps, and drifting semantic enhancers; it also creates semantic-anchor and motion QA sheets.
- `create_anatomy_review.py` records the manual/agent frame-by-frame anatomy review for appendage count, identity props, and state cues that might be mistaken for anatomy.
- `create_state_performance_review.py` records the manual/agent frame-by-frame state-performance review for intended state read, expression, cue motion, and wrong-state failures such as `working` reading as panting or `answering` reading as tired exhale.
- `create_art_direction_review.py` records the manual/agent visual review that the result preserves the reference quality, identity, Codex pixel-art style, creative state readability, theme-native state cues, and native enhancer look.
- `validate_companion_manifest.py` verifies manifest shape, atlas dimensions, transparency, unused cells, cropped sprites, state clarity metadata, rendering-style metadata, assembly warnings, quality warnings, anatomy guard specificity, appendage affordance mismatches, anatomy review blockers, state-performance review blockers, art-direction blockers, and residual key-colored outline halos.
- `generate_react_component.py` emits a TypeScript React component that animates by per-frame manifest durations.

The assembler keeps an outline improver enabled by default:

- key-to-alpha removal
- edge spill cleanup
- spill-color replacement
- transparent RGB cleanup
- premultiplied resizing

Production runs should pass strict validation with zero warnings:

`prepare_companion_run.py` writes draft enhancer metadata such as `planned during row generation`; after selecting final row art, update each enhanced state to describe the actual accepted visual aid. Strict validation warns on leftover draft wording so planning placeholders do not ship as production truth.

```bash
python scripts/prepare_companion_run.py \
  --companion-name MyCompanion \
  --reference /path/to/reference.png \
  --output-dir /path/to/run \
  --state-clarity semantic-enhancers \
  --anatomy-class ambiguous-limbs \
  --force

python scripts/companion_job_status.py \
  --run-dir /path/to/run

python scripts/record_companion_imagegen_result.py \
  --run-dir /path/to/run \
  --job-id base \
  --source /path/to/$CODEX_HOME/generated_images/.../ig_*.png

python scripts/analyze_companion_quality.py \
  --manifest /path/to/run/manifest.json

# For production, add one --expected-state-read entry for every state in the manifest.
python scripts/create_state_performance_review.py \
  --manifest /path/to/run/manifest.json \
  --status pass \
  --production-use \
  --review-all-frames \
  --expected-state-read working="Active work with concrete target/progress; not panting, sleeping, talking, or decoration." \
  --expected-state-read answering="Engaged speaking/streaming from the mouth; not tired panting or exhale clouds." \
  --check frameByFrameStateReadReviewed=true \
  --check intendedStateReadable=true \
  --check noWrongStateRead=true \
  --check expressionMatchesState=true \
  --check cueMotionMatchesState=true \
  --check noTiredPantingUnlessStateRequiresIt=true \
  --check noOffVibeGenericCue=true \
  --notes "Frame-by-frame state-performance review passed."

python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile audition \
  --strict \
  --require-state-clarity \
  --require-rendering-style \
  --require-quality-report
```

Use `--profile audition` for one-row or partial-pack tests. Use the full chatbot profile only after the production pack includes the expected chatbot states:

```bash

python scripts/create_art_direction_review.py \
  --manifest /path/to/run/manifest.json \
  --status pass \
  --production-use \
  --generation-method imagegen-integrated-row-art \
  --source-reference /path/to/original-reference.png \
  --check referenceQualityMaintained=true \
  --check identityPreserved=true \
  --check stylePreserved=true \
  --check pixelArtStyle=true \
  --check creativeStateReadability=true \
  --check themeNativeStateCues=true \
  --check nativeEnhancers=true \
  --check integratedEnhancers=true \
  --check anatomyPreserved=true \
  --check noExtraAnatomy=true \
  --check believableOcclusion=true \
  --check noPrototypeFlattening=true \
  --notes "Visual review passed."

python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile chatbot \
  --strict \
  --require-state-clarity \
  --require-rendering-style \
  --require-quality-report \
  --require-state-performance-review \
  --require-art-direction-review \
  --max-outline-halo-pixels 0
```

## Python Dependencies

The scripts use Pillow:

```bash
python -m pip install -r requirements.txt
```

Codex Desktop users can also use the bundled workspace Python runtime if the system Python does not have Pillow installed.

## React Integration

Generated assets are meant to be copied into your app's served assets folder, usually:

```text
public/mascots/<companion-id>/
```

Then use the generated component:

```tsx
import { CompanionMascot } from "./CompanionMascot";
import { toCompanionState } from "./useCompanionState";

export function ChatMascot({ status }: { status: "idle" | "submitted" | "streaming" | "error" }) {
  return (
    <CompanionMascot
      state={toCompanionState(status)}
      size={0.75}
      assetBase="/mascots/my-companion"
    />
  );
}
```

## Repository Contents

```text
SKILL.md
agents/openai.yaml
references/
scripts/
```

Generated mascot assets are intentionally not included in this repository.

## License

MIT
