#!/usr/bin/env python3
"""Independently verify the M31 three-step affine lower-bound package."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

SCHEMA = "mathcase-collatz-m31-three-step-affine-lower-bound-summary-v1"
MANIFEST_SCHEMA = "mathcase-collatz-m31-three-step-affine-lower-bound-manifest-v1"
PARENT_DIR = Path("research/collatz/structure-sample/m31-first-three-above-start-v1")
PARENT_RUN = PARENT_DIR / "run-1"
PARENT_SUMMARY_SHA256 = "074dc937cee95da535bf372d3f5cb1b35e7be2e372ebb3f88da5d55308f32a84"
PARENT_RUN_MANIFEST_SHA256 = "a894f9ec6f2ba8ade337973ed593093bbc7671b6267911a1baffc628e374d6d3"
PARENT_VERIFICATION_SHA256 = "4ea8c1526945e6a3145eb8ef43bdffb591c9a97d90bfa6d909c0b91ae5bd6144"
POPULATION = 23_642_078
EXPECTED = {
    (1, 1): (15_348_104, 27, 19, 8),
    (1, 2): (4_146_987, 27, 19, 16),
    (2, 1): (4_146_987, 27, 23, 16),
    (2, 2): (0, 27, 23, 32),
}
PROTOCOL = Path("research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/protocol.md")
DERIVER = Path("scripts/derive_collatz_m31_three_step_affine_lower_bound_v1.py")
VERIFIER = Path("scripts/verify_collatz_m31_three_step_affine_lower_bound_v1.py")
TESTS = Path("scripts/test_collatz_m31_three_step_affine_lower_bound_v1.py")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return raw, value


def safe_repo_file(repo: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe input path in manifest: {relative}")
    path = (repo / rel).resolve()
    path.relative_to(repo.resolve())
    if not path.is_file():
        raise ValueError(f"input missing or not a regular file: {relative}")
    return path


def fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def expected_margin(slope: int, constant: int, denominator: int) -> tuple[Fraction, Fraction]:
    return Fraction(16 * slope, denominator) - 27, Fraction(16 * constant, denominator)


def verify(repo: Path, output: Path) -> dict[str, Any]:
    repo = repo.resolve()
    output = output.resolve()
    summary_raw, summary = read_json(output / "summary.json")
    manifest_raw, manifest = read_json(output / "run-manifest.json")
    summary_hash = hashlib.sha256(summary_raw).hexdigest()
    manifest_hash = hashlib.sha256(manifest_raw).hexdigest()
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("status") != "PASS_DERIVED_FINITE_AFFINE_LOWER_BOUND":
        raise ValueError("run manifest schema/status mismatch")
    if manifest.get("source_git_head") != "d1649d3ca9cea5de4d5b5de33a2f0942c75fff4c" or manifest.get("source_worktree_state") != "UNCOMMITTED_SOURCE_HASHES_BOUND":
        raise ValueError("run manifest source revision/worktree disclosure differs")
    if manifest.get("summary_sha256") != summary_hash:
        raise ValueError("run manifest does not bind summary bytes")
    for rel, field in ((PROTOCOL, "protocol_sha256"), (DERIVER, "derivation_script_sha256"), (VERIFIER, "verification_script_sha256"), (TESTS, "test_script_sha256")):
        actual = sha256_file(safe_repo_file(repo, rel.as_posix()))
        if manifest.get(field) != actual:
            raise ValueError(f"run manifest does not bind current {rel.as_posix()}")
    inputs = manifest.get("input_sha256")
    if not isinstance(inputs, dict):
        raise ValueError("run manifest input map is missing")
    for rel, expected_hash in sorted(inputs.items()):
        if sha256_file(safe_repo_file(repo, rel)) != expected_hash:
            raise ValueError(f"bound input hash mismatch: {rel}")

    parent_summary_raw, parent_summary = read_json(safe_repo_file(repo, PARENT_RUN / "summary.json"))
    parent_manifest_raw, parent_manifest = read_json(safe_repo_file(repo, PARENT_RUN / "run-manifest.json"))
    parent_verification_raw, parent_verification = read_json(safe_repo_file(repo, PARENT_RUN / "verification-receipt.json"))
    parent_summary_hash = hashlib.sha256(parent_summary_raw).hexdigest()
    parent_manifest_hash = hashlib.sha256(parent_manifest_raw).hexdigest()
    parent_verification_hash = hashlib.sha256(parent_verification_raw).hexdigest()
    if (parent_summary_hash, parent_manifest_hash, parent_verification_hash) != (PARENT_SUMMARY_SHA256, PARENT_RUN_MANIFEST_SHA256, PARENT_VERIFICATION_SHA256):
        raise ValueError("pinned parent result bytes differ")
    if parent_verification.get("status") != "PASS_INDEPENDENT_DERIVATION_AND_BINDING_CHECK" or parent_verification.get("summary_sha256") != parent_summary_hash or parent_verification.get("run_manifest_sha256") != parent_manifest_hash:
        raise ValueError("pinned parent independent receipt is absent or unbound")
    if parent_manifest.get("schema") != "mathcase-collatz-m31-first-three-above-start-manifest-v1" or parent_manifest.get("status") != "PASS_DERIVED_FINITE_ABOVE_START" or parent_manifest.get("summary_sha256") != parent_summary_hash or parent_manifest.get("trajectory_rescan_performed") is not False:
        raise ValueError("pinned parent manifest binding or scope differs")
    parent_inputs = parent_manifest.get("input_sha256")
    if not isinstance(parent_inputs, dict) or len(parent_inputs) != parent_verification.get("inputs_rehashed"):
        raise ValueError("parent input map/recheck count mismatch")
    parent_source_bindings = (
        ("protocol_path", "protocol_sha256", "research/collatz/structure-sample/m31-first-three-above-start-v1/protocol.md"),
        ("derivation_script_path", "derivation_script_sha256", "scripts/derive_collatz_m31_first_three_above_start_v1.py"),
        ("verification_script_path", "verification_script_sha256", "scripts/verify_collatz_m31_first_three_above_start_v1.py"),
    )
    for path_field, hash_field, pinned_path in parent_source_bindings:
        rel = parent_manifest.get(path_field)
        expected_hash = parent_manifest.get(hash_field)
        if rel != pinned_path or not isinstance(expected_hash, str):
            raise ValueError("parent manifest source path/hash binding is missing or unexpected")
        actual_hash = sha256_file(safe_repo_file(repo, rel))
        if actual_hash != expected_hash or inputs.get(rel) != expected_hash:
            raise ValueError(f"parent manifest source hash does not match its bytes: {rel}")
    for rel, expected_hash in parent_inputs.items():
        if inputs.get(rel) != expected_hash:
            raise ValueError(f"child manifest omits or changes parent input binding: {rel}")
    if manifest.get("parent_input_count") != len(parent_inputs):
        raise ValueError("child manifest parent input count mismatch")

    if summary.get("schema") != SCHEMA or summary.get("status") != "PASS_DERIVED_FINITE_AFFINE_LOWER_BOUND":
        raise ValueError("derived summary schema/status mismatch")
    if summary.get("population") != POPULATION or summary.get("modulus") != 1 << 31:
        raise ValueError("derived scope population or modulus mismatch")
    if summary.get("class_member_convention") != parent_summary.get("class_member_convention"):
        raise ValueError("derived class-member convention differs from checked parent")
    result = summary.get("result", {})
    if result.get("exact_inequality") != "16*T^3(n) - 27*n >= 19" or result.get("equivalent_lower_bound") != "T^3(n) >= (27*n + 19)/16":
        raise ValueError("derived inequality text differs")
    if result.get("bound_holds_for_all_positive_members_of_saved_classes") is not True or result.get("sharp") is not True:
        raise ValueError("summary overstates or omits the finite bound")

    parent_rows = parent_summary.get("result", {}).get("third_step_strata", [])
    output_rows = result.get("strata", [])
    if len(parent_rows) != len(EXPECTED) or len(output_rows) != len(EXPECTED):
        raise ValueError("expected four parent and derived strata")
    seen: set[tuple[int, int]] = set()
    sharp_count = 0
    class_total = 0
    for parent_row, output_row in zip(parent_rows, output_rows, strict=True):
        key = (parent_row.get("a2"), parent_row.get("a3"))
        if key not in EXPECTED or key in seen:
            raise ValueError(f"duplicate or unknown stratum: {key}")
        seen.add(key)
        count, slope, constant, denominator = EXPECTED[key]
        if (parent_row.get("class_count"), parent_row.get("t3_formula")) != (count, f"({slope}*n + {constant})/{denominator}"):
            raise ValueError(f"parent formula/count differs in stratum {key}")
        if (output_row.get("a2"), output_row.get("a3"), output_row.get("class_count"), output_row.get("t3_formula"), output_row.get("claim_applies")) != (key[0], key[1], count, parent_row["t3_formula"], count > 0):
            raise ValueError(f"derived row binding differs in stratum {key}")
        class_total += count
        if count == 0:
            if output_row.get("margin_at_least_19") is not None or output_row.get("empty_stratum_no_claim") is not True:
                raise ValueError("empty stratum improperly receives a population claim")
            continue
        margin_slope, margin_constant = expected_margin(slope, constant, denominator)
        if margin_slope < 0 or margin_slope + margin_constant < 19:
            raise ValueError(f"affine margin fails for some positive n in stratum {key}")
        expression = f"{fraction_text(margin_slope)}*n + {fraction_text(margin_constant)}"
        equality = margin_slope == 0 and margin_constant == 19
        if output_row.get("exact_margin_expression") != expression or output_row.get("margin_at_least_19") is not True or output_row.get("equality_for_every_positive_n") is not equality:
            raise ValueError(f"derived exact margin or sharpness differs in stratum {key}")
        if equality:
            sharp_count += count
    if seen != set(EXPECTED) or class_total != POPULATION or sharp_count != 4_146_987:
        raise ValueError("strata population or sharpness count is not conserved")
    if summary.get("trajectory_rescan_performed") is not False or summary.get("lean_compiled") is not False or summary.get("m0_or_m4_promoted") is not False:
        raise ValueError("derived run claims a forbidden execution or gate change")
    if manifest.get("trajectory_rescan_performed") is not False or manifest.get("lean_compiled") is not False or manifest.get("m0_or_m4_promoted") is not False:
        raise ValueError("run manifest claims a forbidden execution or gate change")

    receipt = {
        "schema": "mathcase-collatz-m31-three-step-affine-lower-bound-verification-v1",
        "status": "PASS_INDEPENDENT_AFFINE_BOUND_AND_BINDING_CHECK",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "summary_sha256": summary_hash,
        "run_manifest_sha256": manifest_hash,
        "verification_script_path": VERIFIER.as_posix(),
        "verification_script_sha256": sha256_file(safe_repo_file(repo, VERIFIER.as_posix())),
        "input_files_rehashed": len(inputs),
        "parent_inputs_rehashed": len(parent_inputs),
        "strata_checked": len(seen),
        "population_conserved": class_total,
        "classes_satisfying_bound": POPULATION,
        "sharp_equality_classes": sharp_count,
        "trajectory_rescan_performed": False,
        "lean_compiled": False,
        "m0_or_m4_promoted": False,
        "external_calls": 0,
        "cost_usd": 0,
    }
    (output / "verification-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = verify(args.repo_root, args.output_dir)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except Exception as exc:
        failure = {
            "schema": "mathcase-collatz-m31-three-step-affine-lower-bound-verification-failure-v1",
            "status": "FAIL_PRESERVED",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "external_calls": 0,
            "cost_usd": 0,
        }
        output = args.output_dir.resolve()
        if output.is_dir() and not (output / "verification-receipt.json").exists():
            (output / "verification-failure-receipt.json").write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"verification failed; preserved failure receipt if output directory was available: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
