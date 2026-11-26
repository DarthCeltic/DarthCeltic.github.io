#!/usr/bin/env python3
"""Independently verify the corrected M31 above-start derivation and bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POPULATION = 23_642_078
EXPECTED = {"1": {"1": 15_348_104, "2": 4_146_987}, "2": {"1": 4_146_987, "2": 0}}
BASE = "research/collatz/structure-sample"
PROTOCOL = f"{BASE}/m31-first-three-above-start-v1/protocol.md"
SUMMARY = f"{BASE}/m31-first-three-above-start-v1/run-1/summary.json"
MANIFEST = f"{BASE}/m31-first-three-above-start-v1/run-1/run-manifest.json"
SOURCES = (
    ("initial", f"{BASE}/m31-residual-initial-valuation-v1", "", "PASS_EXACT_FINITE_RESIDUAL_CLASS_AUDIT", "scripts/audit_collatz_m31_residual_initial_valuation.py"),
    ("second", f"{BASE}/m31-residual-second-valuation-v1", "run-1", "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS", "scripts/audit_collatz_m31_residual_second_valuation.py"),
    ("third", f"{BASE}/m31-residual-third-valuation-v1", "run-1", "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS", "scripts/audit_collatz_m31_residual_third_valuation.py"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    return raw, json.loads(raw.decode("utf-8", errors="strict"))


def sign_for_positive_n(slope: int, constant: int) -> str:
    if slope >= 0 and constant > 0:
        return "POSITIVE"
    if slope < 0 and slope + constant < 0:
        return "NEGATIVE"
    return "NOT_UNIFORM"


def expected_strata() -> list[dict[str, Any]]:
    rows = []
    for a2_text in ("1", "2"):
        for a3_text in ("1", "2"):
            a2, a3 = int(a2_text), int(a3_text)
            count = EXPECTED[a2_text][a3_text]
            t2_den = 4 if a2 == 1 else 8
            t3_num_const = 19 if a2 == 1 else 23
            t3_den = 1 << (a3 + (2 if a2 == 1 else 3))
            t3_slope = 27
            t2_t1_slope, t2_t1_const = (3, 3) if a2 == 1 else (-3, 1)
            common_den = max(t2_den, t3_den)
            t3_t2_slope = t3_slope * (common_den // t3_den) - 9 * (common_den // t2_den)
            t3_t2_const = t3_num_const * (common_den // t3_den) - 5 * (common_den // t2_den)
            t2_n_slope, t2_n_const = 9 - t2_den, 5
            t3_n_slope, t3_n_const = t3_slope - t3_den, t3_num_const
            rows.append({
                "a2": a2,
                "a3": a3,
                "class_count": count,
                "t2_formula": f"(9*n + 5)/{t2_den}",
                "t2_minus_n_numerator": {"slope": t2_n_slope, "constant": t2_n_const, "denominator": t2_den},
                "t2_above_start_for_every_positive_n_in_observed_stratum": bool(count and sign_for_positive_n(t2_n_slope, t2_n_const) == "POSITIVE"),
                "t3_formula": f"({t3_slope}*n + {t3_num_const})/{t3_den}",
                "t3_minus_n_numerator": {"slope": t3_n_slope, "constant": t3_n_const, "denominator": t3_den},
                "t3_above_start_for_every_positive_n_in_observed_stratum": bool(count and sign_for_positive_n(t3_n_slope, t3_n_const) == "POSITIVE"),
                "t2_minus_t1": {
                    "numerator": {"slope": t2_t1_slope, "constant": t2_t1_const},
                    "denominator": t2_den,
                    "sign_for_positive_n": sign_for_positive_n(t2_t1_slope, t2_t1_const),
                },
                "t3_minus_t2": {
                    "numerator": {"slope": t3_t2_slope, "constant": t3_t2_const},
                    "denominator": common_den,
                    "sign_for_positive_n": sign_for_positive_n(t3_t2_slope, t3_t2_const),
                },
            })
    return rows


def parent_statuses(repo: Path) -> dict[str, str]:
    found = {}
    for key, folder_rel, run_rel, expected_status, audit_rel in SOURCES:
        run = repo / folder_rel / run_rel if run_rel else repo / folder_rel
        manifest_raw, parent = load(run / "run-manifest.json")
        summary_raw, parent_summary = load(run / "summary.json")
        if parent.get("status") != expected_status or parent.get("summary_sha256") != sha(summary_raw):
            raise ValueError(f"{key} source status or summary binding mismatch")
        protocol = repo / parent["protocol_path"] if parent.get("protocol_path") else run / "protocol.md"
        if file_sha(protocol) != parent.get("protocol_sha256"):
            raise ValueError(f"{key} source protocol binding mismatch")
        if file_sha(repo / audit_rel) != parent.get("audit_code_sha256"):
            raise ValueError(f"{key} source audit-code binding mismatch")
        if key == "initial":
            result = parent_summary.get("result", {})
            if result.get("m31_unresolved_classes") != POPULATION or result.get("representative_v2_3n_plus_1_histogram") != {"1": POPULATION}:
                raise ValueError("initial valuation source differs from the saved population")
        elif key == "second":
            result = parent_summary.get("result", {})
            uniformity = result.get("second_valuation_invariant_for_all_class_members_by_congruence", {})
            if result.get("m31_unresolved_classes") != POPULATION or result.get("second_odd_to_odd_valuation_histogram") != {"1": 19_495_091, "2": 4_146_987}:
                raise ValueError("second valuation source differs from the saved histogram")
            if uniformity.get("classes_with_a2_below_cutoff") != POPULATION or uniformity.get("classes_at_or_above_cutoff_without_uniformity_claim") != 0:
                raise ValueError("second valuation uniformity is not established for every class")
        else:
            result = parent_summary.get("result", {})
            uniformity = result.get("third_valuation_uniformity_by_congruence", {})
            if result.get("m31_unresolved_classes") != POPULATION or uniformity.get("classes_uniformly_certified") != POPULATION or uniformity.get("classes_not_certified_uniform_by_bound") != 0:
                raise ValueError("third valuation uniformity is not established for every class")
            third_dir = run
            _, third_verify = load(third_dir / "verification-receipt.json")
            _, analysis = load(third_dir / "analysis.json")
            _, analysis_receipt = load(third_dir / "analysis-receipt.json")
            if third_verify.get("status") != "PASS_INDEPENDENT_DIRECT_TRAJECTORY_AND_POPULATION_CHECK":
                raise ValueError("third-valuation independent verification is not a pass")
            if third_verify.get("run_manifest_sha256") != sha(manifest_raw) or third_verify.get("summary_sha256") != sha(summary_raw):
                raise ValueError("third-valuation independent verification is bound to other source bytes")
            if third_verify.get("residual_index_sha256") != file_sha(third_dir / "residual-classes.u32le"):
                raise ValueError("third-valuation residual index binding mismatch")
            if file_sha(repo / third_verify["verification_code_path"]) != third_verify.get("verification_code_sha256"):
                raise ValueError("third-valuation verifier code hash mismatch")
            if analysis_receipt.get("status") != "PASS_DERIVED_EXACT_FINITE_AGGREGATE_DECOMPOSITION" or analysis.get("a2_by_a3") != EXPECTED:
                raise ValueError("third-valuation exact aggregate decomposition mismatch")
            if analysis_receipt.get("analysis_sha256") != sha((third_dir / "analysis.json").read_bytes()):
                raise ValueError("third-valuation aggregate analysis hash mismatch")
            if analysis_receipt.get("run_manifest_sha256") != sha(manifest_raw):
                raise ValueError("third-valuation aggregate is bound to other manifest bytes")
            if analysis_receipt.get("verification_receipt_sha256") != file_sha(third_dir / "verification-receipt.json"):
                raise ValueError("third-valuation aggregate is bound to other verifier bytes")
            if file_sha(repo / analysis_receipt["protocol_path"]) != analysis_receipt.get("protocol_sha256"):
                raise ValueError("third-valuation aggregate protocol hash mismatch")
            if file_sha(repo / analysis_receipt["analysis_code_path"]) != analysis_receipt.get("analysis_code_sha256"):
                raise ValueError("third-valuation aggregate code hash mismatch")
        found[key] = expected_status
    third_run = repo / SOURCES[2][1] / SOURCES[2][2]
    _, verification = load(third_run / "verification-receipt.json")
    _, analysis_receipt = load(third_run / "analysis-receipt.json")
    found["third_independent_verification"] = verification["status"]
    found["third_aggregate_decomposition"] = analysis_receipt["status"]
    return found


def verify(repo: Path) -> dict[str, Any]:
    summary_path, manifest_path = repo / SUMMARY, repo / MANIFEST
    summary_raw, summary = load(summary_path)
    manifest_raw, manifest = load(manifest_path)
    if manifest.get("status") != "PASS_DERIVED_FINITE_ABOVE_START":
        raise ValueError("derived status is not a pass")
    if sha(summary_raw) != manifest.get("summary_sha256"):
        raise ValueError("summary hash differs from run manifest")
    if manifest.get("input_sha256") != summary.get("input_sha256"):
        raise ValueError("summary and manifest input maps differ")
    if file_sha(repo / PROTOCOL) != manifest.get("protocol_sha256"):
        raise ValueError("new protocol hash mismatch")
    for script_field, hash_field in (("derivation_script_path", "derivation_script_sha256"), ("verification_script_path", "verification_script_sha256")):
        if file_sha(repo / manifest[script_field]) != manifest.get(hash_field):
            raise ValueError(f"{script_field} hash mismatch")
    for relative, expected_hash in summary["input_sha256"].items():
        path = repo / Path(relative)
        if not path.is_file() or file_sha(path) != expected_hash:
            raise ValueError(f"input bytes differ: {relative}")
    if parent_statuses(repo) != summary.get("source_statuses"):
        raise ValueError("parent evidence status map differs")
    if summary.get("classification") != "DERIVED_EXACT_FINITE_AFFINE_RESULT" or summary.get("population") != POPULATION or summary.get("modulus") != 1 << 31:
        raise ValueError("summary population or scope mismatch")
    if summary.get("external_calls") != 0 or summary.get("cost_usd") != 0:
        raise ValueError("summary violates local zero-cost boundary")
    result = summary.get("result", {})
    if result.get("every_saved_class_member_has_T1_T2_and_T3_strictly_above_original_n") is not True:
        raise ValueError("above-start conclusion missing")
    if result.get("first_step_at_which_below_original_n_is_not_ruled_out") != 4:
        raise ValueError("step-four scope boundary is missing")
    if result.get("consecutive_iterates_are_not_claimed_to_increase") is not True:
        raise ValueError("consecutive monotonicity limit is missing")
    rows = expected_strata()
    if result.get("third_step_strata") != rows:
        raise ValueError("affine formulas, signs, or strata differ from independently reconstructed values")
    if sum(row["class_count"] for row in rows) != POPULATION:
        raise ValueError("stratum counts do not conserve the population")
    if any(row["class_count"] and (not row["t2_above_start_for_every_positive_n_in_observed_stratum"] or not row["t3_above_start_for_every_positive_n_in_observed_stratum"]) for row in rows):
        raise ValueError("an observed class stratum does not remain above its original start")
    if not any(row["class_count"] and row["t2_minus_t1"]["sign_for_positive_n"] == "NEGATIVE" for row in rows):
        raise ValueError("the v2 nonmonotonicity correction is not demonstrated")
    if not any(row["class_count"] and row["t3_minus_t2"]["sign_for_positive_n"] == "NEGATIVE" for row in rows):
        raise ValueError("the v2 third-step nonmonotonicity correction is not demonstrated")
    return {
        "schema": "mathcase-collatz-m31-first-three-above-start-verification-v1",
        "status": "PASS_INDEPENDENT_DERIVATION_AND_BINDING_CHECK",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "summary_sha256": sha(summary_raw),
        "run_manifest_sha256": sha(manifest_raw),
        "verification_script_path": Path(__file__).resolve().relative_to(repo).as_posix(),
        "verification_script_sha256": file_sha(Path(__file__).resolve()),
        "inputs_rehashed": len(summary["input_sha256"]),
        "class_strata_checked": len(rows),
        "population_conserved": POPULATION,
        "nonmonotone_observed_strata_confirmed": 2,
        "external_calls": 0,
        "cost_usd": 0,
        "lean_compiled": False,
        "trajectory_rescan_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    try:
        receipt = verify(repo)
        output = args.output.resolve(strict=False)
        if output.exists():
            raise FileExistsError("refusing to overwrite verification receipt")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"verification blocked: {exc}\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
