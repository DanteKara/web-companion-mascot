#!/usr/bin/env python3
"""Show ready and blocked $imagegen jobs for a web companion mascot run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "imagegen-jobs.json"
    if not path.exists():
        raise SystemExit(f"job manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def jobs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw = manifest.get("jobs")
    if not isinstance(raw, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in raw if isinstance(job, dict)]


def completed_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        str(job["id"])
        for job in jobs(manifest)
        if job.get("status") == "complete" and isinstance(job.get("id"), str)
    }


def missing_deps(job: dict[str, Any], completed: set[str]) -> list[str]:
    deps = job.get("depends_on", [])
    if not isinstance(deps, list):
        return []
    return [dep for dep in deps if isinstance(dep, str) and dep not in completed]


def job_view(job: dict[str, Any], run_dir: Path, completed: set[str]) -> dict[str, Any]:
    prompt_file = job.get("prompt_file")
    output_path = job.get("output_path")
    inputs = job.get("input_images") if isinstance(job.get("input_images"), list) else []
    input_images: list[dict[str, Any]] = []
    for item in inputs:
        path = (
            run_dir / item["path"]
            if isinstance(item, dict) and isinstance(item.get("path"), str)
            else None
        )
        input_images.append(
            {
                "path": str(path) if path else None,
                "role": item.get("role") if isinstance(item, dict) else None,
                "exists": path.is_file() if path else False,
            }
        )

    return {
        "id": job.get("id"),
        "kind": job.get("kind"),
        "state": job.get("state"),
        "frames": job.get("frames"),
        "status": job.get("status", "pending"),
        "prompt_file": str(run_dir / prompt_file) if isinstance(prompt_file, str) else None,
        "input_images": input_images,
        "output_path": str(run_dir / output_path) if isinstance(output_path, str) else None,
        "missing_dependencies": missing_deps(job, completed),
        "generation_skill": job.get("generation_skill"),
        "requires_grounded_generation": job.get("requires_grounded_generation", False),
        "allow_prompt_only_generation": job.get("allow_prompt_only_generation", False),
        "identity_reference_paths": job.get("identity_reference_paths", []),
        "source_provenance": job.get("source_provenance"),
        "recording_owner": job.get("recording_owner", "parent"),
    }


def status(run_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(run_dir)
    completed = completed_ids(manifest)
    pending = [job for job in jobs(manifest) if job.get("status", "pending") != "complete"]
    ready = [job for job in pending if not missing_deps(job, completed)]
    blocked = [job for job in pending if missing_deps(job, completed)]
    return {
        "ok": True,
        "run_dir": str(run_dir),
        "counts": {
            "total": len(jobs(manifest)),
            "complete": len(completed),
            "ready": len(ready),
            "blocked": len(blocked),
        },
        "ready_jobs": [job_view(job, run_dir, completed) for job in ready],
        "blocked_jobs": [job_view(job, run_dir, completed) for job in blocked],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).expanduser().resolve()
    print(json.dumps(status(run_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
