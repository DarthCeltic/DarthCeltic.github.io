#!/usr/bin/env python3
"""Derive exact first-three iterates-above-start bounds from hash-bound audits."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL = "research/collatz/structure-sample/m31-first-three-above-start-v1/protocol.md"
POPULATION = 23_642_078
EXPECTED_CROSS_TAB = {"1": {"1": 15_348_104, "2": 4_146_987}, "2": {"1": 4_146_987, "2": 0}}
SOURCES = (
    ("initial", "research/collatz/structure-sample/m31-residual-initial-valuation-v1", "", "PASS_EXACT_FINITE_RESIDUAL_CLASS_AUDIT", "scripts/audit_collatz_m31_residual_initial_valuation.py"),
    ("second", "research/collatz/structure-sample/m31-residual-second-valuation-v1", "run-1", "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS", "scripts/audit_collatz_m31_residual_second_valuation.py"),
    ("third", "research/collatz/structure-sample/m31-residual-third-valuation-v1", "run-1", "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS", "scripts/audit_collatz_m31_residual_third_valuation.py"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    return raw, json.loads(raw.decode("utf-8", errors="strict"))


def bind(repo: Path, path: Path, inputs: dict[str, str]) -> str:
    resolved = path.resolve(strict=True)
    relative = resolved.relative_to(repo.resolve(strict=True)).as_posix()
    digest = file_sha(resolved)
    inputs[relative] = digest
    return digest


def load_source(repo: Path, key: str, folder_rel: str, run_rel: str, expected_status: str, audit_script_rel: str, inputs: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    folder = repo / folder_rel
    run = folder / run_rel if run_rel else folder
    manifest_path = run / "run-manifest.json"
    summary_path = run / "summary.json"
    manifest_bytes, manifest = read_json(manifest_path)
    summary_bytes, summary = read_json(summary_path)
    if manifest.get("status") != expected_status:
        raise ValueError(f"{key} source status differs from its exact required pass")
    if sha(summary_bytes) != manifest.get("summary_sha256"):
        raise ValueError(f"{key} source summary hash mismatch")
    protocol_rel = manifest.get("protocol_path")
    protocol_path = repo / protocol_rel if protocol_rel else folder / "protocol.md"
    protocol_hash = bind(repo, protocol_path, inputs)
    if protocol_hash != manifest.get("protocol_sha256"):
        raise ValueError(f"{key} source protocol hash mismatch")
    audit_path = repo / audit_script_rel
    audit_hash = bind(repo, audit_path, inputs)
    if audit_hash != manifest.get("audit_code_sha256"):
        raise ValueError(f"{key} source audit code hash mismatch")
    bind(repo, manifest_path, inputs)
    bind(repo, summary_path, inputs)
    if key == "third":
        verify_path = repo / manifest["verification_code_path"]
        test_path = repo / manifest["test_code_path"]
        if bind(repo, verify_path, inputs) != manifest.get("verification_code_sha256"):
            raise ValueError("third source verifier code hash mismatch")
        if bind(repo, test_path, inputs) != manifest.get("test_code_sha256"):
            raise ValueError("third source test code hash mismatch")
    return manifest, summary, {"status": manifest["status"], "protocol_path": protocol_rel or str(protocol_path.relative_to(repo)).replace("\\", "/")}


def third_formula_parameters(a2: int, a3: int) -> tuple[int, int, int]:
    if a2 == 1:
        return 27, 19, 1 << (a3 + 2)
    if a2 == 2:
        return 27, 23, 1 << (a3 + 3)
    raise ValueError("a2 must be 1 or 2")


def sign_for_positive_n(slope: int, constant: int) -> str:
    """Classify slope*n + constant for every integer n >= 1."""
    if slope >= 0 and constant > 0:
        return "POSITIVE"
    if slope < 0 and slope + constant < 0:
        return "NEGATIVE"
    return "NOT_UNIFORM"


def derive(repo: Path) -> tuple[dict[str, Any], dict[str, str]]:
    inputs: dict[str, str] = {}
    loaded: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    for spec in SOURCES:
        key, folder, run, status, audit = spec
        loaded[key] = load_source(repo, key, folder, run, status, audit, inputs)

    initial_manifest, initial, _ = loaded["initial"]
    second_manifest, second, _ = loaded["second"]
    third_manifest, third, third_info = loaded["third"]
    third_dir = repo / "research/collatz/structure-sample/m31-residual-third-valuation-v1/run-1"

    verification_path = third_dir / "verification-receipt.json"
    verification_bytes, verification = read_json(verification_path)
    if verification.get("status") != "PASS_INDEPENDENT_DIRECT_TRAJECTORY_AND_POPULATION_CHECK":
        raise ValueError("third-census independent verification did not pass")
    if verification.get("run_manifest_sha256") != file_sha(third_dir / "run-manifest.json"):
        raise ValueError("third-census verification is bound to different manifest bytes")
    if verification.get("summary_sha256") != file_sha(third_dir / "summary.json"):
        raise ValueError("third-census verification is bound to different summary bytes")
    if verification.get("protocol_sha256") != third_manifest.get("protocol_sha256"):
        raise ValueError("third-census verification is bound to a different protocol")
    if bind(repo, repo / verification["verification_code_path"], inputs) != verification.get("verification_code_sha256"):
        raise ValueError("third-census verification code hash mismatch")
    if verification.get("test_code_sha256") != third_manifest.get("test_code_sha256"):
        raise ValueError("third-census test-code binding mismatch")
    residual_path = third_dir / "residual-classes.u32le"
    if bind(repo, residual_path, inputs) != verification.get("residual_index_sha256"):
        raise ValueError("third-census residual index hash mismatch")
    bind(repo, verification_path, inputs)

    analysis_path = third_dir / "analysis.json"
    analysis_bytes, analysis = read_json(analysis_path)
    analysis_receipt_path = third_dir / "analysis-receipt.json"
    analysis_receipt_bytes, analysis_receipt = read_json(analysis_receipt_path)
    analysis_protocol_path = repo / analysis_receipt["protocol_path"]
    if analysis_receipt.get("status") != "PASS_DERIVED_EXACT_FINITE_AGGREGATE_DECOMPOSITION":
        raise ValueError("third-census aggregate decomposition did not pass")
    if analysis_receipt.get("analysis_sha256") != sha(analysis_bytes):
        raise ValueError("third-census aggregate analysis hash mismatch")
    if analysis_receipt.get("run_manifest_sha256") != file_sha(third_dir / "run-manifest.json"):
        raise ValueError("third-census aggregate analysis is bound to a different manifest")
    if analysis_receipt.get("verification_receipt_sha256") != sha(verification_bytes):
        raise ValueError("third-census aggregate analysis is bound to different verification bytes")
    if bind(repo, analysis_protocol_path, inputs) != analysis_receipt.get("protocol_sha256"):
        raise ValueError("third-census analysis protocol hash mismatch")
    if bind(repo, repo / analysis_receipt["analysis_code_path"], inputs) != analysis_receipt.get("analysis_code_sha256"):
        raise ValueError("third-census analysis code hash mismatch")
    bind(repo, analysis_path, inputs)
    bind(repo, analysis_receipt_path, inputs)

    initial_result = initial.get("result", {})
    second_result = second.get("result", {})
    third_result = third.get("result", {})
    if not initial.get("all_unresolved_residuals_have_v2_one_for_fixed_representative"):
        raise ValueError("initial audit does not certify the first valuation result")
    if initial_result.get("m31_unresolved_classes") != POPULATION or initial_result.get("representative_v2_3n_plus_1_histogram") != {"1": POPULATION}:
        raise ValueError("initial valuation result differs from frozen population")
    if second_result.get("m31_unresolved_classes") != POPULATION or second_result.get("second_odd_to_odd_valuation_histogram") != {"1": 19_495_091, "2": 4_146_987}:
        raise ValueError("second valuation result differs from frozen population")
    second_uniformity = second_result.get("second_valuation_invariant_for_all_class_members_by_congruence", {})
    if second_uniformity.get("classes_with_a2_below_cutoff") != POPULATION or second_uniformity.get("classes_at_or_above_cutoff_without_uniformity_claim") != 0:
        raise ValueError("second valuation is not certified uniform throughout every class")
    if third_result.get("m31_unresolved_classes") != POPULATION:
        raise ValueError("third valuation population differs from frozen count")
    third_uniformity = third_result.get("third_valuation_uniformity_by_congruence", {})
    if third_uniformity.get("classes_uniformly_certified") != POPULATION or third_uniformity.get("classes_not_certified_uniform_by_bound") != 0:
        raise ValueError("third valuation is not certified uniform throughout every class")
    if third_result.get("three_odd_step_descent", {}).get("fixed_representatives_with_t3_below_n") != 0:
        raise ValueError("third-step representative descent count differs from frozen result")
    if analysis.get("a2_by_a3") != EXPECTED_CROSS_TAB:
        raise ValueError("third valuation cross-tab differs from frozen result")
    if sum(v for inner in EXPECTED_CROSS_TAB.values() for v in inner.values()) != POPULATION:
        raise ValueError("third valuation cross-tab fails population conservation")

    strata = []
    for a2_text in ("1", "2"):
        for a3_text in ("1", "2"):
            count = EXPECTED_CROSS_TAB[a2_text][a3_text]
            a2, a3 = int(a2_text), int(a3_text)
            slope, constant, denominator = third_formula_parameters(a2, a3)
            t2_denominator = 4 if a2 == 1 else 8
            t2_minus_t1_slope = 3 if a2 == 1 else -3
            t2_minus_t1_constant = 3 if a2 == 1 else 1
            common_denominator = max(denominator, t2_denominator)
            t3_minus_t2_slope = (
                slope * (common_denominator // denominator)
                - 9 * (common_denominator // t2_denominator)
            )
            t3_minus_t2_constant = (
                constant * (common_denominator // denominator)
                - 5 * (common_denominator // t2_denominator)
            )
            t2_minus_n_slope = 9 - t2_denominator
            t2_minus_n_constant = 5
            t3_minus_n_slope = slope - denominator
            t3_minus_n_constant = constant
            t2_above_start = sign_for_positive_n(t2_minus_n_slope, t2_minus_n_constant) == "POSITIVE"
            t3_above_start = sign_for_positive_n(t3_minus_n_slope, t3_minus_n_constant) == "POSITIVE"
            if count and (not t2_above_start or not t3_above_start):
                raise ValueError("an observed stratum does not keep both iterates above the original start")
            strata.append({
                "a2": a2, "a3": a3, "class_count": count,
                "t2_formula": f"(9*n + 5)/{t2_denominator}",
                "t2_minus_n_numerator": {"slope": t2_minus_n_slope, "constant": t2_minus_n_constant, "denominator": t2_denominator},
                "t2_above_start_for_every_positive_n_in_observed_stratum": bool(count and t2_above_start),
                "t3_formula": f"({slope}*n + {constant})/{denominator}",
                "t3_minus_n_numerator": {"slope": t3_minus_n_slope, "constant": t3_minus_n_constant, "denominator": denominator},
                "t3_above_start_for_every_positive_n_in_observed_stratum": bool(count and t3_above_start),
                "t2_minus_t1": {
                    "numerator": {"slope": t2_minus_t1_slope, "constant": t2_minus_t1_constant},
                    "denominator": t2_denominator,
                    "sign_for_positive_n": sign_for_positive_n(t2_minus_t1_slope, t2_minus_t1_constant),
                },
                "t3_minus_t2": {
                    "numerator": {"slope": t3_minus_t2_slope, "constant": t3_minus_t2_constant},
                    "denominator": common_denominator,
                    "sign_for_positive_n": sign_for_positive_n(t3_minus_t2_slope, t3_minus_t2_constant),
                },
            })
    if sum(row["class_count"] for row in strata) != POPULATION:
        raise ValueError("affine strata do not conserve the residual population")
    if any(row["class_count"] and row["t2_minus_t1"]["sign_for_positive_n"] != "NEGATIVE" for row in strata if row["a2"] == 2):
        raise ValueError("the observed a2=2 second-step decrease is not represented")
    if any(row["class_count"] and row["t3_minus_t2"]["sign_for_positive_n"] != "NEGATIVE" for row in strata if (row["a2"], row["a3"]) == (1, 2)):
        raise ValueError("the observed (a2,a3)=(1,2) third-step decrease is not represented")
    if bind(repo, repo / PROTOCOL, inputs) != file_sha(repo / PROTOCOL):
        raise ValueError("new protocol could not be bound")

    summary = {
        "schema": "mathcase-collatz-m31-first-three-above-start-summary-v1",
        "classification": "DERIVED_EXACT_FINITE_AFFINE_RESULT",
        "status": "PASS_DERIVED_FINITE_ABOVE_START",
        "population": POPULATION,
        "modulus": 1 << 31,
        "class_member_convention": "n = r + k*2^31 for each saved odd residual residue r and integer k >= 0",
        "result": {
            "every_saved_class_member_has_T1_T2_and_T3_strictly_above_original_n": True,
            "first_step_at_which_below_original_n_is_not_ruled_out": 4,
            "consecutive_iterates_are_not_claimed_to_increase": True,
            "third_step_strata": strata,
        },
        "input_sha256": inputs,
        "source_statuses": {"initial": initial_manifest["status"], "second": second_manifest["status"], "third": third_manifest["status"], "third_independent_verification": verification["status"], "third_aggregate_decomposition": analysis_receipt["status"]},
        "limits": ["Finite result for every positive member of the saved M31 residual classes, conditioned on the hash-bound valuation audits.", "T2 can be below T1 in the observed a2=2 strata; T3 can be below T2 in the observed (a2,a3)=(1,2) stratum.", "No new trajectory scan, Lean compilation, M4 promotion, convergence proof, probability claim, or novelty claim.", "A value below the original n at step four or later is not established; step four is only the first step not excluded by this result."],
        "external_calls": 0,
        "cost_usd": 0,
    }
    return summary, inputs


def execute(repo: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    try:
        summary, inputs = derive(repo)
        protocol_path = repo / PROTOCOL
        derivation_path = Path(__file__).resolve()
        verifier_path = repo / "scripts/verify_collatz_m31_first_three_above_start_v1.py"
        summary_bytes = (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        manifest = {
            "schema": "mathcase-collatz-m31-first-three-above-start-manifest-v1",
            "status": "PASS_DERIVED_FINITE_ABOVE_START",
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "protocol_path": PROTOCOL,
            "protocol_sha256": file_sha(protocol_path),
            "derivation_script_path": derivation_path.relative_to(repo).as_posix(),
            "derivation_script_sha256": file_sha(derivation_path),
            "verification_script_path": verifier_path.relative_to(repo).as_posix(),
            "verification_script_sha256": file_sha(verifier_path),
            "summary_sha256": sha(summary_bytes),
            "input_sha256": inputs,
            "external_calls": 0,
            "cost_usd": 0,
            "lean_compiled": False,
            "m4_promoted": False,
            "trajectory_rescan_performed": False,
        }
        (output / "summary.json").write_bytes(summary_bytes)
        (output / "run-manifest.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return manifest
    except Exception as exc:
        failure = {
            "schema": "mathcase-collatz-m31-first-three-above-start-failure-v1",
            "status": "FAIL_PRESERVED",
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "script_path": Path(__file__).resolve().relative_to(repo).as_posix(),
            "script_sha256": file_sha(Path(__file__).resolve()),
            "protocol_sha256": file_sha(repo / PROTOCOL),
            "failure_type": type(exc).__name__,
            "failure": str(exc),
            "external_calls": 0,
            "cost_usd": 0,
        }
        (output / "failure-receipt.json").write_bytes((json.dumps(failure, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    output = args.output_dir.resolve(strict=False)
    if output.exists():
        parser.error("output directory exists; refusing overwrite")
    try:
        manifest = execute(repo, output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"derivation blocked; failure receipt preserved: {exc}\n")
    print(json.dumps({"status": manifest["status"], "summary_sha256": manifest["summary_sha256"], "output_dir": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
