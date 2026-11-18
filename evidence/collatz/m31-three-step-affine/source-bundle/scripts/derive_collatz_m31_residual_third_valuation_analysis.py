#!/usr/bin/env python3
"""Derive the exact a2-by-a3 table from the verified census marginals."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL = Path("research/collatz/structure-sample/m31-residual-third-valuation-v1/analysis-protocol.md")
RUN = Path("research/collatz/structure-sample/m31-residual-third-valuation-v1/run-1")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive(summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    result = summary["result"]
    a2 = {int(key): value for key, value in result["second_odd_to_odd_valuation_histogram"].items()}
    a3 = {int(key): value for key, value in result["third_odd_to_odd_valuation_histogram"].items()}
    descent = result["three_odd_step_descent"]
    if verification.get("status") != "PASS_INDEPENDENT_DIRECT_TRAJECTORY_AND_POPULATION_CHECK":
        raise ValueError("independent direct-trajectory verification is not a pass")
    if verification.get("direct_trajectory_records_checked") != result["m31_unresolved_classes"]:
        raise ValueError("independent verifier did not check the full residual population")
    if descent.get("fixed_representatives_with_t3_below_n") != 0:
        raise ValueError("zero-descent decomposition requires the verified zero count")
    if a2 != {1: 19_495_091, 2: 4_146_987} or a3 != {1: 19_495_091, 2: 4_146_987}:
        raise ValueError("frozen marginal counts differ from the registered census")

    a2_2_a3_2 = 0
    a2_2_a3_1 = a2[2]
    a2_1_a3_2 = a3[2]
    a2_1_a3_1 = a2[1] - a2_1_a3_2
    if a2_2_a3_2 != 0 or a2_1_a3_1 < 0 or a2_1_a3_2 + a2_1_a3_1 != a2[1]:
        raise ValueError("derived cross-tab fails conservation")
    if a2_2_a3_1 + a2_2_a3_2 != a2[2] or a2_1_a3_2 + a2_2_a3_2 != a3[2]:
        raise ValueError("derived cross-tab fails marginal reconstruction")

    uniform = result["third_valuation_uniformity_by_congruence"]
    total = result["m31_unresolved_classes"]
    if uniform.get("classes_uniformly_certified") != total or uniform.get("classes_not_certified_uniform_by_bound") != 0:
        raise ValueError("not every residual class is certified uniform by the registered bound")
    if max(a3) >= min(uniform["a2_1_cutoff_exclusive"], uniform["a2_2_cutoff_exclusive"]):
        # The branch-specific bounds are checked by the source census. This
        # guard prevents an unexpectedly large observed valuation from being
        # summarized as uniform merely from aggregate totals.
        raise ValueError("observed third valuation reaches a registered uniformity cutoff")

    return {
        "schema": "mathcase-collatz-m31-residual-third-valuation-derived-analysis-v1",
        "classification": "DERIVED_EXACT_FINITE_AGGREGATE_DECOMPOSITION",
        "population": total,
        "a2_by_a3": {
            "1": {"1": a2_1_a3_1, "2": a2_1_a3_2},
            "2": {"1": a2_2_a3_1, "2": a2_2_a3_2},
        },
        "uniform_third_valuation_classes": total,
        "uniform_three_odd_step_descent_classes": 0,
        "interpretation": "Every saved residual class has a third valuation below its registered congruence-uniformity cutoff, so that valuation is fixed across the class. The directly checked representatives all fail the three-step strict-descent threshold. This adds no descent family and says nothing about global Collatz convergence.",
        "derivation": "The direct verifier confirms zero representative descents. With the registered thresholds, every a2=2 case must therefore have a3=1. Its count equals the full a3=2 marginal, so all a3=2 cases lie in a2=1; subtraction gives the remaining a2=1,a3=1 count.",
        "trajectory_rescan_performed": False,
        "provider_calls": 0,
        "network_calls": 0,
        "lean_compiled": False,
        "global_collatz_proof": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    run_dir = (args.run_dir or repo / RUN).resolve()
    analysis_path = run_dir / "analysis.json"
    receipt_path = run_dir / "analysis-receipt.json"
    if analysis_path.exists() or receipt_path.exists():
        print(json.dumps({"status": "REFUSED", "reason": "analysis output already exists"}), file=sys.stderr)
        return 2
    try:
        summary_path = run_dir / "summary.json"
        manifest_path = run_dir / "run-manifest.json"
        verification_path = run_dir / "verification-receipt.json"
        summary_bytes = summary_path.read_bytes()
        manifest_bytes = manifest_path.read_bytes()
        verification_bytes = verification_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        summary = json.loads(summary_bytes)
        verification = json.loads(verification_bytes)
        if hashlib.sha256(summary_bytes).hexdigest() != manifest.get("summary_sha256"):
            raise ValueError("primary summary hash mismatch")
        if verification.get("run_manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest():
            raise ValueError("independent receipt is bound to a different primary manifest")
        if verification.get("summary_sha256") != hashlib.sha256(summary_bytes).hexdigest():
            raise ValueError("independent receipt is bound to a different primary summary")
        if verification.get("protocol_sha256") != manifest.get("protocol_sha256"):
            raise ValueError("independent receipt is bound to a different protocol")
        if verification.get("status") != "PASS_INDEPENDENT_DIRECT_TRAJECTORY_AND_POPULATION_CHECK":
            raise ValueError("independent receipt is not valid")
        analysis = derive(summary, verification)
        analysis_bytes = (json.dumps(analysis, sort_keys=True, indent=2) + "\n").encode("utf-8")
        analysis_path.write_bytes(analysis_bytes)
        receipt = {
            "schema": "mathcase-collatz-m31-residual-third-valuation-analysis-receipt-v1",
            "status": "PASS_DERIVED_EXACT_FINITE_AGGREGATE_DECOMPOSITION",
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "protocol_path": str(PROTOCOL).replace("\\", "/"),
            "protocol_sha256": sha256_file(repo / PROTOCOL),
            "analysis_code_path": str(Path(__file__).resolve().relative_to(repo)).replace("\\", "/"),
            "analysis_code_sha256": sha256_file(Path(__file__).resolve()),
            "run_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
            "verification_receipt_sha256": hashlib.sha256(verification_bytes).hexdigest(),
            "analysis_sha256": hashlib.sha256(analysis_bytes).hexdigest(),
            "trajectory_rescan_performed": False,
            "provider_calls": 0,
            "network_calls": 0,
        }
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"status": receipt["status"], "a2_by_a3": analysis["a2_by_a3"]}, sort_keys=True))
        return 0
    except Exception as exc:
        failure_path = run_dir / "analysis-failure-receipt.json"
        failure = {
            "schema": "mathcase-collatz-m31-residual-third-valuation-analysis-failure-v1",
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "provider_calls": 0,
            "network_calls": 0,
        }
        if run_dir.is_dir() and not failure_path.exists():
            failure_path.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
