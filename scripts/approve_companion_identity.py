#!/usr/bin/env python3
"""Approve the production-v3 companion identity contract before visual jobs complete."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3


def approve_identity(manifest_path: Path | str, *, from_json: Path | str | None = None) -> dict[str, Any]:
    manifest_path = Path(manifest_path).expanduser().resolve()
    run_dir = manifest_path.parent
    manifest = v3.read_json(manifest_path)
    jobs = v3.jobs_data(run_dir)

    complete = [str(job.get("id")) for job in v3.job_list(jobs) if job.get("status") == "complete"]
    if complete:
        raise SystemExit("cannot approve identity after visual jobs are already complete: " + ", ".join(complete))

    source = Path(from_json).expanduser().resolve() if from_json else run_dir / v3.IDENTITY_PATH
    identity = v3.read_json(source)
    errors = v3.identity_contract_errors(identity, v3.run_states(manifest))
    if errors:
        raise SystemExit("identity contract is not approvable: " + "; ".join(errors))
    identity["approvedAt"] = datetime.now(timezone.utc).isoformat()
    identity["sourceManifestSha256"] = v3.sha256_file(manifest_path)

    dest = run_dir / v3.IDENTITY_PATH
    v3.write_json(dest, identity)
    identity_sha = v3.sha256_file(dest)

    style = manifest.setdefault("style", {})
    style["identityContract"] = {
        "path": v3.IDENTITY_PATH,
        "status": "approved",
        "sha256": identity_sha,
        "approvedAt": identity["approvedAt"],
    }
    v3.write_json(manifest_path, manifest)

    bindings = jobs.setdefault("quality_gate_bindings", {})
    bindings["identityContractSha256"] = identity_sha
    for job in v3.job_list(jobs):
        job_bindings = job.setdefault("quality_gate_bindings", {})
        job_bindings["identityContractSha256"] = identity_sha
    v3.write_jobs(run_dir, jobs)

    return {"ok": True, "identityContract": str(dest), "identityContractSha256": identity_sha}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--from-json", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(approve_identity(args.manifest, from_json=args.from_json), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
