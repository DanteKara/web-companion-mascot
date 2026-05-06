#!/usr/bin/env python3
"""Record a selected $imagegen output for a web companion mascot generation job."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_BASE_PATH = "references/canonical-base.png"
USER_ART_PROVENANCE = {
    "user-provided-integrated-row-art",
    "artist-provided-integrated-row-art",
}


def load_jobs(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"job manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def job_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in jobs if isinstance(job, dict)]


def find_job(manifest: dict[str, Any], job_id: str) -> dict[str, Any]:
    for job in job_list(manifest):
        if job.get("id") == job_id:
            return job
    raise SystemExit(f"unknown job id: {job_id}")


def image_metadata(path: Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_relative(path: Path, run_dir: Path) -> str:
    return str(path.resolve().relative_to(run_dir.resolve()))


def completed_job_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        str(job["id"])
        for job in job_list(manifest)
        if job.get("status") == "complete" and isinstance(job.get("id"), str)
    }


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def default_generated_images_root() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser().resolve()
    return codex_home / "generated_images"


def validate_source_path(
    *,
    source: Path,
    run_dir: Path,
    requested_provenance: str,
    allow_synthetic_test_source: bool,
) -> str:
    if allow_synthetic_test_source:
        return "synthetic-test"
    if is_relative_to(source, run_dir):
        raise SystemExit(
            "source image is inside the companion run directory; record the original "
            "$imagegen output from $CODEX_HOME/generated_images/.../ig_*.png instead"
        )
    if requested_provenance in USER_ART_PROVENANCE:
        return requested_provenance
    generated_root = default_generated_images_root()
    if not is_relative_to(source, generated_root) or not source.name.startswith("ig_"):
        raise SystemExit(
            "source image does not look like a built-in $imagegen output; expected "
            f"{generated_root}/.../ig_*.png. Do not ingest locally drawn, post-processed, "
            "or composited row strips as production visual job outputs."
        )
    return "built-in-imagegen"


def validate_required_grounding(job: dict[str, Any], run_dir: Path) -> None:
    if job.get("allow_prompt_only_generation") is not False:
        return
    inputs = job.get("input_images")
    if not isinstance(inputs, list) or not inputs:
        raise SystemExit(
            f"job {job.get('id')} does not list input_images; grounded companion row jobs must attach references"
        )
    missing = []
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise SystemExit(f"job {job.get('id')} has an invalid input image entry")
        path = run_dir / item["path"]
        if not path.is_file():
            missing.append(str(path))
    if missing:
        raise SystemExit(
            f"job {job.get('id')} is missing required grounding image(s): " + ", ".join(missing)
        )


def update_manifest_canonical_base(
    *,
    run_dir: Path,
    reference: dict[str, Any],
) -> None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(manifest, dict):
        manifest["canonicalIdentityReference"] = reference
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def update_request_canonical_base(
    *,
    run_dir: Path,
    reference: dict[str, Any],
) -> None:
    request_path = run_dir / "companion_request.json"
    if not request_path.exists():
        return
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if isinstance(request, dict):
        request["canonicalIdentityReference"] = reference
        request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")


def update_base_canonical_reference(
    *,
    run_dir: Path,
    output: Path,
    manifest: dict[str, Any],
    job: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    if job.get("id") != "base":
        return

    canonical = run_dir / CANONICAL_BASE_PATH
    canonical.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, canonical)
    reference = {
        "path": manifest_relative(canonical, run_dir),
        "source_job": "base",
        "sha256": file_sha256(canonical),
        "metadata": metadata,
    }
    job["canonical_reference_path"] = reference["path"]
    manifest["canonical_identity_reference"] = reference
    update_manifest_canonical_base(run_dir=run_dir, reference=reference)
    update_request_canonical_base(run_dir=run_dir, reference=reference)


def record_result(
    *,
    run_dir: Path,
    job_id: str,
    source: Path,
    source_provenance: str,
    force: bool,
    allow_synthetic_test_source: bool,
) -> dict[str, Any]:
    if not source.is_file():
        raise SystemExit(f"source image not found: {source}")
    source_provenance = validate_source_path(
        source=source,
        run_dir=run_dir,
        requested_provenance=source_provenance,
        allow_synthetic_test_source=allow_synthetic_test_source,
    )

    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = load_jobs(manifest_path)
    job = find_job(manifest, job_id)

    missing_deps = [
        dep
        for dep in job.get("depends_on", [])
        if isinstance(dep, str) and dep not in completed_job_ids(manifest)
    ]
    if missing_deps:
        raise SystemExit(f"job {job_id} is not ready; missing dependency result(s): {', '.join(missing_deps)}")
    validate_required_grounding(job, run_dir)

    output_raw = job.get("output_path")
    if not isinstance(output_raw, str):
        raise SystemExit(f"job {job_id} has no output_path")
    output = run_dir / output_raw
    if output.exists() and not force:
        raise SystemExit(f"{output} already exists; pass --force to replace it")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    metadata = image_metadata(output)

    job["status"] = "complete"
    job["source_path"] = str(source)
    job["source_provenance"] = source_provenance
    job["source_sha256"] = file_sha256(source)
    job["output_sha256"] = file_sha256(output)
    if source_provenance == "synthetic-test":
        job["synthetic_test_source"] = True
    else:
        job.pop("synthetic_test_source", None)
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    job["metadata"] = metadata
    for key in ["last_error", "secondary_fallback", "repair_reason", "queued_at"]:
        job.pop(key, None)

    update_base_canonical_reference(
        run_dir=run_dir,
        output=output,
        manifest=manifest,
        job=job,
        metadata=metadata,
    )

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "job_id": job_id,
        "output": str(output),
        "metadata": metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--source-provenance",
        choices=["auto", "built-in-imagegen", "user-provided-integrated-row-art", "artist-provided-integrated-row-art"],
        default="auto",
        help="Use auto/built-in-imagegen for normal $imagegen outputs, or explicitly mark finished user/artist integrated row art.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-synthetic-test-source", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = record_result(
        run_dir=Path(args.run_dir).expanduser().resolve(),
        job_id=args.job_id,
        source=Path(args.source).expanduser().resolve(),
        source_provenance=args.source_provenance,
        force=args.force,
        allow_synthetic_test_source=args.allow_synthetic_test_source,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
