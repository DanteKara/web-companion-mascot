# Web Companion Mascot

A Codex skill for creating complete animated **16-bit pixel-art** companions for React, chatbot, hover, and drag/drop website experiences.

Production output includes an approved character identity, a canonical base, grounded state rows, transparent atlases, extracted frames, previews, QA evidence, strict validation, and React integration files.

## Install

```bash
npx --yes skills add DanteKara/web-companion-mascot -g -y
```

Restart Codex after installing or updating the skill.

## Use

```text
Use $web-companion-mascot to create a complete production React companion from this character brief.
The canonical reference and every row must be authentic native 16-bit pixel art, not a 3D render converted afterward.
```

## Quality pipeline v3

New production runs use:

```bash
python scripts/prepare_production_companion_run.py ...
python scripts/approve_companion_identity.py --manifest /path/to/run/manifest.json
python scripts/record_companion_imagegen_result_v3.py ...
python scripts/create_canonical_base_review.py ...
python scripts/audit_companion_imagegen_sources_v3.py --run-dir /path/to/run
python scripts/analyze_companion_quality_v3.py --manifest /path/to/run/manifest.json
python scripts/create_companion_review_bundle.py ...
python scripts/validate_production_contract_v3.py --manifest /path/to/run/manifest.json
python scripts/create_companion_production_readiness_report_v3.py --manifest /path/to/run/manifest.json
```

The v3 pipeline prevents:

- quantisation or posterisation being disguised as chroma cleanup;
- state rows being generated before identity and base approval;
- QA thresholds being loosened after warnings appear;
- post-hoc cue/overlap metadata changes;
- blanket boolean visual reviews;
- smooth 3D or glossy render references being accepted as production sprite art.

Read [SKILL.md](SKILL.md) and `references/quality-pipeline-v3.md` for the complete workflow.

## Production review notes

For high-visibility audition rows, especially thinking, working, and answering, do not accept output without anatomy review, state-performance review, and eye-grammar review. For focused auditions, run strict validation with the review gates enabled:

```bash
python scripts/validate_companion_manifest.py \
  --manifest /path/to/run/manifest.json \
  --profile audition \
  --strict \
  --require-anatomy-review \
  --require-state-performance-review \
  --require-eye-grammar-review
```

Anatomy review must name the body core, appendage count, placement/anchors, allowed motion/interactors, and forbidden extra anatomy. State-performance review must confirm the mascot is acting the state rather than hiding weak motion behind a symbol. Eye-grammar review must confirm every used frame preserves the approved eye count, shape, fill/pupil color, highlight logic, spacing, placement, and blink style.

Thinking cues should use an accepted cue vocabulary and a stable source-to-peak trail. At the idea peak, the primary cue element is only slightly larger, never oversized; do not enlarge the cue to prove the idea landed. For separated elements, the smallest element stays closest to the inferred source. Do not let intermediate cue elements drift downward, reverse direction, jump sideways, or reorder the trail.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

MIT
