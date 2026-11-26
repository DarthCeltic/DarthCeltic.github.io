#!/usr/bin/env python3
"""Build a hash-bound exact affine-family index from saved Collatz packages."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


BASE = "research/collatz"
OUTPUT = "research/collatz/m15-m20-affine-basis-v1/run-5"
PROTOCOL = "research/collatz/m15-m20-affine-basis-v1/protocol.md"
M13_LEAN = "research/collatz/m15/lean/BoundedDescentPlusM13.lean"
M13_SUMMARY = "research/collatz/m15/m13/m13-prefix-summary-r2.json"
M20_README = "research/collatz/m20/README.md"
LEVELS = (
    {"name": "m15", "m": 15, "q": 9, "steps": 24, "expected_new": 173, "expected_shards": 23,
     "scan": "research/collatz/m15/scan/m15-prefix-scan.json", "package": "research/collatz/m15/package-manifest.json", "source_manifest": None},
    {"name": "m16", "m": 16, "q": 10, "steps": 26, "expected_new": 476, "expected_shards": 24,
     "scan": "research/collatz/m16/scan/m16-residual-affine-screen.json", "package": "research/collatz/m16/package-manifest.json", "source_manifest": "research/collatz/m16/lean/source-manifest.json"},
    {"name": "m18", "m": 18, "q": 11, "steps": 29, "expected_new": 961, "expected_shards": 49,
     "scan": "research/collatz/m18/scan/m18-residual-affine-screen.json", "package": "research/collatz/m18/package-manifest.json", "source_manifest": "research/collatz/m18/lean/source-manifest.json"},
    {"name": "m20", "m": 20, "q": 12, "steps": 32, "expected_new": 2652, "expected_shards": 133,
     "scan": "research/collatz/m20/scan/m20-residual-affine-screen.json", "package": "research/collatz/m20/package-manifest.json", "source_manifest": "research/collatz/m20/lean/source-manifest.json"},
)
TRACE_SPECS = (
    {"name": "M29Residue167", "source": "research/collatz/affine-trace/M29Residue167.lean",
     "receipt": "research/collatz/affine-trace/evidence/m29-residue167-attempt-3/attempt-receipt.json"},
    {"name": "M31Residue111", "source": "research/collatz/affine-trace/M31Residue111.lean",
     "receipt": "research/collatz/affine-trace/lean-check-receipt.json"},
    {"name": "M31Residue223", "source": "research/collatz/affine-trace/M31Residue223.lean",
     "receipt": "research/collatz/affine-trace/evidence/m31-residue223-attempt-1/attempt-receipt.json"},
)
EXPECTED_COVERAGE = {"m15": 31473, "m16": 63422, "m18": 254649, "m20": 1021248}
EXPECTED_COVERAGE_KEYS = {"m15": "combined_covered_mod_32768", "m16": "combined_covered_mod65536", "m18": "combined_covered_mod262144", "m20": "combined_covered_mod1048576"}


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


def bind_receipt_references(repo: Path, receipt_path: Path, receipt: dict[str, Any], inputs: dict[str, str]) -> None:
    records = receipt.get("bindings")
    if not isinstance(records, dict):
        records = {key: value for key, value in receipt.items() if isinstance(value, dict)}
    for value in records.values():
        if not isinstance(value, dict) or "path" not in value or "sha256" not in value:
            continue
        base = value.get("base", "repository")
        if base in ("repository", "repo"):
            target = repo / value["path"]
        elif base == "receipt_directory":
            target = receipt_path.parent / value["path"]
        else:
            raise ValueError(f"unsupported receipt reference base: {base}")
        digest = bind(repo, target, inputs)
        if digest != value["sha256"]:
            raise ValueError(f"receipt-bound input hash mismatch: {value['path']}")


def find_definition(lean: str, name: str) -> str:
    marker = f"def {name} (r : Nat) : Bool :="
    start = lean.find(marker)
    if start < 0:
        raise ValueError(f"missing M13 predicate definition {name}")
    end = lean.find("\n\n", start)
    return lean[start:end if end >= 0 else len(lean)]


def m13_covered_residues(lean: str) -> set[int]:
    conditions: list[tuple[int, int]] = []
    for name in ("eligibleResidue", "eligibleResidue256", "eligibleResidue4096", "eligibleResidue8192"):
        body = find_definition(lean, name)
        conditions.extend((int(modulus), int(value)) for modulus, value in re.findall(r"r % (\d+) = (\d+)", body))
        if name == "eligibleResidue8192":
            match = re.search(r"\[([0-9, ]+)\]\.contains", body)
            if not match:
                raise ValueError("could not parse the saved M13 final residue list")
            conditions.extend((8192, int(value.strip())) for value in match.group(1).split(","))
    if not conditions:
        raise ValueError("M13 eligibility parser found no modular conditions")
    return {r for r in range(8192) if any(r % modulus == value for modulus, value in conditions)}


def level_manifest_modules(repo: Path, level: dict[str, Any], package: dict[str, Any], source_manifest: dict[str, Any] | None, inputs: dict[str, str]) -> dict[int, dict[str, Any]]:
    level_name = level["name"]
    package_rel = level["package"]
    package_path = repo / package_rel
    package_files = {row["path"]: row["sha256"] for row in package.get("files", [])}
    modules = package.get("modules", []) if level_name == "m15" else (source_manifest or {}).get("modules", [])
    if not modules:
        raise ValueError(f"{level_name} source manifest contains no shard modules")
    result: dict[int, dict[str, Any]] = {}
    for module in modules:
        module_name = module["module"]
        source_rel_in_package = module["source"]
        source_repo_rel = f"research/collatz/{level_name}/{source_rel_in_package}"
        source_path = repo / source_repo_rel
        source_hash = bind(repo, source_path, inputs)
        if source_hash != module.get("source_sha256"):
            raise ValueError(f"{level_name} source-manifest hash mismatch for {module_name}")
        if package_files.get(source_rel_in_package) != source_hash:
            raise ValueError(f"{level_name} package hash mismatch for {module_name} source")
        if level_name == "m15":
            receipt_rel_in_package = module["receipt"]
        else:
            basenames = {f"{module_name}.json", f"{module_name}.receipt.json"}
            candidates = [rel for rel in package_files if Path(rel).name in basenames]
            if len(candidates) != 1:
                raise ValueError(f"{level_name} expected one shard receipt for {module_name}, got {len(candidates)}")
            receipt_rel_in_package = candidates[0]
        receipt_repo_rel = f"research/collatz/{level_name}/{receipt_rel_in_package}"
        receipt_path = repo / receipt_repo_rel
        receipt_hash = bind(repo, receipt_path, inputs)
        if package_files.get(receipt_rel_in_package) != receipt_hash:
            raise ValueError(f"{level_name} package hash mismatch for {module_name} receipt")
        _, receipt = read_json(receipt_path)
        if receipt.get("exit_code") != 0:
            raise ValueError(f"{level_name} shard receipt is not exit 0: {module_name}")
        if receipt.get("source_sha256") not in (None, source_hash):
            raise ValueError(f"{level_name} receipt binds a different source for {module_name}")
        source_text = source_path.read_text(encoding="utf-8", errors="strict")
        theorem_names = module.get("theorem_names", [])
        residue_to_theorem = {}
        if theorem_names:
            for residue, theorem in zip(module.get("residues", []), theorem_names, strict=True):
                residue_to_theorem[int(residue)] = theorem
        for residue in module.get("residues", []):
            residue = int(residue)
            theorem = residue_to_theorem.get(residue, f"descent_mod{1 << level['m']}_{residue}")
            if not re.search(rf"\btheorem\s+{re.escape(theorem)}\b", source_text):
                raise ValueError(f"{level_name} Lean source lacks expected theorem {theorem}")
            if residue in result:
                raise ValueError(f"duplicate residue in {level_name} source manifests: {residue}")
            result[residue] = {
                "module": module_name,
                "theorem": theorem,
                "source_path": source_repo_rel,
                "source_sha256": source_hash,
                "receipt_path": receipt_repo_rel,
                "receipt_sha256": receipt_hash,
                "receipt_exit_code": 0,
            }
    return result


def exact_power_exponent(value: int, base: int) -> int:
    count = 0
    remaining = value
    while remaining > 1 and remaining % base == 0:
        remaining //= base
        count += 1
    if remaining != 1:
        raise ValueError(f"{value} is not an exact power of {base}")
    return count


def normalize_family(level: dict[str, Any], row: dict[str, Any], source: dict[str, Any], scan_rel: str, scan_sha: str) -> dict[str, Any]:
    m, q = level["m"], level["q"]
    modulus, residue = 1 << m, int(row["r"])
    endpoint_a, endpoint_b = int(row["endpoint_a"]), int(row["endpoint_b"])
    if row.get("m") != m or row.get("modulus") != modulus or row.get("steps") != level["steps"]:
        raise ValueError(f"{level['name']} scan row has a different modulus or step count")
    if endpoint_a != 3 ** q or level["steps"] != m + q:
        raise ValueError(f"{level['name']} row does not match the common exact affine template")
    if row.get("strict_gap_coeff") != modulus - endpoint_a or row.get("strict_gap_const") != residue - endpoint_b:
        raise ValueError(f"{level['name']} row has inconsistent strict-descent gap")
    gap_a, gap_b = modulus - endpoint_a, residue - endpoint_b
    if gap_a <= 0 or gap_b <= 0:
        raise ValueError(f"{level['name']} row does not descend for every k >= 0")
    word = row.get("parity_word")
    if word is not None and (len(word) != level["steps"] or word.count("O") != q or word.count("E") != m):
        raise ValueError(f"{level['name']} parity word does not match odd/even step counts")
    return {
        "family_id": f"{level['name']}-r{residue}",
        "level": level["name"],
        "modulus_exponent": m,
        "modulus": modulus,
        "residue": residue,
        "odd_steps": q,
        "standard_steps": level["steps"],
        "endpoint_coefficient": endpoint_a,
        "endpoint_intercept": endpoint_b,
        "descent_gap_coefficient": gap_a,
        "descent_gap_intercept": gap_b,
        "input_formula": f"2^{m}*k + {residue}",
        "iterate_formula": f"C^{level['steps']}(2^{m}*k + {residue}) = 3^{q}*k + {endpoint_b}",
        "descent_formula": f"(2^{m} - 3^{q})*k + ({residue} - {endpoint_b}) = {gap_a}*k + {gap_b} > 0",
        "parity_word": word,
        "scan_path": scan_rel,
        "scan_sha256": scan_sha,
        **source,
    }


def lift_and_add(previous: bytearray, old_modulus: int, new_modulus: int, new_residues: set[int]) -> tuple[bytearray, int]:
    if len(previous) != old_modulus or new_modulus % old_modulus:
        raise ValueError("coverage lift dimensions are invalid")
    lifted = bytearray(new_modulus)
    factor = new_modulus // old_modulus
    for residue, covered in enumerate(previous):
        if covered:
            for copy in range(factor):
                lifted[residue + copy * old_modulus] = 1
    overlap = 0
    for residue in new_residues:
        if not 0 <= residue < new_modulus:
            raise ValueError("new family residue is outside its modulus")
        if lifted[residue]:
            overlap += 1
        lifted[residue] = 1
    return lifted, overlap


def parse_trace(repo: Path, spec: dict[str, str], inputs: dict[str, str]) -> dict[str, Any]:
    source_path = repo / spec["source"]
    source_hash = bind(repo, source_path, inputs)
    source_text = source_path.read_text(encoding="utf-8", errors="strict")
    match = re.search(
        r"theorem\s+universalDescent\s*:\s*∀ k : Nat,\s*iterate\s*\((\d+)\s*\* k \+ (\d+)\)\s+(\d+)\s*=\s*(\d+)\s*\* k \+ (\d+)\s*∧\s*(\d+)\s*\* k \+ (\d+)\s*<\s*(\d+)\s*\* k \+ (\d+)",
        source_text,
        re.S,
    )
    if not match:
        raise ValueError(f"could not parse exact affine theorem from {spec['source']}")
    modulus, residue, steps, slope, intercept, inequality_slope, inequality_intercept, start_slope, start_intercept = map(int, match.groups())
    exponent = exact_power_exponent(modulus, 2)
    odd_steps = exact_power_exponent(slope, 3)
    gap_slope = modulus - slope
    gap_intercept = residue - intercept
    if steps != exponent + odd_steps or (inequality_slope, inequality_intercept) != (slope, intercept):
        raise ValueError(f"{spec['name']} theorem does not fit the standard exact affine descent identity")
    if gap_slope <= 0 or gap_intercept <= 0 or (start_slope, start_intercept) != (modulus, residue):
        raise ValueError(f"{spec['name']} theorem's strict-descent inequality is inconsistent")
    receipt_path = repo / spec["receipt"]
    receipt_hash = bind(repo, receipt_path, inputs)
    _, receipt = read_json(receipt_path)
    if receipt.get("status") != "PASS_FINITE_FAMILY_ONLY":
        raise ValueError(f"{spec['name']} receipt is not a finite-family pass")
    if spec["name"] == "M31Residue111":
        binding = receipt.get("certificate_source", {})
        execution = receipt.get("execution", {})
        if binding.get("path") != spec["source"] or binding.get("sha256") != source_hash:
            raise ValueError("M31 residue-111 receipt does not bind current theorem source")
        if execution.get("network") != "none":
            raise ValueError("M31 residue-111 receipt does not report network disabled")
    else:
        execution = receipt.get("execution", {})
        family = receipt.get("family", {})
        binding = receipt.get("bindings", {}).get("certificate_source", {})
        expected_family = {"modulus": modulus, "residue": residue, "steps": steps, "endpoint_slope": slope, "endpoint_intercept": intercept, "strict_gap_slope": gap_slope, "strict_gap_intercept": gap_intercept}
        if any(family.get(key) != value for key, value in expected_family.items()):
            raise ValueError(f"{spec['name']} receipt family differs from Lean source")
        if binding.get("path") != spec["source"] or binding.get("sha256") != source_hash:
            raise ValueError(f"{spec['name']} receipt does not bind current theorem source")
        if execution.get("exit_code") != 0 or execution.get("network") != "none" or execution.get("timed_out") is True:
            raise ValueError(f"{spec['name']} receipt has nonqualifying execution metadata")
    bind_receipt_references(repo, receipt_path, receipt, inputs)
    projected = residue % (1 << 20)
    return {
        "family_id": spec["name"],
        "modulus_exponent": exponent,
        "modulus": modulus,
        "residue": residue,
        "odd_steps": odd_steps,
        "standard_steps": steps,
        "endpoint_coefficient": slope,
        "endpoint_intercept": intercept,
        "descent_gap_coefficient": gap_slope,
        "descent_gap_intercept": gap_intercept,
        "m20_projection_residue": projected,
        "m20_projection_covered_by_saved_union": None,
        "classes_at_modulus_2^31": (1 << (31 - exponent)) if exponent <= 31 else 0,
        "source_path": spec["source"],
        "source_sha256": source_hash,
        "receipt_path": spec["receipt"],
        "receipt_sha256": receipt_hash,
        "receipt_status": receipt["status"],
        "source_use_note": receipt.get("source_use", ""),
    }


def derive(repo: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, str]]:
    inputs: dict[str, str] = {}
    m13_lean_path = repo / M13_LEAN
    m13_lean_hash = bind(repo, m13_lean_path, inputs)
    m13_lean_text = m13_lean_path.read_text(encoding="utf-8", errors="strict")
    m13_summary_path = repo / M13_SUMMARY
    m13_summary_bytes, m13_summary = read_json(m13_summary_path)
    m13_summary_hash = bind(repo, m13_summary_path, inputs)
    m20_readme_path = repo / M20_README
    m20_readme_hash = bind(repo, m20_readme_path, inputs)
    if "97.395%" not in m20_readme_path.read_text(encoding="utf-8", errors="strict"):
        raise ValueError("the recorded M20 README percentage changed; review the rounding note")
    if m13_summary.get("source_sha256") != m13_lean_hash:
        raise ValueError("M13 summary does not bind its exact Lean source")
    seed = m13_covered_residues(m13_lean_text)
    if len(seed) != 7825 or m13_summary.get("covered") != len(seed) or m13_summary.get("denominator") != 8192:
        raise ValueError("M13 exact eligibility set differs from its accepted summary")
    coverage = bytearray(1 << 13)
    for residue in seed:
        coverage[residue] = 1
    previous_modulus = 1 << 13
    family_rows: list[dict[str, Any]] = []
    level_summaries = []
    level_inputs: dict[str, dict[str, Any]] = {}
    previous_level_name: str | None = None

    for level in LEVELS:
        package_path = repo / level["package"]
        package_raw, package = read_json(package_path)
        package_hash = bind(repo, package_path, inputs)
        source_manifest = None
        if level["source_manifest"]:
            source_manifest_path = repo / level["source_manifest"]
            _, source_manifest = read_json(source_manifest_path)
            bind(repo, source_manifest_path, inputs)
        scan_path = repo / level["scan"]
        _, scan = read_json(scan_path)
        scan_hash = bind(repo, scan_path, inputs)
        package_file_hashes = {row["path"]: row["sha256"] for row in package.get("files", [])}
        scan_rel_package = Path(level["scan"]).relative_to(Path(level["package"]).parent).as_posix()
        if package_file_hashes.get(scan_rel_package) != scan_hash:
            raise ValueError(f"{level['name']} package manifest does not bind its scan")
        if package.get("scan_sha256") and package["scan_sha256"] != scan_hash:
            raise ValueError(f"{level['name']} declared scan digest mismatch")
        if source_manifest and source_manifest.get("screen_sha256") != scan_hash:
            raise ValueError(f"{level['name']} Lean source manifest binds another scan")
        if level["name"] == "m15":
            if scan.get("accepted_m13_summary_sha256") != m13_summary_hash:
                raise ValueError("M15 scan does not bind the M13 summary")
            new_rows = scan.get("families", [])
            declared_new = scan.get("new_families")
        else:
            baseline = scan.get("baseline_inputs", {})
            if baseline.get("m13_summary_sha256") != m13_summary_hash:
                raise ValueError(f"{level['name']} scan does not bind the M13 summary")
            if previous_level_name is None:
                raise ValueError(f"{level['name']} has no preceding scan")
            previous_scan_hash = level_inputs[previous_level_name]["scan_sha256"]
            if baseline.get(f"{previous_level_name}_scan_sha256") != previous_scan_hash:
                raise ValueError(f"{level['name']} baseline does not bind the preceding scan")
            new_rows = scan.get("families", [])
            declared_new = scan.get("search", {}).get("new_affine_descent_families")
        if declared_new != level["expected_new"] or len(new_rows) != level["expected_new"]:
            raise ValueError(f"{level['name']} family count differs from the frozen expected count")
        modules = level_manifest_modules(repo, level, package, source_manifest, inputs)
        shard_module_count = len(package.get("modules", [])) if level["name"] == "m15" else len((source_manifest or {}).get("modules", []))
        if shard_module_count != level["expected_shards"]:
            raise ValueError(f"{level['name']} shard-module count differs from its source manifest")
        scan_residues = {int(row["r"]) for row in new_rows}
        if len(scan_residues) != len(new_rows) or set(modules) != scan_residues:
            raise ValueError(f"{level['name']} Lean source modules and affine scan rows do not match exactly")
        new_modulus = 1 << level["m"]
        lifted, overlap = lift_and_add(coverage, previous_modulus, new_modulus, scan_residues)
        if overlap:
            raise ValueError(f"{level['name']} new family rows overlap the lifted prior set")
        for row in sorted(new_rows, key=lambda item: int(item["r"])):
            family_rows.append(normalize_family(level, row, modules[int(row["r"])], level["scan"], scan_hash))
        covered_count = sum(lifted)
        package_expected = package.get("expected", {})
        coverage_key = EXPECTED_COVERAGE_KEYS[level["name"]]
        if package_expected.get(coverage_key) != covered_count or covered_count != EXPECTED_COVERAGE[level["name"]]:
            raise ValueError(f"{level['name']} coverage total differs from package manifest")
        previous_coverage = int(covered_count - len(scan_residues))
        level_summaries.append({
            "level": level["name"],
            "modulus": new_modulus,
            "new_families": len(scan_residues),
            "previous_coverage_lifted": previous_coverage,
            "new_families_disjoint": True,
            "combined_coverage": covered_count,
            "outside_classes": new_modulus - covered_count,
            "coverage_percent_exact_decimal": format(Decimal(100 * covered_count) / Decimal(new_modulus), ".12f"),
            "odd_steps": level["q"],
            "standard_steps": level["steps"],
            "endpoint_coefficient": 3 ** level["q"],
            "descent_gap_coefficient": new_modulus - 3 ** level["q"],
            "shard_modules": shard_module_count,
        })
        level_inputs[level["name"]] = {"scan_sha256": scan_hash, "package_sha256": package_hash}
        previous_level_name = level["name"]
        coverage = lifted
        previous_modulus = new_modulus

    if len(family_rows) != sum(level["expected_new"] for level in LEVELS):
        raise ValueError("normalized basis row count differs from M15-M20 scan totals")
    trace_rows = [parse_trace(repo, spec, inputs) for spec in TRACE_SPECS]
    trace_classes: set[int] = set()
    for row in trace_rows:
        covered = bool(coverage[row["m20_projection_residue"]])
        row["m20_projection_covered_by_saved_union"] = covered
        if covered:
            raise ValueError(f"{row['family_id']} projects into a previously covered M20 class; projection analysis changed")
        exponent = row["modulus_exponent"]
        lifted_residues = [row["residue"] + copy * (1 << exponent) for copy in range(1 << (31 - exponent))]
        if any(residue % (1 << 20) != row["m20_projection_residue"] for residue in lifted_residues):
            raise ValueError(f"{row['family_id']} modulus-2^31 lifts are inconsistent")
        if trace_classes.intersection(lifted_residues):
            raise ValueError("the three sparse families overlap at modulus 2^31")
        trace_classes.update(lifted_residues)
        row["modulus_2^31_residue_classes"] = lifted_residues
        row["all_lifts_outside_m20_union"] = True
    m20_covered = sum(coverage)
    m20_lift_factor = (1 << 11)
    combined_2_31 = m20_covered * m20_lift_factor + len(trace_classes)
    basis_bytes = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8") for row in family_rows)
    traces_bytes = (json.dumps(trace_rows, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    protocol_hash = bind(repo, repo / PROTOCOL, inputs)
    summary = {
        "schema": "mathcase-collatz-m15-m20-affine-basis-summary-v1",
        "classification": "DERIVED_EXACT_FINITE_AFFINE_INDEX_AND_COVERAGE_AUDIT",
        "status": "PASS_HASH_BOUND_AFFINE_BASIS_AUDIT",
        "m13_seed": {"modulus": 1 << 13, "covered": len(seed), "affine_family_rows_in_summary": len(m13_summary.get("m13_families", []))},
        "levels": level_summaries,
        "m15_m20_new_affine_family_rows": len(family_rows),
        "m15_m20_shard_modules": sum(row["shard_modules"] for row in level_summaries),
        "common_template": "For each listed family at modulus 2^m, C^(m+q)(2^m*k+r)=3^q*k+b_r and the exact positive gap is (2^m-3^q)*k+(r-b_r), for every k>=0.",
        "sparse_trace_comparison": {
            "families": len(trace_rows),
            "all_three_project_to_m20_classes_outside_saved_union": all(not row["m20_projection_covered_by_saved_union"] for row in trace_rows),
            "new_modulus_2^31_residue_classes": len(trace_classes),
            "m20_coverage_lifted_to_modulus_2^31": m20_covered * m20_lift_factor,
            "combined_coverage_after_three_sparse_families": combined_2_31,
            "remaining_classes_at_modulus_2^31": (1 << 31) - combined_2_31,
            "coverage_percent": format(Decimal(100 * combined_2_31) / Decimal(1 << 31), ".12f"),
            "interpretation": "The three Lean-checked families share the exact affine template but are sparse additions outside the saved M20 residue union; they do not compress the M15-M20 proof set.",
        },
        "m20_percent_rounding_audit": {
            "m20_readme_text": "97.395%",
            "m20_readme_sha256": m20_readme_hash,
            "exact_fraction": f"{m20_covered}/{1 << 20}",
            "exact_percent": format(Decimal(100 * m20_covered) / Decimal(1 << 20), ".12f"),
            "rounded_to_three_decimal_places": format((Decimal(100 * m20_covered) / Decimal(1 << 20)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP), ".3f") + "%",
            "disposition": "The README percentage is inconsistent with its exact count; this derived report records the correction and leaves the historical package files untouched.",
        },
        "input_sha256": inputs,
        "outputs_sha256": {"family_basis_jsonl": sha(basis_bytes), "sparse_trace_comparison_json": sha(traces_bytes)},
        "limits": [
            "This is a derived index and residue-set audit over saved, hash-bound scans and source manifests; it does not rerun a trajectory search or compile Lean.",
            "Existing shard receipts are reused as provenance and are not fresh replays or M4 receipts.",
            "The common affine template reorganizes the theorem data; it does not reduce the number of independently checked family statements or prove a global Collatz result.",
            "The three higher-modulus affine families add six residue classes at modulus 2^31; the density change is negligible and they do not imply convergence or novelty.",
            "The M20 aggregate/M4/publication state is not changed by this analysis.",
        ],
        "external_calls": 0,
        "cost_usd": 0,
        "lean_compiled": False,
        "trajectory_rescan_performed": False,
        "m4_promoted": False,
    }
    return family_rows, trace_rows, summary, inputs


def execute(repo: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    try:
        families, traces, summary, inputs = derive(repo)
        basis_bytes = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8") for row in families)
        traces_bytes = (json.dumps(traces, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        summary_bytes = (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        basis_path = output / "family-basis.jsonl"
        traces_path = output / "sparse-trace-comparison.json"
        summary_path = output / "summary.json"
        basis_path.write_bytes(basis_bytes)
        traces_path.write_bytes(traces_bytes)
        summary_path.write_bytes(summary_bytes)
        derivation_path = Path(__file__).resolve()
        verifier_path = repo / "scripts/verify_collatz_m15_m20_affine_basis_v1.py"
        protocol_path = repo / PROTOCOL
        manifest = {
            "schema": "mathcase-collatz-m15-m20-affine-basis-manifest-v1",
            "status": summary["status"],
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "protocol_path": PROTOCOL,
            "protocol_sha256": file_sha(protocol_path),
            "derivation_script_path": derivation_path.relative_to(repo).as_posix(),
            "derivation_script_sha256": file_sha(derivation_path),
            "verification_script_path": verifier_path.relative_to(repo).as_posix(),
            "verification_script_sha256": file_sha(verifier_path),
            "outputs": {"family-basis.jsonl": sha(basis_bytes), "sparse-trace-comparison.json": sha(traces_bytes), "summary.json": sha(summary_bytes)},
            "input_sha256": inputs,
            "family_rows": len(families),
            "shard_modules": summary["m15_m20_shard_modules"],
            "sparse_trace_families": len(traces),
            "external_calls": 0,
            "cost_usd": 0,
            "lean_compiled": False,
            "trajectory_rescan_performed": False,
            "m4_promoted": False,
        }
        manifest_path = output / "run-manifest.json"
        manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return manifest
    except Exception as exc:
        failure = {
            "schema": "mathcase-collatz-m15-m20-affine-basis-failure-v1",
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
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / OUTPUT)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    output = args.output_dir.resolve(strict=False)
    if output.exists():
        parser.error("output directory exists; refusing overwrite")
    try:
        manifest = execute(repo, output)
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        parser.exit(2, f"derivation blocked; failure receipt preserved: {exc}\n")
    print(json.dumps({"status": manifest["status"], "family_rows": manifest["family_rows"], "output_dir": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
