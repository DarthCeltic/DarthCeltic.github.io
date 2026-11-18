#!/usr/bin/env python3
"""Census the third odd-to-odd valuation on every unresolved M31 class."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_RELATIVE = "research/collatz/structure-sample/m31-residual-third-valuation-v1/protocol.md"
SECOND_RELATIVE = "research/collatz/structure-sample/m31-residual-second-valuation-v1"
EXPECTED_RESIDUALS = 23_642_078
EXPECTED_FAMILY_ROWS = 1_900_470
EXPECTED_EXAMINED = 25_542_548
EXPECTED_MODULUS = 1 << 31


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


def third_valuation(n: int, a2: int) -> int:
    if n <= 0 or n & 1 == 0:
        raise ValueError("third valuation requires a positive odd representative")
    u = (3 * n + 1) // 2
    v = (3 * u + 1) // (1 << a2)
    return valuation_two(3 * v + 1)


def third_odd_iterate(n: int, a2: int, a3: int) -> int:
    u = (3 * n + 1) // 2
    v = (3 * u + 1) // (1 << a2)
    return (3 * v + 1) // (1 << a3)


def formula_third_odd_iterate(n: int, a2: int, a3: int) -> int:
    if a2 == 1:
        return (27 * n + 19) // (1 << (a3 + 2))
    if a2 == 2:
        return (27 * n + 23) // (1 << (a3 + 3))
    raise ValueError("the frozen residual set requires a2 to be 1 or 2")


def descent_minimum(a2: int) -> int:
    if a2 == 1:
        return 4
    if a2 == 2:
        return 5
    raise ValueError("the frozen residual set requires a2 to be 1 or 2")


def class_uniformity_cutoff(a2: int) -> int:
    if a2 == 1:
        return 29
    if a2 == 2:
        return 28
    raise ValueError("the frozen residual set requires a2 to be 1 or 2")


def load_parent(repo: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    parent = repo / SECOND_RELATIVE
    manifest_path = parent / "run-1" / "run-manifest.json"
    summary_path = parent / "run-1" / "summary.json"
    manifest = json.loads(manifest_path.read_bytes())
    summary_bytes = summary_path.read_bytes()
    summary = json.loads(summary_bytes)
    if manifest.get("status") != "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS":
        raise ValueError("prior second-valuation census is not a recorded pass")
    if hashlib.sha256(summary_bytes).hexdigest() != manifest.get("summary_sha256"):
        raise ValueError("prior second-valuation summary hash mismatch")
    result = summary.get("result", {})
    if result.get("m31_unresolved_classes") != EXPECTED_RESIDUALS or result.get("m31_residual_classes_examined") != EXPECTED_EXAMINED:
        raise ValueError("prior census population differs from the frozen count")
    if result.get("m31_saved_family_rows_matched") != EXPECTED_FAMILY_ROWS:
        raise ValueError("prior census family count differs from the frozen count")
    if result.get("first_odd_to_odd_valuation_histogram") != {"1": EXPECTED_RESIDUALS}:
        raise ValueError("prior first-valuation histogram differs from the frozen result")
    if result.get("second_odd_to_odd_valuation_histogram") != {"1": 19_495_091, "2": 4_146_987}:
        raise ValueError("prior second-valuation histogram differs from the frozen result")
    return manifest, summary, {
        "manifest": sha256_file(manifest_path),
        "summary": hashlib.sha256(summary_bytes).hexdigest(),
        "protocol": sha256_file(parent / "protocol.md"),
    }


def census(mask: bytearray, family_residues: Any, residual_stream: Any = None) -> dict[str, Any]:
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
    third_valuation_histogram = Counter()
    uniform_valuation_classes = 0
    not_uniformly_certified_classes = 0
    fixed_representative_descent = 0
    uniform_class_descent = 0
    direct_formula_checks = 0
    minimum_residue: int | None = None
    minimum_residue_by_a2 = {1: None, 2: None}
    residual_buffer = array("I")
    residual_hasher = hashlib.sha256()
    residual_index_records = 0

    if residual_stream is not None and residual_buffer.itemsize != 4:
        raise ValueError("the residual index requires four-byte unsigned integers")

    def flush_residual_buffer() -> None:
        nonlocal residual_buffer
        if not residual_buffer:
            return
        payload = residual_buffer.tobytes()
        if sys.byteorder != "little":
            block = array("I", residual_buffer)
            block.byteswap()
            payload = block.tobytes()
        residual_stream.write(payload)
        residual_hasher.update(payload)
        residual_buffer = array("I")

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
                if residue & 1 == 0:
                    raise ValueError("an unresolved M31 class is not odd")
                minimum_residue = residue if minimum_residue is None else min(minimum_residue, residue)
                n = residue + modulus
                a1 = valuation_two(3 * n + 1)
                first_valuation[str(a1)] += 1
                if a1 != 1:
                    raise ValueError("first valuation disagrees with the frozen previous census")
                a2 = valuation_two(3 * ((3 * n + 1) // 2) + 1)
                second_valuation[str(a2)] += 1
                if a2 not in (1, 2):
                    raise ValueError("second valuation disagrees with the frozen previous census")
                minimum_residue_by_a2[a2] = residue if minimum_residue_by_a2[a2] is None else min(minimum_residue_by_a2[a2], residue)
                a3 = third_valuation(n, a2)
                third_valuation_histogram[str(a3)] += 1
                cutoff = class_uniformity_cutoff(a2)
                uniform = a3 < cutoff
                t3_direct = third_odd_iterate(n, a2, a3)
                t3_formula = formula_third_odd_iterate(n, a2, a3)
                if t3_direct != t3_formula:
                    raise ValueError("direct third iterate disagrees with the registered affine formula")
                direct_formula_checks += 1
                if (t3_direct < n) != (a3 >= (3 if a2 == 1 else 2)):
                    raise ValueError("direct third-step descent disagrees with the registered threshold")
                if uniform:
                    uniform_valuation_classes += 1
                else:
                    not_uniformly_certified_classes += 1
                if t3_direct < n:
                    fixed_representative_descent += 1
                    if uniform and residue >= descent_minimum(a2):
                        uniform_class_descent += 1
                if residual_stream is not None:
                    residual_buffer.append(residue)
                    residual_index_records += 1
                    if len(residual_buffer) == 262_144:
                        flush_residual_buffer()
            residue_index = mask.find(b"\x00", residue_index + 1)

    if family_index != len(family_residues):
        raise ValueError("not all saved M31 family rows matched the M30-uncovered lifts")
    if examined != EXPECTED_EXAMINED or family_matches != EXPECTED_FAMILY_ROWS or unresolved != EXPECTED_RESIDUALS:
        raise ValueError("reconstructed population or family counts disagree with frozen bindings")
    if sum(first_valuation.values()) != unresolved or first_valuation != Counter({"1": EXPECTED_RESIDUALS}):
        raise ValueError("rechecked first-valuation histogram does not conserve the population")
    if second_valuation != Counter({"1": 19_495_091, "2": 4_146_987}):
        raise ValueError("rechecked second-valuation histogram differs from the frozen result")
    if sum(third_valuation_histogram.values()) != unresolved:
        raise ValueError("third-valuation histogram does not conserve the population")
    if uniform_valuation_classes + not_uniformly_certified_classes != unresolved:
        raise ValueError("third-valuation uniformity counts do not conserve the population")
    flush_residual_buffer()

    return {
        "base_modulus": base_modulus,
        "m31_modulus": modulus,
        "m31_residual_classes_examined": examined,
        "m31_saved_family_rows_matched": family_matches,
        "m31_unresolved_classes": unresolved,
        "residual_class_index": {
            "encoding": "sorted uint32 little-endian M31 residue IDs",
            "records": residual_index_records,
            "sha256": residual_hasher.hexdigest() if residual_stream is not None else None,
        },
        "representative_convention": "n = r + 2^31",
        "minimum_unresolved_residue": minimum_residue,
        "minimum_unresolved_residue_by_a2": {str(key): value for key, value in minimum_residue_by_a2.items()},
        "first_odd_to_odd_valuation_histogram": dict(sorted(first_valuation.items(), key=lambda pair: int(pair[0]))),
        "second_odd_to_odd_valuation_histogram": dict(sorted(second_valuation.items(), key=lambda pair: int(pair[0]))),
        "third_odd_to_odd_valuation_histogram": dict(sorted(third_valuation_histogram.items(), key=lambda pair: int(pair[0]))),
        "third_valuation_uniformity_by_congruence": {
            "a2_1_cutoff_exclusive": 29,
            "a2_2_cutoff_exclusive": 28,
            "classes_uniformly_certified": uniform_valuation_classes,
            "classes_not_certified_uniform_by_bound": not_uniformly_certified_classes,
        },
        "three_odd_step_descent": {
            "fixed_representatives_with_t3_below_n": fixed_representative_descent,
            "uniform_classes_with_t3_below_every_positive_member": uniform_class_descent,
            "direct_formula_checks": direct_formula_checks,
            "thresholds": {"a2_1_requires_a3_at_least": 3, "a2_2_requires_a3_at_least": 2},
        },
        "scope": "Exact finite census on the saved M31 residual classes and fixed representatives; no global Collatz or probability claim.",
    }


def run(repo: Path, output_dir: Path, protocol_path: Path) -> dict[str, Any]:
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = str((repo / "scripts").resolve())
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from sample_collatz_m31_unresolved_structure import MODULUS, _load_m31_family_residues, _load_verified_m31, sha256_bytearray
    import scan_collatz_m31_residual as scanner31

    if MODULUS != EXPECTED_MODULUS:
        raise ValueError("existing verified M31 loader has an unexpected modulus")
    parent_manifest, parent_summary, parent_hashes = load_parent(repo)
    m31_manifest, m31_validation, scan_path = _load_verified_m31(repo)
    mask, baseline = scanner31._covered_m30(repo)
    if baseline != m31_manifest.get("baseline"):
        raise ValueError("reconstructed M30 baseline differs from the M31 package")
    if sha256_bytearray(mask) != parent_manifest.get("m30_coverage_mask_sha256"):
        raise ValueError("reconstructed M30 coverage mask differs from the prior census")
    families, odd_family_count = _load_m31_family_residues(scan_path, EXPECTED_FAMILY_ROWS)
    if odd_family_count != EXPECTED_FAMILY_ROWS:
        raise ValueError("not every saved M31 family row is odd")

    print("[census] enumerating the frozen unresolved M31 class population", flush=True)
    residual_index_path = output_dir / "residual-classes.u32le"
    with residual_index_path.open("wb") as residual_stream:
        result = census(mask, families, residual_stream)
    if result["residual_class_index"]["records"] != EXPECTED_RESIDUALS:
        raise ValueError("written residual class index has the wrong number of records")
    if result["m31_unresolved_classes"] != m31_manifest["search"]["residual_after_search"]:
        raise ValueError("census count differs from the M31 package manifest")
    if result["m31_unresolved_classes"] != m31_validation["residual_after_search"]:
        raise ValueError("census count differs from independent M31 validation")
    if result["m31_unresolved_classes"] != parent_summary["result"]["m31_unresolved_classes"]:
        raise ValueError("census count differs from the prior exact residual census")

    summary = {
        "schema": "mathcase-collatz-m31-residual-third-valuation-summary-v1",
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
        "prior_census_protocol": repo / SECOND_RELATIVE / "protocol.md",
        "prior_census_manifest": repo / SECOND_RELATIVE / "run-1/run-manifest.json",
        "prior_census_summary": repo / SECOND_RELATIVE / "run-1/summary.json",
    }
    manifest = {
        "schema": "mathcase-collatz-m31-residual-third-valuation-manifest-v1",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS",
        "protocol_path": PROTOCOL_RELATIVE,
        "protocol_sha256": sha256_file(protocol_path),
        "audit_code_sha256": sha256_file(Path(__file__).resolve()),
        "verification_code_path": "scripts/verify_collatz_m31_residual_third_valuation.py",
        "verification_code_sha256": sha256_file(repo / "scripts/verify_collatz_m31_residual_third_valuation.py"),
        "test_code_path": "scripts/test_collatz_m31_residual_third_valuation.py",
        "test_code_sha256": sha256_file(repo / "scripts/test_collatz_m31_residual_third_valuation.py"),
        "residual_index_path": str(residual_index_path.relative_to(repo)).replace("\\", "/"),
        "residual_index_sha256": sha256_file(residual_index_path),
        "inputs": {name: {"path": str(path.relative_to(repo)).replace("\\", "/"), "sha256": sha256_file(path)} for name, path in input_paths.items()},
        "prior_census_binding": parent_hashes,
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
            "schema": "mathcase-collatz-m31-residual-third-valuation-failure-v1",
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "network_calls": 0,
            "provider_calls": 0,
            "gpu_used": False,
        }
        failure_path = output / "failure-receipt.json"
        if not failure_path.exists():
            failure_path.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    result = summary["result"]
    print(json.dumps({
        "status": "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS",
        "population": result["m31_unresolved_classes"],
        "third_valuation_histogram": result["third_odd_to_odd_valuation_histogram"],
        "fixed_representative_descent": result["three_odd_step_descent"]["fixed_representatives_with_t3_below_n"],
        "uniform_class_descent": result["three_odd_step_descent"]["uniform_classes_with_t3_below_every_positive_member"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
