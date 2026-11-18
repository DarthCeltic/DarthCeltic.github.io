#!/usr/bin/env python3
"""Derive a sharp affine lower bound from the checked M31 three-step strata."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
MODULUS = 1 << 31
PROTOCOL = Path("research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/protocol.md")
DERIVER = Path("scripts/derive_collatz_m31_three_step_affine_lower_bound_v1.py")
VERIFIER = Path("scripts/verify_collatz_m31_three_step_affine_lower_bound_v1.py")
TESTS = Path("scripts/test_collatz_m31_three_step_affine_lower_bound_v1.py")
EXPECTED = {
    (1, 1): (15_348_104, 27, 19, 8),
    (1, 2): (4_146_987, 27, 19, 16),
    (2, 1): (4_146_987, 27, 23, 16),
    (2, 2): (0, 27, 23, 32),
}
FORMULA_RE = re.compile(r"^\((\d+)\*n \+ (\d+)\)/(\d+)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_file(repo: Path, relative: str | Path) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe repository-relative input: {relative}")
    path = (repo / rel).resolve()
    path.relative_to(repo.resolve())
    if not path.is_file():
        raise ValueError(f"required input is missing or not a file: {relative}")
    return path


def load_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return raw, value


def register(repo: Path, inputs: dict[str, str], relative: str | Path) -> str:
    rel = Path(relative).as_posix()
    digest = sha256_file(repo_file(repo, rel))
    prior = inputs.setdefault(rel, digest)
    if prior != digest:
        raise ValueError(f"input changed while deriving: {rel}")
    return digest


def fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def affine_margin(slope: int, constant: int, denominator: int) -> tuple[Fraction, Fraction]:
    """Return exact coefficients for 16*T^3(n)-27*n from T^3=(s*n+c)/d."""
    if denominator <= 0:
        raise ValueError("affine denominator must be positive")
    return Fraction(16 * slope, denominator) - 27, Fraction(16 * constant, denominator)


def validate_parent(repo: Path, inputs: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol_rel = PARENT_DIR / "protocol.md"
    summary_rel = PARENT_RUN / "summary.json"
    manifest_rel = PARENT_RUN / "run-manifest.json"
    verification_rel = PARENT_RUN / "verification-receipt.json"
    protocol_hash = register(repo, inputs, protocol_rel)
    summary_raw, summary = load_json(repo_file(repo, summary_rel))
    manifest_raw, manifest = load_json(repo_file(repo, manifest_rel))
    verification_raw, verification = load_json(repo_file(repo, verification_rel))
    summary_hash = hashlib.sha256(summary_raw).hexdigest()
    manifest_hash = hashlib.sha256(manifest_raw).hexdigest()
    verification_hash = hashlib.sha256(verification_raw).hexdigest()
    if summary_hash != PARENT_SUMMARY_SHA256 or manifest_hash != PARENT_RUN_MANIFEST_SHA256 or verification_hash != PARENT_VERIFICATION_SHA256:
        raise ValueError("pinned parent summary, run manifest, or independent receipt changed")
    if summary.get("schema") != "mathcase-collatz-m31-first-three-above-start-summary-v1" or summary.get("status") != "PASS_DERIVED_FINITE_ABOVE_START":
        raise ValueError("parent summary is not the expected passed finite result")
    if summary.get("population") != POPULATION or summary.get("modulus") != MODULUS:
        raise ValueError("parent population or modulus differs from the pinned M31 set")
    if not summary.get("result", {}).get("every_saved_class_member_has_T1_T2_and_T3_strictly_above_original_n"):
        raise ValueError("parent does not certify all three affine steps above the original value")
    if manifest.get("summary_sha256") != summary_hash or manifest.get("protocol_sha256") != protocol_hash:
        raise ValueError("parent run manifest does not bind the protocol and summary")
    if manifest.get("schema") != "mathcase-collatz-m31-first-three-above-start-manifest-v1" or manifest.get("status") != "PASS_DERIVED_FINITE_ABOVE_START" or manifest.get("trajectory_rescan_performed") is not False:
        raise ValueError("parent manifest status or trajectory-rescan boundary changed")
    if verification.get("status") != "PASS_INDEPENDENT_DERIVATION_AND_BINDING_CHECK":
        raise ValueError("parent independent verification did not pass")
    if verification.get("summary_sha256") != summary_hash or verification.get("run_manifest_sha256") != manifest_hash:
        raise ValueError("parent independent receipt is not bound to its summary and manifest")
    if verification.get("trajectory_rescan_performed") is not False or verification.get("population_conserved") != POPULATION:
        raise ValueError("parent verifier receipt does not preserve the bounded scope")
    parent_inputs = manifest.get("input_sha256")
    if not isinstance(parent_inputs, dict) or len(parent_inputs) != verification.get("inputs_rehashed"):
        raise ValueError("parent input map does not match its independent rehash count")
    for rel, expected_hash in sorted(parent_inputs.items()):
        if register(repo, inputs, rel) != expected_hash:
            raise ValueError(f"parent source input hash mismatch: {rel}")
    for rel in (protocol_rel, summary_rel, manifest_rel, verification_rel):
        register(repo, inputs, rel)
    parent_source_bindings = (
        (manifest.get("protocol_path"), manifest.get("protocol_sha256")),
        (manifest.get("derivation_script_path"), manifest.get("derivation_script_sha256")),
        (manifest.get("verification_script_path"), manifest.get("verification_script_sha256")),
    )
    expected_parent_paths = (
        protocol_rel.as_posix(),
        "scripts/derive_collatz_m31_first_three_above_start_v1.py",
        "scripts/verify_collatz_m31_first_three_above_start_v1.py",
    )
    for (rel, expected_hash), pinned_path in zip(parent_source_bindings, expected_parent_paths, strict=True):
        if rel != pinned_path or not isinstance(expected_hash, str):
            raise ValueError("parent manifest source path/hash binding is missing or unexpected")
        actual_hash = register(repo, inputs, rel)
        if actual_hash != expected_hash:
            raise ValueError(f"parent manifest source hash does not match its bytes: {rel}")
    return summary, manifest


def derive(summary: dict[str, Any]) -> dict[str, Any]:
    rows = summary.get("result", {}).get("third_step_strata")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError("parent is missing the four exact third-step strata")
    seen: set[tuple[int, int]] = set()
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (row.get("a2"), row.get("a3"))
        if key not in EXPECTED or key in seen:
            raise ValueError(f"unexpected or duplicate valuation stratum: {key}")
        seen.add(key)
        expected_count, expected_slope, expected_constant, expected_denominator = EXPECTED[key]
        match = FORMULA_RE.fullmatch(row.get("t3_formula", ""))
        if not match:
            raise ValueError(f"unparseable parent affine formula for {key}")
        slope, constant, denominator = map(int, match.groups())
        if (row.get("class_count"), slope, constant, denominator) != (expected_count, expected_slope, expected_constant, expected_denominator):
            raise ValueError(f"parent stratum differs from its pinned formula/count: {key}")
        item: dict[str, Any] = {
            "a2": key[0], "a3": key[1], "class_count": expected_count,
            "t3_formula": row["t3_formula"], "claim_applies": expected_count > 0,
        }
        if expected_count:
            margin_slope, margin_constant = affine_margin(slope, constant, denominator)
            gap_slope = margin_slope
            gap_constant = margin_constant - 19
            if gap_slope < 0 or gap_slope + gap_constant < 0:
                raise ValueError(f"the claimed margin is not nonnegative for all n>=1 in stratum {key}")
            item["exact_margin_expression"] = f"{fraction_text(margin_slope)}*n + {fraction_text(margin_constant)}"
            item["margin_at_least_19"] = True
            item["equality_for_every_positive_n"] = gap_slope == 0 and gap_constant == 0
        else:
            item["exact_margin_expression"] = None
            item["margin_at_least_19"] = None
            item["equality_for_every_positive_n"] = False
            item["empty_stratum_no_claim"] = True
        output_rows.append(item)
    if seen != set(EXPECTED):
        raise ValueError("parent third-step strata are incomplete")
    if sum(row["class_count"] for row in output_rows) != POPULATION:
        raise ValueError("third-step strata do not conserve the frozen population")
    bound_classes = sum(row["class_count"] for row in output_rows if row["claim_applies"])
    equality_rows = [row for row in output_rows if row["equality_for_every_positive_n"]]
    if bound_classes != POPULATION or sum(row["class_count"] for row in equality_rows) != 4_146_987:
        raise ValueError("bound population or sharpness count differs from the pinned strata")
    return {
        "schema": SCHEMA,
        "classification": "DERIVED_EXACT_FINITE_AFFINE_COROLLARY",
        "status": "PASS_DERIVED_FINITE_AFFINE_LOWER_BOUND",
        "population": POPULATION,
        "modulus": MODULUS,
        "class_member_convention": summary["class_member_convention"],
        "map": "T(x)=(3*x+1)/2^v2(3*x+1), accelerated odd-to-odd Collatz map",
        "result": {
            "exact_inequality": "16*T^3(n) - 27*n >= 19",
            "equivalent_lower_bound": "T^3(n) >= (27*n + 19)/16",
            "plain_language": "After three accelerated odd-to-odd steps, each positive member is more than 27/16 of its starting value, with a uniform additive margin of at least 19/16.",
            "bound_holds_for_all_positive_members_of_saved_classes": bound_classes == POPULATION,
            "sharp": True,
            "equality_strata": [{"a2": 1, "a3": 2, "class_count": 4_146_987}],
            "strata": output_rows,
            "empty_stratum": {"a2": 2, "a3": 2, "class_count": 0, "claim": "NONE"},
        },
        "parent_result": {
            "summary_sha256": PARENT_SUMMARY_SHA256,
            "run_manifest_sha256": PARENT_RUN_MANIFEST_SHA256,
            "verification_receipt_sha256": PARENT_VERIFICATION_SHA256,
            "independent_parent_status": "PASS_INDEPENDENT_DERIVATION_AND_BINDING_CHECK",
            "parent_inputs_rehashed": 21,
        },
        "limits": [
            "Finite affine consequence only for the 23,642,078 pinned odd residue classes modulo 2^31.",
            "No claim for other residues or all odd integers.",
            "No step-four decrease is established; no later descent or convergence claim follows.",
            "No Lean proof, M0/M4 evidence, novelty claim, or independent mathematical review is claimed.",
            "No trajectory rescan is performed; only the verified summary formulas and parent bindings are used.",
        ],
        "external_calls": 0,
        "cost_usd": 0,
        "lean_compiled": False,
        "m0_or_m4_promoted": False,
        "trajectory_rescan_performed": False,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def execute(repo: Path, output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    inputs: dict[str, str] = {}
    try:
        summary, parent_manifest = validate_parent(repo.resolve(), inputs)
        for rel in (PROTOCOL, DERIVER, VERIFIER, TESTS):
            register(repo.resolve(), inputs, rel)
        result = derive(summary)
        summary_path = output / "summary.json"
        write_json(summary_path, result)
        summary_hash = sha256_file(summary_path)
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "status": result["status"],
            "created_utc": started.isoformat(),
            "source_git_head": "d1649d3ca9cea5de4d5b5de33a2f0942c75fff4c",
            "source_worktree_state": "UNCOMMITTED_SOURCE_HASHES_BOUND",
            "protocol_path": PROTOCOL.as_posix(),
            "protocol_sha256": inputs[PROTOCOL.as_posix()],
            "derivation_script_path": DERIVER.as_posix(),
            "derivation_script_sha256": inputs[DERIVER.as_posix()],
            "verification_script_path": VERIFIER.as_posix(),
            "verification_script_sha256": inputs[VERIFIER.as_posix()],
            "test_script_path": TESTS.as_posix(),
            "test_script_sha256": inputs[TESTS.as_posix()],
            "summary_sha256": summary_hash,
            "parent_input_count": len(parent_manifest["input_sha256"]),
            "input_sha256": dict(sorted(inputs.items())),
            "external_calls": 0,
            "cost_usd": 0,
            "lean_compiled": False,
            "m0_or_m4_promoted": False,
            "trajectory_rescan_performed": False,
        }
        write_json(output / "run-manifest.json", manifest)
        return {"status": "PASS_DERIVED_FINITE_AFFINE_LOWER_BOUND", "summary_sha256": summary_hash, "input_count": len(inputs)}
    except Exception as exc:
        failure = {
            "schema": "mathcase-collatz-m31-three-step-affine-lower-bound-failure-v1",
            "status": "FAIL_PRESERVED",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "input_sha256": dict(sorted(inputs.items())),
            "trajectory_rescan_performed": False,
            "external_calls": 0,
            "cost_usd": 0,
        }
        write_json(output / "failure-receipt.json", failure)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(execute(args.repo_root, args.output_dir), sort_keys=True))
        return 0
    except Exception as exc:
        print(f"derive failed; preserved failure receipt if output directory was created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
