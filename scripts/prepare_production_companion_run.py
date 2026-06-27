#!/usr/bin/env python3
"""Prepare a production-v3 companion run with locked quality gates."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3


PREPARE_SCRIPT = Path(__file__).with_name("prepare_companion_run.py")
_prepare_spec = importlib.util.spec_from_file_location("prepare_companion_run", PREPARE_SCRIPT)
prepare = importlib.util.module_from_spec(_prepare_spec)
assert _prepare_spec.loader is not None
_prepare_spec.loader.exec_module(prepare)

PIXEL_ART_LOCK = (
    "Production v3 lock: native 16-bit console sprite art, crisp square pixel clusters, "
    "discrete shade steps, no 3D/gloss/soft gradients, do not rely on post-generation quantization."
)


def parse_output_dir(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output-dir", required=True)
    args, _rest = parser.parse_known_args(argv)
    return Path(args.output_dir).expanduser().resolve()


def append_lock(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if PIXEL_ART_LOCK not in text:
        path.write_text(text.rstrip() + "\n\n" + PIXEL_ART_LOCK + "\n", encoding="utf-8")


def state_rule_for(state: str) -> dict[str, Any]:
    return {
        "attachment": "body-pose",
        "componentPolicy": "separate",
        "approvedAllowances": [],
        "notes": f"{state} cue must be source-bound, native pixel-art, and secondary to mascot acting.",
    }


def draft_character_bible(manifest: dict[str, Any]) -> dict[str, Any]:
    states = v3.run_states(manifest)
    return {
        "schemaVersion": 3,
        "status": "draft",
        "pixelArtProfile": "16-bit-console",
        "sourceVibe": "",
        "speciesOrForm": "",
        "bodyCore": "",
        "speciesAnchors": [],
        "silhouetteAnchors": [],
        "proportionRules": [],
        "faceGrammar": [],
        "paletteRoles": [],
        "appendages": [],
        "forbiddenMutations": [
            "fancy 3D render",
            "glossy app icon",
            "foreground quantization or posterization as cleanup",
        ],
        "personalityTraits": [],
        "motionVocabulary": [],
        "stateCueRules": {state: state_rule_for(state) for state in states},
        "qualityProfile": {"profile": "production-v3", "stateAllowances": {}},
    }


def upgrade_run(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    jobs_path = run_dir / "imagegen-jobs.json"
    manifest = v3.read_json(manifest_path)
    jobs = v3.read_json(jobs_path)

    profile_dest = run_dir / "references" / "qa-profiles-v3.json"
    profile_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(v3.V3_PROFILE_PATH, profile_dest)
    profile_sha = v3.sha256_file(profile_dest)

    style = manifest.setdefault("style", {})
    style["pixelArtProfile"] = "16-bit-console"
    style["qualityProfile"] = "production-v3"
    style["qualityProfileV3"] = {
        "profile": "production-v3",
        "path": "references/qa-profiles-v3.json",
        "sha256": profile_sha,
        "locked": True,
    }
    manifest["qualityPipelineVersion"] = 3

    character_bible_path = run_dir / v3.IDENTITY_PATH
    if not character_bible_path.exists():
        v3.write_json(character_bible_path, draft_character_bible(manifest))

    jobs["schema_version"] = max(3, int(jobs.get("schema_version") or 1))
    jobs["qualityPipelineVersion"] = 3
    jobs["quality_gate_bindings"] = {
        "qualityProfile": "production-v3",
        "qualityProfileSha256": profile_sha,
        "identityContractSha256": None,
        "canonicalBaseReviewSha256": None,
    }
    for job in v3.job_list(jobs):
        required = ["approved_identity_contract"]
        if job.get("id") != "base":
            required.append("current_canonical_base_review")
        job["quality_gates"] = {
            "contractVersion": 3,
            "requires": required,
        }
        bindings = job.setdefault("quality_gate_bindings", {})
        bindings["qualityProfileSha256"] = profile_sha
        bindings.setdefault("identityContractSha256", None)
        bindings.setdefault("canonicalBaseReviewSha256", None)

    append_lock(run_dir / "prompts" / "base.md")
    for state in v3.run_states(manifest):
        for prompt_path in (run_dir / "prompts" / f"{state}.md", run_dir / "prompts" / "rows" / f"{state}.md"):
            if prompt_path.exists():
                append_lock(prompt_path)

    v3.write_json(manifest_path, manifest)
    v3.write_json(jobs_path, jobs)
    return {
        "ok": True,
        "runDir": str(run_dir),
        "manifest": str(manifest_path),
        "characterBible": str(character_bible_path),
        "qualityProfileSha256": profile_sha,
    }


def main(argv: list[str] | None = None) -> int:
    run_dir = parse_output_dir(argv)
    prepare.main(argv)
    result = upgrade_run(run_dir)
    if "--quiet" not in (argv or []):
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
