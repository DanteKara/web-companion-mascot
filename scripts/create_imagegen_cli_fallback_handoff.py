#!/usr/bin/env python3
"""Create reproducible commands for an approved $imagegen CLI fallback repair."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def ps_quote(value: Path | str) -> str:
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def resolve_run_path(run_dir: Path, value: Path | str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return path.resolve()


def load_jobs(run_dir: Path) -> list[dict[str, Any]]:
    jobs_path = run_dir / "imagegen-jobs.json"
    try:
        data = json.loads(jobs_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise SystemExit(f"could not read {jobs_path}: {exc}") from exc
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in jobs if isinstance(job, dict)]


def find_job(jobs: list[dict[str, Any]], job_id: str) -> dict[str, Any]:
    for job in jobs:
        if job.get("id") == job_id:
            return job
    raise SystemExit(f"job {job_id!r} not found in imagegen-jobs.json")


def job_grounding_images(run_dir: Path, job: dict[str, Any]) -> list[Path]:
    input_images = job.get("input_images")
    if not isinstance(input_images, list):
        raise SystemExit(f"job {job.get('id')} is missing input_images")
    images: list[Path] = []
    for index, image in enumerate(input_images):
        if not isinstance(image, dict) or not isinstance(image.get("path"), str):
            raise SystemExit(f"job {job.get('id')} input_images[{index}] is missing a path")
        path = resolve_run_path(run_dir, image["path"])
        if not path.exists():
            raise SystemExit(f"grounding image does not exist: {path}")
        images.append(path)
    if not images:
        raise SystemExit(f"job {job.get('id')} must list at least one grounding image")
    return images


def job_recorded_source(run_dir: Path, job: dict[str, Any]) -> Path:
    source = maybe_job_recorded_source(run_dir, job)
    if source is None:
        raise SystemExit(
            f"job {job.get('id')!r} is missing source_path; record the selected row before CLI fallback handoff, "
            "or pass --allow-rejected-candidate-source for a non-mutating repair handoff from a rejected candidate"
        )
    return source


def maybe_job_recorded_source(run_dir: Path, job: dict[str, Any]) -> Path | None:
    raw_source = job.get("source_path") or job.get("source")
    if not isinstance(raw_source, str) or not raw_source.strip():
        return None
    source = resolve_run_path(run_dir, raw_source)
    if not source.exists():
        raise SystemExit(f"recorded job source_path does not exist: {source}")
    return source


def imagegen_command(
    *,
    python_exe: Path,
    imagegen_script: Path,
    images: list[Path],
    prompt_file: Path,
    output: Path,
    model: str,
    background: str,
    output_format: str,
    quality: str,
    size: str,
    input_fidelity: str,
    dry_run: bool,
) -> str:
    parts = [
        "&",
        ps_quote(python_exe),
        ps_quote(imagegen_script),
        "edit",
        "--model",
        model,
    ]
    for image in images:
        parts.extend(["--image", ps_quote(image)])
    parts.extend(
        [
            "--prompt-file",
            ps_quote(prompt_file),
            "--background",
            background,
            "--output-format",
            output_format,
            "--quality",
            quality,
            "--size",
            size,
            "--input-fidelity",
            input_fidelity,
            "--out",
            ps_quote(output),
            "--no-augment",
        ]
    )
    if dry_run:
        parts.append("--dry-run")
    return " ".join(parts)


def record_command(
    *,
    python_exe: Path,
    record_script: Path,
    run_dir: Path,
    job_id: str,
    output: Path,
    prompt_file: Path,
    model: str,
    background: str,
    output_format: str,
) -> str:
    parts = [
        "&",
        ps_quote(python_exe),
        ps_quote(record_script),
        "--run-dir",
        ps_quote(run_dir),
        "--job-id",
        job_id,
        "--source",
        ps_quote(output),
        "--source-provenance",
        "imagegen-cli-fallback",
        "--cli-fallback-approved",
        "--cli-fallback-model",
        model,
        "--cli-fallback-background",
        background,
        "--cli-fallback-output-format",
        output_format,
        "--cli-fallback-prompt-file",
        ps_quote(prompt_file),
        "--force",
        "--strict-row-style",
    ]
    return " ".join(parts)


def repair_intent() -> dict[str, list[str] | str]:
    return {
        "mode": "story-preserving-source-repair",
        "preserve": [
            "current row frame count and order",
            "current row state story",
            "accepted cue timing and compactness",
            "accepted expression, blink, mouth, and appendage performance",
            "apparent mascot body scale and padding",
            "native pixel-art style",
            "canonical identity, palette, props, and anatomy",
        ],
        "repair": [
            "transparent or cleanup-ready background",
            "source eye grammar",
            "strict row-source evidence",
            "identity or anatomy drift called out by visual review",
        ],
        "forbidden": [
            "do not redesign the mascot",
            "do not change the row into a different state story",
            "do not zoom, shrink, or recenter the mascot to hide the failing cue",
            "do not add generic UI symbols, detached icons, or new props",
            "do not use locally normalized backgrounds as generated production provenance",
        ],
    }


STATE_REPAIR_STORIES = {
    "thinking": (
        "preserve the current thinking loop: neutral curiosity -> thought forming -> compact idea lands -> "
        "pleased settle/reset"
    ),
    "answering": (
        "preserve the current answering loop: ready/listening -> mouth-led speech beats -> conversational "
        "blink/smile -> settled speaking loop"
    ),
    "working": (
        "preserve the current working loop: notice the task -> focus -> concrete work/progress beat -> "
        "resolved settle"
    ),
}


def default_repair_prompt_path(run_dir: Path, job_id: str) -> Path:
    return run_dir / "prompts" / "rows" / f"{job_id}-true-transparency-fallback.md"


def frame_count_text(job: dict[str, Any]) -> str:
    frames = job.get("frames")
    if isinstance(frames, int) and frames > 0:
        return f"exactly {frames} separated frames"
    return "the same separated frame count as the first input row source"


def build_default_repair_prompt(job: dict[str, Any]) -> str:
    job_id = str(job.get("id") or "row")
    state = str(job.get("state") or job_id)
    frame_text = frame_count_text(job)
    story = STATE_REPAIR_STORIES.get(
        state,
        f"preserve the current {state} loop and every accepted frame-to-frame state beat",
    )
    thinking_block = ""
    if state == "thinking":
        thinking_block = """
Thinking cue repair:
- Preserve the accepted compact cue vocabulary, timing, placement, and idea-lands beat from the first input row.
- Keep the cue close, source-bound, hard-edged, secondary to the mascot, and never oversized.
- Do not enlarge the cue to prove the idea landed, do not switch cue vocabulary, and do not add lightbulbs, stars, rays, punctuation, icons, or generic UI symbols.
"""
    answering_block = ""
    if state == "answering":
        answering_block = """
Answering repair:
- Preserve mouth-led talking as the main read, including the accepted mouth cycle, eye engagement, body rhythm, and any accepted side-appendage beat.
- Omit voice marks if they look like thought bubbles, cheek marks, punctuation, chat UI, detached flecks, or exhale clouds.
"""
    return f"""Edit the first input image as the current {state} row source. Use the other input images only as identity, scale, eye-grammar, and layout references.

This is a narrow story-preserving source repair, not a redesign.

Preserve:
- current row frame count and order
- current row state story: {story}
- accepted expression, blink, mouth, appendage, prop, cue, and body-performance acting
- apparent mascot body scale, spacing, and padding
- canonical mascot identity, silhouette, palette, outline weight, appendage count, markings, accessories, and held props
- native Codex digital-pet pixel-art style

Repair only:
- output true transparency with alpha 0 outside the sprite and accepted state-cue pixels
- restore source eye grammar from the canonical base/reference
- remove cleanup blockers such as non-flat chroma, fake checkerboard transparency, matte backgrounds, halos, shadows, or background texture
- fix only the visual-review blockers called out for this row

Output one horizontal production sprite row with {frame_text} on true transparency. Do not draw a green background, white background, gray background, checkerboard, matte color, shadow, glow, floor, vignette, or fake transparency.

Eye grammar is a hard identity lock. Preserve the canonical base eye count, shape, fill/pupil color, outline, spacing, highlight/catchlight logic, and blink style. Do not create white sclera, white crescent side-glance eyes, hollow eyes, mismatched eyes, extra catchlights, symbol eyes, or glossy anime eyes. If a gaze or blink would require changing eye style, keep the eyes forward or nearly forward and carry the acting through mouth, blink timing, body, appendage, prop, or cue timing instead.

Keep native pixel-art sprite style: hard square pixels, chunky dark outline, limited palette, flat cel shading, and hard-edged integrated state cues. No smooth illustration, glossy sticker rendering, painterly gradients, soft antialiasing, vector symbols, text, UI panels, or scenery.
{thinking_block}{answering_block}
Do not redesign the mascot, change the state story, zoom or shrink the mascot, recenter to hide a failing cue, invent new props, add generic UI symbols, add detached icons, alter identity colors, duplicate held props, add extra limbs, or use a locally normalized background as production provenance.

Reject/regenerate internally if any frame has wrong eye grammar, non-transparent background pixels outside the sprite/cue, fake checkerboard transparency, non-native pixel-art rendering, scale drift versus the first input row, changed identity, extra/missing appendages or props, random symbols, or a different state read.
"""


def normalize_prompt_text(text: str) -> str:
    return " ".join(text.lower().split())


def prompt_has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def prompt_has_preserve_word(text: str) -> bool:
    return prompt_has_any(text, ("preserve", "keep", "same", "current"))


def analyze_prompt_repair_contract(prompt_file: Path, job_id: str) -> dict[str, Any]:
    text = normalize_prompt_text(prompt_file.read_text(encoding="utf-8-sig"))
    checks: dict[str, bool] = {
        "preserve-story": prompt_has_preserve_word(text)
        and prompt_has_any(text, ("story", "performance story", "state story", "frame count")),
        "preserve-scale": prompt_has_preserve_word(text)
        and prompt_has_any(text, ("body scale", "body size", "scale", "spacing", "padding")),
        "preserve-performance-acting": prompt_has_preserve_word(text)
        and prompt_has_any(
            text,
            (
                "expression",
                "blink",
                "mouth",
                "appendage",
                "hand",
                "hand rhythm",
                "body rhythm",
                "acting",
                "performance",
            ),
        ),
        "repair-eye-grammar": "eye grammar" in text
        or ("source" in text and prompt_has_any(text, ("eyes", "eye"))),
        "repair-transparency": prompt_has_any(text, ("true transparency", "transparent", "transparency", "alpha 0"))
        and prompt_has_any(text, ("background", "alpha", "outside")),
        "no-redesign": "do not redesign" in text
        or "same mascot identity" in text
        or "preserve the mascot identity" in text
        or "keep the same mascot identity" in text,
        "no-generic-symbols": prompt_has_any(
            text,
            (
                "generic ui symbols",
                "detached icons",
                "random symbols",
                "random symbol",
                "new props",
                "chat panels",
                "punctuation",
            ),
        ),
    }
    if job_id == "thinking":
        checks.update(
            {
                "thinking-cue-compactness": prompt_has_any(
                    text,
                    (
                        "cue",
                        "state cue",
                        "visual aid",
                        "enhancer",
                        "thought",
                        "puff",
                        "bubble",
                        "orb",
                        "idea",
                        "effect",
                    ),
                )
                and prompt_has_any(
                    text,
                    (
                        "compact",
                        "small",
                        "secondary",
                        "close",
                        "source-bound",
                        "source bound",
                        "near",
                        "low",
                        "not oversized",
                        "never oversized",
                    ),
                ),
                "thinking-do-not-enlarge-cue": prompt_has_any(
                    text,
                    (
                        "do not make the cue bigger",
                        "do not enlarge the cue",
                        "do not enlarge",
                        "not oversized",
                        "never oversized",
                        "do not increase the cue",
                        "keep the cue compact",
                        "cue stays compact",
                    ),
                ),
                "thinking-no-new-cue-vocabulary": prompt_has_any(
                    text,
                    (
                        "do not add generic ui symbols",
                        "generic ui symbols",
                        "detached icons",
                        "random symbols",
                        "random symbol",
                        "new props",
                        "switch cue vocabulary",
                        "different cue vocabulary",
                        "new cue vocabulary",
                        "lightbulb",
                        "punctuation",
                    ),
                ),
            }
        )
    missing = [name for name, ok in checks.items() if not ok]
    return {
        "ok": not missing,
        "promptFile": str(prompt_file),
        "checks": checks,
        "missingRequiredChecks": missing,
    }


def default_imagegen_script() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / ".system" / "imagegen" / "scripts" / "image_gen.py"


def build_handoff(
    *,
    run_dir: Path,
    job_id: str,
    source: Path,
    prompt_file: Path | None,
    output: Path,
    imagegen_script: Path,
    record_script: Path,
    python_exe: Path,
    model: str = "gpt-image-1.5",
    background: str = "transparent",
    output_format: str = "png",
    quality: str = "high",
    size: str = "auto",
    input_fidelity: str = "high",
    allow_source_mismatch: bool = False,
    allow_rejected_candidate_source: bool = False,
    write_default_prompt: bool = False,
    user_approved: bool = False,
    approval_note: str = "",
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    if not run_dir.exists():
        raise SystemExit(f"run directory does not exist: {run_dir}")
    source = source.expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"source image does not exist: {source}")
    output = output.expanduser().resolve()
    imagegen_script = imagegen_script.expanduser().resolve()
    record_script = record_script.expanduser().resolve()
    python_exe = python_exe.expanduser().resolve()

    job = find_job(load_jobs(run_dir), job_id)
    if job.get("kind") != "row-strip":
        raise SystemExit(f"job {job_id!r} must be a row-strip job for imagegen CLI fallback handoff")
    job_status = str(job.get("status") or "")
    if job_status != "complete" and not allow_rejected_candidate_source:
        raise SystemExit(
            f"job {job_id!r} must be complete before CLI fallback handoff; pass "
            "--allow-rejected-candidate-source only for a non-mutating handoff from a visually promising "
            "but strict-rejected candidate"
        )
    prompt_file = resolve_run_path(run_dir, prompt_file) if prompt_file is not None else default_repair_prompt_path(run_dir, job_id)
    default_prompt_written = False
    if write_default_prompt:
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(build_default_repair_prompt(job), encoding="utf-8")
        default_prompt_written = True
    if not prompt_file.exists():
        raise SystemExit(
            f"prompt file does not exist: {prompt_file}; pass --write-default-prompt to create a generic "
            "story-preserving repair prompt"
        )
    recorded_source = maybe_job_recorded_source(run_dir, job)
    source_matches_recorded_job: bool | None
    source_mode = "recorded-row"
    if recorded_source is None:
        if not allow_rejected_candidate_source:
            recorded_source = job_recorded_source(run_dir, job)
        source_matches_recorded_job = None
        source_mode = "rejected-candidate"
    else:
        source_matches_recorded_job = source == recorded_source
        if not source_matches_recorded_job and allow_rejected_candidate_source:
            source_mode = "rejected-candidate"
        elif not source_matches_recorded_job and allow_source_mismatch:
            source_mode = "manual-source-mismatch"
        elif not source_matches_recorded_job:
            raise SystemExit(
                f"source image {source} does not match recorded job source_path {recorded_source}; "
                "pass --allow-source-mismatch only for an intentional manual repair branch, or "
                "--allow-rejected-candidate-source for a non-mutating repair handoff from a rejected candidate"
            )
    if recorded_source is not None and source_matches_recorded_job is False and not (
        allow_source_mismatch or allow_rejected_candidate_source
    ):
        raise SystemExit(
            f"source image {source} does not match recorded job source_path {recorded_source}; "
            "pass --allow-source-mismatch only for an intentional manual repair branch"
        )
    approval_note = approval_note.strip()
    if user_approved and not approval_note:
        raise SystemExit("--approval-note is required when recording --user-approved fallback handoff approval")

    prompt_repair_contract = analyze_prompt_repair_contract(prompt_file, job_id)
    grounding_images = job_grounding_images(run_dir, job)
    images = [source] + grounding_images
    dry_run_command = imagegen_command(
        python_exe=python_exe,
        imagegen_script=imagegen_script,
        images=images,
        prompt_file=prompt_file,
        output=output,
        model=model,
        background=background,
        output_format=output_format,
        quality=quality,
        size=size,
        input_fidelity=input_fidelity,
        dry_run=True,
    )
    run_command = imagegen_command(
        python_exe=python_exe,
        imagegen_script=imagegen_script,
        images=images,
        prompt_file=prompt_file,
        output=output,
        model=model,
        background=background,
        output_format=output_format,
        quality=quality,
        size=size,
        input_fidelity=input_fidelity,
        dry_run=False,
    )
    return {
        "ok": True,
        "jobId": job_id,
        "jobStatus": job_status,
        "sourceMode": source_mode,
        "source": str(source),
        "recordedJobSource": str(recorded_source) if recorded_source is not None else None,
        "sourceMatchesRecordedJob": source_matches_recorded_job,
        "repairIntent": repair_intent(),
        "promptRepairContract": prompt_repair_contract,
        "promptFile": str(prompt_file),
        "defaultPromptWritten": default_prompt_written,
        "repairPromptSource": (
            "generic-story-preserving-default" if default_prompt_written else "user-provided-or-existing"
        ),
        "output": str(output),
        "inputImages": [str(image) for image in images],
        "requiredEnvironment": ["OPENAI_API_KEY"],
        "requiresExplicitUserApproval": True,
        "explicitUserApprovalReceived": bool(user_approved),
        "approvalNote": approval_note,
        "dryRunCommand": dry_run_command,
        "runCommand": run_command,
        "recordCommand": record_command(
            python_exe=python_exe,
            record_script=record_script,
            run_dir=run_dir,
            job_id=job_id,
            output=output,
            prompt_file=prompt_file,
            model=model,
            background=background,
            output_format=output_format,
        ),
        "notes": [
            *(
                ["Approval has been recorded for this $imagegen CLI/API fallback handoff."]
                if user_approved
                else ["Do not run the real command until the user explicitly approves $imagegen CLI/API fallback."]
            ),
            "The real command requires OPENAI_API_KEY in the shell environment.",
            "This is a narrow source repair: preserve the current row story and scale while fixing cleanup, eye grammar, or review blockers.",
            *(
                ["Generic story-preserving fallback prompt was written before handoff creation."]
                if default_prompt_written
                else []
            ),
            *(
                [
                    "Prompt repair contract is incomplete; update the fallback prompt before running the real command: "
                    + ", ".join(prompt_repair_contract["missingRequiredChecks"])
                ]
                if not prompt_repair_contract["ok"]
                else []
            ),
            "After generation, visually inspect the output before running the record command.",
            *(
                ["Source mismatch was explicitly allowed; confirm this is an intentional manual repair branch."]
                if source_mode == "manual-source-mismatch"
                else []
            ),
            *(
                [
                    "This handoff uses a visually promising rejected or unrecorded candidate as the edit input; "
                    "do not record that candidate, and record only the inspected CLI fallback output if it passes strict row style."
                ]
                if source_mode == "rejected-candidate"
                else []
            ),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source", required=True, type=Path, help="Promising generated row source to edit")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Fallback prompt file; defaults to prompts/rows/<job-id>-true-transparency-fallback.md",
    )
    parser.add_argument(
        "--write-default-prompt",
        action="store_true",
        help="Write a compact generic story-preserving repair prompt before creating the handoff",
    )
    parser.add_argument("--out", required=True, type=Path, help="Expected CLI fallback output image")
    parser.add_argument("--imagegen-script", type=Path, default=default_imagegen_script())
    parser.add_argument("--record-script", type=Path, default=Path(__file__).with_name("record_companion_imagegen_result.py"))
    parser.add_argument("--python-exe", type=Path, default=Path(sys.executable))
    parser.add_argument("--model", default="gpt-image-1.5")
    parser.add_argument("--background", default="transparent")
    parser.add_argument("--output-format", default="png")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--size", default="auto")
    parser.add_argument("--input-fidelity", default="high")
    parser.add_argument(
        "--allow-source-mismatch",
        action="store_true",
        help="Allow --source to differ from the row source_path currently recorded in imagegen-jobs.json",
    )
    parser.add_argument(
        "--allow-rejected-candidate-source",
        action="store_true",
        help=(
            "Allow --source to be a visually promising but strict-rejected candidate for a pending or mismatched row. "
            "Creates a non-mutating repair handoff and does not record the rejected candidate."
        ),
    )
    parser.add_argument(
        "--user-approved",
        action="store_true",
        help="Record that the user explicitly approved this CLI/API fallback handoff in the current workflow.",
    )
    parser.add_argument(
        "--approval-note",
        default="",
        help="Required with --user-approved; short note capturing the explicit approval context.",
    )
    parser.add_argument("--json-out", type=Path, help="Optional JSON handoff file to write")
    args = parser.parse_args(argv)

    result = build_handoff(
        run_dir=args.run_dir,
        job_id=args.job_id,
        source=args.source,
        prompt_file=args.prompt_file,
        output=args.out,
        imagegen_script=args.imagegen_script,
        record_script=args.record_script,
        python_exe=args.python_exe,
        model=args.model,
        background=args.background,
        output_format=args.output_format,
        quality=args.quality,
        size=args.size,
        input_fidelity=args.input_fidelity,
        allow_source_mismatch=args.allow_source_mismatch,
        allow_rejected_candidate_source=args.allow_rejected_candidate_source,
        write_default_prompt=args.write_default_prompt,
        user_approved=args.user_approved,
        approval_note=args.approval_note,
    )
    if args.json_out:
        json_out = args.json_out.expanduser().resolve()
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
