#!/usr/bin/env python3
"""Create a production-readiness summary from the v3 contract report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import quality_pipeline_v3 as v3
import validate_production_contract_v3 as contract_v3


def build_readiness(contract_report: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(blocker) for blocker in contract_report.get("blockers", []) if blocker]
    approved_exceptions = contract_report.get("approvedExceptions", []) or []
    if blockers or contract_report.get("ok") is not True:
        status = "notProductionReady"
    elif approved_exceptions:
        status = "productionReadyWithApprovedExceptions"
    else:
        status = "productionReady"
    return {
        "schemaVersion": 3,
        "ok": status != "notProductionReady",
        "status": status,
        "productionReady": status == "productionReady",
        "productionReadyWithApprovedExceptions": status == "productionReadyWithApprovedExceptions",
        "notProductionReady": status == "notProductionReady",
        "blockers": blockers,
        "approvedExceptions": approved_exceptions,
        "contractReport": contract_report,
    }


def create_report(
    *,
    manifest_path: Path | None = None,
    contract_report_path: Path | None = None,
    json_out: Path | None = None,
) -> dict[str, Any]:
    if contract_report_path is not None:
        contract_report = v3.read_json(contract_report_path)
        run_dir = contract_report_path.expanduser().resolve().parents[1]
    elif manifest_path is not None:
        manifest_path = manifest_path.expanduser().resolve()
        run_dir = manifest_path.parent
        contract_report = contract_v3.validate_contract(manifest_path)
    else:
        raise SystemExit("provide --manifest or --contract-report")

    report = build_readiness(contract_report)
    out_path = json_out or run_dir / "qa" / "production-readiness-v3.json"
    if not out_path.is_absolute():
        out_path = run_dir / out_path
    v3.write_json(out_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--contract-report", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = create_report(
        manifest_path=args.manifest,
        contract_report_path=args.contract_report,
        json_out=args.json_out,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
