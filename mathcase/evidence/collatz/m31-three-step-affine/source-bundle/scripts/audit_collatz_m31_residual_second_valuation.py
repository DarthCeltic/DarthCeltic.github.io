#!/usr/bin/env python3
"""Census the second odd-to-odd valuation on every unresolved M31 class."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_RELATIVE = "research/collatz/structure-sample/m31-residual-second-valuation-v1/protocol.md"
PREVIOUS_RELATIVE = "research/collatz/structure-sample/m31-residual-initial-valuation-v1"
EXPECTED_RESIDUALS = 23_642_078
EXPECTED_FAMILY_ROWS = 1_900_470
EXPECTED_EXAMINED = 25_542_548
EXPECTED_MODULUS = 1 << 31
UNIFORMITY_CUTOFF = 30


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valuation_two(value: int) -> int:
    if value <= 0:
        raise ValueError("valuation input must be positive")
    return (value & -value).bit_length() - 1


def load_parent(repo: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parent = repo / PREVIOUS_RELATIVE
    manifest_path = parent / "run-manifest.json"
    summary_path = parent / "summary.json"
    manifest = json.loads(manifest_path.read_bytes())
    summary_bytes = summary_path.read_bytes()
    summary = json.loads(summary_bytes)
    if manifest.get("status") != "PASS_EXACT_FINITE_RESIDUAL_CLASS_AUDIT":
        raise ValueError("prior exact residual audit is not a recorded pass")
    if hashlib.sha256(summary_bytes).hexdigest() != manifest.get("summary_sha256"):
        raise ValueError("prior audit summary hash mismatch")
    result = summary.get("result", {})
    if result.get("m31_unresolved_classes") != EXPECTED_RESIDUALS:
        raise ValueError("prior unresolved population differs from the frozen count")
    if result.get("m31_residual_classes_examined") != EXPECTED_EXAMINED:
        raise ValueError("prior enumerated population differs from the frozen count")
    if result.get("m31_saved_family_rows_matched") != EXPECTED_FAMILY_ROWS:
        raise ValueError("prior family match count differs from the frozen count")
    if result.get("representative_v2_3n_plus_1_histogram") != {"1": EXPECTED_RESIDUALS}:
        raise ValueError("prior first-valuation histogram differs from the frozen result")
    return manifest, summary, {"manifest": sha256_file(manifest_path), "summary": hashlib.sha256(summary_bytes).hexdigest()}


def census(mask: bytearray, family_residues: Any) -> dict[str, Any]:
    base_modulus = len(mask)
    if base_modulus * 2 != EXPECTED_MODULUS:
        raise ValueError("reconstructed M30 mask has the wrong modulus")
    modulus = 2 * base_modulus
    family_index = 0
    examined = 0
    family_matches = 0
    unresolved = 0
    first_valuation = Counter()
    second_valuation = Counter()
    invariant_classes = 0
    noninvariant_classes = 0
    uniform_two_odd_step_descent = 0
    fixed_representative_two_odd_step_descent = 0
    examples_uniform: list[dict[str, int]] = []
    examples_nonuniform: list[dict[str, int]] = []

    for lift in (0, 1):
        offset = lift * base_modulus
        residue_index = mask.find(b"\x00", 0)
        while residue_index >= 0:
            residue = residue_index + offset
            examined += 1
            while family_index < len(family_residues) and family_residues[family_index] < residue:
                family_index += 1
            if family_index < len(family_residues) and family_residues[family_index] == residue:
                family_matches += 1
                family_index += 1
            else:
                unresolved += 1
                representative = residue + modulus
                if representative & 1 == 0:
                    raise ValueError("an unresolved M31 class is not odd")
                a1 = valuation_two(3 * representative + 1)
                first_valuation[str(a1)] += 1
                if a1 != 1:
                    raise ValueError("first valuation disagrees with the prior exact audit")
                first_odd = (3 * representative + 1) // 2
                a2 = valuation_two(3 * first_odd + 1)
                second_valuation[str(a2)] += 1
                if a2 < UNIFORMITY_CUTOFF:
                    invariant_classes += 1
                    if a2 >= 3:
                        uniform_two_odd_step_descent += 1
                        if len(examples_uniform) < 12:
                            examples_uniform.append({"residue": residue, "representative": representative, "a2": a2})
                else:
                    noninvariant_classes += 1
                    if len(examples_nonuniform) < 12:
                        examples_nonuniform.append({"residue": residue, "representative": representative, "a2": a2})
                if a2 >= 3:
                    fixed_representative_two_odd_step_descent += 1
            residue_index = mask.find(b"\x00", residue_index + 1)

    if family_index != len(family_residues):
        raise ValueError("not all saved M31 family rows matched the M30-uncovered lifts")
    if examined != EXPECTED_EXAMINED or family_matches != EXPECTED_FAMILY_ROWS or unresolved != EXPECTED_RESIDUALS:
        raise ValueError("reconstructed population or family counts disagree with frozen bindings")
    if sum(first_valuation.values()) != unresolved or first_valuation != Counter({"1": EXPECTED_RESIDUALS}):
        raise ValueError("rechecked first-valuation histogram does not conserve the population")
    if sum(second_valuation.values()) != unresolved:
        raise ValueError("second-valuation histogram does not conserve the population")
    if invariant_classes + noninvariant_classes != unresolved:
        raise ValueError("class-uniformity counts do not conserve the population")

    return {
        "base_modulus": base_modulus,
        "m31_modulus": modulus,
        "m31_residual_classes_examined": examined,
        "m31_saved_family_rows_matched": family_matches,
        "m31_unresolved_classes": unresolved,
        "representative_convention": "n = r + 2^31",
        "first_odd_to_odd_valuation_histogram": dict(sorted(first_valuation.items(), key=lambda pair: int(pair[0]))),
        "second_odd_to_odd_valuation_histogram": dict(sorted(second_valuation.items(), key=lambda pair: int(pair[0]))),
        "second_valuation_invariant_for_all_class_members_by_congruence": {
            "cutoff_exclusive": UNIFORMITY_CUTOFF,
            "classes_with_a2_below_cutoff": invariant_classes,
            "classes_at_or_above_cutoff_without_uniformity_claim": noninvariant_classes,
        },
        "two_odd_step_descent": {
            "fixed_representatives_with_a2_at_least_3": fixed_representative_two_odd_step_descent,
            "uniform_residue_classes_with_3_le_a2_lt_30": uniform_two_odd_step_descent,
            "uniformity_reason": "(9n+5)/2 changes by 9*k*2^30 within a fixed residue class; valuations below 30 are unchanged",
            "representative_examples_of_uniform_classes": examples_uniform,
            "representative_examples_at_or_above_cutoff": examples_nonuniform,
        },
        "scope": "Exact census on fixed representatives of the finite M31 unresolved set. Uniform two-step statements are only the congruence consequences stated in the protocol; no global convergence or novelty claim.",
    }


def run(repo: Path, output_dir: Path, protocol_path: Path) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = str((repo / "scripts").resolve())
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from sample_collatz_m31_unresolved_structure import (
        MODULUS,
        _load_m31_family_residues,
        _load_verified_m31,
        sha256_bytearray,
    )
    import scan_collatz_m31_residual as scanner31

    if MODULUS != EXPECTED_MODULUS:
        raise ValueError("existing verified M31 loader has an unexpected modulus")
    prior_manifest, prior_summary, prior_hashes = load_parent(repo)
    m31_manifest, m31_validation, scan_path = _load_verified_m31(repo)
    mask, baseline = scanner31._covered_m30(repo)
    if baseline != m31_manifest.get("baseline"):
        raise ValueError("reconstructed M30 baseline differs from the M31 package")
    if sha256_bytearray(mask) != prior_manifest.get("m30_coverage_mask_sha256"):
        raise ValueError("reconstructed M30 coverage mask differs from the prior audit")
    families, odd_family_count = _load_m31_family_residues(scan_path, EXPECTED_FAMILY_ROWS)
    if odd_family_count != EXPECTED_FAMILY_ROWS:
        raise ValueError("not every saved M31 family row is odd")

    print("[census] enumerating the frozen unresolved M31 class population", flush=True)
    result = census(mask, families)
    if result["m31_unresolved_classes"] != m31_manifest["search"]["residual_after_search"]:
        raise ValueError("census count differs from the M31 package manifest")
    if result["m31_unresolved_classes"] != m31_validation["residual_after_search"]:
        raise ValueError("census count differs from independent M31 validation")
    if result["m31_unresolved_classes"] != prior_summary["result"]["m31_unresolved_classes"]:
        raise ValueError("census count differs from the prior exact residual audit")

    summary = {
        "schema": "mathcase-collatz-m31-residual-second-valuation-summary-v1",
        "classification": "EXACT_FINITE_RESIDUAL_CLASS_CENSUS",
        "protocol_path": PROTOCOL_RELATIVE,
        "result": result,
        "lean_compiled": False,
        "axiom_checked": False,
        "global_collatz_proof": False,
    }
    summary_bytes = (json.dumps(summary, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (output_dir / "summary.json").write_bytes(summary_bytes)

    input_paths = {
        "m31_package_manifest": repo / "research/collatz/m31-exploratory/package-manifest.json",
        "m31_scan": scan_path,
        "m31_independent_validation": repo / "research/collatz/m31-exploratory/independent-validation.json",
        "m30_package_manifest": repo / "research/collatz/m30-exploratory/package-manifest.json",
        "m30_scan": repo / "research/collatz/m30-exploratory/scan/m30-residual-affine-screen.json.gz",
        "prior_audit_protocol": repo / PREVIOUS_RELATIVE / "protocol.md",
        "prior_audit_manifest": repo / PREVIOUS_RELATIVE / "run-manifest.json",
        "prior_audit_summary": repo / PREVIOUS_RELATIVE / "summary.json",
    }
    manifest = {
        "schema": "mathcase-collatz-m31-residual-second-valuation-manifest-v1",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS",
        "protocol_path": PROTOCOL_RELATIVE,
        "protocol_sha256": sha256_file(protocol_path),
        "audit_code_sha256": sha256_file(Path(__file__).resolve()),
        "inputs": {name: {"path": str(path.relative_to(repo)).replace("\\", "/"), "sha256": sha256_file(path)} for name, path in input_paths.items()},
        "prior_audit_binding": prior_hashes,
        "m30_baseline_binding": baseline,
        "m30_coverage_mask_sha256": sha256_bytearray(mask),
        "m31_family_rows": len(families),
        "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
        "network_calls": 0,
        "provider_calls": 0,
        "gpu_used": False,
        "docker_used": False,
        "lean_compiled": False,
        "axiom_checked": False,
        "global_collatz_proof": False,
    }
    (output_dir / "run-manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir.resolve()
    protocol = (args.protocol or repo / PROTOCOL_RELATIVE).resolve()
    if output.exists() and output.is_dir() and any(output.iterdir()):
        print(json.dumps({"status": "REFUSED", "reason": "output directory is not empty"}), file=sys.stderr)
        return 2
    try:
        summary = run(repo, output, protocol)
    except Exception as exc:
        output.mkdir(parents=True, exist_ok=True)
        failure = {
            "schema": "mathcase-collatz-m31-residual-second-valuation-failure-v1",
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "network_calls": 0,
            "provider_calls": 0,
            "gpu_used": False,
        }
        path = output / "failure-receipt.json"
        if not path.exists():
            path.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS", "population": summary["result"]["m31_unresolved_classes"], "second_valuation_histogram": summary["result"]["second_odd_to_odd_valuation_histogram"], "uniform_two_odd_step_descent_classes": summary["result"]["two_odd_step_descent"]["uniform_residue_classes_with_3_le_a2_lt_30"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
