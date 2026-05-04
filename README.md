# Web Companion Mascot

Create high-quality animated mascot companions for React and chatbot websites from character art, screenshots, Codex pets, or generated references.

This is a Codex skill. It helps produce a web-ready mascot package with:

- stateful animation rows such as `idle`, `listening`, `thinking`, `working`, `answering`, `success`, `error`, `confused`, and `sleeping`
- a transparent sprite atlas in `atlas.webp` and `atlas.png`
- a strict `manifest.json`
- extracted per-frame PNGs
- visual QA sheets for contact, cutout, and semantic readability checks
- a generated React component and companion-state hook

The skill is designed for mascot companions that need to feel alive inside a product UI, especially AI chatbots.

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
  manifest.json
  atlas.webp
  atlas.png
  frames/<state>/*.png
  qa/assembly-report.json
  qa/contact-sheet.png
  qa/cutout-check.png
  qa/state-readability-check.png
  qa/previews/*.gif
  react/CompanionMascot.tsx
  react/useCompanionState.ts
```

## Quality Gates

The skill includes deterministic QA scripts and requires visual inspection before accepting a mascot:

- `assemble_companion_atlas.py` extracts and cleans row strips into an atlas.
- `create_state_readability_sheet.py` creates 64, 96, and 128 px previews for state readability.
- `validate_companion_manifest.py` verifies manifest shape, atlas dimensions, transparency, unused cells, cropped sprites, state clarity metadata, assembly warnings, and residual key-colored outline halos.
- `generate_react_component.py` emits a TypeScript React component that animates by per-frame manifest durations.

The assembler keeps an outline improver enabled by default:

- key-to-alpha removal
- edge spill cleanup
- spill-color replacement
- transparent RGB cleanup
- premultiplied resizing

Production runs should pass strict validation with zero warnings:

```bash
python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile chatbot \
  --strict \
  --require-state-clarity \
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
