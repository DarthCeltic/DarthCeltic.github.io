#!/usr/bin/env python3
"""Independent direct-trajectory verification for the M31 third-valuation census."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


RELATIVE_PROTOCOL = "research/collatz/structure-sample/m31-residual-third-valuation-v1/protocol.md"
RELATIVE_RUN = "research/collatz/structure-sample/m31-residual-third-valuation-v1/run-1"
MODULUS = 1 << 31
EXPECTED_EXAMINED = 25_542_548
EXPECTED_FAMILY_ROWS = 1_900_470
EXPECTED_RESIDUALS = 23_642_078


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def odd_step(n: int) -> tuple[int, int]:
    if n <= 0 or n & 1 == 0:
        raise ValueError("direct odd-step input must be a positive odd integer")
    value = 3 * n + 1
    valuation = (value & -value).bit_length() - 1
    return value >> valuation, valuation


def expected_residuals(mask: bytearray, family_set: set[int], stats: dict[str, int]) -> Iterator[int]:
    half = len(mask)
    if half * 2 != MODULUS:
        raise ValueError("M30 mask has the wrong size")
    for lift in (0, 1):
        offset = lift * half
        index = mask.find(b"\x00", 0)
        while index >= 0:
            residue = index + offset
            stats["examined"] += 1
            if residue in family_set:
                stats["family_matches"] += 1
            else:
                stats["residuals"] += 1
                yield residue
            index = mask.find(b"\x00", index + 1)


def compare_histogram(actual: Counter[int], recorded: Any, label: str) -> None:
    expected = {str(key): value for key, value in sorted(actual.items())}
    if recorded != expected:
        raise ValueError(f"{label} differs from the independently recomputed histogram")


def verify(repo: Path, run_dir: Path) -> dict[str, Any]:
    if (run_dir / "verification-receipt.json").exists() or (run_dir / "verification-failure-receipt.json").exists():
        raise ValueError("verification output already exists; this version permits one verification attempt")
    if (run_dir / "failure-receipt.json").exists():
        raise ValueError("primary run has a failure receipt; do not verify or retry a failed run")

    manifest_path = run_dir / "run-manifest.json"
    summary_path = run_dir / "summary.json"
    residual_path = run_dir / "residual-classes.u32le"
    protocol_path = repo / RELATIVE_PROTOCOL
    manifest_bytes = manifest_path.read_bytes()
    summary_bytes = summary_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    summary = json.loads(summary_bytes)

    if manifest.get("status") != "PASS_EXACT_FINITE_RESIDUAL_CLASS_CENSUS":
        raise ValueError("primary run did not record the exact finite census pass")
    if hashlib.sha256(summary_bytes).hexdigest() != manifest.get("summary_sha256"):
        raise ValueError("primary summary hash mismatch")
    if sha256_file(protocol_path) != manifest.get("protocol_sha256"):
        raise ValueError("protocol hash mismatch")
    if sha256_file(repo / "scripts/audit_collatz_m31_residual_third_valuation.py") != manifest.get("audit_code_sha256"):
        raise ValueError("primary audit source hash mismatch")
    if sha256_file(Path(__file__).resolve()) != manifest.get("verification_code_sha256"):
        raise ValueError("independent verifier source hash mismatch")
    if sha256_file(repo / "scripts/test_collatz_m31_residual_third_valuation.py") != manifest.get("test_code_sha256"):
        raise ValueError("focused test source hash mismatch")
    for binding in manifest.get("inputs", {}).values():
        path = repo / binding["path"]
        if sha256_file(path) != binding["sha256"]:
            raise ValueError(f"bound input changed: {binding['path']}")
    if sha256_file(residual_path) != manifest.get("residual_index_sha256"):
        raise ValueError("residual class index hash mismatch")

    scripts_dir = str((repo / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from sample_collatz_m31_unresolved_structure import _load_m31_family_residues, _load_verified_m31, sha256_bytearray
    import scan_collatz_m31_residual as scanner31

    m31_manifest, m31_validation, scan_path = _load_verified_m31(repo)
    family_rows, odd_family_count = _load_m31_family_residues(scan_path, EXPECTED_FAMILY_ROWS)
    if odd_family_count != EXPECTED_FAMILY_ROWS:
        raise ValueError("saved M31 family rows failed their count or parity binding")
    family_set = set(family_rows)
    if len(family_set) != EXPECTED_FAMILY_ROWS:
        raise ValueError("saved M31 family residue set contains duplicates")

    mask, baseline = scanner31._covered_m30(repo)
    if baseline != manifest.get("m30_baseline_binding"):
        raise ValueError("M30 baseline differs from the primary run binding")
    if sha256_bytearray(mask) != manifest.get("m30_coverage_mask_sha256"):
        raise ValueError("M30 coverage mask differs from the primary run binding")
    if manifest.get("m31_family_rows") != len(family_rows):
        raise ValueError("M31 family count differs from the primary run binding")

    stats = {"examined": 0, "family_matches": 0, "residuals": 0}
    expected_iter = expected_residuals(mask, family_set, stats)
    result = summary.get("result", {})
    first_hist: Counter[int] = Counter()
    second_hist: Counter[int] = Counter()
    third_hist: Counter[int] = Counter()
    minima: dict[int, int | None] = {1: None, 2: None}
    uniform_count = 0
    uncertified_count = 0
    representative_descent = 0
    uniform_descent = 0
    direct_formula_checks = 0
    read_records = 0

    with residual_path.open("rb") as stream:
        while True:
            block = stream.read(4 * 65_536)
            if not block:
                break
            if len(block) % 4:
                raise ValueError("residual class index ends in a partial uint32 record")
            for start in range(0, len(block), 4):
                residue = int.from_bytes(block[start : start + 4], "little")
                expected = next(expected_iter, None)
                if expected is None or expected != residue:
                    raise ValueError(f"residual index differs from independent set reconstruction at row {read_records}")
                if residue >= MODULUS or residue & 1 == 0:
                    raise ValueError(f"residual index contains a non-odd or out-of-range residue at row {read_records}")

                representative = residue + MODULUS
                t1, a1 = odd_step(representative)
                t2, a2 = odd_step(t1)
                t3, a3 = odd_step(t2)
                if a1 != 1 or a2 not in (1, 2):
                    raise ValueError(f"frozen first/second valuation binding failed at row {read_records}")
                first_hist[a1] += 1
                second_hist[a2] += 1
                third_hist[a3] += 1
                minima[a2] = residue if minima[a2] is None else min(minima[a2], residue)

                if a2 == 1:
                    formula = (27 * representative + 19) // (1 << (a3 + 2))
                    cutoff = 29
                    threshold = 3
                    least_member_threshold = 4
                else:
                    formula = (27 * representative + 23) // (1 << (a3 + 3))
                    cutoff = 28
                    threshold = 2
                    least_member_threshold = 5
                if formula != t3:
                    raise ValueError(f"direct third iterate disagrees with the affine formula at row {read_records}")
                direct_formula_checks += 1
                if (t3 < representative) != (a3 >= threshold):
                    raise ValueError(f"direct descent disagrees with threshold at row {read_records}")
                uniform = a3 < cutoff
                if uniform:
                    uniform_count += 1
                else:
                    uncertified_count += 1
                if t3 < representative:
                    representative_descent += 1
                    if uniform and residue >= least_member_threshold:
                        uniform_descent += 1
                read_records += 1

    if next(expected_iter, None) is not None:
        raise ValueError("residual class index omitted one or more expected residual classes")

    if stats != {"examined": EXPECTED_EXAMINED, "family_matches": EXPECTED_FAMILY_ROWS, "residuals": EXPECTED_RESIDUALS}:
        raise ValueError("independent population reconstruction has unexpected counts")
    if read_records != EXPECTED_RESIDUALS:
        raise ValueError("residual class index has an unexpected record count")
    if result.get("m31_residual_classes_examined") != stats["examined"]:
        raise ValueError("primary examined-count result differs from independent reconstruction")
    if result.get("m31_saved_family_rows_matched") != stats["family_matches"]:
        raise ValueError("primary matched-family result differs from independent reconstruction")
    if result.get("m31_unresolved_classes") != stats["residuals"]:
        raise ValueError("primary unresolved count differs from independent reconstruction")
    if summary.get("result", {}).get("residual_class_index", {}).get("records") != read_records:
        raise ValueError("summary residual index record count mismatch")
    if summary["result"]["residual_class_index"].get("sha256") != sha256_file(residual_path):
        raise ValueError("summary residual index digest mismatch")

    compare_histogram(first_hist, result.get("first_odd_to_odd_valuation_histogram"), "first valuation")
    compare_histogram(second_hist, result.get("second_odd_to_odd_valuation_histogram"), "second valuation")
    compare_histogram(third_hist, result.get("third_odd_to_odd_valuation_histogram"), "third valuation")
    if result.get("minimum_unresolved_residue") != min(value for value in minima.values() if value is not None):
        raise ValueError("primary minimum unresolved residue differs from independent result")
    if result.get("minimum_unresolved_residue_by_a2") != {str(key): value for key, value in minima.items()}:
        raise ValueError("primary minimum residues by a2 differ from independent result")
    if result.get("third_valuation_uniformity_by_congruence", {}).get("classes_uniformly_certified") != uniform_count:
        raise ValueError("primary uniformity count differs from independent result")
    if result.get("third_valuation_uniformity_by_congruence", {}).get("classes_not_certified_uniform_by_bound") != uncertified_count:
        raise ValueError("primary non-uniformly-certified count differs from independent result")
    descent_result = result.get("three_odd_step_descent", {})
    if descent_result.get("fixed_representatives_with_t3_below_n") != representative_descent:
        raise ValueError("primary fixed-representative descent count differs from independent result")
    if descent_result.get("uniform_classes_with_t3_below_every_positive_member") != uniform_descent:
        raise ValueError("primary uniform-class descent count differs from independent result")
    if descent_result.get("direct_formula_checks") != direct_formula_checks:
        raise ValueError("primary direct/formula count differs from independent result")
    if m31_manifest.get("search", {}).get("residual_after_search") != stats["residuals"] or m31_validation.get("residual_after_search") != stats["residuals"]:
        raise ValueError("M31 package checks do not agree with the independent residual population")

    receipt = {
        "schema": "mathcase-collatz-m31-residual-third-valuation-verification-v1",
        "status": "PASS_INDEPENDENT_DIRECT_TRAJECTORY_AND_POPULATION_CHECK",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "protocol_path": RELATIVE_PROTOCOL,
        "protocol_sha256": sha256_file(protocol_path),
        "verification_code_path": str(Path(__file__).resolve().relative_to(repo)).replace("\\", "/"),
        "verification_code_sha256": sha256_file(Path(__file__).resolve()),
        "primary_audit_code_sha256": manifest["audit_code_sha256"],
        "test_code_sha256": manifest["test_code_sha256"],
        "run_manifest_sha256": sha256_file(manifest_path),
        "summary_sha256": sha256_file(summary_path),
        "residual_index_sha256": sha256_file(residual_path),
        "independent_population": stats,
        "independent_third_valuation_histogram": {str(key): value for key, value in sorted(third_hist.items())},
        "direct_trajectory_records_checked": read_records,
        "provider_calls": 0,
        "network_calls": 0,
        "gpu_used": False,
        "docker_used": False,
        "lean_compiled": False,
        "global_collatz_proof": False,
    }
    receipt_path = run_dir / "verification-receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    run_dir = (args.run_dir or repo / RELATIVE_RUN).resolve()
    try:
        receipt = verify(repo, run_dir)
    except Exception as exc:
        failure = {
            "schema": "mathcase-collatz-m31-residual-third-valuation-verification-failure-v1",
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "provider_calls": 0,
            "network_calls": 0,
        }
        failure_path = run_dir / "verification-failure-receipt.json"
        if run_dir.is_dir() and not failure_path.exists() and not (run_dir / "verification-receipt.json").exists():
            failure_path.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({"status": receipt["status"], "records": receipt["direct_trajectory_records_checked"], "third_valuation_histogram": receipt["independent_third_valuation_histogram"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
