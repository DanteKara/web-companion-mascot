# Quality Pipeline v3

Production v3 exists to keep web companion mascots honest as native sprite art. The production target is native 16-bit-console pixel art: identity is approved before the base, the base is reviewed before rows, visual sources are audited, QA uses a locked profile, and every final frame receives hash-bound observation evidence. Foreground palette or alpha conversion is not chroma cleanup.

## Contract

- Production art must be authentic native 16-bit console-style pixel art from the start.
- Do not accept fancy 3D renders, glossy app icons, painterly illustrations, realistic fur, bloom, soft gradients, or smooth antialiasing as production sprite art.
- Raw unique RGB count and quantized color count are advisory signals. They can trigger review, but they are not hard blockers alone.
- Smooth-gradient, painterly, glossy, 3D-like, missing-foreground, fake-transparency, non-uniform-background, and excessive-partial-alpha risks are blocking.
- Chroma cleanup is background-only. It may remove or alpha out the key background, but it must not remap foreground colors, posterize foreground pixels, change foreground alpha, or change sprite geometry.
- Foreground quantization, posterization, recoloring, binary-alpha foreground conversion, geometry edits, or palette remapping block production.
- Identity approval happens before base generation is accepted.
- Approved identity JSON must follow the v3 contract. Start from the generated `references/character-bible.json` draft or `references/character-bible.example.json`; `paletteRoles` entries are objects such as `{"role":"outline","color":"#101828"}`, not prose strings.
- Canonical base review happens before row generation or row recording is accepted.
- QA profile `production-v3` is locked. Production scripts must not expose threshold override flags.
- Approved exceptions must be declared in the approved identity contract before generation.
- Per-frame review evidence is required. Blanket `--review-all-frames` booleans are compatibility artifacts only when generated from concrete frame observations.

## Readiness Status

Final readiness is one of:

- `productionReady`: no blockers and no approved exceptions.
- `productionReadyWithApprovedExceptions`: no blockers, with predeclared approved exceptions used.
- `notProductionReady`: one or more blockers exist.

## Required Command Path

```bash
python scripts/prepare_production_companion_run.py ...
python scripts/approve_companion_identity.py --manifest /path/to/run/manifest.json
python scripts/record_companion_imagegen_result_v3.py --run-dir /path/to/run --job-id base ...
python scripts/create_canonical_base_review.py --manifest /path/to/run/manifest.json --candidate /path/a.png --candidate /path/b.png --status pass --production-use ...
python scripts/record_companion_imagegen_result_v3.py --run-dir /path/to/run --job-id thinking ...
python scripts/audit_companion_imagegen_sources_v3.py --run-dir /path/to/run
python scripts/analyze_companion_quality_v3.py --manifest /path/to/run/manifest.json
python scripts/create_companion_review_bundle.py template --manifest /path/to/run/manifest.json --out /path/to/template.json
python scripts/create_companion_review_bundle.py consume --manifest /path/to/run/manifest.json --observations /path/to/observations.json
python scripts/validate_production_contract_v3.py --manifest /path/to/run/manifest.json
python scripts/create_companion_production_readiness_report_v3.py --manifest /path/to/run/manifest.json
```

The most important blocked failure is foreground conversion disguised as cleanup: a cleaned output whose protected sprite pixels have been quantized, indexed, posterized, recolored, alpha-flattened, or geometrically changed must fail v3 recording and readiness.

When strict v3 recording blocks a base candidate, preserve the source path, hash, `source_style_analysis_v3` metrics, and visual blockers in a candidate rejection report before retrying. Regenerate with a specifically revised native-pixel prompt/reference strategy. After a small number of repeated built-in-imagegen failures for the same blocker, stop and report `notProductionReady` with the run folder and blockers; do not weaken v3, locally posterize the foreground, or deliver the static base as the completed companion package.
