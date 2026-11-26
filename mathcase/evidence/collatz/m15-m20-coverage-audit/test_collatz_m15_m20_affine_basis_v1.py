#!/usr/bin/env python3
"""Focused tests for the M15–M20 affine-family basis derivation."""

from __future__ import annotations

import unittest
from pathlib import Path

from derive_collatz_m15_m20_affine_basis_v1 import (
    exact_power_exponent,
    lift_and_add,
    m13_covered_residues,
    normalize_family,
)


ROOT = Path(__file__).resolve().parents[1]


class AffineBasisTests(unittest.TestCase):
    def test_saved_m13_predicate_reconstructs_the_exact_finite_count(self) -> None:
        source = (ROOT / "research/collatz/m15/lean/BoundedDescentPlusM13.lean").read_text(encoding="utf-8")
        self.assertEqual(len(m13_covered_residues(source)), 7825)

    def test_exact_power_exponent_rejects_nonpowers(self) -> None:
        self.assertEqual(exact_power_exponent(3**12, 3), 12)
        self.assertEqual(exact_power_exponent(2**20, 2), 20)
        with self.assertRaises(ValueError):
            exact_power_exponent(531440, 3)

    def test_family_normalization_preserves_exact_identity_and_positive_gap(self) -> None:
        level = {"name": "m20", "m": 20, "q": 12, "steps": 32}
        scan_row = {
            "m": 20, "modulus": 1 << 20, "r": 239, "steps": 32,
            "endpoint_a": 3**12, "endpoint_b": 122,
            "strict_gap_coeff": (1 << 20) - 3**12, "strict_gap_const": 117,
        }
        source = {"module": "M20Shard001", "theorem": "descent_mod1048576_239", "source_path": "src.lean", "source_sha256": "s", "receipt_path": "receipt.json", "receipt_sha256": "r", "receipt_exit_code": 0}
        result = normalize_family(level, scan_row, source, "scan.json", "h")
        self.assertEqual(result["iterate_formula"], "C^32(2^20*k + 239) = 3^12*k + 122")
        self.assertEqual(result["descent_gap_coefficient"], 517135)
        self.assertEqual(result["descent_gap_intercept"], 117)

    def test_lifting_and_adding_requires_disjoint_residues(self) -> None:
        previous = bytearray(8)
        previous[1] = previous[5] = 1
        lifted, overlap = lift_and_add(previous, 8, 16, {3, 11})
        self.assertEqual(sum(lifted), 6)
        self.assertEqual(overlap, 0)
        _, overlap = lift_and_add(previous, 8, 16, {1})
        self.assertEqual(overlap, 1)


if __name__ == "__main__":
    unittest.main()
